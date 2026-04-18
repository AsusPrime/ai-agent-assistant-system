import sqlite3
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.concurrency import run_in_threadpool

from api.schemas import (
    HistoryResponse,
    HistoryTurn,
    QueryRequest,
    QueryResponse,
    StatusResponse,
    TaskExecution,
)
from config import settings
from core.akashi import AkashiCore


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
    yield
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

            parts = _json.loads(blob.decode("utf-8") if isinstance(blob, bytes) else blob)
        except Exception:
            parts = []
        turns.append(HistoryTurn(turn_index=turn_index, parts=parts))
    return HistoryResponse(turns=turns)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
