import sqlite3
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
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


_state: dict = {} # TODO: why do we need it?


def _build_core() -> AkashiCore:
    auto_approve = settings.API_AUTO_APPROVE
    confirm_fn = (lambda _msg: True) if auto_approve else (lambda _msg: False)
    messages: list[str] = []
    core = AkashiCore(confirm_fn=confirm_fn, on_message=messages.append)
    _state["messages_buffer"] = messages
    return core


@asynccontextmanager
async def lifespan(_app: FastAPI):
    _state["core"] = _build_core()
    _state["started_at"] = time.monotonic()
    yield
    _state.clear()


app = FastAPI(title="Akashi API", version="0.1.0", lifespan=lifespan)


def _get_core() -> AkashiCore:
    core = _state.get("core")
    if core is None:
        raise HTTPException(status_code=503, detail="core not initialized")
    return core


@app.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest) -> QueryResponse:
    core = _get_core()
    buf: list[str] = _state["messages_buffer"]
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
async def status() -> StatusResponse:
    core = _get_core()
    uptime = time.monotonic() - _state.get("started_at", time.monotonic())
    return StatusResponse(
        status="ok",
        session_id=core.session.session_id,
        uptime_seconds=round(uptime, 2),
        history_turns=len(core.session.message_history),
        auto_approve=settings.API_AUTO_APPROVE,
    )


@app.get("/history", response_model=HistoryResponse)
async def history(limit: int = 10) -> HistoryResponse:
    core = _get_core()
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
