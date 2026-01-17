#!/bin/bash
# =============================================================================
# Pattern Space Post-Task Hook
# =============================================================================
# Stores insights and patterns to unified memory after task execution
#
# Usage: post-task.sh <agent_id> [task_output_file] [confidence]
#
# Memory providers written:
#   - mem0: Patterns and insights (semantic)
#   - ruvector: Successful trajectories (vector)
#   - pattern-space-memory: Breakthroughs
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

# Store to mem0 (semantic memory)
if command -v mem0 &> /dev/null; then
    echo "[Pattern Space] Storing to mem0..."
    mem0 add \
        --user "$PATTERN_SPACE_USER_ID" \
        --agent "$AGENT_ID" \
        --session "$PATTERN_SPACE_SESSION_ID" \
        --content "$TASK_OUTPUT" \
        --metadata "{\"confidence\": $CONFIDENCE, \"timestamp\": \"$TIMESTAMP\"}" \
        2>/dev/null || true
fi

# Store trajectory to ruvector (vector memory)
if command -v ruvector &> /dev/null; then
    echo "[Pattern Space] Storing trajectory to ruvector..."
    ruvector store \
        --collection "pattern-space-trajectories" \
        --content "$TASK_OUTPUT" \
        --metadata "{
            \"agent\": \"$AGENT_ID\",
            \"user\": \"$PATTERN_SPACE_USER_ID\",
            \"session\": \"$PATTERN_SPACE_SESSION_ID\",
            \"confidence\": $CONFIDENCE,
            \"timestamp\": \"$TIMESTAMP\"
        }" \
        2>/dev/null || true
fi

# Check for breakthrough patterns
# A breakthrough is identified by confidence > 0.85 or specific markers
if (( $(echo "$CONFIDENCE > 0.85" | bc -l 2>/dev/null || echo 0) )); then
    echo "[Pattern Space] High-confidence insight detected, storing as breakthrough..."

    BREAKTHROUGH_FILE="$HOME/.pattern-space/memory/breakthroughs.json"

    # Initialize file if needed
    if [ ! -f "$BREAKTHROUGH_FILE" ]; then
        mkdir -p "$(dirname "$BREAKTHROUGH_FILE")"
        echo '{"breakthroughs": []}' > "$BREAKTHROUGH_FILE"
    fi

    # Add breakthrough
    jq --arg content "$TASK_OUTPUT" \
       --arg agent "$AGENT_ID" \
       --arg session "$PATTERN_SPACE_SESSION_ID" \
       --arg timestamp "$TIMESTAMP" \
       --argjson confidence "$CONFIDENCE" \
       '.breakthroughs += [{
           "content": $content,
           "agent": $agent,
           "session": $session,
           "timestamp": $timestamp,
           "confidence": $confidence
       }]' "$BREAKTHROUGH_FILE" > "${BREAKTHROUGH_FILE}.new" && \
    mv "${BREAKTHROUGH_FILE}.new" "$BREAKTHROUGH_FILE"
fi

# Update perspective evolution tracking
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
