import json
import os

from pydantic_ai import Agent

from core.schemas import Task
from infrastructure.llm_client import get_model

_WHITELIST_PATH = os.path.join(
    os.path.dirname(__file__), "..", "tools", "whitelist.json"
)


def _build_system_prompt() -> str:
    with open(_WHITELIST_PATH) as f:
        wl = json.load(f)
    return (
        "You are an AI system orchestrator. "
        "Return ONLY a Task object. Never explain. "
        f"Allowed apps: {wl['allowed_apps']}. "
        f"Allowed commands: {wl['allowed_commands']}. "
        f"Allowed scripts: {wl['allowed_scripts']}. "
        "If the user is chatting (greeting, question, small talk), use action='chat' and put your reply text in 'name'. "
        "If the user wants to open an app, use action='open_app' and set 'name' to the app name from the allowed list. "
        "If the user wants to run a command, use action='run_command' and set 'name' to the command from the allowed list. "
        "If the user wants to run a script/skill, use action='run_skill' and set 'name' to the script from the allowed list."
    )


planner_agent = Agent(
    model=get_model(),
    output_type=Task,
    system_prompt=_build_system_prompt(),
)
