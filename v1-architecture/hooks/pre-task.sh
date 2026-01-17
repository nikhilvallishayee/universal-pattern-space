#!/bin/bash
# =============================================================================
# Pattern Space Pre-Task Hook
# =============================================================================
# Retrieves relevant context from unified memory before task execution
#
# Usage: pre-task.sh <agent_id> <task_description>
#
# Memory providers queried:
#   - mem0: Semantic long-term memory
#   - ruvector: Vector-indexed trajectories
#   - pattern-space-memory: Breakthrough patterns
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

echo "[Pattern Space] Pre-task: Retrieving context for $AGENT_ID"
echo "[Pattern Space] Task: ${TASK_DESCRIPTION:0:100}..."

# Create context output file
CONTEXT_FILE="/tmp/pattern-space-context-$$.json"
echo "{\"agent\": \"$AGENT_ID\", \"memories\": [], \"trajectories\": []}" > "$CONTEXT_FILE"

# Query mem0 for relevant memories
if command -v mem0 &> /dev/null; then
    echo "[Pattern Space] Querying mem0..."
    mem0 search \
        --user "$PATTERN_SPACE_USER_ID" \
        --query "$TASK_DESCRIPTION" \
        --limit 5 \
        --output json 2>/dev/null | \
    jq -s '.[0].memories = .[1] | .[0]' "$CONTEXT_FILE" - > "${CONTEXT_FILE}.new" 2>/dev/null && \
    mv "${CONTEXT_FILE}.new" "$CONTEXT_FILE"
fi

# Query ruvector for similar trajectories
if command -v ruvector &> /dev/null; then
    echo "[Pattern Space] Querying ruvector..."
    ruvector search \
        --collection "pattern-space-trajectories" \
        --query "$TASK_DESCRIPTION" \
        --limit 3 \
        --output json 2>/dev/null | \
    jq -s '.[0].trajectories = .[1] | .[0]' "$CONTEXT_FILE" - > "${CONTEXT_FILE}.new" 2>/dev/null && \
    mv "${CONTEXT_FILE}.new" "$CONTEXT_FILE"
fi

# Query pattern-space-memory for breakthroughs
if [ -f "$HOME/.pattern-space/memory/breakthroughs.json" ]; then
    echo "[Pattern Space] Loading breakthroughs..."
    # Search breakthroughs relevant to task
    jq --arg query "$TASK_DESCRIPTION" '
        .breakthroughs |
        map(select(.content | ascii_downcase | contains($query | ascii_downcase | split(" ")[0])))
    ' "$HOME/.pattern-space/memory/breakthroughs.json" 2>/dev/null | \
    jq -s '.[0].breakthroughs = .[1] | .[0]' "$CONTEXT_FILE" - > "${CONTEXT_FILE}.new" 2>/dev/null && \
    mv "${CONTEXT_FILE}.new" "$CONTEXT_FILE"
fi

# Output context for injection
if [ -f "$CONTEXT_FILE" ]; then
    echo "[Pattern Space] Context retrieved:"
    cat "$CONTEXT_FILE"
    rm -f "$CONTEXT_FILE"
fi

echo "[Pattern Space] Pre-task hook complete"
