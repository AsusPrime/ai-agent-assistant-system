import json
import time
from pathlib import Path
from typing import Callable

from config import settings
from core.enums import ActionTypeEnum
from core.executor import Executor
from core.memory import MessageRepository
from core.planner import planner_agent
from core.privacy import PrivacyGuard
from core.schemas import Plan, TaskResult
from core.session import SessionState
from core.summarizer import summary_agent

MAX_RETRIES = 3
_WHITELIST_PATH = Path(__file__).resolve().parent.parent / "tools" / "whitelist.json"

ConfirmFn = Callable[[str], bool]
MessageFn = Callable[[str], None]


class QueryResult:
    def __init__(
        self,
        reply: str | None = None,
        task_results: list[TaskResult] | None = None,
        summary: str | None = None,
    ):
        self.reply = reply
        self.task_results = task_results or []
        self.summary = summary

    @property
    def is_chat(self) -> bool:
        return self.reply is not None


class AkashiCore:
    def __init__(
        self,
        confirm_fn: ConfirmFn | None = None,
        on_message: MessageFn | None = None,
    ):
        self.executor = Executor()
        self.guard = PrivacyGuard()
        self.msg_repo = MessageRepository(data_dir=settings.DATA_DIR)
        self.session = SessionState()
        self._confirm = confirm_fn or self._default_confirm
        self._print = on_message or print

        self.session.message_history = self.msg_repo.load_recent(settings.MEMORY_TURNS)

    @staticmethod
    def _default_confirm(prompt: str) -> bool:
        return input(prompt).strip().lower() == "y"

    def process_query(self, user_input: str) -> QueryResult:
        masked_input, pii_map = self.guard.mask(user_input)
        self.session.pii_map.update(pii_map)
        if pii_map:
            self._print(
                f"[Privacy] Masked {len(pii_map)} sensitive pattern(s) before sending to LLM."
            )
            self.session.privacy_events.append(
                {"input_length": len(user_input), "masked_count": len(pii_map)}
            )

        plan = self._get_plan(masked_input)
        if plan is None:
            return QueryResult()
        plan = _unmask_plan(plan, self.session.pii_map)

        if len(plan.tasks) == 1 and plan.tasks[0].action == ActionTypeEnum.CHAT:
            return QueryResult(reply=plan.tasks[0].name)

        self._print_plan(plan)
        task_results = self._execute_plan(plan)

        retries_exhausted = self._retry_loop(task_results)

        summary = self._summarize(user_input, task_results, retries_exhausted)
        return QueryResult(task_results=task_results, summary=summary)

    # -- planning --------------------------------------------------------

    def _get_plan(self, masked_input: str) -> Plan | None:
        prev_len = len(self.session.message_history)
        try:
            result = self._run_planner(masked_input)
        except Exception as e:
            self._print(f"[LLM Error] {e}")
            return None

        self.session.message_history = result.all_messages()
        new_msgs = self.session.message_history[prev_len:]
        if new_msgs:
            self.msg_repo.save_turn(self.session.session_id, new_msgs)
        return result.output

    def _run_planner(self, prompt: str):
        try:
            return planner_agent.run_sync(
                prompt, message_history=self.session.message_history
            )
        except Exception as e:
            if _is_history_malformed_error(e) and self.session.message_history:
                if settings.DEBUG:
                    self._print(
                        f"[Memory] History rejected by LLM, retrying without it: {e}"
                    )
                else:
                    self._print(
                        "[Memory] Previous session history was malformed — starting fresh."
                    )
                self.session.message_history = []
                return planner_agent.run_sync(prompt)
            raise

    # -- execution -------------------------------------------------------

    def _execute_plan(self, plan: Plan) -> list[TaskResult]:
        results: list[TaskResult] = []
        auto_cmds = _load_auto_approved()
        failed = False

        for i, task in enumerate(plan.tasks, 1):
            if failed:
                results.append(TaskResult(task=task, skipped=True))
                continue

            needs_confirm = (
                task.action == ActionTypeEnum.RUN_COMMAND and task.name not in auto_cmds
            )
            if needs_confirm:
                msg = f"  Дія №{i} потребує дозволу: {task.action.value} | {task.name} | {task.params}. Виконати? [y/N]: "
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
        if settings.DEBUG:
            self._print_execution_log(results)
        return results

    # -- self-correction -------------------------------------------------

    def _retry_loop(self, task_results: list[TaskResult]) -> bool:
        for attempt in range(1, MAX_RETRIES + 1):
            failed_steps = [r for r in task_results if not r.success and not r.skipped]
            if not failed_steps:
                return False

            self._print(
                f"[Correction] Attempt {attempt}/{MAX_RETRIES} — asking LLM for a corrected plan..."
            )
            correction_prompt = self._build_correction_prompt(task_results)

            plan = self._get_plan(correction_prompt)
            if plan is None:
                return False

            plan = _unmask_plan(plan, self.session.pii_map)

            if len(plan.tasks) == 1 and plan.tasks[0].action == ActionTypeEnum.CHAT:
                self._print(f"Assistant: {plan.tasks[0].name}")
                return False

            self._print_plan(plan)

            msg = f"Execute corrected plan (attempt {attempt})? [y/N]: "
            if not self._confirm(msg):
                self._print("Cancelled.")
                return False

            task_results.clear()
            task_results.extend(self._execute_plan(plan))

            if attempt == MAX_RETRIES:
                if any(not r.success and not r.skipped for r in task_results):
                    return True
        return False

    def _build_correction_prompt(self, results: list[TaskResult]) -> str:
        lines = [
            "The following steps were executed and one failed. Suggest a corrected plan:"
        ]
        for r in results:
            lines.append(
                f"  [{r.status}] {r.task.action.value} {r.task.name} → rc={r.returncode}"
            )
            if r.stdout.strip():
                masked, _ = self.guard.mask(r.stdout.strip()[:200])
                lines.append(f"    stdout: {masked!r}")
            if r.stderr.strip():
                masked, _ = self.guard.mask(r.stderr.strip()[:200])
                lines.append(f"    stderr: {masked!r}")
        return "\n".join(lines)

    # -- summarization ---------------------------------------------------

    def _summarize(
        self, user_input: str, results: list[TaskResult], retries_exhausted: bool
    ) -> str | None:
        lines = [f'User asked: "{user_input}"', "Execution results:"]
        for r in results:
            masked_out, _ = self.guard.mask(r.stdout.strip()[:100])
            masked_err, _ = self.guard.mask(r.stderr.strip()[:100])
            lines.append(
                f"  [{r.status}] {r.task.name} → "
                f"stdout: {masked_out!r}, stderr: {masked_err!r}"
            )
        if retries_exhausted:
            lines.append("\nAll retry attempts failed. Inform the user clearly.")
        lines.append(
            "\nProvide a short, friendly summary in the same language the user used."
        )

        try:
            result = summary_agent.run_sync("\n".join(lines))
            return result.output
        except Exception as e:
            if settings.DEBUG:
                self._print(f"[Summary Error] {e}")
            return None

    # -- display helpers -------------------------------------------------

    def _print_plan(self, plan: Plan) -> None:
        self._print(f"[Plan] {len(plan.tasks)} step(s):")
        for i, task in enumerate(plan.tasks, 1):
            self._print(f"  {i}. {task.action.value} | {task.name} | {task.params}")
        if plan.reasoning and settings.DEBUG:
            self._print(f"  Reasoning: {plan.reasoning}")

    def _print_execution_log(self, results: list[TaskResult]) -> None:
        self._print("\n[Execution log]")
        for r in results:
            self._print(
                f"  {r.status:7} | {r.task.action.value:12} | {r.task.name} | {r.duration_ms}ms"
            )


