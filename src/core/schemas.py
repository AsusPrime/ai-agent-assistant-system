import json
import os
from pydantic import BaseModel, model_validator
from typing import Dict, Any

from core.enums import ActionTypeEnum

_WHITELIST_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "tools",
    "whitelist.json",  # TODO: не подобається те що воно від цього відносного шляху, треба якось зробити щоб у проекта коренева папка була там де CLAUDE.md
)


class Task(BaseModel):
    action: ActionTypeEnum
    name: str
    params: Dict[str, Any] = {}

    @model_validator(mode="after")
    def check_allowed(self) -> "Task":
        if self.action == ActionTypeEnum.CHAT:
            return self
        if self.action in (ActionTypeEnum.RUN_COMMAND, ActionTypeEnum.WRITE_FILE):
            return self  # any command/file allowed; HITL is the safety net
        with open(_WHITELIST_PATH) as f:
            wl = json.load(f)
        mapping = {
            ActionTypeEnum.OPEN_APP: wl["allowed_apps"],
            ActionTypeEnum.RUN_SKILL: wl["allowed_scripts"],
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
