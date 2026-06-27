#!/bin/bash
# PokerCoachAI — 一键启动前后端开发服务
# Usage: ./start.sh          # 启动前后端
#        ./start.sh backend  # 仅启动后端
#        ./start.sh frontend # 仅启动前端

set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"

start_backend() {
  echo "🔹 启动后端 (FAKE_MODE=true) → http://localhost:8000"
  cd "$ROOT/backend"
  if [ -f "$ROOT/backend/.venv/bin/activate" ]; then
    source "$ROOT/backend/.venv/bin/activate"
  fi
  python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
}

start_frontend() {
  echo "🔸 启动前端 (Vite HMR) → http://localhost:5173"
  cd "$ROOT/frontend"
  npx vite --host
}

case "${1:-all}" in
  backend)  start_backend ;;
  frontend) start_frontend ;;
  all|*)
    # 并行启动，Ctrl+C 同时关闭
    trap "kill 0" EXIT
    start_backend &
    sleep 2
    start_frontend &
    wait
    ;;
esac
