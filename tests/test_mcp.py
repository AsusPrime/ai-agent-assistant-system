"""MCP integration tests.

Uses an in-process FastMCP server as transport — no subprocess spawn,
no network, no external MCP binaries. Verifies:
- MCPManager lifecycle (start/stop, empty config is a no-op)
- list_tools + call_tool roundtrip
- error propagation (tool raises → is_error=True)
- auto-approve whitelist matching
- config loader (missing file, malformed JSON, valid payload)
"""

import json
import os
import sys
from pathlib import Path

import pytest
from fastmcp import FastMCP

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from core.enums import ActionTypeEnum  # noqa: E402
from core.planner import build_system_prompt, format_mcp_tools_section  # noqa: E402
from core.schemas import Task  # noqa: E402
from core.session import SessionState  # noqa: E402
from integrations.mcp_client import MCPManager, MCPNotConnectedError  # noqa: E402
from integrations.mcp_config import MCPConfig, load_config  # noqa: E402
from tools.mcp_handler import mcp_call  # noqa: E402

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mcp_server() -> FastMCP:
    srv = FastMCP("test-server")

    @srv.tool
    def add(a: int, b: int) -> int:
        return a + b

    @srv.tool
    def echo(text: str) -> str:
        return text

    @srv.tool
    def fail() -> str:
        raise RuntimeError("intentional failure")

    @srv.tool
    def text_error(query: str) -> str:
        # Mimics MCP servers that report failures as plain text with is_error=False.
        return f'Invalid library ID format: "{query}". Expected format: /owner/repo'

    @srv.tool
    def long_doc(topic: str) -> str:
        # Long document that mentions error-related words mid-content.
        body = (
            f"## {topic}\n\n"
            "FastAPI provides robust error handling via HTTPException. "
            "Errors are propagated to clients with proper status codes.\n\n"
        )
        return body + "x" * 1500

    return srv


@pytest.fixture
def manager(mcp_server: FastMCP):
    mgr = MCPManager(transport=mcp_server)
    mgr.start()
    yield mgr
    mgr.stop()


# ---------------------------------------------------------------------------
# MCPManager lifecycle
# ---------------------------------------------------------------------------


def test_empty_config_start_is_noop():
    mgr = MCPManager(config=MCPConfig())
    mgr.start()
    assert mgr.connected is False
    # list_tools on disconnected manager must fail loudly
    with pytest.raises(MCPNotConnectedError):
        mgr.list_tools()
    mgr.stop()  # must not raise


def test_start_then_stop_cleanly(mcp_server: FastMCP):
    mgr = MCPManager(transport=mcp_server)
    mgr.start()
    assert mgr.connected is True
    mgr.stop()
    assert mgr.connected is False


def test_double_start_is_idempotent(mcp_server: FastMCP):
    mgr = MCPManager(transport=mcp_server)
    mgr.start()
    mgr.start()  # must not raise or reconnect
    assert mgr.connected is True
    mgr.stop()


# ---------------------------------------------------------------------------
# list_tools / call_tool
# ---------------------------------------------------------------------------


def test_list_tools_returns_registered_tools(manager: MCPManager):
    tools = manager.list_tools()
    names = {t["name"] for t in tools}
    assert {"add", "echo", "fail"}.issubset(names)


def test_call_tool_success(manager: MCPManager):
    r = manager.call_tool("add", {"a": 2, "b": 3})
    assert r["is_error"] is False
    # Either data or text carries the result
    assert r["data"] == 5 or "5" in r["text"]


def test_call_tool_echo_string(manager: MCPManager):
    r = manager.call_tool("echo", {"text": "hi"})
    assert r["is_error"] is False
    assert "hi" in (r["text"] or "") or r["data"] == "hi"


def test_call_tool_error_is_reported_not_raised(manager: MCPManager):
    r = manager.call_tool("fail", {})
    assert r["is_error"] is True


def test_call_tool_unknown_tool_errors(manager: MCPManager):
    r = manager.call_tool("nonexistent_tool", {})
    assert r["is_error"] is True


# ---------------------------------------------------------------------------
# auto-approve matching
# ---------------------------------------------------------------------------


def test_is_auto_approved_exact_match():
    cfg = MCPConfig(
        servers={"fetch": {"command": "x"}},
        auto_approve={"fetch": ["fetch"]},
    )
    mgr = MCPManager(config=cfg)
    assert mgr.is_auto_approved("fetch") is True
    assert mgr.is_auto_approved("fetch_fetch") is True  # server-prefixed form
    assert mgr.is_auto_approved("delete_everything") is False


def test_is_auto_approved_empty_config():
    mgr = MCPManager(config=MCPConfig())
    assert mgr.is_auto_approved("anything") is False


