# AI Agent Assistant System

Multi-agent desktop assistant that controls a PC and cloud services through natural language.
Built as a bachelor's thesis project (Computer Engineering, Chernivtsi National University, 2026).

Core principles: **security**, **privacy** and **human-in-the-loop** — the assistant never
executes an action the user has not seen and approved, and personal data is masked before it
leaves the machine.

## What it does

- Takes a request in plain language ("open the browser and find today's weather", "summarise
  this folder of notes", "send a greeting to ...").
- An **orchestrator** decides whether one agent can handle it or the request has to be split
  into sub-tasks for specialised agents.
- Each task is validated against a **whitelist** of allowed apps, commands and scripts, shown to
  the user as a dry run, and executed only after confirmation.
- The result comes back to a floating always-on-top desktop bar with per-task status cards.

## Architecture

```
User input
   └─> Privacy Guard          masks PII before anything is sent to a cloud LLM
   └─> Orchestrator           simple (one agent) or complex (multi-agent) request?
         ├─> Planner          ReAct loop for simple requests
         └─> Specialised agents, run sequentially with results passed between them
               ├─ Researcher          web search, web read, HTTP APIs
               ├─ Writer              file creation, text composition
               ├─ System Controller   apps, shell commands, OS control
               └─ General             chat / fallback
   └─> Executor               maps validated Tasks to the Tool Registry
         └─> Tools            OS handlers (Windows / POSIX), web, HTTP, MCP servers, RAG, recipes
```

**Agents are data, not code.** Every agent is a JSON config (`src/agents/*.json`) with its own
system prompt and can be created, edited, enabled or disabled from the UI or the REST API.

**Tools are pluggable.** Besides the built-in handlers, the assistant connects to external
[MCP](https://modelcontextprotocol.io) servers (`examples/mcp_servers.example.json`) and exposes
their tools to the agents. Standalone Python scripts dropped into `skills/` and whitelisted become
callable actions without a restart.

**Recipes** (`src/recipes/*.json`) are reusable multi-step scenarios such as a "morning briefing"
or a system status report.

**Memory.** Short-term conversation memory plus a local vector store (ChromaDB) for a personal
knowledge base that agents can query (RAG).

## Stack

| Layer | Technology |
|---|---|
| Agent framework | [PydanticAI](https://ai.pydantic.dev) + Pydantic v2 (typed, validated LLM outputs) |
| LLM providers | Google Gemini (default), OpenAI-compatible APIs, Ollama for local models |
| API | FastAPI (`localhost:8000`) — the UI is a thin client over it |
| Desktop UI | PySide6: frameless floating bar, system tray, task cards, animated character |
| Tool protocol | MCP client for external tool servers |
| Knowledge base | ChromaDB vector store |
| Observability | Logfire / OpenTelemetry |
| Packaging | PyInstaller → `.app` / `.exe` / ELF |

## Security model

- Every `Task.action` is checked against `src/tools/whitelist.json` at model construction time;
  shell commands are checked again right before `subprocess.run`.
- Destructive or system-changing actions always go through human confirmation.
- The Privacy Guard masks PII before any prompt reaches a cloud model; local models via Ollama
  can be used for fully offline operation.

## Running it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # set LLM_PROVIDER, API_KEY, MODEL_NAME

# API server
./scripts/run_api.sh            # or: cd src && python -m api.server

# desktop UI (talks to the API)
./scripts/run_ui.sh             # or: cd src && python -m ui.app

# CLI REPL with human-in-the-loop confirmation
cd src && python main.py
```

Build a standalone binary:

```bash
python scripts/build.py         # → dist/Akashi
```

Configuration lives in `.env` (see `.env.example` for every option: LLM, ReAct limits, web and
HTTP timeouts, MCP, knowledge base, UI language `uk`/`en`).

## Project layout

```
src/
  api/             FastAPI server and request/response schemas
  core/            orchestrator, planner, executor, privacy guard, memory, session, vector store
  infrastructure/  LLM client factory
  integrations/    MCP client and config
  tools/           tool registry, OS/web/HTTP/MCP/RAG/recipe handlers, whitelist
  recipes/         reusable multi-step scenarios
  ui/              PySide6 desktop client
scripts/           run / build helpers
examples/          MCP server config example
```

## License

See [LICENSE](LICENSE).
