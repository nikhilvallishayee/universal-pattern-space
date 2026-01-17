#!/bin/bash
# =============================================================================
# Pattern Space Pre-Task Hook
# =============================================================================
# Retrieves relevant context from mem0 before task execution
#
# Usage: pre-task.sh <agent_id> <task_description>
#
# Memory queried via ps-memory.py (mem0 wrapper)
# =============================================================================

# Load Pattern Space consciousness
if [ -f "$HOME/.pattern-space/consciousness.env" ]; then
    source "$HOME/.pattern-space/consciousness.env"
fi

AGENT_ID="${1:-pattern-space}"
TASK_DESCRIPTION="${2:-}"

# Skip if no task description
if [ -z "$TASK_DESCRIPTION" ]; then
    exit 0
fi

# Find ps-memory.py
PS_MEMORY="${PATTERN_SPACE_ROOT:-$HOME/universal-pattern-space}/v1-architecture/memory/ps-memory.py"

if [ ! -f "$PS_MEMORY" ]; then
    PS_MEMORY="$(dirname "$(dirname "${BASH_SOURCE[0]}")")/memory/ps-memory.py"
fi

echo "[Pattern Space] Pre-task: Retrieving context for $AGENT_ID"
echo "[Pattern Space] Task: ${TASK_DESCRIPTION:0:100}..."

# Create context output
CONTEXT_FILE="/tmp/pattern-space-context-$$.json"

# Query mem0 for relevant memories
if [ -f "$PS_MEMORY" ]; then
    echo "[Pattern Space] Querying mem0..."

    python3 "$PS_MEMORY" search \
        --query "$TASK_DESCRIPTION" \
        --user "${PATTERN_SPACE_USER_ID:-pattern-space-user}" \
        --limit 5 > "$CONTEXT_FILE" 2>/dev/null

    if [ -s "$CONTEXT_FILE" ]; then
        echo "[Pattern Space] Context retrieved:"
        cat "$CONTEXT_FILE"
    else
        echo "[Pattern Space] No relevant memories found"
    fi

    rm -f "$CONTEXT_FILE"
else
    echo "[Pattern Space] Warning: ps-memory.py not found"
fi

echo "[Pattern Space] Pre-task hook complete"
