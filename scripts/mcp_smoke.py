"""MCP smoke test: connect to all configured servers and list tools.

Usage:
    cd src && python ../scripts/mcp_smoke.py
    cd src && python ../scripts/mcp_smoke.py --call fetch:fetch '{"url": "https://example.com"}'

Exits 0 on success, 1 if MCP did not connect.
"""

import argparse
import json
import sys
from pathlib import Path

# Allow running from repo root or from src/. Match main.py convention.
ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from config import settings
from integrations.mcp_client import MCPManager
from integrations.mcp_config import load_config


def _print_tools(manager: MCPManager) -> None:
    tools = manager.list_tools()
    if not tools:
        print("[!] No tools discovered (servers connected but list_tools empty).")
        return

    print(f"\n[OK] Discovered {len(tools)} tool(s):\n")
    width = max(len(t["name"]) for t in tools) + 2
    for t in tools:
        desc = (t.get("description") or "").splitlines()[0][:80]
        print(f"  {t['name']:<{width}} {desc}")


def _print_auto_approve(manager: MCPManager) -> None:
    aa = manager.config.auto_approve
    if not aa:
        print("\n[i] No auto_approve entries — every tool call goes through HITL.")
        return
    print("\n[i] auto_approve (HITL skipped for these):")
    for server, names in aa.items():
        print(f"  {server}: {', '.join(names)}")


def _do_call(manager: MCPManager, target: str, args_json: str) -> int:
    if ":" not in target:
        print(f"[!] --call expects 'server:tool', got {target!r}")
        return 2
    server, tool = target.split(":", 1)
    full_name = f"{server}_{tool}"
    try:
        args = json.loads(args_json) if args_json else {}
    except json.JSONDecodeError as e:
        print(f"[!] Invalid JSON in args: {e}")
        return 2

    forced = manager.config.default_args.get(server, {})
    args = {**args, **forced}

    print(f"\n[>] calling {full_name} with {args!r}")
    try:
        out = manager.call_tool(full_name, args)
    except Exception as e:
        print(f"[X] call_tool raised: {e}")
        return 1
    print(f"  is_error: {out['is_error']}")
    text = out.get("text") or ""
    print(f"  text:    {text[:400]}{'...' if len(text) > 400 else ''}")
    return 1 if out["is_error"] else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="MCP smoke test")
    parser.add_argument(
        "--call",
        nargs=2,
        metavar=("SERVER:TOOL", "ARGS_JSON"),
        help="Optionally invoke a tool, e.g. --call fetch:fetch '{\"url\":\"...\"}'",
    )
    args = parser.parse_args()

    cfg = load_config(settings.MCP_CONFIG_PATH)
    if cfg.is_empty:
        print(f"[!] No MCP config at {settings.MCP_CONFIG_PATH} (or empty).")
        print("    Copy examples/mcp_servers.example.json and edit.")
        return 1

    print(f"[i] config: {settings.MCP_CONFIG_PATH}")
    print(f"[i] servers: {', '.join(cfg.servers.keys())}")

    manager = MCPManager(config=cfg)
    try:
        manager.start(timeout=30.0)
    except Exception as e:
        print(f"[X] MCPManager.start() failed: {e}")
        return 1

    if not manager.connected:
        print("[X] MCPManager did not connect.")
        return 1

    try:
        _print_tools(manager)
        _print_auto_approve(manager)
        if args.call:
            return _do_call(manager, args.call[0], args.call[1])
        return 0
    finally:
        manager.stop()


if __name__ == "__main__":
    sys.exit(main())
