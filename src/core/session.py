import os

from core.schemas import TaskResult


class SessionState:
    def __init__(self) -> None:
        self.cwd: str = os.path.expanduser("~")
        self.message_history: list = []
        self.execution_log: list[TaskResult] = []
        self.privacy_events: list[dict] = []  # {"input": original, "masked_count": n}
        self.pii_map: dict[str, str] = {}  # {placeholder: original} for current request
