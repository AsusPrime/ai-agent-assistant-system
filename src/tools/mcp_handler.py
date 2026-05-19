"""MCP_CALL handler.

Task contract (flat, same shape as other actions):
    Task(action=MCP_CALL, name=<tool>, params=<args dict>)

Error model (each branch produces stderr useful to the self-correction loop):
  - server name used as tool: "'<x>' is an MCP server name, not a tool ..."
  - unknown tool:             "Unknown MCP tool '<x>'. Available: [...]"
  - tool returns plain-text error with is_error=False (some MCP servers
    do this): _looks_like_error_in_text() detects and elevates to rc=1.

NOTE: Privacy Guard is intentionally NOT applied to tool args. Rationale:
blindly masking breaks auth-like params (tokens, emails as identity, phone
numbers for SMS-MCPs). See W8 TODO — per-server `mask_args` profile.
"""

import json
import re
from typing import Any

from config import settings
from core.schemas import Task, TaskResult
from core.session import SessionState

# MCP servers vary: some report tool errors via `is_error=True`, others return
# the error as plain text with `is_error=False`. We detect the latter via the
# first non-empty line of the response. Conservative on purpose — long
# responses (>800 chars) or non-matching prefixes are treated as success.
_ERROR_LINE_RE = re.compile(
    r"^\s*("
    r"error[: ]"
    r"|invalid\b"
    r"|failed\b"
    r"|cannot\b"
    r"|unable to\b"
    r"|not found\b"
    r"|no such\b"
    r"|expected (format|input|type)\b"
    r"|usage:\b"
    r"|missing (required|argument)\b"
    r")",
    re.IGNORECASE,
)


def _looks_like_error_in_text(text: str) -> bool:
    if not text or len(text) > settings.MCP_ERROR_BODY_MAX:
        return False
    first = next((ln for ln in text.splitlines() if ln.strip()), "")
    return bool(_ERROR_LINE_RE.match(first))


def _forced_args_for(tool: str, default_args: dict[str, dict]) -> dict[str, Any]:
    matches = [s for s in default_args if tool.startswith(f"{s}_")]
    if not matches:
        return {}
    server = max(matches, key=len)
    return default_args[server]


def mcp_call(task: Task, session: SessionState) -> TaskResult:
    manager = session.mcp_manager
    if manager is None or not manager.connected:
        return TaskResult(
            task=task, stderr="MCP manager is not available", returncode=1
        )

    try:
        known_tools_info = manager.list_tools()
    except Exception as e:
        return TaskResult(
            task=task, stderr=f"Could not list MCP tools: {e}", returncode=1
        )
    known_tools = {t["name"] for t in known_tools_info}
    known_servers = set(manager.config.servers.keys())

    tool = str(task.name or "").strip()
    if not tool:
        return TaskResult(
            task=task,
            stderr=f"missing MCP tool name (Task.name). Available: {sorted(known_tools)}",
            returncode=1,
        )

    args: dict[str, Any] = {k: v for k, v in task.params.items() if v is not None}

    if tool not in known_tools:
        if tool in known_servers:
            return TaskResult(
                task=task,
                stderr=(
                    f"'{tool}' is an MCP server name, not a tool. "
                    f"Available tools: {sorted(known_tools)}"
                ),
                returncode=1,
            )
        return TaskResult(
            task=task,
            stderr=f"Unknown MCP tool '{tool}'. Available: {sorted(known_tools)}",
            returncode=1,
        )

    forced = _forced_args_for(tool, manager.config.default_args)
    final_args = {**args, **forced}

    if not manager.is_auto_approved(tool):
        confirm = session.confirm_fn
        if confirm is None:
            return TaskResult(
                task=task,
                stderr=f"MCP tool '{tool}' requires HITL but no confirm_fn is set",
                returncode=1,
            )
        prompt = f"  MCP call requires approval: {tool} | args={final_args}. Execute? [y/N]: "
        if not confirm(prompt):
            return TaskResult(
                task=task, stderr="cancelled by user", skipped=True, returncode=1
            )

    try:
        result = manager.call_tool(tool, final_args)
    except Exception as e:
        return TaskResult(task=task, stderr=f"MCP call failed: {e}", returncode=1)

    stdout = result.get("text") or ""
    if not stdout and result.get("data") is not None:
        try:
            stdout = json.dumps(result["data"], ensure_ascii=False, indent=2)
        except (TypeError, ValueError):
            stdout = str(result["data"])

    is_error = bool(result.get("is_error"))
    if not is_error and _looks_like_error_in_text(stdout):
        is_error = True

    return TaskResult(
        task=task,
        stdout="" if is_error else stdout,
        stderr=stdout if is_error else "",
        returncode=1 if is_error else 0,
    )
