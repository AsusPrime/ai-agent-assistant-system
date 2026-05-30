import json
from pathlib import Path
from pydantic import BaseModel, Field, model_validator
from typing import Dict

from core.enums import ActionTypeEnum

# src/core/schemas.py → src/tools/whitelist.json
_WHITELIST_PATH = Path(__file__).resolve().parent.parent / "tools" / "whitelist.json"


class Task(BaseModel):
    action: ActionTypeEnum
    name: str = Field(
        description="For action='chat': the FULL reply text the user will see. "
        "For other actions: the command, app name, or tool name to execute."
    )
    description: str = Field(
        default="",
        description="Short human-readable description of what this step does, "
        "in the same language the user used. "
        "Examples: 'Searching the web', 'Installing a tool', 'Reading a file'. "
        "Displayed to the user in the UI.",
    )
    params: Dict[str, str | list[str] | None] = {}

    @model_validator(mode="after")
    def check_allowed(self) -> "Task":
        if self.action == ActionTypeEnum.CHAT:
            return self
        if self.action in (
            ActionTypeEnum.RUN_COMMAND,
            ActionTypeEnum.WRITE_FILE,
            ActionTypeEnum.READ_FILE,
            ActionTypeEnum.SEARCH_KNOWLEDGE,
            ActionTypeEnum.INDEX_KNOWLEDGE,
            ActionTypeEnum.WEB_SEARCH,
            ActionTypeEnum.IMAGE_SEARCH,
            ActionTypeEnum.WEB_READ,
            ActionTypeEnum.HTTP_REQUEST,
            ActionTypeEnum.MCP_CALL,
            ActionTypeEnum.SYSTEM_CONTROL,
            ActionTypeEnum.SAVE_RECIPE,
            ActionTypeEnum.RUN_RECIPE,
            ActionTypeEnum.LIST_RECIPES,
        ):
            return self  # any command/file allowed; HITL is the safety net
        with open(_WHITELIST_PATH) as f:
            wl = json.load(f)
        mapping = {
            ActionTypeEnum.OPEN_APP: wl["allowed_apps"],
        }
        allowed = mapping[self.action]
        if self.name not in allowed:
            raise ValueError(f"'{self.name}' не дозволено для {self.action}")
        return self


class TaskResult(BaseModel):
    task: Task
    stdout: str = ""
    stderr: str = ""
    returncode: int = 0
    skipped: bool = False
    duration_ms: int = 0

    @property
    def success(self) -> bool:
        return not self.skipped and self.returncode == 0

    @property
    def status(self) -> str:
        if self.skipped:
            return "SKIPPED"
        return "SUCCESS" if self.returncode == 0 else "FAILED"


class Plan(BaseModel):
    tasks: list[Task]
    reasoning: str = ""
