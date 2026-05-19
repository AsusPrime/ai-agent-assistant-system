import json
import os
import platform
from typing import Any

from pydantic_ai import Agent

from config import settings
from core.schemas import Plan
from infrastructure.llm_client import get_model

_WHITELIST_PATH = os.path.join(
    os.path.dirname(__file__), "..", "tools", "whitelist.json"
)
_SKILLS_DIR = os.path.join(os.path.dirname(__file__), "..", "skills")


def build_system_prompt(mcp_tools_section: str = "") -> str:
    with open(_WHITELIST_PATH) as f:
        wl = json.load(f)
    os_info = f"{platform.system()} {platform.release()}"
    auto_cmds = wl["allowed_commands"]
    auto_apps = wl["allowed_apps"]
    scripts = [
        s for s in wl["allowed_scripts"] if os.path.isfile(os.path.join(_SKILLS_DIR, s))
    ]
    base = (
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
        "return EXACTLY ONE Task with action='chat' and name=<your full reply text to the user>. "
        "CRITICAL RULE FOR CHAT: the 'name' field MUST contain the ENTIRE reply message as a human-readable sentence/paragraph. "
        "NEVER put a label, identifier, function name, or category in 'name'. "
        'CORRECT example: {"tasks": [{"action": "chat", "name": "Привіт! Я — Akashi, твій AI-асистент. Чим можу допомогти?", "params": {}}], "reasoning": ""}\n'
        'WRONG example: {"tasks": [{"action": "chat", "name": "chat_response", "params": {}}], "reasoning": "..."}\n'
        'WRONG example: {"tasks": [{"action": "chat", "name": "greeting", "params": {}}], "reasoning": "..."}\n'
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
        "If the user asks a follow-up about something already fetched in this conversation, answer from message_history — do NOT call web_search/web_read again.\n"
        "\n"
        "STEP-BY-STEP EXECUTION MODE:\n"
        "You operate in a think-act-observe loop. You will be called repeatedly.\n"
        "Each call, return a Plan with ONLY ONE Task — the next action to perform.\n"
        "After execution, you will receive the result (stdout/stderr/returncode) and must decide the next step.\n"
        "When the user's original request is fully satisfied, return a single Task with action='chat' "
        "containing your final answer/summary. This ends the loop.\n"
        "If a step fails, analyze the error and either retry with a different approach or return a chat explaining what went wrong.\n"
        "Never return multiple tasks at once — always exactly one."
    )
    if mcp_tools_section:
        base = base + "\n\n" + mcp_tools_section
    return base


def format_mcp_tools_section(
    tools: list[dict[str, Any]],
    servers: list[str] | None = None,
) -> str:
    """Render a list of MCP tools into a concise system-prompt section.

    `tools` is the output of `MCPManager.list_tools()`: each entry has
    `name`, `description`, `input_schema`.
    `servers` is the list of configured MCP server names (for clarity —
    LLMs otherwise confuse server names with tool names).
    """
    if not tools:
        return ""
    lines = [
        "You also have external tools available via the Model Context Protocol (MCP).",
        "",
        "How to invoke an MCP tool (flat, same shape as other actions):",
        "  action='mcp_call'",
        "  name=<EXACT tool name from the list below>",
        "  params=<the tool's arguments as a plain dict>",
        "",
        "RULES:",
        "  * `name` MUST be one of the tool names listed below — never a server name.",
        "  * Never invent tool names. If the tool you want is not in the list below,",
        "    it does not exist.",
        "  * `params` contains the tool's arguments directly — do NOT wrap them in",
        '    an "args" key, do NOT stringify to JSON.',
    ]

    if servers:
        lines += [
            "",
            "MCP servers present (providers only — these names are NEVER valid `name` values):",
            *(f"  - {s}" for s in servers),
        ]

    lines += [
        "",
        "Available MCP tools (use the EXACT arg names shown):",
    ]
    for t in tools:
        lines.append(_render_tool_block(t))

    lines += [
        "",
        "Use MCP tools only when the user clearly needs them (external docs/services).",
        "For vague requests ('try X', 'use X'), pick a specific tool from the list first.",
    ]
    return "\n".join(lines)


_JSON_TYPE_MAP = {
    "string": "str",
    "integer": "int",
    "number": "float",
    "boolean": "bool",
    "array": "list",
    "object": "dict",
}


def _render_tool_block(t: dict[str, Any]) -> str:
    name = t.get("name", "?")
    desc = (t.get("description") or "").strip().replace("\n", " ")
    max_len = settings.MCP_DESC_MAX_LEN
    if len(desc) > max_len:
        desc = desc[: max_len - 3] + "..."

    schema = t.get("input_schema") or {}
    props = (schema.get("properties") if isinstance(schema, dict) else {}) or {}
    required = set((schema.get("required") if isinstance(schema, dict) else []) or [])

    parts: list[str] = []
    if not props:
        head = f"- {name}() — {desc}" if desc else f"- {name}()"
        return head

    typed_args = []
    sample: dict[str, Any] = {}
    for key, spec in props.items():
        ptype = (spec or {}).get("type") if isinstance(spec, dict) else None
        ptype_str = _JSON_TYPE_MAP.get(ptype or "", ptype or "any")
        marker = "*" if key in required else ""
        typed_args.append(f"{key}{marker}: {ptype_str}")
        if key in required:
            sample[key] = _placeholder_for(ptype_str)

    head = f"- {name}({', '.join(typed_args)})"
    parts.append(head)
    if desc:
        parts.append(f"    {desc}")
    if sample:
        parts.append(f"    e.g. params={json.dumps(sample, ensure_ascii=False)}")
    elif props:
        first_key = next(iter(props))
        first_type = (
            props[first_key].get("type") if isinstance(props[first_key], dict) else None
        )
        parts.append(
            f"    e.g. params={json.dumps({first_key: _placeholder_for(_JSON_TYPE_MAP.get(first_type or '', 'any'))}, ensure_ascii=False)}"
        )
    return "\n".join(parts)


def _placeholder_for(type_name: str) -> Any:
    return {
        "str": "<value>",
        "int": 0,
        "float": 0.0,
        "bool": False,
        "list": [],
        "dict": {},
    }.get(type_name, "<value>")


def build_planner_agent(mcp_tools_section: str = "") -> Agent:
    return Agent(
        model=get_model(),
        output_type=Plan,
        system_prompt=build_system_prompt(mcp_tools_section),
    )


planner_agent = build_planner_agent()
