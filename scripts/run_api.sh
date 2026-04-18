#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/src"

HOST="${API_HOST:-127.0.0.1}"
PORT="${API_PORT:-8000}"

exec "$ROOT/.venv/bin/uvicorn" api.server:app --host "$HOST" --port "$PORT" --reload
