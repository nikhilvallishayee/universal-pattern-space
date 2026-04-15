
#!/usr/bin/env bash

# Check if jq is installed
if ! command -v jq &>/dev/null; then
  echo "Warning: jq is not installed. JSON output will not be pretty-printed."
  echo "Install jq for better output formatting."
  JQ_AVAILABLE=false
else
  JQ_AVAILABLE=true
fi
set -euo pipefail

# Quick, self-cleaning smoke test of the unified server.
# Starts uvicorn in the background, probes endpoints, and exits cleanly.

HOST="127.0.0.1"
PORT="${GODELOS_PORT:-8000}"
LOG_LEVEL="warning"
APP="backend.unified_server:app"

# Endpoints to probe (space-separated)
ENDPOINTS=("/api/health" "/cognitive/state")

if [[ $# -gt 0 ]]; then
  ENDPOINTS=("$@")
fi

server_pid=""

cleanup() {
  if [[ -n "${server_pid}" ]] && kill -0 "${server_pid}" 2>/dev/null; then
    kill "${server_pid}" 2>/dev/null || true
    # Give it a moment to exit
    sleep 1
    kill -KILL "${server_pid}" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

echo "Starting server: uvicorn ${APP} on http://${HOST}:${PORT}"
python -m uvicorn "${APP}" --host "${HOST}" --port "${PORT}" --log-level "${LOG_LEVEL}" &
server_pid=$!

# Wait for readiness
attempts=0
max_attempts=40
until curl -sf "http://${HOST}:${PORT}/api/health" >/dev/null 2>&1; do
  attempts=$((attempts+1))
  if [[ ${attempts} -ge ${max_attempts} ]]; then
    echo "Server failed to become ready within $((max_attempts))s" >&2
    exit 1
  fi
  sleep 1
done

echo "Server is ready. Probing endpoints..."
for ep in "${ENDPOINTS[@]}"; do
  echo "==> GET ${ep}"
  if [ "$JQ_AVAILABLE" = true ]; then
    curl -sf "http://${HOST}:${PORT}${ep}" | jq '.' || true
  else
    curl -sf "http://${HOST}:${PORT}${ep}" | head -c 400 || true
  fi
  echo "---"
done

echo "Smoke test complete. Shutting down server."

