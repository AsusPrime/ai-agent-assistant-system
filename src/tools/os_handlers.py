import subprocess

from src.core.base_os import BaseOSHandler


class WindowsHandler(BaseOSHandler):
    def open_application(self, app_name: str):
        subprocess.Popen(['start', app_name], shell=True)
        return f"Windows: спроба запуску {app_name}"

    def run_shell(self, command: str):
        return subprocess.check_output(command, shell=True).decode()

class PosixHandler(BaseOSHandler):
    def open_application(self, app_name: str):
        import platform
        cmd = "open -a" if platform.system() == "Darwin" else ""
        subprocess.Popen(f"{cmd} {app_name}", shell=True)
        return f"Unix-like: спроба запуску {app_name}"

    def run_shell(self, command: str):
        return subprocess.check_output(command, shell=True).decode()