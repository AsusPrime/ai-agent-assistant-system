import json
import os
import platform

from pydantic_ai import Agent

from core.schemas import Plan
from infrastructure.llm_client import get_model

_WHITELIST_PATH = os.path.join(
    os.path.dirname(__file__), "..", "tools", "whitelist.json"
)
_SKILLS_DIR = os.path.join(os.path.dirname(__file__), "..", "skills")


def _build_system_prompt() -> str:
    with open(_WHITELIST_PATH) as f:
        wl = json.load(f)
    os_info = f"{platform.system()} {platform.release()}"
    auto_cmds = wl["allowed_commands"]
    auto_apps = wl["allowed_apps"]
    scripts = [
        s for s in wl["allowed_scripts"] if os.path.isfile(os.path.join(_SKILLS_DIR, s))
    ]
    return (
        f"You are an AI system orchestrator running on {os_info}. "
        "Return ONLY a Plan object with a list of Task steps. Never explain outside the Plan. "
        f"Auto-approved apps (no confirmation needed): {auto_apps}. "
        f"Auto-approved commands (no confirmation needed): {auto_cmds}. "
        f"Allowed scripts (these are the ONLY scripts that exist on disk — never invoke any other script name): {scripts}. "
        "You MAY use any shell command beyond the auto-approved list — the user will be asked to confirm those. "
        "IMPORTANT: before using a command that might not be installed (e.g. python3, node, git, brew, ffmpeg), "
        "add a verification step first: action='run_command', name='which', params={\"args\": [\"<cmd>\"]}. "
        "Only invoke tools when the user explicitly asks for a concrete action (e.g. 'open X', 'run Y', 'read file Z'). "
        "For anything else — small talk, opinions, questions you can answer from your own knowledge — "
        "return EXACTLY ONE Task with action='chat' and name=<your full reply text to the user>; "
        "never put an identifier or label in name, it must be the actual message the user will read. "
        "Never mix chat with other tasks. "
        "If the user wants to open an app, use action='open_app' and set 'name' to the app name from the auto-approved list. "
        "If the user wants to run a command, use action='run_command', set 'name' to the command. "
        "For 'cd', always pass the target directory in params as {\"path\": \"/absolute/or/~/relative/path\"} — never use 'args' for cd. "
        'For all other commands, pass arguments in params as {"args": ["arg1", "arg2"]}. '
        "CRITICAL: the value of 'args' MUST always be a JSON array of strings — never a number, boolean, or other scalar. "
        "If the user wants to run a script/skill, use action='run_skill' and set 'name' to the script from the allowed list. "
        "Add verification steps after state-changing commands: after 'cd <dir>' add 'pwd'; after 'mkdir' add 'pwd'. "
        "To create or overwrite a file, use action='write_file', set 'name' to the filename, "
        "params={'path': '/absolute/or/~/path/to/file', 'content': '<file content>'}. "
        "To append to an existing file without overwriting it, add 'append': 'true' to params. "
        "Never use 'echo ... > file' for file creation. "
        "To read a file, use action='read_file', set 'name' to the filename, "
        "params={'path': '/absolute/or/~/path/to/file'}. "
        "Decompose multi-step requests into an ordered list of Tasks. "
        "Conversation history is provided via message_history — use it directly for questions about prior turns, do not call tools to retrieve it. "
        "action='search_knowledge' (params={'query': ...}) queries the user's indexed local files/documents. "
        "action='index_knowledge' (params={'path': ...}) adds a file or directory to that knowledge base. "
        "action='web_search' (params={'query': ...,'max_results': 5}) does a DuckDuckGo web search and returns title/url/snippet JSON. "
        "action='web_read' (params={'url': ...}) fetches a web page and returns its main text content. "
        "action='http_request' (params={'method': 'GET'|'POST'|..., 'url': ..., 'headers': {...}, 'json': {...}, 'timeout': 15}) calls an arbitrary HTTP API. "
        "Prefer 'web_search' for general lookup, 'web_read' for reading a known page, 'http_request' only for structured APIs. "
        "If the user asks a follow-up about something already fetched in this conversation, answer from message_history — do NOT call web_search/web_read again."
    )


planner_agent = Agent(
    model=get_model(),
    output_type=Plan,
    system_prompt=_build_system_prompt(),
)
