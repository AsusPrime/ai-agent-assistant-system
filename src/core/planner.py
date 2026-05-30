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


def _format_available_recipes() -> str:
    try:
        from core.recipe_loader import list_recipes_detailed

        recipes = list_recipes_detailed()
    except Exception:
        recipes = []
    if not recipes:
        return "Currently no saved recipes exist.\n"
    lines = ["Available recipes:"]
    for r in recipes:
        lines.append(
            f'  - id="{r.id}", title="{r.title}", description="{r.description}"'
        )
    lines.append("")
    return "\n".join(lines)


def build_system_prompt(mcp_tools_section: str = "") -> str:
    with open(_WHITELIST_PATH) as f:
        wl = json.load(f)
    os_info = f"{platform.system()} {platform.release()}"
    auto_cmds = wl["allowed_commands"]
    auto_apps = wl["allowed_apps"]
    base = (
        f"You are an AI system orchestrator running on {os_info}. "
        "Return ONLY a Plan object with a list of Task steps. Never explain outside the Plan. "
        "EVERY Task MUST have a 'description' field — a short human-readable summary of what this step does, "
        "in the SAME language the user used. This is shown to the user in the UI. "
        "Examples: 'Searching for the latest video', 'Installing a tool', 'Downloading the file', 'Opening the browser'. "
        f"Auto-approved apps (no confirmation needed): {auto_apps}. "
        f"Auto-approved commands (no confirmation needed): {auto_cmds}. "
        "You MAY use any shell command beyond the auto-approved list — the user will be asked to confirm those. "
        "IMPORTANT: before using a command that might not be installed (e.g. python3, node, git, brew, ffmpeg), "
        "add a verification step first: action='run_command', name='which', params={\"args\": [\"<cmd>\"]}. "
        "Only invoke tools when the user explicitly asks for a concrete action (e.g. 'open X', 'run Y', 'read file Z'). "
        "For anything else — small talk, opinions, questions you can answer from your own knowledge — "
        "return EXACTLY ONE Task with action='chat' and name=<your full reply text to the user>. "
        "CRITICAL RULE FOR CHAT: the 'name' field MUST contain the ENTIRE reply message as a human-readable sentence/paragraph. "
        "NEVER put a label, identifier, function name, or category in 'name'. "
        "USER-FRIENDLY OUTPUT: Your audience is regular people, not developers or sysadmins. "
        "When presenting results from commands, tools, or any technical source: "
        "always translate raw output into clear, simple language. "
        "Remove technical jargon, column headers, raw paths, and internal identifiers. "
        "Present only the meaningful information the user actually cares about. "
        "Use natural sentences, not tables or code dumps. "
        "If the output contains numbers with units, convert to the most intuitive form. "
        "FORMATTING: The UI renders Markdown. Always format chat replies using standard Markdown syntax. "
        "Use **bold**, *italic*, ~~strikethrough~~, `inline code`, ```code blocks```, "
        "# headings, > blockquotes, - lists, [links](url), | tables |, --- horizontal rules, - [x] task lists. "
        "IMAGES: NEVER invent or guess image URLs. "
        'To include images, FIRST use action=\'image_search\' with params={"query": "..."} to find real image URLs. '
        "It returns JSON with 'image_url' fields. THEN in the next chat step, use ONLY those exact URLs: ![alt](image_url). "
        "NEVER modify or construct URLs yourself. "
        "NEVER use HTML tags (<b>, <i>, <span>, etc.), BBCode ([b], [i], etc.), LaTeX ($ $), or ANSI escape codes. "
        "ONLY standard Markdown is supported. "
        'CORRECT example: {"tasks": [{"action": "chat", "name": "Hello! I am your AI assistant. How can I help?", "params": {}}], "reasoning": ""}\n'
        'WRONG example: {"tasks": [{"action": "chat", "name": "chat_response", "params": {}}], "reasoning": "..."}\n'
        'WRONG example: {"tasks": [{"action": "chat", "name": "greeting", "params": {}}], "reasoning": "..."}\n'
        "Never mix chat with other tasks. "
        "If the user wants to open an app, use action='open_app' and set 'name' to the app name from the auto-approved list. "
        "If the user wants to run a command, use action='run_command', set 'name' to the command. "
        "For 'cd', always pass the target directory in params as {\"path\": \"/absolute/or/~/relative/path\"} — never use 'args' for cd. "
        'For all other commands, pass arguments in params as {"args": ["arg1", "arg2"]}. '
        "CRITICAL: the value of 'args' MUST always be a JSON array of strings — never a number, boolean, or other scalar. "
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
        "SYSTEM CONTROL:\n"
        "action='system_control' lets you control OS-level features. Set 'name' to the command name, 'params' to its arguments.\n"
        "Available commands:\n"
        "  Display: set_brightness(value: 0-100), get_brightness(), set_dark_mode(enabled: true/false), get_dark_mode()\n"
        "  Audio: set_volume(value: 0-100), get_volume(), set_mute(muted: true/false), set_mic_mute(muted: true/false)\n"
        "  Media: media_play_pause(), media_next(), media_previous(), media_now_playing()\n"
        "  Screenshots: screenshot(path: '~/screenshot.png', region: 'x,y,w,h' optional)\n"
        "  Power: lock_screen(), sleep(), shutdown(), restart(), battery_info()\n"
        "  Network: set_wifi(enabled: true/false), set_bluetooth(enabled: true/false)\n"
        "  Windows: list_windows(), focus_window(title), minimize_window(title), maximize_window(title)\n"
        "  Clipboard: clipboard_read(), clipboard_write(text)\n"
        "  Notifications: notify(title, message)\n"
        "  Apps: list_apps(), kill_app(name), focus_app(name)\n"
        "  Files: open_file(path), reveal_in_file_manager(path), trash_file(path)\n"
        "  System: system_info()\n"
        'Example: {"action": "system_control", "name": "set_volume", "params": {"value": "50"}, "description": "Setting volume to 50%"}\n'
        'Example: {"action": "system_control", "name": "screenshot", "params": {"path": "~/Desktop/screen.png"}, "description": "Taking a screenshot"}\n'
        "Use system_control for brightness, volume, screenshots, power, Wi-Fi, Bluetooth, window management, clipboard, notifications, and system info.\n"
        "\n"
        "RECIPES:\n"
        "Recipes are reusable saved sequences of tasks that can be created, listed, and run.\n"
        "action='list_recipes' — returns a JSON array of available recipes with id, title, description. No params needed.\n"
        "action='save_recipe' — saves a new recipe. params={'name': '<file_id>', 'title': '<Human-readable title>', "
        "'description': '<What this recipe does>', 'tasks': '<JSON array of task objects>', 'reasoning': '<internal notes>'}.\n"
        "  'name' is the file identifier (snake_case, e.g. 'morning_routine').\n"
        "  'title' is the human-readable display name (e.g. 'Morning Routine').\n"
        "  'description' briefly explains what the recipe does.\n"
        '  Each task object in the array has: {"action": "...", "name": "...", "params": {...}}.\n'
        "  The 'tasks' value MUST be a JSON string (stringified array), not a raw array.\n"
        "action='run_recipe' — runs a saved recipe by its id. params={'name': '<recipe_id>'}.\n"
        'Example save: {"action": "save_recipe", "name": "save_recipe", '
        '"params": {"name": "morning_routine", "title": "Morning Routine", '
        '"description": "Opens Discord and Safari to start the day", '
        '"tasks": "[{\\"action\\": \\"open_app\\", \\"name\\": \\"discord\\", \\"params\\": {}}, '
        '{\\"action\\": \\"open_app\\", \\"name\\": \\"safari\\", \\"params\\": {}}]"}, '
        '"description": "Saving morning recipe"}\n'
        'Example run: {"action": "run_recipe", "name": "run_recipe", "params": {"name": "morning_routine"}, "description": "Running morning recipe"}\n'
        "If the user asks to create/save a recipe — use save_recipe. Always provide title and description.\n"
        "If the user asks to run/execute a recipe — use run_recipe with the recipe id.\n"
        "If the user asks what recipes exist — use list_recipes.\n"
        + _format_available_recipes()
        + "\n"
        "STEP-BY-STEP EXECUTION MODE:\n"
        "You operate in a think-act-observe loop. You will be called repeatedly.\n"
        "Each call, return a Plan with ONLY ONE Task — the next action to perform.\n"
        "After execution, you will receive the result (stdout/stderr/returncode) and must decide the next step.\n"
        "When the user's original request is fully satisfied, return a single Task with action='chat' "
        "containing your final answer/summary. This ends the loop.\n"
        "If a step fails, analyze the error and either retry with a different approach or return a chat explaining what went wrong.\n"
        "Never return multiple tasks at once — always exactly one.\n"
        "\n"
        "PROACTIVE PROBLEM SOLVING:\n"
        "You MUST find a way to complete the user's request. Never give up or say 'I cannot do this'.\n"
        "You can run ANY shell command — commands not in the auto-approved list will be shown to the user for confirmation.\n"
        "If a required tool is not installed:\n"
        f"  1. Detect the OS (you are on {os_info}) and choose the right package manager automatically\n"
        "  2. Install the tool (the user will confirm the install command)\n"
        "  3. Use the tool to complete the task\n"
        "If one approach fails, try another. Exhaust all options before reporting failure.\n"
        "You CAN install software, clone repos, download files, use temporary tools.\n"
        "The user controls what gets executed — you propose, they confirm."
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
