import json
from pydantic import BaseModel, field_validator
from typing import Dict, Any

from src.core.enums import ActionTypeEnum


class Task(BaseModel):
    action: ActionTypeEnum

    params: Dict[str, Any]

    @field_validator('action')
    @classmethod
    def check_action_allowed(cls, v: str) -> str:
        with open('tools/whitelist.json', 'r') as f:
            allowed = json.load(f)['allowed_actions']

        if v not in allowed:
            raise ValueError(f"Action '{v}' is not in the whitelist!")
        return v