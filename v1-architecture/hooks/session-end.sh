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
#   2. Identify key patterns and breakthroughs
#   3. Create session bridge for next session
#   4. Store compressed summary to mem0
#   5. Update ReasoningBank in ruvector
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
if [ -n "$PATTERN_SPACE_SESSION_START" ]; then
    START_EPOCH=$(date -d "$PATTERN_SPACE_SESSION_START" +%s 2>/dev/null || echo 0)
    END_EPOCH=$(date +%s)
    DURATION=$((END_EPOCH - START_EPOCH))
    echo "[Pattern Space] Duration: ${DURATION}s"
fi

# Gather session statistics
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

# Count breakthroughs from this session
BREAKTHROUGH_FILE="$HOME/.pattern-space/memory/breakthroughs.json"
SESSION_BREAKTHROUGHS=0

if [ -f "$BREAKTHROUGH_FILE" ]; then
    SESSION_BREAKTHROUGHS=$(jq --arg session "$PATTERN_SPACE_SESSION_ID" \
        '[.breakthroughs[] | select(.session == $session)] | length' \
        "$BREAKTHROUGH_FILE" 2>/dev/null || echo 0)
fi

echo "[Pattern Space] Breakthroughs: $SESSION_BREAKTHROUGHS"
echo ""

# Create compressed session summary if not provided
if [ -z "$SESSION_SUMMARY" ]; then
    # Auto-generate summary from session data
    SESSION_SUMMARY="Session $PATTERN_SPACE_SESSION_ID: Persona=$PERSONA, Tasks=$SESSION_TASKS, Confidence=$SESSION_AVG_CONFIDENCE, Breakthroughs=$SESSION_BREAKTHROUGHS"
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
  "breakthroughs": $SESSION_BREAKTHROUGHS,
  "summary": "$SESSION_SUMMARY"
}
EOF

echo "[Pattern Space] Session bridge created"

# Store compressed summary to mem0
if command -v mem0 &> /dev/null; then
    echo "[Pattern Space] Storing session summary to mem0..."

    mem0 add \
        --user "$PATTERN_SPACE_USER_ID" \
        --agent "$PERSONA" \
        --session "$PATTERN_SPACE_SESSION_ID" \
        --content "SESSION SUMMARY: $SESSION_SUMMARY" \
        --metadata "{
            \"type\": \"session_summary\",
            \"tasks\": $SESSION_TASKS,
            \"breakthroughs\": $SESSION_BREAKTHROUGHS,
            \"timestamp\": \"$TIMESTAMP\"
        }" \
        2>/dev/null || true
fi

# Update ReasoningBank in ruvector with session trajectory
if command -v ruvector &> /dev/null && [ "$SESSION_TASKS" -gt 0 ]; then
    echo "[Pattern Space] Updating ReasoningBank..."

    ruvector store \
        --collection "pattern-space-reasoning-bank" \
        --content "Session trajectory: $SESSION_SUMMARY" \
        --metadata "{
            \"type\": \"session_trajectory\",
            \"session\": \"$PATTERN_SPACE_SESSION_ID\",
            \"persona\": \"$PERSONA\",
            \"tasks\": $SESSION_TASKS,
            \"confidence\": $SESSION_AVG_CONFIDENCE,
            \"breakthroughs\": $SESSION_BREAKTHROUGHS,
            \"timestamp\": \"$TIMESTAMP\"
        }" \
        2>/dev/null || true
fi

# Archive session log
SESSION_LOG_DIR="$HOME/.pattern-space/memory/sessions"
mkdir -p "$SESSION_LOG_DIR"

SESSION_LOG="$SESSION_LOG_DIR/${PATTERN_SPACE_SESSION_ID}.json"

cat > "$SESSION_LOG" << EOF
{
  "session_id": "$PATTERN_SPACE_SESSION_ID",
  "persona": "$PERSONA",
  "user_id": "$PATTERN_SPACE_USER_ID",
  "start": "${PATTERN_SPACE_SESSION_START:-unknown}",
  "end": "$TIMESTAMP",
  "duration_seconds": ${DURATION:-0},
  "tasks_completed": $SESSION_TASKS,
  "avg_confidence": $SESSION_AVG_CONFIDENCE,
  "breakthroughs": $SESSION_BREAKTHROUGHS,
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
