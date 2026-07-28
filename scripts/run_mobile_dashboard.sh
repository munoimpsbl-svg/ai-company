#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${1:-8510}"
HOST="0.0.0.0"
PID_FILE="$ROOT_DIR/.streamlit_mobile.pid"
LOG_FILE="$ROOT_DIR/.streamlit_mobile.log"
SESSION_NAME="ai_company_dashboard"

cd "$ROOT_DIR"

if [[ ! -x ".venv/bin/streamlit" ]]; then
  .venv/bin/python -m pip install -r requirements.txt
fi

if command -v lsof >/dev/null 2>&1 && lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  pid="$(lsof -tiTCP:"$PORT" -sTCP:LISTEN | head -n 1)"
  echo "Streamlit already running on port $PORT: pid=$pid"
  echo "$pid" > "$PID_FILE"
  echo "Local URL: http://localhost:$PORT"
  if command -v ipconfig >/dev/null 2>&1; then
    ip="$(ipconfig getifaddr en0 || ipconfig getifaddr en1 || true)"
    if [[ -n "${ip:-}" ]]; then
      echo "Mobile URL: http://$ip:$PORT"
    fi
  fi
  exit 0
fi

if command -v screen >/dev/null 2>&1; then
  screen -S "$SESSION_NAME" -X quit >/dev/null 2>&1 || true
  screen -dmS "$SESSION_NAME" bash -lc "cd '$ROOT_DIR' && .venv/bin/streamlit run main.py --server.address '$HOST' --server.port '$PORT' --server.headless true >> '$LOG_FILE' 2>&1"
else
  nohup .venv/bin/streamlit run main.py \
    --server.address "$HOST" \
    --server.port "$PORT" \
    --server.headless true \
    > "$LOG_FILE" 2>&1 &
fi

sleep 3
pid="$(lsof -tiTCP:"$PORT" -sTCP:LISTEN | head -n 1 || true)"
if [[ -z "$pid" ]]; then
  echo "Failed to start Streamlit. See log: $LOG_FILE"
  exit 1
fi
echo "$pid" > "$PID_FILE"

echo "Streamlit started: pid=$pid"
echo "Local URL: http://localhost:$PORT"

if command -v ipconfig >/dev/null 2>&1; then
  ip="$(ipconfig getifaddr en0 || ipconfig getifaddr en1 || true)"
  if [[ -n "${ip:-}" ]]; then
    echo "Mobile URL: http://$ip:$PORT"
  fi
fi

echo "Log: $LOG_FILE"
