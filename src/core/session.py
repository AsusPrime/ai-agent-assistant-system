import os
import uuid
from typing import TYPE_CHECKING

from core.schemas import TaskResult

if TYPE_CHECKING:
    from integrations.mcp_client import MCPManager


class SessionState:
    def __init__(self) -> None:
        self.cwd: str = os.path.expanduser("~")
        self.session_id: str = uuid.uuid4().hex
        self.message_history: list = []
        self.execution_log: list[TaskResult] = []
        self.privacy_events: list[dict] = []  # {"input": original, "masked_count": n}
        self.pii_map: dict[str, str] = {}  # {placeholder: original} for current request
        self.mcp_manager: "MCPManager | None" = None
        self.confirm_fn = None  # populated by AkashiCore for handlers that need HITL
