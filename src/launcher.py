"""
Single entry point: starts API server in a background thread, then launches the GUI.
Used by PyInstaller to produce a standalone executable.
"""
from __future__ import annotations

import sys
import threading
import time

import uvicorn


def _run_server() -> None:
    uvicorn.run("api.server:app", host="127.0.0.1", port=8000, log_level="warning")


def main() -> None:
    server_thread = threading.Thread(target=_run_server, daemon=True)
    server_thread.start()
    time.sleep(0.5)

    from ui.app import AssistantApp
    app = AssistantApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
