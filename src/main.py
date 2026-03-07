from core.enums import ActionTypeEnum
from core.executor import Executor
from core.planner import planner_agent

executor = Executor()


def main() -> None:
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
            result = planner_agent.run_sync(user_input)
        except Exception as e:
            print(f"[LLM Error] {e}")
            continue

        task = result.output

        if task.action == ActionTypeEnum.CHAT:
            print(f"Assistant: {task.name}")
            continue

        print(
            f"[Dry Run] Action: {task.action.value} | Name: {task.name} | Params: {task.params}"
        )
        try:
            confirm = input("Execute? [y/N]: ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\nBye.")
            break

        if confirm == "y":
            try:
                output = executor.execute(task)
                print(output)
            except Exception as e:
                print(f"[Execution Error] {e}")
        else:
            print("Cancelled.")


if __name__ == "__main__":
    main()