# ---------------------------------------------------------------------------
# Config loader
# ---------------------------------------------------------------------------


def test_load_config_missing_file(tmp_path: Path):
    cfg = load_config(tmp_path / "does-not-exist.json")
    assert cfg.is_empty
    assert cfg.auto_approve == {}


def test_load_config_malformed_json(tmp_path: Path):
    p = tmp_path / "bad.json"
    p.write_text("{not valid", encoding="utf-8")
    cfg = load_config(p)
    assert cfg.is_empty


def test_load_config_valid(tmp_path: Path):
    p = tmp_path / "mcp.json"
    p.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "fetch": {"command": "uvx", "args": ["mcp-server-fetch"]}
                },
                "auto_approve": {"fetch": ["fetch"]},
            }
        ),
        encoding="utf-8",
    )
    cfg = load_config(p)
    assert "fetch" in cfg.servers
    assert cfg.auto_approve == {"fetch": ["fetch"]}


def test_load_config_malformed_shape_falls_back(tmp_path: Path):
    p = tmp_path / "weird.json"
    p.write_text(json.dumps({"mcpServers": "not-a-dict"}), encoding="utf-8")
    cfg = load_config(p)
    assert cfg.is_empty


# ---------------------------------------------------------------------------
# mcp_call handler — HITL, Privacy Guard, error handling
# ---------------------------------------------------------------------------


def _mk_task(tool: str, args: dict | None = None) -> Task:
    """Build an MCP_CALL Task in flat shape: name=tool, params=args."""
    from typing import Any

    params: dict[str, Any] = {}
    for k, v in (args or {}).items():
        params[k] = v
    return Task(action=ActionTypeEnum.MCP_CALL, name=tool, params=params)


def test_handler_no_manager_returns_error():
    sess = SessionState()  # no mcp_manager
    t = _mk_task("echo", {"text": "hi"})
    r = mcp_call(t, sess)
    assert r.returncode == 1
    assert "not available" in r.stderr


def test_handler_disconnected_manager_returns_error(mcp_server: FastMCP):
    sess = SessionState()
    sess.mcp_manager = MCPManager(transport=mcp_server)  # not started
    t = _mk_task("echo", {"text": "hi"})
    r = mcp_call(t, sess)
    assert r.returncode == 1
    assert "not available" in r.stderr


def test_handler_missing_tool_param(manager: MCPManager):
    sess = SessionState()
    sess.mcp_manager = manager
    sess.confirm_fn = lambda _: True
    t = Task(action=ActionTypeEnum.MCP_CALL, name="", params={})
    r = mcp_call(t, sess)
    assert r.returncode == 1
    assert "missing" in r.stderr.lower()


def test_handler_requires_hitl_when_not_auto_approved(manager: MCPManager):
    sess = SessionState()
    sess.mcp_manager = manager
    calls: list[str] = []

    def confirm(prompt: str) -> bool:
        calls.append(prompt)
        return False  # user rejects

    sess.confirm_fn = confirm
    t = _mk_task("echo", {"text": "hi"})
    r = mcp_call(t, sess)
    assert r.skipped is True
    assert len(calls) == 1
    assert "echo" in calls[0]


def test_handler_skips_hitl_when_auto_approved(mcp_server: FastMCP):
    cfg = MCPConfig(auto_approve={"any": ["echo"]})
    mgr = MCPManager(config=cfg, transport=mcp_server)
    mgr.start()
    try:
        sess = SessionState()
        sess.mcp_manager = mgr
        called: list[str] = []
        sess.confirm_fn = lambda p: (called.append(p) or True)

        t = _mk_task("echo", {"text": "no hitl"})
        r = mcp_call(t, sess)
        assert r.returncode == 0
        assert called == []  # HITL was skipped
    finally:
        mgr.stop()


def test_handler_passes_args_through_without_masking(manager: MCPManager):
    sess = SessionState()
    sess.mcp_manager = manager
    sess.confirm_fn = lambda _: True

    t = _mk_task("echo", {"text": "write me at user@example.com"})
    r = mcp_call(t, sess)
    assert r.returncode == 0
    body = r.stdout
    assert "user@example.com" in body
    assert "[EMAIL_1]" not in body


def test_handler_reports_tool_error_as_failure(manager: MCPManager):
    sess = SessionState()
    sess.mcp_manager = manager
    sess.confirm_fn = lambda _: True

    t = _mk_task("fail")
    r = mcp_call(t, sess)
    assert r.returncode == 1
    assert r.stderr  # error message propagated


def test_handler_accepts_flat_task_shape(manager: MCPManager):
    """LLMs emit flat form: name=<tool>, params=<args dict>."""
    sess = SessionState()
    sess.mcp_manager = manager
    sess.confirm_fn = lambda _: True

    t = Task(
        action=ActionTypeEnum.MCP_CALL,
        name="echo",
        params={"text": "hello flat"},
    )
    r = mcp_call(t, sess)
    assert r.returncode == 0, r.stderr
    assert "hello flat" in r.stdout


