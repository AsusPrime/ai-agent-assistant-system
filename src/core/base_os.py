from abc import ABC, abstractmethod

class BaseOSHandler(ABC):
    @abstractmethod
    def open_application(self, app_name: str):
        pass

    @abstractmethod
    def run_shell(self, command: str):
        pass