from tools.registry import TOOL_REGISTRY
from core.schemas import Task


class Executor:
    def execute(self, task: Task) -> str:
        func = TOOL_REGISTRY.get(task.action.value)
        if func:
            try:
                return func(name=task.name, **task.params)
            except Exception as e:
                return f"Execution error {task.action}: {str(e)}"
        return "Action not found"
