#!/usr/bin/env bash
# 一键启动前后端服务

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NODE_DIR="$SCRIPT_DIR/node-v20.12.2-win-x64"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

echo "========================================"
echo "  Production Management System"
echo "========================================"

# 检查依赖
echo "[1/3] Checking environment..."
if ! command -v python &> /dev/null; then
    echo "Error: python not found"
    exit 1
fi

# 停止已有的前后端进程（避免端口占用）
echo "[2/3] Cleaning up existing processes..."
for port in 8000 8002 8003 8004 5173 5174 5175; do
    for pid in $(netstat -ano | grep ":$port " | grep LISTENING | awk '{print $5}' | sort -u); do
        if [ -n "$pid" ] && [ "$pid" != "0" ]; then
            taskkill //PID "$pid" //F 2>/dev/null || true
        fi
    done
done

sleep 2

# 启动后端
echo "[3/3] Starting services..."
cd "$BACKEND_DIR"
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8005  > backend.log 2>&1 &
echo "  [OK] Backend started (log: backend/backend.log)"

# 启动前端
cd "$FRONTEND_DIR"
export PATH="$NODE_DIR:$PATH"
nohup npm run dev > frontend.log 2>&1 &
echo "  [OK] Frontend started (log: frontend/frontend.log)"

sleep 3

echo ""
echo "========================================"
echo "  Services started!"
echo "========================================"
echo "  Frontend: http://localhost:5173"
echo "  Backend:  http://localhost:8005"
echo "  API Docs: http://localhost:8005/docs"
echo ""
echo "  View logs:"
echo "    tail -f drawing-system/backend/backend.log"
echo "    tail -f drawing-system/frontend/frontend.log"
echo ""
echo "  Stop services:"
echo "    ./stop.sh"
echo "========================================"
