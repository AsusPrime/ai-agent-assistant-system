from typing import Callable

from tools.handlers import open_app, run_command, run_skill

TOOL_REGISTRY: dict[str, Callable] = {
    "open_app": open_app,
    "run_command": run_command,
    "run_skill": run_skill,
}