# -- module-level helpers ------------------------------------------------


def _unmask_str(s: str, mapping: dict[str, str]) -> str:
    for placeholder, original in mapping.items():
        s = s.replace(placeholder, original)
    return s


def _unmask_plan(plan: Plan, mapping: dict[str, str]) -> Plan:
    if not mapping:
        return plan
    unmasked_tasks = []
    for task in plan.tasks:
        unmasked_name = _unmask_str(task.name, mapping)
        unmasked_params: dict = {}
        for k, v in task.params.items():
            if isinstance(v, str):
                unmasked_params[k] = _unmask_str(v, mapping)
            elif isinstance(v, list):
                unmasked_params[k] = [
                    _unmask_str(i, mapping) if isinstance(i, str) else i for i in v
                ]
            else:
                unmasked_params[k] = v
        unmasked_tasks.append(
            task.model_copy(update={"name": unmasked_name, "params": unmasked_params})
        )
    return plan.model_copy(update={"tasks": unmasked_tasks})


def _load_auto_approved() -> set[str]:
    with open(_WHITELIST_PATH) as f:
        wl = json.load(f)
    return set(wl.get("allowed_commands", []))


def _is_history_malformed_error(err: Exception) -> bool:
    msg = str(err).lower()
    return "function response" in msg or "function call" in msg
