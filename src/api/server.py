import sqlite3
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.concurrency import run_in_threadpool

from api.schemas import (
    ExecuteResponse,
    HistoryResponse,
    HistoryTurn,
    PlanRequest,
    QueryRequest,
    QueryResponse,
    RecipeListResponse,
    RecipeRunRequest,
    RecipeSaveRequest,
    StatusResponse,
    TaskExecution,
)
from config import settings
from core.akashi import AkashiCore
from core.recipe_loader import Recipe, list_recipes, load_recipe, save_recipe
from core.requirements import check_requirements
from core.schemas import Plan, Task


def _build_core() -> tuple[AkashiCore, list[str]]:
    auto_approve = settings.API_AUTO_APPROVE
    confirm_fn = (lambda _msg: True) if auto_approve else (lambda _msg: False)
    messages: list[str] = []
    core = AkashiCore(confirm_fn=confirm_fn, on_message=messages.append)
    return core, messages


@asynccontextmanager
async def lifespan(app: FastAPI):
    core, messages = _build_core()
    app.state.core = core
    app.state.messages_buffer = messages
    app.state.started_at = time.monotonic()
    try:
        yield
    finally:
        core.close()
        app.state.core = None
        app.state.messages_buffer = []


app = FastAPI(title="Akashi API", version="0.1.0", lifespan=lifespan)


def _get_core(request: Request) -> AkashiCore:
    core: AkashiCore | None = getattr(request.app.state, "core", None)
    if core is None:
        raise HTTPException(status_code=503, detail="core not initialized")
    return core


@app.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest, request: Request) -> QueryResponse:
    core = _get_core(request)
    buf: list[str] = request.app.state.messages_buffer
    buf.clear()

    try:
        result = await run_in_threadpool(core.process_query, req.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"query failed: {e}")

    tasks = [
        TaskExecution(
            action=r.task.action.value,
            name=r.task.name,
            status=r.status,
            stdout=r.stdout,
            stderr=r.stderr,
            duration_ms=r.duration_ms,
        )
        for r in result.task_results
    ]
    return QueryResponse(
        reply=result.reply,
        summary=result.summary,
        tasks=tasks,
        messages=list(buf),
    )


@app.get("/status", response_model=StatusResponse)
async def status(request: Request) -> StatusResponse:
    core = _get_core(request)
    started_at = getattr(request.app.state, "started_at", time.monotonic())
    uptime = time.monotonic() - started_at
    return StatusResponse(
        status="ok",
        session_id=core.session.session_id,
        uptime_seconds=round(uptime, 2),
        history_turns=len(core.session.message_history),
        auto_approve=settings.API_AUTO_APPROVE,
    )


@app.get("/history", response_model=HistoryResponse)
async def history(request: Request, limit: int = 10) -> HistoryResponse:
    core = _get_core(request)
    db_path = core.msg_repo._db_path
    limit = max(1, min(limit, 100))
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT turn_index, turn_blob FROM messages "
            "WHERE session_id = ? ORDER BY ts DESC LIMIT ?",
            (core.session.session_id, limit),
        ).fetchall()

    turns: list[HistoryTurn] = []
    for turn_index, blob in rows:
        try:
            import json as _json

            parts = _json.loads(
                blob.decode("utf-8") if isinstance(blob, bytes) else blob
            )
        except Exception:
            parts = []
        turns.append(HistoryTurn(turn_index=turn_index, parts=parts))
    return HistoryResponse(turns=turns)


@app.post("/execute", response_model=ExecuteResponse)
async def execute_plan(req: PlanRequest, request: Request) -> ExecuteResponse:
    core = _get_core(request)
    buf: list[str] = request.app.state.messages_buffer
    buf.clear()

    plan = Plan(
        tasks=[Task(action=t.action, name=t.name, params=t.params) for t in req.tasks],
        reasoning=req.reasoning,
    )

    try:
        results = await run_in_threadpool(core.execute_plan, plan)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"execution failed: {e}")

    tasks = [
        TaskExecution(
            action=r.task.action.value,
            name=r.task.name,
            status=r.status,
            stdout=r.stdout,
            stderr=r.stderr,
            duration_ms=r.duration_ms,
        )
        for r in results
    ]
    return ExecuteResponse(tasks=tasks, messages=list(buf))


@app.get("/recipes", response_model=RecipeListResponse)
async def get_recipes() -> RecipeListResponse:
    return RecipeListResponse(recipes=list_recipes())


@app.post("/recipes", status_code=201)
async def create_recipe(req: RecipeSaveRequest) -> dict:
    from core.requirements import Requirement

    recipe = Recipe(
        tasks=[Task(action=t.action, name=t.name, params=t.params) for t in req.tasks],
        reasoning=req.reasoning,
        requirements=[Requirement(**r.model_dump()) for r in req.requirements],
    )
    path = save_recipe(req.name, recipe)
    return {"name": req.name, "path": str(path)}


@app.post("/recipes/{name}/run", response_model=ExecuteResponse)
async def run_recipe(
    name: str, request: Request, body: RecipeRunRequest | None = None
) -> ExecuteResponse:
    import os

    core = _get_core(request)
    buf: list[str] = request.app.state.messages_buffer
    buf.clear()

    try:
        recipe = load_recipe(name)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Recipe '{name}' not found")

    provided_vars = (body.variables if body else None) or {}
    for key, value in provided_vars.items():
        os.environ[key] = value

    if recipe.requirements:
        preflight = check_requirements(recipe.requirements)
        if not preflight.passed:
            raise HTTPException(status_code=422, detail=preflight.summary)

    try:
        results = await run_in_threadpool(core.execute_plan, recipe.to_plan())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"recipe execution failed: {e}")

    tasks = [
        TaskExecution(
            action=r.task.action.value,
            name=r.task.name,
            status=r.status,
            stdout=r.stdout,
            stderr=r.stderr,
            duration_ms=r.duration_ms,
        )
        for r in results
    ]
    return ExecuteResponse(tasks=tasks, messages=list(buf))


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
