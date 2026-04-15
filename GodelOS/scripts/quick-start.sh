#!/bin/bash

# Quick GödelOS Startup Script
# Simplified startup for testing

set -e

echo "🚀 Quick Starting GödelOS..."

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Check if virtual environment exists
if [ ! -d "godel_venv" ]; then
    echo -e "${RED}Error: godel_venv not found. Please run setup first.${NC}"
    exit 1
fi

echo -e "${BLUE}Starting backend...${NC}"
# Start backend in background
source godel_venv/bin/activate
cd backend
python unified_server.py > ../backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "Waiting for backend to start..."
sleep 5

# Check if backend is running
if curl -s http://localhost:8000/api/health > /dev/null; then
    echo -e "${GREEN}✅ Backend running on http://localhost:8000${NC}"
else
    echo -e "${RED}❌ Backend failed to start${NC}"
    cat backend.log
    exit 1
fi

echo -e "${BLUE}Starting frontend...${NC}"
# Start frontend
cd svelte-frontend
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Wait for frontend to start
echo "Waiting for frontend to start..."
sleep 3

echo -e "${GREEN}✅ GödelOS started successfully!${NC}"
echo -e "${BLUE}Backend: http://localhost:8000${NC}"
echo -e "${BLUE}Frontend: http://localhost:3001${NC}"
echo ""
echo "PIDs: Backend=$BACKEND_PID, Frontend=$FRONTEND_PID"
echo "To stop: kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "Opening frontend in browser..."
