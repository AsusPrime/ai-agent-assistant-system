import asyncio
import threading
from typing import Any

from fastmcp import Client

from integrations.mcp_config import AkashiMCPConfig


class MCPNotConnectedError(RuntimeError):
    pass


class MCPManager:
    """Sync façade over fastmcp.Client running in a background event loop.

    fastmcp.Client is async and its session is a context manager. Akashi's
    executor/handlers are sync, so we run the client inside a persistent
    asyncio loop on a background thread and expose sync methods that block
    on `asyncio.run_coroutine_threadsafe(...).result()`.
    """

    def __init__(
        self,
        config: AkashiMCPConfig | None = None,
        transport: Any = None,
    ):
        """One of `config` or `transport` is used. `transport` is for tests —
        pass a FastMCP instance or any value accepted by `fastmcp.Client`.
        """
        self._config = config or AkashiMCPConfig()
        self._transport = transport
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._client: Client | None = None
        self._connected = False
        self._tools_cache: list[dict[str, Any]] | None = None

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def config(self) -> AkashiMCPConfig:
        return self._config

    def start(self, timeout: float = 15.0) -> None:
        if self._connected:
            return
        if self._transport is None and self._config.is_empty:
            return

        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self._loop.run_forever, daemon=True, name="MCPLoop"
        )
        self._thread.start()

        transport = (
            self._transport
            if self._transport is not None
            else self._config.fastmcp_config()
        )

        async def _enter() -> Client:
            c = Client(transport)
            await c.__aenter__()
            return c

        fut = asyncio.run_coroutine_threadsafe(_enter(), self._loop)
        self._client = fut.result(timeout=timeout)
        self._connected = True

    def stop(self, timeout: float = 5.0) -> None:
        if not self._connected:
            return
        try:
            if self._client is not None and self._loop is not None:
                fut = asyncio.run_coroutine_threadsafe(
                    self._client.__aexit__(None, None, None), self._loop
                )
                fut.result(timeout=timeout)
        finally:
            self._connected = False
            self._tools_cache = None
            if self._loop is not None:
                self._loop.call_soon_threadsafe(self._loop.stop)
            if self._thread is not None:
                self._thread.join(timeout=timeout)
            self._client = None
            self._loop = None
            self._thread = None

    def list_tools(
        self, timeout: float = 10.0, refresh: bool = False
    ) -> list[dict[str, Any]]:
        if self._tools_cache is not None and not refresh:
            return self._tools_cache
        self._require_connected()
        fut = asyncio.run_coroutine_threadsafe(self._client.list_tools(), self._loop)
        raw = fut.result(timeout=timeout)
        self._tools_cache = [
            {
                "name": t.name,
                "description": t.description or "",
                "input_schema": getattr(t, "inputSchema", None),
            }
            for t in raw
        ]
        return self._tools_cache

    def call_tool(
        self,
        name: str,
        arguments: dict | None = None,
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        self._require_connected()
        fut = asyncio.run_coroutine_threadsafe(
            self._client.call_tool(name, arguments or {}, raise_on_error=False),
            self._loop,
        )
        result = fut.result(timeout=timeout)
        text_parts = []
        for c in result.content or []:
            text = getattr(c, "text", None)
            if text:
                text_parts.append(text)
        return {
            "is_error": bool(result.is_error),
            "text": "\n".join(text_parts),
            "data": result.data,
            "structured": result.structured_content,
        }

    def is_auto_approved(self, tool_name: str) -> bool:
        """Check if a fully-qualified MCP tool name is in auto_approve list.

        Tool names in multi-server mode are prefixed by the server (e.g.
        "fetch_fetch"). We check against the server-scoped whitelist.
        """
        for server, approved in self._config.auto_approve.items():
            for t in approved:
                if tool_name == t or tool_name == f"{server}_{t}":
                    return True
        return False

    def _require_connected(self) -> None:
        if not self._connected or self._client is None or self._loop is None:
            raise MCPNotConnectedError("MCPManager is not started")
