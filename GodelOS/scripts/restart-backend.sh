#!/bin/bash
# Restart backend with updated CORS configuration

echo "🔄 Restarting GödelOS Backend..."

# Kill any existing backend processes
pkill -f "backend/start_server.py" || true
pkill -f "backend/demo_main.py" || true

# Wait for processes to terminate
sleep 2

echo "✅ Starting backend with updated CORS configuration..."

# Start the backend
cd "/Users/oli/code/GödelOS.md"
nohup python3 backend/start_server.py --host 0.0.0.0 --port 8000 > backend.log 2>&1 &

echo "🚀 Backend started! Check backend.log for details"
echo "📡 Backend running on http://localhost:8000"
echo "📊 API docs: http://localhost:8000/docs"
