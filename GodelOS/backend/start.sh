#!/bin/bash

# GödelOS Backend Startup Script
# Simple shell script to start the GödelOS backend API server

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting GödelOS Backend API Server${NC}"
echo "======================================"

# Check if we're in the right directory
if [ ! -f "backend/main.py" ]; then
    echo -e "${RED}Error: Please run this script from the GödelOS root directory${NC}"
    exit 1
fi

# Set up environment
export PYTHONPATH="${PWD}:${PYTHONPATH}"
export GODELOS_ENVIRONMENT="${GODELOS_ENVIRONMENT:-development}"

echo -e "${YELLOW}Environment: ${GODELOS_ENVIRONMENT}${NC}"
echo -e "${YELLOW}Python Path: ${PYTHONPATH}${NC}"

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${YELLOW}Python Version: ${python_version}${NC}"

# Check if virtual environment is recommended
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}Warning: No virtual environment detected. Consider using one.${NC}"
fi

# Install dependencies if needed
if [ "$1" = "--install" ]; then
    echo -e "${BLUE}Installing dependencies...${NC}"
    pip install -r backend/requirements.txt
    echo -e "${GREEN}Dependencies installed${NC}"
fi

# Create logs directory
mkdir -p backend/logs

# Check if port is available
PORT=${GODELOS_PORT:-8000}
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${RED}Error: Port $PORT is already in use${NC}"
    echo "Please stop the existing service or use a different port:"
    echo "  export GODELOS_PORT=3001"
    exit 1
fi

# Start the server
echo -e "${GREEN}Starting server on port $PORT...${NC}"
echo -e "${BLUE}API Documentation will be available at: http://localhost:$PORT/docs${NC}"
echo -e "${BLUE}WebSocket endpoint: ws://localhost:$PORT/ws/cognitive-stream${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

# Determine startup method
if [ "$1" = "--debug" ] || [ "$GODELOS_DEBUG" = "true" ]; then
    echo -e "${YELLOW}Starting in debug mode with auto-reload...${NC}"
    python3 backend/start_server.py --debug --log-level DEBUG
elif [ "$1" = "--uvicorn" ]; then
    echo -e "${YELLOW}Starting with uvicorn directly...${NC}"
    uvicorn backend.main:app --host 0.0.0.0 --port $PORT --reload
else
    echo -e "${GREEN}Starting in production mode...${NC}"
    python3 backend/start_server.py --host 0.0.0.0 --port $PORT
fi