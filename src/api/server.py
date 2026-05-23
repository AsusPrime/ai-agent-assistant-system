import sqlite3
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.concurrency import run_in_threadpool

from api.schemas import (
    ExecuteResponse,
    ExecuteSingleRequest,
    ExecuteSingleResponse,
    HistoryResponse,
    HistoryTurn,
    PlanRequest,
    PlanResponse,
    PlanTask,
    QueryRequest,
    QueryResponse,
    RecipeListResponse,
    RecipeRunRequest,
    RecipeSaveRequest,
    SettingsResponse,
    SettingsUpdateRequest,
    StatusResponse,
    StepRequest,
    StepResponse,
    TaskExecution,
)
from config import settings
from core.assistant import AssistantCore
from core.recipe_loader import Recipe, list_recipes, load_recipe, save_recipe
from core.requirements import check_requirements
from core.schemas import Plan, Task


def _build_core() -> tuple[AssistantCore, list[str]]:
    def confirm_fn(_msg: str) -> bool:
        return settings.API_AUTO_APPROVE

    messages: list[str] = []
    core = AssistantCore(confirm_fn=confirm_fn, on_message=messages.append)
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


app = FastAPI(title="AI Assistant API", version="0.1.0", lifespan=lifespan)


def _get_core(request: Request) -> AssistantCore:
    core: AssistantCore | None = getattr(request.app.state, "core", None)
    if core is None:
        raise HTTPException(status_code=503, detail="core not initialized")
    return core


@app.post("/plan", response_model=PlanResponse)
async def plan(req: QueryRequest, request: Request) -> PlanResponse:
    core = _get_core(request)
    buf: list[str] = request.app.state.messages_buffer
    buf.clear()

    try:
        plan_obj, reply = await run_in_threadpool(core.plan_only, req.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"planning failed: {e}")

    if reply is not None:
        return PlanResponse(reply=reply, messages=list(buf))

    if plan_obj is None:
        return PlanResponse(messages=list(buf))

    tasks = [
        PlanTask(
            action=t.action.value,
            name=t.name,
            description=t.description,
            params=t.params,
        )
        for t in plan_obj.tasks
    ]
    return PlanResponse(tasks=tasks, reasoning=plan_obj.reasoning, messages=list(buf))


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
        results = await run_in_threadpool(core.execute_plan, plan, True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"execution failed: {e}")

    summary = None
    if req.query:
        try:
            summary = await run_in_threadpool(core.summarize, req.query, results)
        except Exception as e:
            buf.append(f"[Summary Error] {e}")

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
    return ExecuteResponse(tasks=tasks, summary=summary, messages=list(buf))


@app.post("/step", response_model=StepResponse)
async def react_step(req: StepRequest, request: Request) -> StepResponse:
    core = _get_core(request)
    buf: list[str] = request.app.state.messages_buffer
    buf.clear()

    observations = [o.model_dump() for o in req.observations]

    try:
        task, reply = await run_in_threadpool(core.react_step, req.text, observations)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"step failed: {e}")

    if reply is not None:
        return StepResponse(reply=reply, done=True, messages=list(buf))

    if task is None:
        error_reply = next(
            (m for m in buf if "[LLM Error]" in m or "[Memory]" in m), None
        )
        return StepResponse(reply=error_reply, done=True, messages=list(buf))

    return StepResponse(
        task=PlanTask(action=task.action.value, name=task.name, description=task.description, params=task.params),
        done=False,
        messages=list(buf),
    )


@app.post("/execute-single", response_model=ExecuteSingleResponse)
async def execute_single(
    req: ExecuteSingleRequest, request: Request
) -> ExecuteSingleResponse:
    core = _get_core(request)
    buf: list[str] = request.app.state.messages_buffer
    buf.clear()

    try:
        result = await run_in_threadpool(core.execute_single, req.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"execution failed: {e}")

    return ExecuteSingleResponse(
        action=result.task.action.value,
        name=result.task.name,
        status=result.status,
        stdout=result.stdout,
        stderr=result.stderr,
        returncode=result.returncode,
        skipped=result.skipped,
        duration_ms=result.duration_ms,
        messages=list(buf),
    )


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


_SETTINGS_FIELDS = [
    f.alias or name for name, f in SettingsUpdateRequest.model_fields.items()
]

_SECRET_KEYS = {"API_KEY"}


def _persist_env(updates: dict) -> None:
    from dotenv import find_dotenv

    env_path = find_dotenv(filename=".env", usecwd=True)
    if not env_path:
        env_path = str(Path.cwd().parent / ".env")

    path = Path(env_path)
    lines = path.read_text().splitlines() if path.exists() else []

    for key, value in updates.items():
        if key in _SECRET_KEYS:
            continue
        env_line = f"{key}={value}"
        found = False
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith(f"{key}=") or stripped.startswith(f"# {key}="):
                lines[i] = env_line
                found = True
                break
        if not found:
            lines.append(env_line)

    path.write_text("\n".join(lines) + "\n")


@app.get("/settings", response_model=SettingsResponse)
async def get_settings() -> SettingsResponse:
    return SettingsResponse(**{k: getattr(settings, k) for k in _SETTINGS_FIELDS})


@app.patch("/settings", response_model=SettingsResponse)
async def update_settings(req: SettingsUpdateRequest) -> SettingsResponse:
    updates = req.model_dump(exclude_none=True)
    for key, value in updates.items():
        setattr(settings, key, value)
    _persist_env(updates)
    return SettingsResponse(**{k: getattr(settings, k) for k in _SETTINGS_FIELDS})


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
