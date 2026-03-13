import os


class SessionState:
    def __init__(self) -> None:
        self.cwd: str = os.path.expanduser("~")
        self.message_history: list = []
