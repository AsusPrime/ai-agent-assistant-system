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
    `default_args` is an Akashi-specific map: server_name -> dict of args that
    are merged into every tool call for that server and OVERRIDE any LLM-supplied
    values. Use for identity/auth fields the LLM cannot know (e.g. mcp-gsuite's
    __user_id__, which must equal an email from accounts.json).
    """

    servers: dict = field(default_factory=dict)
    auto_approve: dict[str, list[str]] = field(default_factory=dict)
    default_args: dict[str, dict] = field(default_factory=dict)

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

    default_args: dict[str, dict] = {}
    servers_clean: dict = {}
    for name, spec in servers.items():
        if isinstance(spec, dict):
            da = spec.get("default_args")
            if isinstance(da, dict) and da:
                default_args[name] = da
            servers_clean[name] = {k: v for k, v in spec.items() if k != "default_args"}
        else:
            servers_clean[name] = spec

    return AkashiMCPConfig(
        servers=servers_clean,
        auto_approve=auto_approve,
        default_args=default_args,
    )
