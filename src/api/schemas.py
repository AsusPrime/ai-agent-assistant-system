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


class PlanTask(BaseModel):
    action: str
    name: str
    params: dict[str, str | list[str] | None] = {}


class PlanResponse(BaseModel):
    reply: str | None = None
    tasks: list[PlanTask] = []
    reasoning: str = ""
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


# --- Engine (direct plan execution) ---


class TaskInput(BaseModel):
    action: str
    name: str
    params: dict[str, str | list[str] | None] = {}


class PlanRequest(BaseModel):
    tasks: list[TaskInput]
    reasoning: str = ""
    query: str = ""


class ExecuteResponse(BaseModel):
    tasks: list[TaskExecution] = []
    summary: str | None = None
    messages: list[str] = []


# --- ReAct step-by-step ---


class StepObservation(BaseModel):
    action: str
    name: str
    params: dict[str, str | list[str] | None] = {}
    stdout: str = ""
    stderr: str = ""
    returncode: int = 0
    skipped: bool = False


class StepRequest(BaseModel):
    text: str = Field(min_length=1, max_length=8000)
    observations: list[StepObservation] = []


class StepResponse(BaseModel):
    task: PlanTask | None = None
    reply: str | None = None
    done: bool = False
    messages: list[str] = []


class ExecuteSingleRequest(BaseModel):
    action: str
    name: str
    params: dict[str, str | list[str] | None] = {}


class ExecuteSingleResponse(BaseModel):
    action: str
    name: str
    status: str
    stdout: str = ""
    stderr: str = ""
    returncode: int = 0
    skipped: bool = False
    duration_ms: int = 0
    messages: list[str] = []


# --- Recipes ---


class RecipeListResponse(BaseModel):
    recipes: list[str]


class RequirementInput(BaseModel):
    type: str
    name: str
    description: str = ""
    optional: bool = False


class RecipeSaveRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    tasks: list[TaskInput]
    reasoning: str = ""
    requirements: list[RequirementInput] = []


class RecipeRunRequest(BaseModel):
    variables: dict[str, str] = {}
