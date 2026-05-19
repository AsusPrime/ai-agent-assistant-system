# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**AI Multi-Agent Assistant System** — дипломний проєкт. Мульти-агентна система для оркестрації локальних операцій ПК та хмарних сервісів. Ключові принципи: Security, Privacy, Human-in-the-Loop (HITL).

Майбутня функція: користувач сам конфігурує набір агентів та схему оркестрації (додає/видаляє агентів), але в системі є набір стандартних агентів за замовчуванням.

## Commands

```bash
# Activate venv
source .venv/bin/activate

# Run entry point
cd src && python main.py

# Install dependencies
pip install -r requirements.txt
```

## Architecture

**Framework:** PydanticAI + Pydantic v2 (strict typing, type-safe AI responses).
**Primary LLM:** Google Gemini via `pydantic_ai.models.google.GoogleModel` + `GoogleProvider`. Ollama — for local dev/testing.
**State management:** Redis (planned).
**Memory:** ChromaDB/FAISS + SQLite (planned).

### Agent Hierarchy (Manager-Worker / Supervisor pattern)

```
User Input
    └─> Planner Agent       — decomposes intent into Task list
            └─> Executor Agent  — maps Tasks to Tool Registry functions
                    ├─> Privacy Agent   — masks PII before sending to cloud LLM
                    └─> Validator Agent — verifies output
```

### Brain Layer (Week 2 — implemented)

Data flow: `user input` → `planner_agent` → `Task` → HITL confirm → `Executor`

- `src/config.py` — `Settings` (pydantic-settings); reads `.env` via `find_dotenv`. Fields: `LLM_PROVIDER`, `API_KEY`, `MODEL_NAME`.
- `src/infrastructure/llm_client.py` — `get_model()` factory; returns `GoogleModel` or `OpenAIChatModel`.
- `src/core/planner.py` — `planner_agent = Agent(model, output_type=Task, system_prompt=...)`. System prompt dynamically injects whitelist contents.
- `src/main.py` — REPL loop with HITL: LLM → dry-run print → confirm `y/N` → execute.

### Execution Layer (Week 1 — implemented)

Data flow: `Task (Pydantic model)` → `Executor` → `TOOL_REGISTRY` → `OSHandler`

- `src/core/schemas.py` — `Task` model; validates `action` against `whitelist.json` on construction. `CHAT` action skips whitelist check.
- `src/core/enums.py` — `ActionTypeEnum` (open_app, run_command, run_skill, chat).
- `src/core/executor.py` — `Executor.execute(task)` dispatches to registry.
- `src/core/base_os.py` — `BaseOSHandler` ABC with `open_application` / `run_shell`.
- `src/tools/registry.py` — `TOOL_REGISTRY` dict mapping action names to callables.
- `src/tools/handlers.py` — concrete tool functions (`open_app`, `run_command`, `run_skill`).
- `src/tools/os_handlers.py` — `WindowsHandler` / `PosixHandler` (Strategy pattern).
- `src/tools/os_factory.py` — `get_os_handler()` selects handler by `platform.system()`.
- `src/tools/whitelist.json` — security whitelist: `allowed_apps`, `allowed_commands`, `allowed_scripts`.

### Dynamic Tool / Skills System

- Skills are standalone Python scripts placed in `skills/` folder.
- Whitelisted via `src/tools/whitelist.json` (`allowed_scripts` array) — no restart needed.
- New action types must be added to `ActionTypeEnum` **and** `TOOL_REGISTRY`.

### Security Invariants

- Every `Task.action` is validated against `whitelist.json` at Pydantic model construction time.
- Shell commands (`run_terminal_command`) are also checked against `allowed_commands` before `subprocess.run`.
- Critical actions (file deletion, system changes) must go through HITL confirmation — never bypass.
- PII masking by Privacy Agent must happen **before** any data reaches a cloud LLM.

### UI Layer (Desktop GUI)

Floating always-on-top bar powered by PySide6. Thin client — sends queries to `localhost:8000/query` API.

- `src/ui/app.py` — `AkashiApp`: QApplication + system tray (show/hide/quit)
- `src/ui/main_window.py` — `FloatingBar`: frameless, always-on-top, draggable window
- `src/ui/input_bar.py` — `InputBar`: text input widget, emits `submitted` signal on Enter
- `src/ui/status_card.py` — `StatusPanel` + `TaskCard`: task execution cards with status dots
- `src/ui/tamagotchi.py` — `TamagotchiWidget`: animated kaomoji character with bounce animations
- `src/ui/emotions.py` — `Emotion` enum, `TimeOfDay`, rule-based emotion mapper
- `src/ui/fonts.py` — cross-platform font family resolver (macOS/Windows/Linux)
- `src/ui/api_client.py` — `AkashiApiClient`: HTTP client in QThread, signals for query lifecycle
- `src/ui/assets/` — SVG icon, future sprites

Launch: `scripts/run_ui.sh` or `cd src && python -m ui.app`
Build: `python scripts/build.py` → `dist/Akashi` (.exe / .app / ELF)

## Key Dependencies

| Package | Purpose |
|---|---|
| `pydantic-ai` | Agent framework |
| `pydantic v2` | Schema validation, type-safe models |
| `google-genai` | Primary LLM (Gemini) |
| `anthropic` | Claude API (alternative LLM) |
| `python-dotenv` | Env config |
| `redis` | State management (planned) |
| `logfire` | Observability |
| `mcp` | MCP protocol support |
| `PySide6` | Desktop GUI (floating bar, system tray) |
| `PyInstaller` | Cross-platform packaging (.exe / .app / ELF) |

## Import Paths

`main.py` runs from `src/` directory, so all imports are relative to `src/` — no `src.` prefix anywhere (e.g. `from core.schemas import Task`, `from infrastructure.llm_client import get_model`).

## pydantic-ai API (v1.63+)

- `Agent(model, output_type=Task, ...)` — not `result_type`
- `result.output` — not `result.data`
- `GoogleModel` from `pydantic_ai.models.google` — API key via `provider=GoogleProvider(api_key=...)`
- `OpenAIChatModel` from `pydantic_ai.models.openai` — not deprecated `OpenAIModel`
- `GeminiModel` and `OpenAIModel` are deprecated — do not use
