import platform

from src.tools.os_handlers import WindowsHandler, PosixHandler


def get_os_handler():
    system = platform.system()
    if system == "Windows":
        return WindowsHandler()
    else:
        return PosixHandler()