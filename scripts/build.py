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
ENTRY = SRC / "ui" / "app.py"
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
        f"{ASSETS}{_sep()}{_asset_dest()}",
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


def _asset_dest() -> str:
    return "ui/assets"


if __name__ == "__main__":
    build()
