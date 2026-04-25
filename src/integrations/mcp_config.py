import json
import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AkashiMCPConfig:
    """Parsed Akashi MCP config.

    `servers` is the raw fastmcp-compatible mcpServers dict.
    `auto_approve` is an Akashi-specific map: server_name -> list of tool names
    that skip HITL confirmation (read-only operations).
    """

    servers: dict = field(default_factory=dict)
    auto_approve: dict[str, list[str]] = field(default_factory=dict)

    @property
    def is_empty(self) -> bool:
        return not self.servers

    def fastmcp_config(self) -> dict:
        return {"mcpServers": self.servers}


def load_config(path: str | os.PathLike) -> AkashiMCPConfig:
    p = Path(path).expanduser()
    if not p.exists():
        return AkashiMCPConfig()
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return AkashiMCPConfig()
    servers = raw.get("mcpServers") or {}
    auto_approve = raw.get("auto_approve") or {}
    if not isinstance(servers, dict) or not isinstance(auto_approve, dict):
        return AkashiMCPConfig()
    return AkashiMCPConfig(servers=servers, auto_approve=auto_approve)
