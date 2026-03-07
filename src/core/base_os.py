from abc import ABC, abstractmethod


class BaseOSHandler(ABC):
    @abstractmethod
    def open_application(self, app_name: str) -> str:
        pass

    @abstractmethod
    def run_shell(self, command: str) -> str:
        pass
