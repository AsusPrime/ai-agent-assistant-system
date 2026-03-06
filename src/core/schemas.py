import json
import os
from pydantic import BaseModel, model_validator
from typing import Dict, Any

from core.enums import ActionTypeEnum

_WHITELIST_PATH = os.path.join(
    os.path.dirname(__file__), "..", "tools", "whitelist.json"
)


class Task(BaseModel):
    action: ActionTypeEnum
    name: str
    params: Dict[str, Any] = {}

    @model_validator(mode="after")
    def check_allowed(self) -> "Task":
        with open(_WHITELIST_PATH) as f:
            wl = json.load(f)
        mapping = {
            ActionTypeEnum.OPEN_APP: wl["allowed_apps"],
            ActionTypeEnum.RUN_COMMAND: wl["allowed_commands"],
            ActionTypeEnum.RUN_SKILL: wl["allowed_scripts"],
        }
        allowed = mapping[self.action]
        if self.name not in allowed:
            raise ValueError(f"'{self.name}' не дозволено для {self.action}")
        return self
