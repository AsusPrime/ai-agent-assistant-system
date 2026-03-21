import json
import time
from pathlib import Path

from config import settings
from core.enums import ActionTypeEnum
from core.executor import Executor
from core.planner import planner_agent
from core.privacy import PrivacyGuard
from core.schemas import Plan, Task, TaskResult
from core.session import SessionState
from core.summarizer import summary_agent

executor = Executor()
MAX_RETRIES = 3

_WHITELIST_PATH = Path(__file__).parent / "tools" / "whitelist.json"


def _unmask_str(s: str, mapping: dict[str, str]) -> str:
    for placeholder, original in mapping.items():
        s = s.replace(placeholder, original)
    return s


def _unmask_plan(plan: Plan, mapping: dict[str, str]) -> Plan:
    """Replace all placeholders in task names and params with original values."""
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
                unmasked_params[k] = [_unmask_str(i, mapping) if isinstance(i, str) else i for i in v]
            else:
                unmasked_params[k] = v
        unmasked_tasks.append(task.model_copy(update={"name": unmasked_name, "params": unmasked_params}))
    return plan.model_copy(update={"tasks": unmasked_tasks})


def _load_auto_approved() -> set[str]:
    with open(_WHITELIST_PATH) as f:
        wl = json.load(f)
    return set(wl.get("allowed_commands", []))


def _print_plan(plan: Plan) -> None:
    print(f"[Plan] {len(plan.tasks)} step(s):")
    for i, task in enumerate(plan.tasks, 1):
        print(f"  {i}. {task.action.value} | {task.name} | {task.params}")
    if plan.reasoning and settings.DEBUG:
        print(f"  Reasoning: {plan.reasoning}")


def _execute_plan(plan: Plan, session: SessionState) -> list[TaskResult]:
    results: list[TaskResult] = []
    auto_cmds = _load_auto_approved()
    failed = False
    for i, task in enumerate(plan.tasks, 1):
        if failed:
            results.append(TaskResult(task=task, skipped=True))
            continue

        needs_confirm = (
            task.action == ActionTypeEnum.RUN_COMMAND
            and task.name not in auto_cmds
        )
        if needs_confirm:
            try:
                confirm = input(
                    f"  Дія №{i} потребує дозволу: {task.action.value} | {task.name} | {task.params}. Виконати? [y/N]: "
                ).strip().lower()
            except (KeyboardInterrupt, EOFError):
                raise
            if confirm != "y":
                print("Cancelled.")
                results.append(TaskResult(task=task, skipped=True))
                failed = True
                continue

        t0 = time.monotonic()
        result = executor.execute(task, session)
        result.duration_ms = int((time.monotonic() - t0) * 1000)
        results.append(result)
        if result.stdout:
            print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
        if result.stderr:
            print(f"[stderr] {result.stderr}")
        if not result.success:
            print(f"[Error] Step '{task.name}' failed (rc={result.returncode}). Stopping.")
            failed = True

    session.execution_log.extend(results)

    if settings.DEBUG:
        _print_execution_log(results)
    return results


def _print_execution_log(results: list[TaskResult]) -> None:
    print("\n[Execution log]")
    for r in results:
        print(f"  {r.status:7} | {r.task.action.value:12} | {r.task.name} | {r.duration_ms}ms")


def _build_correction_prompt(results: list[TaskResult], guard: PrivacyGuard) -> str:
    lines = ["The following steps were executed and one failed. Suggest a corrected plan:"]
    for r in results:
        lines.append(f"  [{r.status}] {r.task.action.value} {r.task.name} → rc={r.returncode}")
        if r.stdout.strip():
            masked, _ = guard.mask(r.stdout.strip()[:200])
            lines.append(f"    stdout: {masked!r}")
        if r.stderr.strip():
            masked, _ = guard.mask(r.stderr.strip()[:200])
            lines.append(f"    stderr: {masked!r}")
    return "\n".join(lines)


def _summarize(user_input: str, results: list[TaskResult], guard: PrivacyGuard, retries_exhausted: bool = False) -> None:
    lines = [f'User asked: "{user_input}"', "Execution results:"]
    for r in results:
        masked_out, _ = guard.mask(r.stdout.strip()[:100])
        masked_err, _ = guard.mask(r.stderr.strip()[:100])
        lines.append(
            f"  [{r.status}] {r.task.name} → "
            f"stdout: {masked_out!r}, stderr: {masked_err!r}"
        )
    if retries_exhausted:
        lines.append("\nAll retry attempts failed. Inform the user clearly.")
    lines.append("\nProvide a short, friendly summary in the same language the user used.")

    try:
        summary = summary_agent.run_sync("\n".join(lines))
        print(f"Assistant: {summary.output}")
    except Exception as e:
        if settings.DEBUG:
            print(f"[Summary Error] {e}")


def main() -> None:
    session = SessionState()
    guard = PrivacyGuard()
    print("Assistant is ready. Type your request (Ctrl+C to exit).")
    if settings.DEBUG:
        print("[DEBUG mode ON]")

    while True:
        try:
            user_input = input("\n> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nBye.")
            break

        if not user_input:
            continue

        masked_input, pii_map = guard.mask(user_input)
        session.pii_map.update(pii_map)
        if pii_map:
            print(f"[Privacy] Masked {len(pii_map)} sensitive pattern(s) before sending to LLM.")
            session.privacy_events.append({"input_length": len(user_input), "masked_count": len(pii_map)})

        try:
            result = planner_agent.run_sync(masked_input, message_history=session.message_history)
        except Exception as e:
            print(f"[LLM Error] {e}")
            continue

        session.message_history = result.all_messages()
        plan: Plan = _unmask_plan(result.output, session.pii_map)

        # Chat-only plan: no HITL
        if len(plan.tasks) == 1 and plan.tasks[0].action == ActionTypeEnum.CHAT:
            print(f"Assistant: {plan.tasks[0].name}")
            continue

        _print_plan(plan)

        try:
            task_results = _execute_plan(plan, session)
        except (KeyboardInterrupt, EOFError):
            print("\nBye.")
            return
        retries_exhausted = False

        for attempt in range(1, MAX_RETRIES + 1):
            failed_steps = [r for r in task_results if not r.success and not r.skipped]
            if not failed_steps:
                break

            print(f"[Correction] Attempt {attempt}/{MAX_RETRIES} — asking LLM for a corrected plan...")
            correction_prompt = _build_correction_prompt(task_results, guard)

            try:
                correction_result = planner_agent.run_sync(
                    correction_prompt, message_history=session.message_history
                )
            except Exception as e:
                print(f"[LLM Error] {e}")
                break

            session.message_history = correction_result.all_messages()
            correction_plan: Plan = _unmask_plan(correction_result.output, session.pii_map)

            if len(correction_plan.tasks) == 1 and correction_plan.tasks[0].action == ActionTypeEnum.CHAT:
                print(f"Assistant: {correction_plan.tasks[0].name}")
                break

            _print_plan(correction_plan)

            try:
                confirm = input(f"Execute corrected plan (attempt {attempt})? [y/N]: ").strip().lower()
            except (KeyboardInterrupt, EOFError):
                print("\nBye.")
                return

            if confirm != "y":
                print("Cancelled.")
                break

            try:
                task_results = _execute_plan(correction_plan, session)
            except (KeyboardInterrupt, EOFError):
                print("\nBye.")
                return

            if attempt == MAX_RETRIES:
                failed_final = [r for r in task_results if not r.success and not r.skipped]
                if failed_final:
                    retries_exhausted = True

        _summarize(user_input, task_results, guard, retries_exhausted=retries_exhausted)


if __name__ == "__main__":
    main()
