from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    text: str = Field(min_length=1, max_length=8000)


class TaskExecution(BaseModel):
    action: str
    name: str
    status: str
    stdout: str = ""
    stderr: str = ""
    duration_ms: int = 0


class QueryResponse(BaseModel):
    reply: str | None = None
    summary: str | None = None
    tasks: list[TaskExecution] = []
    messages: list[str] = []


class StatusResponse(BaseModel):
    status: str
    session_id: str
    uptime_seconds: float
    history_turns: int
    auto_approve: bool


class HistoryTurn(BaseModel):
    turn_index: int
    parts: list[dict]


class HistoryResponse(BaseModel):
    turns: list[HistoryTurn]
