from tools.registry import TOOL_REGISTRY
from core.schemas import Task, TaskResult
from core.session import SessionState


class Executor:
    def execute(self, task: Task, session: SessionState) -> TaskResult:
        func = TOOL_REGISTRY.get(task.action.value)
        if func is None:
            return TaskResult(task=task, stderr="Action not found", returncode=127)
        try:
            return func(task=task, session=session)
        except Exception as e:
            return TaskResult(task=task, stderr=str(e), returncode=1)
