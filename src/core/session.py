import os

from core.schemas import TaskResult


class SessionState:
    def __init__(self) -> None:
        self.cwd: str = os.path.expanduser("~")
        self.message_history: list = []
        self.execution_log: list[TaskResult] = []
