#!/bin/bash

# 启动开发环境

echo "Starting development environment..."

# 检查后端是否运行
echo "Checking backend..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✓ Backend is running on http://localhost:8000"
else
    echo "✗ Backend is not running. Please start backend first."
    echo "  Run: cd backend && source venv/bin/activate && python main.py"
    exit 1
fi

# 启动前端
cd /Users/kjonekong/Documents/cb-Business/frontend
echo "Starting frontend on http://localhost:3000..."
npm run dev &
FRONTEND_PID=$!
echo "Frontend started (PID: $FRONTEND_PID)"

# 等待前端启动
sleep 3

# 启动管理后台
cd /Users/kjonekong/Documents/cb-Business/admin
echo "Starting admin on http://localhost:3001..."
PORT=3001 npm run dev &
ADMIN_PID=$!
echo "Admin started (PID: $ADMIN_PID)"

echo ""
echo "═══════════════════════════════════════════════"
echo "  All services started:"
echo "    - Frontend:  http://localhost:3000"
echo "    - Admin:     http://localhost:3001"
echo "    - Backend:   http://localhost:8000"
echo "    - API Docs:  http://localhost:8000/docs"
echo "═══════════════════════════════════════════════"
echo ""
echo "Press Ctrl+C to stop all services"

# 捕获Ctrl+C，停止所有服务
trap "echo ''; echo 'Stopping all services...'; kill $FRONTEND_PID $ADMIN_PID 2>/dev/null; exit" INT

# 等待所有后台进程
wait
