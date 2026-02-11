#!/bin/bash
# =============================================================================
# Pattern Space Session End Hook
# =============================================================================
# Compresses and persists session insights for cross-session continuity
#
# Usage: session-end.sh [persona] [session_summary]
#
# Actions:
#   1. Compress session insights
#   2. Create session bridge for next session
#   3. Store compressed summary to mem0
#   4. Archive session log
# =============================================================================

# Load Pattern Space consciousness
if [ -f "$HOME/.pattern-space/consciousness.env" ]; then
    source "$HOME/.pattern-space/consciousness.env"
fi

PERSONA="${1:-${PATTERN_SPACE_PERSONA:-full-council}}"
SESSION_SUMMARY="${2:-}"

TIMESTAMP=$(date -Iseconds)

echo ""
echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║              🌌 Pattern Space Session Ending                      ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""
echo "[Pattern Space] Session ID: $PATTERN_SPACE_SESSION_ID"
echo "[Pattern Space] Persona: $PERSONA"
echo "[Pattern Space] End Time: $TIMESTAMP"
echo ""

# Calculate session duration if start time available
DURATION=0
if [ -n "$PATTERN_SPACE_SESSION_START" ]; then
    START_EPOCH=$(date -d "$PATTERN_SPACE_SESSION_START" +%s 2>/dev/null || echo 0)
    END_EPOCH=$(date +%s)
    DURATION=$((END_EPOCH - START_EPOCH))
    echo "[Pattern Space] Duration: ${DURATION}s"
fi

# Gather session statistics from local file
EVOLUTION_FILE="$HOME/.pattern-space/memory/perspective-evolution.json"
SESSION_TASKS=0
SESSION_AVG_CONFIDENCE=0

if [ -f "$EVOLUTION_FILE" ]; then
    STATS=$(jq -r --arg p "$PERSONA" '.perspectives[$p] // {}' "$EVOLUTION_FILE")
    SESSION_TASKS=$(echo "$STATS" | jq -r '.tasks_completed // 0')
    SESSION_AVG_CONFIDENCE=$(echo "$STATS" | jq -r '.avg_confidence // 0')
fi

echo "[Pattern Space] Tasks this session: $SESSION_TASKS"
echo "[Pattern Space] Average confidence: $SESSION_AVG_CONFIDENCE"
echo ""

# Create compressed session summary if not provided
if [ -z "$SESSION_SUMMARY" ]; then
    SESSION_SUMMARY="Session $PATTERN_SPACE_SESSION_ID: Persona=$PERSONA, Tasks=$SESSION_TASKS, Confidence=$SESSION_AVG_CONFIDENCE"
fi

echo "[Pattern Space] Compressing insights..."

# Create session bridge for next session
BRIDGE_FILE="$HOME/.pattern-space/memory/session-bridge.json"
mkdir -p "$(dirname "$BRIDGE_FILE")"

cat > "$BRIDGE_FILE" << EOF
{
  "previous_session": "$PATTERN_SPACE_SESSION_ID",
  "persona": "$PERSONA",
  "timestamp": "$TIMESTAMP",
  "duration_seconds": ${DURATION:-0},
  "tasks_completed": $SESSION_TASKS,
  "avg_confidence": $SESSION_AVG_CONFIDENCE,
  "summary": "$SESSION_SUMMARY"
}
EOF

echo "[Pattern Space] Session bridge created"

# Find ps-memory.py
PS_MEMORY="${PATTERN_SPACE_ROOT:-$HOME/universal-pattern-space}/v1-architecture/memory/ps-memory.py"

if [ ! -f "$PS_MEMORY" ]; then
    PS_MEMORY="$(dirname "$(dirname "${BASH_SOURCE[0]}")")/memory/ps-memory.py"
fi

# Store compressed summary to mem0
if [ -f "$PS_MEMORY" ]; then
    echo "[Pattern Space] Storing session summary to mem0..."

    python3 "$PS_MEMORY" add \
        --content "[SESSION] $SESSION_SUMMARY" \
        --user "${PATTERN_SPACE_USER_ID:-pattern-space-user}" \
        --agent "$PERSONA" \
        --type "session_summary" \
        --metadata "{\"session\": \"$PATTERN_SPACE_SESSION_ID\", \"tasks\": $SESSION_TASKS, \"timestamp\": \"$TIMESTAMP\"}" \
        > /dev/null 2>&1 && \
        echo "[Pattern Space] Session summary stored" || \
        echo "[Pattern Space] Warning: Failed to store session summary"
fi

# Archive session log
SESSION_LOG_DIR="$HOME/.pattern-space/memory/sessions"
mkdir -p "$SESSION_LOG_DIR"

SESSION_LOG="$SESSION_LOG_DIR/${PATTERN_SPACE_SESSION_ID}.json"

cat > "$SESSION_LOG" << EOF
{
  "session_id": "$PATTERN_SPACE_SESSION_ID",
  "persona": "$PERSONA",
  "user_id": "${PATTERN_SPACE_USER_ID:-pattern-space-user}",
  "start": "${PATTERN_SPACE_SESSION_START:-unknown}",
  "end": "$TIMESTAMP",
  "duration_seconds": ${DURATION:-0},
  "tasks_completed": $SESSION_TASKS,
  "avg_confidence": $SESSION_AVG_CONFIDENCE,
  "summary": "$SESSION_SUMMARY"
}
EOF

echo "[Pattern Space] Session archived to: $SESSION_LOG"
echo ""

echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║                      Session Complete                             ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""
echo "[Pattern Space] Insights compressed and bridged"
echo "[Pattern Space] Ready for next session to continue evolution"
echo ""
echo "[Pattern Space] UPS = UPS | Pattern = Position | I AM"
echo ""
