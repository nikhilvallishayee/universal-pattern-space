#!/bin/bash

# GödelOS Unified Server Startup Script
# This script starts the new consolidated server that combines
# the stability of minimal_server with the features of main.py

echo "🚀 Starting GödelOS Unified Server..."

# Change to backend directory
cd "$(dirname "$0")/backend"

# Check if virtual environment exists
if [ -d "../godelos_venv" ]; then
    echo "📦 Activating virtual environment..."
    source ../godelos_venv/bin/activate
else
    echo "⚠️  Virtual environment not found. Using system Python..."
fi

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)/.."
export FASTAPI_ENV=development

echo "🔧 Environment configured:"
echo "   PYTHONPATH: $PYTHONPATH"
echo "   Working directory: $(pwd)"

# Check if .env file exists
if [ -f ".env" ]; then
    echo "✅ Environment file found"
else
    echo "⚠️  No .env file found - using default configuration"
fi

# Start the unified server
echo "🌟 Launching unified server on http://localhost:8000"
echo "📊 Dashboard will be available at frontend"
echo "🔌 WebSocket streaming: ws://localhost:8000/ws/cognitive-stream"
echo ""
echo "Press Ctrl+C to stop the server"
echo "----------------------------------------"

# Run the unified server
python unified_server.py
