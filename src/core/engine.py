import json
import time
from pathlib import Path
from typing import Callable

from core.enums import ActionTypeEnum
from core.executor import Executor
from core.schemas import Plan, Task, TaskResult
from core.session import SessionState

_WHITELIST_PATH = Path(__file__).resolve().parent.parent / "tools" / "whitelist.json"

ConfirmFn = Callable[[str], bool]
MessageFn = Callable[[str], None]


class ExecutionEngine:
    def __init__(
        self,
        session: SessionState,
        confirm_fn: ConfirmFn | None = None,
        on_message: MessageFn | None = None,
    ):
        self.executor = Executor()
        self.session = session
        self._confirm = confirm_fn or (lambda _: True)
        self._print = on_message or print

    def run(self, plan: Plan, pre_approved: bool = False) -> list[TaskResult]:
        results: list[TaskResult] = []
        auto_cmds = _load_auto_approved()
        failed = False

        for i, task in enumerate(plan.tasks, 1):
            if failed:
                results.append(TaskResult(task=task, skipped=True))
                continue

            needs_confirm = (
                not pre_approved
                and task.action == ActionTypeEnum.RUN_COMMAND
                and task.name not in auto_cmds
            )
            if needs_confirm:
                msg = (
                    f"  Дія №{i} потребує дозволу: {task.action.value} "
                    f"| {task.name} | {task.params}. Виконати? [y/N]: "
                )
                if not self._confirm(msg):
                    self._print("Cancelled.")
                    results.append(TaskResult(task=task, skipped=True))
                    failed = True
                    continue

            t0 = time.monotonic()
            result = self.executor.execute(task, self.session)
            result.duration_ms = int((time.monotonic() - t0) * 1000)
            results.append(result)

            if result.stdout:
                self._print(
                    result.stdout
                    if result.stdout.endswith("\n")
                    else result.stdout + "\n"
                )
            if result.stderr:
                self._print(f"[stderr] {result.stderr}")
            if not result.success:
                self._print(
                    f"[Error] Step '{task.name}' failed (rc={result.returncode}). Stopping."
                )
                failed = True

        self.session.execution_log.extend(results)
        return results

    def run_single(self, task: Task, pre_approved: bool = False) -> TaskResult:
        auto_cmds = _load_auto_approved()

        needs_confirm = (
            not pre_approved
            and task.action == ActionTypeEnum.RUN_COMMAND
            and task.name not in auto_cmds
        )
        if needs_confirm:
            msg = (
                f"  Дія потребує дозволу: {task.action.value} "
                f"| {task.name} | {task.params}. Виконати? [y/N]: "
            )
            if not self._confirm(msg):
                self._print("Cancelled.")
                result = TaskResult(task=task, skipped=True)
                self.session.execution_log.append(result)
                return result

        t0 = time.monotonic()
        result = self.executor.execute(task, self.session)
        result.duration_ms = int((time.monotonic() - t0) * 1000)

        if result.stdout:
            self._print(
                result.stdout if result.stdout.endswith("\n") else result.stdout + "\n"
            )
        if result.stderr:
            self._print(f"[stderr] {result.stderr}")
        if not result.success:
            self._print(f"[Error] Step '{task.name}' failed (rc={result.returncode}).")

        self.session.execution_log.append(result)
        return result


def _load_auto_approved() -> set[str]:
    with open(_WHITELIST_PATH) as f:
        wl = json.load(f)
    return set(wl.get("allowed_commands", []))
