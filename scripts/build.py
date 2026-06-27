"""
Cross-platform build script for AIAssistant UI.
Produces:
  - Windows: dist/AIAssistant.exe
  - macOS:   dist/AIAssistant.app
  - Linux:   dist/AIAssistant (ELF binary)

Usage:
  python scripts/build.py
"""

from __future__ import annotations

import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
ENTRY = SRC / "launcher.py"
ASSETS = SRC / "ui" / "assets"
DIST = ROOT / "dist"
ICON_WIN = ASSETS / "icon.ico"
ICON_MAC = ASSETS / "icon.icns"


def build() -> None:
    if not ENTRY.exists():
        print(f"Entry point not found: {ENTRY}")
        sys.exit(1)

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name",
        "AIAssistant",
        "--onefile",
        "--noconsole",
        "--distpath",
        str(DIST),
        "--workpath",
        str(ROOT / "build"),
        "--specpath",
        str(ROOT),
        "--add-data",
        f"{ASSETS}{_sep()}ui/assets",
        "--add-data",
        f"{SRC / 'tools' / 'whitelist.json'}{_sep()}tools",
        "--add-data",
        f"{SRC / 'agents'}{_sep()}agents",
        "--add-data",
        f"{SRC / 'recipes'}{_sep()}recipes",
        "--hidden-import", "uvicorn.logging",
        "--hidden-import", "uvicorn.loops.auto",
        "--hidden-import", "uvicorn.protocols.http.auto",
        "--hidden-import", "uvicorn.lifespan.on",
        "--paths",
        str(SRC),
    ]

    os_name = platform.system()

    if os_name == "Windows" and ICON_WIN.exists():
        cmd.extend(["--icon", str(ICON_WIN)])
    elif os_name == "Darwin":
        cmd.append("--windowed")
        if ICON_MAC.exists():
            cmd.extend(["--icon", str(ICON_MAC)])
    # Linux: no special flags needed

    cmd.append(str(ENTRY))

    print(f"Building for {os_name}...")
    print(f"Command: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    print(f"\nDone! Output: {DIST}/")


def _sep() -> str:
    return ";" if platform.system() == "Windows" else ":"



if __name__ == "__main__":
    build()
