import json
import os
import platform

from pydantic_ai import Agent

from core.schemas import Plan
from infrastructure.llm_client import get_model

_WHITELIST_PATH = os.path.join(
    os.path.dirname(__file__), "..", "tools", "whitelist.json"
)


def _build_system_prompt() -> str:
    with open(_WHITELIST_PATH) as f:
        wl = json.load(f)
    os_info = f"{platform.system()} {platform.release()}"
    auto_cmds = wl["allowed_commands"]
    auto_apps = wl["allowed_apps"]
    scripts = wl["allowed_scripts"]
    return (
        f"You are an AI system orchestrator running on {os_info}. "
        "Return ONLY a Plan object with a list of Task steps. Never explain outside the Plan. "
        f"Auto-approved apps (no confirmation needed): {auto_apps}. "
        f"Auto-approved commands (no confirmation needed): {auto_cmds}. "
        f"Allowed scripts: {scripts}. "
        "You MAY use any shell command beyond the auto-approved list — the user will be asked to confirm those. "
        "IMPORTANT: before using a command that might not be installed (e.g. python3, node, git, brew, ffmpeg), "
        "add a verification step first: action='run_command', name='which', params={\"args\": [\"<cmd>\"]}. "
        "If the user is chatting (greeting, question, small talk), return a Plan with one Task: action='chat', name=<your reply text>. "
        "If the user wants to open an app, use action='open_app' and set 'name' to the app name from the auto-approved list. "
        "If the user wants to run a command, use action='run_command', set 'name' to the command. "
        "For 'cd', always pass the target directory in params as {\"path\": \"/absolute/or/~/relative/path\"} — never use 'args' for cd. "
        "For all other commands, pass arguments in params as {\"args\": [\"arg1\", \"arg2\"]}. "
        "If the user wants to run a script/skill, use action='run_skill' and set 'name' to the script from the allowed list. "
        "Add verification steps after state-changing commands: after 'cd <dir>' add 'pwd'; after 'mkdir' add 'ls'. "
        "Decompose multi-step requests into an ordered list of Tasks."
    )


planner_agent = Agent(
    model=get_model(),
    output_type=Plan,
    system_prompt=_build_system_prompt(),
)
