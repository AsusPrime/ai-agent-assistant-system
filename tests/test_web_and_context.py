"""Web/HTTP handlers + context-awareness contract tests.

Verifies:
- web_search/web_read/http_request return the expected TaskResult shape
  with mocked network calls (no real HTTP).
- AkashiCore feeds prior message_history back into the planner on the next
  query (the "context awareness" invariant from W6).
"""

import json
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from core.enums import ActionTypeEnum  # noqa: E402
from core.schemas import Plan, Task  # noqa: E402
from core.session import SessionState  # noqa: E402


# ---------------------------------------------------------------------------
# web_search
# ---------------------------------------------------------------------------


def test_web_search_returns_trimmed_json():
    from tools import web_handlers

    fake_results = [
        {"title": "T1", "href": "https://a.test", "body": "snip1"},
        {"title": "T2", "href": "https://b.test", "body": "snip2"},
    ]

    with patch.object(web_handlers, "DDGS") as ddgs_cls:
        ddgs_cls.return_value.text.return_value = fake_results
        task = Task(
            action=ActionTypeEnum.WEB_SEARCH,
            name="ddg",
            params={"query": "anything", "max_results": "2"},
        )
        result = web_handlers.web_search(task=task, session=SessionState())

    assert result.returncode == 0
    parsed = json.loads(result.stdout)
    assert parsed == [
        {"title": "T1", "url": "https://a.test", "snippet": "snip1"},
        {"title": "T2", "url": "https://b.test", "snippet": "snip2"},
    ]


def test_web_search_empty_query_fails():
    from tools.web_handlers import web_search

    task = Task(action=ActionTypeEnum.WEB_SEARCH, name="", params={"query": ""})
    result = web_search(task=task, session=SessionState())
    assert result.returncode == 1
    assert "empty" in result.stderr


def test_web_search_handles_provider_exception():
    from tools import web_handlers

    with patch.object(web_handlers, "DDGS") as ddgs_cls:
        ddgs_cls.return_value.text.side_effect = RuntimeError("boom")
        task = Task(
            action=ActionTypeEnum.WEB_SEARCH, name="x", params={"query": "x"}
        )
        result = web_handlers.web_search(task=task, session=SessionState())

    assert result.returncode == 1
    assert "boom" in result.stderr


# ---------------------------------------------------------------------------
# web_read
# ---------------------------------------------------------------------------


def test_web_read_extracts_main_text():
    from tools import web_handlers

    html = "<html><body><article><p>hello world</p></article></body></html>"
    fake_resp = MagicMock(text=html)
    fake_resp.raise_for_status.return_value = None

    with (
        patch.object(web_handlers.httpx, "get", return_value=fake_resp),
        patch.object(web_handlers.trafilatura, "extract", return_value="hello world"),
    ):
        task = Task(
            action=ActionTypeEnum.WEB_READ,
            name="page",
            params={"url": "https://example.com"},
        )
        result = web_handlers.web_read(task=task, session=SessionState())

    assert result.returncode == 0
    assert result.stdout == "hello world"


def test_web_read_rejects_invalid_scheme():
    from tools.web_handlers import web_read

    task = Task(
        action=ActionTypeEnum.WEB_READ, name="bad", params={"url": "ftp://x"}
    )
    result = web_read(task=task, session=SessionState())
    assert result.returncode == 1
    assert "scheme" in result.stderr


def test_web_read_truncates_long_text():
    from tools import web_handlers

    long_text = "x" * 20_000
    fake_resp = MagicMock(text="<html/>")
    fake_resp.raise_for_status.return_value = None
    with (
        patch.object(web_handlers.httpx, "get", return_value=fake_resp),
        patch.object(web_handlers.trafilatura, "extract", return_value=long_text),
    ):
        task = Task(
            action=ActionTypeEnum.WEB_READ,
            name="page",
            params={"url": "https://example.com"},
        )
        result = web_handlers.web_read(task=task, session=SessionState())
    assert "[truncated]" in result.stdout
    assert len(result.stdout) < len(long_text)


# ---------------------------------------------------------------------------
# http_request
# ---------------------------------------------------------------------------


