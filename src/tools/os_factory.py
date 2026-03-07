import platform

from core.base_os import BaseOSHandler
from tools.os_handlers import WindowsHandler, PosixHandler


def get_os_handler() -> BaseOSHandler:
    system = platform.system()
    if system == "Windows":
        return WindowsHandler()
    else:
        return PosixHandler()
