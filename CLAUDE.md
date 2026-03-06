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
**Primary LLM:** Google Gemini (via `google-genai`). Ollama — for local dev/testing.
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

### Execution Layer (current focus)

Data flow: `Task (Pydantic model)` → `Executor` → `TOOL_REGISTRY` → `OSHandler`

- `src/core/schemas.py` — `Task` model; validates `action` against `whitelist.json` on construction.
- `src/core/enums.py` — `ActionTypeEnum` (open_app, run_command, run_skill).
- `src/core/executor.py` — `Executor.execute(task)` dispatches to registry.
- `src/core/base_os.py` — `BaseOSHandler` ABC with `open_application` / `run_shell`.
- `src/tools/registry.py` — `TOOL_REGISTRY` dict mapping action names to callables.
- `src/tools/handlers.py` — concrete tool functions (`run_terminal_command`, `run_python_skill`).
- `src/tools/os_handlers.py` — `WindowsHandler` / `PosixHandler` (Strategy pattern).
- `src/tools/os_factory.py` — `get_os_handler()` selects handler by `platform.system()`.
- `src/tools/whitelist.json` — security whitelist: `allowed_commands`, `allowed_scripts`.

### Dynamic Tool / Skills System

- Skills are standalone Python scripts placed in `skills/` folder.
- Whitelisted via `src/tools/whitelist.json` (`allowed_scripts` array) — no restart needed.
- New action types must be added to `ActionTypeEnum` **and** `TOOL_REGISTRY`.

### Security Invariants

- Every `Task.action` is validated against `whitelist.json` at Pydantic model construction time.
- Shell commands (`run_terminal_command`) are also checked against `allowed_commands` before `subprocess.run`.
- Critical actions (file deletion, system changes) must go through HITL confirmation — never bypass.
- PII masking by Privacy Agent must happen **before** any data reaches a cloud LLM.

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

## Import Paths

`main.py` runs from `src/` directory, so imports are relative to `src/` (e.g. `from core.schemas import Task`). Files inside `src/` that import each other use full `src.` prefix (e.g. `from src.core.base_os import BaseOSHandler`). Keep this consistent when adding new modules.