def test_http_request_get_success():
    from tools import api_handler

    fake_resp = MagicMock(
        status_code=200,
        headers={"x-test": "1"},
        text='{"ok":true}',
        is_success=True,
    )
    with patch.object(api_handler.httpx, "request", return_value=fake_resp) as req:
        task = Task(
            action=ActionTypeEnum.HTTP_REQUEST,
            name="api",
            params={"method": "GET", "url": "https://api.test/x"},
        )
        result = api_handler.http_request(task=task, session=SessionState())

    assert result.returncode == 0
    assert req.call_args.args[0] == "GET"
    body = json.loads(result.stdout)
    assert body["status_code"] == 200
    assert "ok" in body["body"]


def test_http_request_rejects_unknown_method():
    from tools.api_handler import http_request

    task = Task(
        action=ActionTypeEnum.HTTP_REQUEST,
        name="api",
        params={"method": "BOGUS", "url": "https://x.test"},
    )
    result = http_request(task=task, session=SessionState())
    assert result.returncode == 1
    assert "method not allowed" in result.stderr


def test_http_request_invalid_json_body():
    from tools.api_handler import http_request

    task = Task(
        action=ActionTypeEnum.HTTP_REQUEST,
        name="api",
        params={
            "method": "POST",
            "url": "https://x.test",
            "json": "{not valid",
        },
    )
    result = http_request(task=task, session=SessionState())
    assert result.returncode == 1
    assert "json" in result.stderr.lower()


def test_http_request_http_error_returns_failure():
    from tools import api_handler

    with patch.object(
        api_handler.httpx, "request", side_effect=api_handler.httpx.ConnectError("nope")
    ):
        task = Task(
            action=ActionTypeEnum.HTTP_REQUEST,
            name="api",
            params={"method": "GET", "url": "https://x.test"},
        )
        result = api_handler.http_request(task=task, session=SessionState())
    assert result.returncode == 1
    assert "request failed" in result.stderr


# ---------------------------------------------------------------------------
# Context awareness: planner receives prior history on the second turn
# ---------------------------------------------------------------------------


class _FakeRun:
    """Mimics pydantic-ai run result: .output + .all_messages()."""

    def __init__(self, plan: Plan, messages: list):
        self.output = plan
        self._messages = messages

    def all_messages(self):
        return list(self._messages)


def test_second_query_receives_prior_message_history(tmp_path):
    """
    Invariant: after a turn that produced a web_search result,
    the next planner.run_sync call must be invoked with a non-empty
    message_history kwarg.
    """
    os.environ["DATA_DIR"] = str(tmp_path)
    # Re-import settings so DATA_DIR is picked up fresh
    from importlib import reload

    import config
    reload(config)
    from core import akashi
    reload(akashi)

    plan_search = Plan(
        tasks=[
            Task(
                action=ActionTypeEnum.WEB_SEARCH,
                name="ddg",
                params={"query": "weather kyiv"},
            )
        ]
    )
    plan_chat = Plan(
        tasks=[Task(action=ActionTypeEnum.CHAT, name="It is 12C, cloudy.")]
    )

    turn1_msgs = ["MSG_FROM_TURN_1"]
    turn2_msgs = turn1_msgs + ["MSG_FROM_TURN_2"]

    fake_search_result = [{"title": "Kyiv weather", "href": "https://w.test", "body": "12C cloudy"}]

    with (
        patch("core.akashi.planner_agent") as planner,
        patch("core.akashi.summary_agent") as summary,
        patch("tools.web_handlers.DDGS") as ddgs_cls,
    ):
        planner.run_sync.side_effect = [
            _FakeRun(plan_search, turn1_msgs),
            _FakeRun(plan_chat, turn2_msgs),
        ]
        summary.run_sync.return_value = MagicMock(output="done")
        ddgs_cls.return_value.text.return_value = fake_search_result

        core = akashi.AkashiCore(
            confirm_fn=lambda _m: True, on_message=lambda _m: None
        )
        # both queries
        r1 = core.process_query("what is the weather in Kyiv?")
        r2 = core.process_query("what was the result?")

    assert r1.summary == "done"
    assert r2.is_chat is True
    assert r2.reply == "It is 12C, cloudy."

    # Two planner invocations
    assert planner.run_sync.call_count == 2

    first_call = planner.run_sync.call_args_list[0]
    second_call = planner.run_sync.call_args_list[1]

    # First call: empty history (fresh session, tmp DATA_DIR)
    assert first_call.kwargs.get("message_history") == []
    # Second call: history from turn 1 must be present
    assert turn1_msgs[0] in (second_call.kwargs.get("message_history") or [])
