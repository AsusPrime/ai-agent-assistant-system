import subprocess

from core.base_os import BaseOSHandler


class WindowsHandler(BaseOSHandler):
    def open_application(self, app_name: str) -> str:
        subprocess.Popen(["start", app_name], shell=True)
        return f"Windows: спроба запуску {app_name}"

    def run_shell(self, command: str, cwd: str | None = None) -> tuple[str, str, int]:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, cwd=cwd
        )
        return result.stdout, result.stderr, result.returncode


class PosixHandler(BaseOSHandler):
    def open_application(self, app_name: str) -> str:
        import platform

        cmd = "open -a" if platform.system() == "Darwin" else ""
        subprocess.Popen(f"{cmd} {app_name}", shell=True)
        return f"Unix-like: спроба запуску {app_name}"

    def run_shell(self, command: str, cwd: str | None = None) -> tuple[str, str, int]:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, cwd=cwd
        )
        return result.stdout, result.stderr, result.returncode
