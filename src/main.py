from core.enums import ActionTypeEnum
from core.executor import Executor
from core.planner import planner_agent
from core.schemas import Plan, TaskResult
from core.session import SessionState

executor = Executor()


def _print_plan(plan: Plan) -> None:
    print(f"[Plan] {len(plan.tasks)} step(s):")
    for i, task in enumerate(plan.tasks, 1):
        print(f"  {i}. {task.action.value} | {task.name} | {task.params}")
    if plan.reasoning:
        print(f"  Reasoning: {plan.reasoning}")


def _execute_plan(plan: Plan, session: SessionState) -> list[TaskResult]:
    results: list[TaskResult] = []
    for task in plan.tasks:
        result = executor.execute(task, session)
        results.append(result)
        if result.stdout:
            print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
        if result.stderr:
            print(f"[stderr] {result.stderr}")
        if not result.success:
            print(f"[Error] Step '{task.name}' failed (rc={result.returncode}). Stopping.")
            break
    return results


def _build_correction_prompt(results: list[TaskResult]) -> str:
    lines = ["The following steps were executed and one failed. Suggest a corrected plan:"]
    for r in results:
        status = "OK" if r.success else "FAILED"
        lines.append(f"  [{status}] {r.task.action.value} {r.task.name} → rc={r.returncode}")
        if r.stderr:
            lines.append(f"    stderr: {r.stderr.strip()}")
    return "\n".join(lines)


def main() -> None:
    session = SessionState()
    print("Assistant is ready. Type your request (Ctrl+C to exit).")

    while True:
        try:
            user_input = input("\n> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nBye.")
            break

        if not user_input:
            continue

        try:
            result = planner_agent.run_sync(user_input, message_history=session.message_history)
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
        try:
            confirm = input("Execute plan? [y/N]: ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\nBye.")
            break

        if confirm != "y":
            print("Cancelled.")
            continue

        task_results = _execute_plan(plan, session)

        # Check if any step failed → correction cycle
        failed = [r for r in task_results if not r.success]
        if not failed:
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
        try:
            confirm = input("Execute corrected plan? [y/N]: ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\nBye.")
            break

        if confirm == "y":
            _execute_plan(correction_plan, session)
        else:
            print("Cancelled.")


if __name__ == "__main__":
    main()
