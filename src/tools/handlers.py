import os
import subprocess

from tools.os_factory import get_os_handler

_SKILLS_DIR = os.path.join(os.path.dirname(__file__), "..", "skills")


def open_app(name: str, **params):
    return get_os_handler().open_application(name)


def run_command(name: str, args: list = [], **params):
    return get_os_handler().run_shell(f"{name} {' '.join(args)}")


def run_skill(name: str, args: list = [], **params):
    skill_path = os.path.join(_SKILLS_DIR, name)
    result = subprocess.run(
        ["python3", skill_path] + args, capture_output=True, text=True
    )
    return result.stdout
