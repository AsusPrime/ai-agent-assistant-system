import os
import subprocess

from core.schemas import Task, TaskResult
from core.session import SessionState
from tools.os_factory import get_os_handler

_SKILLS_DIR = os.path.join(os.path.dirname(__file__), "..", "skills")


def open_app(task: Task, session: SessionState) -> TaskResult:
    msg = get_os_handler().open_application(task.name)
    return TaskResult(task=task, stdout=msg, returncode=0)


def run_command(task: Task, session: SessionState) -> TaskResult:
    args: list[str] = task.params.get("args", [])
    name = task.name

    if name == "cd":
        path = args[0] if args else task.params.get("path", "~")
        new_cwd = os.path.expanduser(str(path))
        if not os.path.isabs(new_cwd):
            new_cwd = os.path.normpath(os.path.join(session.cwd, new_cwd))
        if os.path.isdir(new_cwd):
            session.cwd = new_cwd
            return TaskResult(task=task, stdout=f"Changed to {session.cwd}", returncode=0)
        else:
            return TaskResult(task=task, stderr=f"cd: {new_cwd}: No such directory", returncode=1)

    cmd = f"{name} {' '.join(args)}" if args else name
    stdout, stderr, returncode = get_os_handler().run_shell(cmd, cwd=session.cwd)
    return TaskResult(task=task, stdout=stdout, stderr=stderr, returncode=returncode)


def run_skill(task: Task, session: SessionState) -> TaskResult:
    args: list[str] = task.params.get("args", [])
    skill_path = os.path.join(_SKILLS_DIR, task.name)
    result = subprocess.run(
        ["python3", skill_path] + args, capture_output=True, text=True, cwd=session.cwd
    )
    return TaskResult(task=task, stdout=result.stdout, stderr=result.stderr, returncode=result.returncode)
