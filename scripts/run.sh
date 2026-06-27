#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/src"

HOST="${API_HOST:-127.0.0.1}"
PORT="${API_PORT:-8000}"

cleanup() {
    echo "Shutting down..."
    kill "$API_PID" 2>/dev/null
    wait "$API_PID" 2>/dev/null
    exit 0
}
trap cleanup INT TERM

"$ROOT/.venv/bin/uvicorn" api.server:app --host "$HOST" --port "$PORT" --reload &
API_PID=$!

sleep 1

python -m ui.app "$@"

cleanup
