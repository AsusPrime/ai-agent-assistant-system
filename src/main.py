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

executor = Executor()

_WHITELIST_PATH = Path(__file__).parent / "tools" / "whitelist.json"


def _load_auto_approved() -> set[str]:
    with open(_WHITELIST_PATH) as f:
        wl = json.load(f)
    return set(wl.get("allowed_commands", []))


def _requires_confirmation(plan: Plan) -> bool:
    auto_cmds = _load_auto_approved()
    for task in plan.tasks:
        if task.action == ActionTypeEnum.RUN_COMMAND and task.name not in auto_cmds:
            return True
    return False


def _print_plan(plan: Plan) -> None:
    print(f"[Plan] {len(plan.tasks)} step(s):")
    auto_cmds = _load_auto_approved()
    for i, task in enumerate(plan.tasks, 1):
        needs_confirm = (
            task.action == ActionTypeEnum.RUN_COMMAND
            and task.name not in auto_cmds
        )
        marker = " [!]" if needs_confirm else ""
        print(f"  {i}.{marker} {task.action.value} | {task.name} | {task.params}")
    if plan.reasoning and settings.DEBUG:
        print(f"  Reasoning: {plan.reasoning}")


def _execute_plan(plan: Plan, session: SessionState) -> list[TaskResult]:
    results: list[TaskResult] = []
    failed = False
    for task in plan.tasks:
        if failed:
            results.append(TaskResult(task=task, skipped=True))
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
    if settings.DEBUG:
        _print_execution_log(results)
    return results


def _print_execution_log(results: list[TaskResult]) -> None:
    print("\n[Execution log]")
    for r in results:
        print(f"  {r.status:7} | {r.task.action.value:12} | {r.task.name} | {r.duration_ms}ms")


def _build_correction_prompt(results: list[TaskResult]) -> str:
    lines = ["The following steps were executed and one failed. Suggest a corrected plan:"]
    for r in results:
        lines.append(f"  [{r.status}] {r.task.action.value} {r.task.name} → rc={r.returncode}")
        if r.stderr:
            lines.append(f"    stderr: {r.stderr.strip()}")
    return "\n".join(lines)


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
        if pii_map:
            print(f"[Privacy] Masked {len(pii_map)} sensitive pattern(s) before sending to LLM.")

        try:
            result = planner_agent.run_sync(masked_input, message_history=session.message_history)
        except Exception as e:
            print(f"[LLM Error] {e}")
            continue

        session.message_history = result.all_messages()
        plan: Plan = result.output

        # Chat-only plan: no HITL
        if len(plan.tasks) == 1 and plan.tasks[0].action == ActionTypeEnum.CHAT:
            print(f"Assistant: {plan.tasks[0].name}")
            continue

        _print_plan(plan)

        if _requires_confirmation(plan):
            try:
                confirm = input("Plan contains non-approved command(s) [!]. Execute? [y/N]: ").strip().lower()
            except (KeyboardInterrupt, EOFError):
                print("\nBye.")
                break
            if confirm != "y":
                print("Cancelled.")
                continue

        task_results = _execute_plan(plan, session)

        # Check if any step failed → correction cycle
        failed_steps = [r for r in task_results if not r.success and not r.skipped]
        if not failed_steps:
            continue

        correction_prompt = _build_correction_prompt(task_results)
        print("[Correction] Asking LLM for a corrected plan...")
        try:
            correction_result = planner_agent.run_sync(
                correction_prompt, message_history=session.message_history
            )
        except Exception as e:
            print(f"[LLM Error] {e}")
            continue

        session.message_history = correction_result.all_messages()
        correction_plan: Plan = correction_result.output

        if len(correction_plan.tasks) == 1 and correction_plan.tasks[0].action == ActionTypeEnum.CHAT:
            print(f"Assistant: {correction_plan.tasks[0].name}")
            continue

        _print_plan(correction_plan)

        if _requires_confirmation(correction_plan):
            try:
                confirm = input("Corrected plan has non-approved command(s) [!]. Execute? [y/N]: ").strip().lower()
            except (KeyboardInterrupt, EOFError):
                print("\nBye.")
                break
            if confirm != "y":
                print("Cancelled.")
                continue
        else:
            try:
                confirm = input("Execute corrected plan? [y/N]: ").strip().lower()
            except (KeyboardInterrupt, EOFError):
                print("\nBye.")
                break
            if confirm != "y":
                print("Cancelled.")
                continue

        _execute_plan(correction_plan, session)


if __name__ == "__main__":
    main()