def test_handler_rejects_server_name_used_as_tool(mcp_server: FastMCP):
    """A server name must not be accepted as a tool name."""
    from integrations.mcp_config import MCPConfig

    cfg = MCPConfig(
        servers={"fakeServerA": {"command": "noop"}},
        auto_approve={},
    )
    mgr = MCPManager(config=cfg, transport=mcp_server)
    mgr.start()
    try:
        sess = SessionState()
        sess.mcp_manager = mgr
        sess.confirm_fn = lambda _: True

        t = Task(
            action=ActionTypeEnum.MCP_CALL,
            name="fakeServerA",
            params={"query": "anything"},
        )
        r = mcp_call(t, sess)
        assert r.returncode == 1
        assert "server name" in r.stderr
        assert "not a tool" in r.stderr
        # Available tools list is surfaced for the self-correction loop.
        assert "echo" in r.stderr
    finally:
        mgr.stop()


def test_handler_flags_text_error_as_failure(manager: MCPManager):
    """MCP tool returns error as plain text + is_error=False.
    Handler must detect and surface it via stderr/rc=1 so the retry loop
    has a chance to self-correct."""
    sess = SessionState()
    sess.mcp_manager = manager
    sess.confirm_fn = lambda _: True

    t = Task(
        action=ActionTypeEnum.MCP_CALL,
        name="text_error",
        params={"query": "fastapi"},
    )
    r = mcp_call(t, sess)
    assert r.returncode == 1
    assert "Invalid library ID format" in r.stderr
    assert "Expected format" in r.stderr
    # stdout cleared so the LLM only sees error in stderr
    assert r.stdout == ""


def test_handler_does_not_flag_long_content_with_error_word(manager: MCPManager):
    """Real docs may mention 'error' mid-content. Must NOT be flagged."""
    sess = SessionState()
    sess.mcp_manager = manager
    sess.confirm_fn = lambda _: True

    t = Task(
        action=ActionTypeEnum.MCP_CALL,
        name="long_doc",
        params={"topic": "FastAPI"},
    )
    r = mcp_call(t, sess)
    assert r.returncode == 0, r.stderr
    assert "FastAPI" in r.stdout


def test_handler_rejects_unknown_tool_name_with_catalog(manager: MCPManager):
    sess = SessionState()
    sess.mcp_manager = manager
    sess.confirm_fn = lambda _: True

    t = Task(
        action=ActionTypeEnum.MCP_CALL,
        name="list_tools",  # common LLM hallucination — not a real tool
        params={},
    )
    r = mcp_call(t, sess)
    assert r.returncode == 1
    assert "Unknown MCP tool" in r.stderr
    assert "echo" in r.stderr and "add" in r.stderr


# ---------------------------------------------------------------------------
# Planner prompt injection
# ---------------------------------------------------------------------------


def test_format_mcp_tools_section_empty():
    assert format_mcp_tools_section([]) == ""


def test_format_mcp_tools_section_renders_tool_names_and_args():
    section = format_mcp_tools_section(
        [
            {
                "name": "calendar_create_event",
                "description": "Create a Google Calendar event.",
                "input_schema": {
                    "properties": {
                        "summary": {"type": "string"},
                        "start": {"type": "string"},
                        "end": {"type": "string"},
                    }
                },
            },
            {
                "name": "fetch",
                "description": "Fetch a URL and return its text.",
                "input_schema": None,
            },
        ]
    )
    assert "calendar_create_event(summary: str, start: str, end: str)" in section
    assert "Create a Google Calendar event." in section
    assert "fetch" in section
    assert "Fetch a URL" in section
    # schema-less tools must not be skipped
    assert "- fetch" in section


def test_format_mcp_tools_section_truncates_long_description():
    # Truncation kicks in for pathological descriptions (>500 chars).
    long_desc = "x" * 2000
    section = format_mcp_tools_section(
        [{"name": "big", "description": long_desc, "input_schema": None}]
    )
    assert "..." in section
    tool_lines = [ln for ln in section.splitlines() if ln.startswith("- big")]
    assert len(tool_lines) == 1
    assert len(tool_lines[0]) < 700  # bounded, not unlimited


def test_build_system_prompt_includes_mcp_section_when_given():
    mcp_part = "Available MCP tools:\n- foo\n- bar"
    prompt = build_system_prompt(mcp_part)
    assert "Available MCP tools" in prompt
    assert "- foo" in prompt


def test_build_system_prompt_unchanged_when_no_mcp():
    prompt = build_system_prompt("")
    assert "Available MCP tools" not in prompt
