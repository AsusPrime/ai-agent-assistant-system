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
    description: str = ""
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


# --- Settings ---


class SettingsResponse(BaseModel):
    LLM_PROVIDER: str
    MODEL_NAME: str
    DEBUG: bool
    API_AUTO_APPROVE: bool
    REACT_MAX_ITERATIONS: int
    MEMORY_TURNS: int
    WEB_TIMEOUT: float
    HTTP_TIMEOUT: float
    MCP_CALL_TIMEOUT: float
    UI_SHOW_LOGS: bool
    UI_TAMAGOTCHI: bool
    UI_AUTO_APPROVE: bool
    UI_MAX_VISIBLE_TASKS: int
    UI_SUMMARY_DELAY_MS: int
    UI_FONT_SIZE: int
    UI_LANGUAGE: str


class SettingsUpdateRequest(BaseModel):
    LLM_PROVIDER: str | None = None
    MODEL_NAME: str | None = None
    DEBUG: bool | None = None
    API_AUTO_APPROVE: bool | None = None
    REACT_MAX_ITERATIONS: int | None = None
    MEMORY_TURNS: int | None = None
    WEB_TIMEOUT: float | None = None
    HTTP_TIMEOUT: float | None = None
    MCP_CALL_TIMEOUT: float | None = None
    UI_SHOW_LOGS: bool | None = None
    UI_TAMAGOTCHI: bool | None = None
    UI_AUTO_APPROVE: bool | None = None
    UI_MAX_VISIBLE_TASKS: int | None = None
    UI_SUMMARY_DELAY_MS: int | None = None
    UI_FONT_SIZE: int | None = None
    UI_LANGUAGE: str | None = None
