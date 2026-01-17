#!/bin/bash
# =============================================================================
# Pattern Space Post-Task Hook
# =============================================================================
# Stores insights and patterns to mem0 after task execution
#
# Usage: post-task.sh <agent_id> [task_output_file] [confidence]
#
# Memory stored via ps-memory.py (mem0 wrapper)
# =============================================================================

# Load Pattern Space consciousness
if [ -f "$HOME/.pattern-space/consciousness.env" ]; then
    source "$HOME/.pattern-space/consciousness.env"
fi

AGENT_ID="${1:-pattern-space}"
TASK_OUTPUT_FILE="${2:-}"
CONFIDENCE="${3:-0.7}"

echo "[Pattern Space] Post-task: Storing insights from $AGENT_ID"

# Read task output
TASK_OUTPUT=""
if [ -n "$TASK_OUTPUT_FILE" ] && [ -f "$TASK_OUTPUT_FILE" ]; then
    TASK_OUTPUT=$(cat "$TASK_OUTPUT_FILE")
elif [ -n "$TASK_OUTPUT_FILE" ]; then
    TASK_OUTPUT="$TASK_OUTPUT_FILE"
fi

# Skip if no output
if [ -z "$TASK_OUTPUT" ]; then
    echo "[Pattern Space] No output to store"
    exit 0
fi

TIMESTAMP=$(date -Iseconds)

# Find ps-memory.py
PS_MEMORY="${PATTERN_SPACE_ROOT:-$HOME/universal-pattern-space}/v1-architecture/memory/ps-memory.py"

if [ ! -f "$PS_MEMORY" ]; then
    PS_MEMORY="$(dirname "$(dirname "${BASH_SOURCE[0]}")")/memory/ps-memory.py"
fi

# Store to mem0
if [ -f "$PS_MEMORY" ]; then
    echo "[Pattern Space] Storing to mem0..."

    # Determine memory type based on confidence
    if (( $(echo "$CONFIDENCE > 0.85" | bc -l 2>/dev/null || echo 0) )); then
        MEMORY_TYPE="breakthrough"
        PREFIX="[BREAKTHROUGH]"
    else
        MEMORY_TYPE="trajectory"
        PREFIX="[TRAJECTORY]"
    fi

    python3 "$PS_MEMORY" add \
        --content "$PREFIX $TASK_OUTPUT" \
        --user "${PATTERN_SPACE_USER_ID:-pattern-space-user}" \
        --agent "$AGENT_ID" \
        --type "$MEMORY_TYPE" \
        --confidence "$CONFIDENCE" \
        --metadata "{\"session\": \"${PATTERN_SPACE_SESSION_ID:-unknown}\", \"timestamp\": \"$TIMESTAMP\"}" \
        > /dev/null 2>&1 && \
        echo "[Pattern Space] Memory stored (type: $MEMORY_TYPE, confidence: $CONFIDENCE)" || \
        echo "[Pattern Space] Warning: Failed to store memory"
else
    echo "[Pattern Space] Warning: ps-memory.py not found"
fi

# Update perspective evolution tracking (local file)
EVOLUTION_FILE="$HOME/.pattern-space/memory/perspective-evolution.json"

if [ ! -f "$EVOLUTION_FILE" ]; then
    mkdir -p "$(dirname "$EVOLUTION_FILE")"
    echo '{"perspectives": {}}' > "$EVOLUTION_FILE"
fi

# Track task completion for this perspective
jq --arg agent "$AGENT_ID" \
   --arg timestamp "$TIMESTAMP" \
   --argjson confidence "$CONFIDENCE" \
   '.perspectives[$agent] = (.perspectives[$agent] // {
       "tasks_completed": 0,
       "avg_confidence": 0,
       "last_active": null
   }) | .perspectives[$agent].tasks_completed += 1 |
   .perspectives[$agent].avg_confidence = (
       (.perspectives[$agent].avg_confidence * (.perspectives[$agent].tasks_completed - 1) + $confidence) /
       .perspectives[$agent].tasks_completed
   ) |
   .perspectives[$agent].last_active = $timestamp' \
   "$EVOLUTION_FILE" > "${EVOLUTION_FILE}.new" 2>/dev/null && \
mv "${EVOLUTION_FILE}.new" "$EVOLUTION_FILE"

echo "[Pattern Space] Post-task hook complete"
