#!/bin/bash

# GödelOS Web Demonstration Interface Startup Script
# This script starts both the backend and frontend components

set -e

echo "🚀 Starting GödelOS Web Demonstration Interface..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed."
    exit 1
fi

# Check if Node.js is available (for serving frontend)
if ! command -v python3 -m http.server &> /dev/null; then
    print_warning "Python HTTP server will be used for frontend serving."
fi

# Function to cleanup background processes
cleanup() {
    print_status "Shutting down services..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    print_success "Services stopped."
}

# Set up signal handlers
trap cleanup EXIT INT TERM

# Step 1: Install backend dependencies
print_status "Installing backend dependencies..."
cd backend
if [ ! -d "venv" ]; then
    print_status "Creating virtual environment..."
    python3 -m venv venv
fi

print_status "Activating virtual environment..."
source venv/bin/activate

print_status "Installing Python packages..."
pip install -r requirements.txt

# Step 2: Start the backend server
print_status "Starting GödelOS backend server..."
python unified_server.py &
BACKEND_PID=$!

# Wait for backend to start
print_status "Waiting for backend to initialize..."
sleep 5

# Check if backend is running
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    print_error "Backend failed to start!"
    exit 1
fi

# Test backend health
print_status "Testing backend health..."
if curl -s http://localhost:8000/health > /dev/null; then
    print_success "Backend is running and healthy!"
else
    print_warning "Backend health check failed, but continuing..."
fi

cd ..

# Step 3: Start the frontend server
print_status "Starting frontend server..."
cd godelos-frontend

# Use Python's built-in HTTP server for simplicity
python3 -m http.server 3000 &
FRONTEND_PID=$!

print_success "Frontend server started on http://localhost:3000"

cd ..

# Step 4: Display status and instructions
echo ""
echo "=========================================="
echo "🎉 GödelOS Web Interface is now running!"
echo "=========================================="
echo ""
echo "📊 Backend API:     http://localhost:8000"
echo "🌐 Frontend UI:     http://localhost:3000"
echo "📡 WebSocket:       ws://localhost:8000/ws/cognitive-stream"
echo ""
echo "📋 API Endpoints:"
echo "   • Health Check:  GET  /health"
echo "   • Process Query: POST /api/query"
echo "   • Get Knowledge: GET  /api/knowledge"
echo "   • Add Knowledge: POST /api/knowledge"
echo "   • Cognitive State: GET /api/cognitive-state"
echo ""
echo "🔧 To test the system:"
echo "   1. Open http://localhost:3000 in your browser"
echo "   2. Enter a natural language query"
echo "   3. Watch real-time cognitive layer updates"
echo ""
echo "⏹️  Press Ctrl+C to stop all services"
echo ""

# Keep script running and monitor processes
while true; do
    # Check if backend is still running
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        print_error "Backend process died unexpectedly!"
        exit 1
    fi
    
    # Check if frontend is still running
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        print_error "Frontend process died unexpectedly!"
        exit 1
    fi
    
    sleep 5
done