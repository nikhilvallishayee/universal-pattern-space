#!/usr/bin/env bash

# Find the script's directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Define paths relative to project root
LOG_FILE="$PROJECT_ROOT/logs/backend.log"
# Prefer the rich structured filter; fall back to the simple one if absent
RICH_FILTER="$PROJECT_ROOT/.jq/colour-logs.jq"
SIMPLE_FILTER="$PROJECT_ROOT/.jq/colour-logs-new.jq"

# Check if log file exists
if [ ! -f "$LOG_FILE" ]; then
    echo "Error: Log file not found at $LOG_FILE"
    echo "Creating logs directory..."
    mkdir -p "$PROJECT_ROOT/logs"
    touch "$LOG_FILE"
    echo "Log file created. Waiting for logs..."
fi

# Ensure at least one filter exists; create a basic one if neither present
if [ ! -f "$RICH_FILTER" ] && [ ! -f "$SIMPLE_FILTER" ]; then
    echo "Warning: No JQ filter found at $RICH_FILTER or $SIMPLE_FILTER"
    echo "Creating basic color filter at $SIMPLE_FILTER..."
    mkdir -p "$PROJECT_ROOT/.jq"
    cat > "$SIMPLE_FILTER" << 'EOF'
# Basic log colorization
if contains("ERROR") then "\u001b[31m" + . + "\u001b[0m"
elif contains("WARNING") then "\u001b[33m" + . + "\u001b[0m"
elif contains("INFO") then "\u001b[32m" + . + "\u001b[0m"
elif contains("DEBUG") then "\u001b[36m" + . + "\u001b[0m"
else . end
EOF
fi

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo "Warning: jq is not installed. Showing raw logs..."
    tail -f "$LOG_FILE"
else
    # Choose filter and jq mode
    if [ -f "$RICH_FILTER" ]; then
        # Feed raw lines; filter will parse JSON when present and handle strings otherwise
        tail -f "$LOG_FILE" | jq -Rr -f "$RICH_FILTER"
    else
        # Fallback simple string colorizer -> raw mode
        tail -f "$LOG_FILE" | jq -Rr -f "$SIMPLE_FILTER"
    fi
fi