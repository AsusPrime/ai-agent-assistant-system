from prompt_toolkit import PromptSession

from core.assistant import AssistantCore


def main() -> None:
    core = AssistantCore()

    if core.session.message_history:
        print("[Memory] Restored context from previous session.")
    print("Assistant is ready. Type your request (Ctrl+C to exit).")

    prompt_session: PromptSession = PromptSession()

    try:
        while True:
            try:
                user_input = prompt_session.prompt("\n> ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nBye.")
                break

            if not user_input:
                continue

            try:
                result = core.process_query(user_input)
            except (KeyboardInterrupt, EOFError):
                print("\nBye.")
                break

            if result.is_chat:
                print(f"Assistant: {result.reply}")
            elif result.summary:
                print(f"Assistant: {result.summary}")
    finally:
        core.close()


if __name__ == "__main__":
    main()
