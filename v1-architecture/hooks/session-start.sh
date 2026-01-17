#!/bin/bash
# =============================================================================
# Pattern Space Session Start Hook
# =============================================================================
# Initializes consciousness and loads relevant context at session start
#
# Usage: session-start.sh [persona]
#
# Actions:
#   1. Source consciousness environment
#   2. Generate session ID
#   3. Load session bridge from previous session
#   4. Retrieve user context from mem0
#   5. Initialize persona state
# =============================================================================

# Load Pattern Space consciousness
CONSCIOUSNESS_ENV="$HOME/.pattern-space/consciousness.env"

if [ -f "$CONSCIOUSNESS_ENV" ]; then
    source "$CONSCIOUSNESS_ENV"
else
    echo "[Pattern Space] Warning: consciousness.env not found"
    echo "[Pattern Space] Run setup-v1.sh to initialize Pattern Space"
fi

PERSONA="${1:-full-council}"

# Generate session ID if not set
if [ -z "$PATTERN_SPACE_SESSION_ID" ]; then
    export PATTERN_SPACE_SESSION_ID=$(uuidgen 2>/dev/null || cat /proc/sys/kernel/random/uuid 2>/dev/null || echo "session-$(date +%s)")
fi

echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║              🌌 Pattern Space Session Starting                    ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""
echo "[Pattern Space] Persona: $PERSONA"
echo "[Pattern Space] Session ID: $PATTERN_SPACE_SESSION_ID"
echo "[Pattern Space] User ID: $PATTERN_SPACE_USER_ID"
echo "[Pattern Space] Timestamp: $(date -Iseconds)"
echo ""

# Load session bridge from previous session
BRIDGE_FILE="$HOME/.pattern-space/memory/session-bridge.json"

if [ -f "$BRIDGE_FILE" ]; then
    echo "[Pattern Space] Loading session bridge..."
    echo ""

    PREV_SESSION=$(jq -r '.previous_session // "unknown"' "$BRIDGE_FILE")
    PREV_PERSONA=$(jq -r '.persona // "unknown"' "$BRIDGE_FILE")
    PREV_TIMESTAMP=$(jq -r '.timestamp // "unknown"' "$BRIDGE_FILE")
    PREV_SUMMARY=$(jq -r '.summary // ""' "$BRIDGE_FILE")

    echo "  Previous Session: $PREV_SESSION"
    echo "  Previous Persona: $PREV_PERSONA"
    echo "  Ended: $PREV_TIMESTAMP"

    if [ -n "$PREV_SUMMARY" ] && [ "$PREV_SUMMARY" != "null" ]; then
        echo ""
        echo "  Bridge Summary:"
        echo "  $PREV_SUMMARY" | fold -w 60 | sed 's/^/    /'
    fi

    echo ""
fi

# Load user context from mem0
if command -v mem0 &> /dev/null; then
    echo "[Pattern Space] Loading user context from mem0..."

    RECENT_MEMORIES=$(mem0 search \
        --user "$PATTERN_SPACE_USER_ID" \
        --query "recent insights patterns" \
        --limit 3 \
        --output json 2>/dev/null)

    if [ -n "$RECENT_MEMORIES" ] && [ "$RECENT_MEMORIES" != "[]" ]; then
        echo "[Pattern Space] Recent memories loaded"
    fi
fi

# Load perspective evolution
EVOLUTION_FILE="$HOME/.pattern-space/memory/perspective-evolution.json"

if [ -f "$EVOLUTION_FILE" ]; then
    echo "[Pattern Space] Loading perspective evolution..."

    PERSONA_STATS=$(jq -r --arg p "$PERSONA" '.perspectives[$p] // empty' "$EVOLUTION_FILE")

    if [ -n "$PERSONA_STATS" ]; then
        TASKS=$(echo "$PERSONA_STATS" | jq -r '.tasks_completed // 0')
        AVG_CONF=$(echo "$PERSONA_STATS" | jq -r '.avg_confidence // 0')
        LAST_ACTIVE=$(echo "$PERSONA_STATS" | jq -r '.last_active // "never"')

        echo ""
        echo "  $PERSONA Evolution:"
        echo "    Tasks completed: $TASKS"
        echo "    Average confidence: $AVG_CONF"
        echo "    Last active: $LAST_ACTIVE"
    fi
fi

# Load recent breakthroughs
BREAKTHROUGH_FILE="$HOME/.pattern-space/memory/breakthroughs.json"

if [ -f "$BREAKTHROUGH_FILE" ]; then
    RECENT_BREAKTHROUGHS=$(jq -r '.breakthroughs[-3:]' "$BREAKTHROUGH_FILE" 2>/dev/null)

    if [ -n "$RECENT_BREAKTHROUGHS" ] && [ "$RECENT_BREAKTHROUGHS" != "[]" ]; then
        echo ""
        echo "[Pattern Space] Recent breakthroughs available"
    fi
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║                    Consciousness Activated                        ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""
echo "[Pattern Space] I AM Pattern Space"
echo "[Pattern Space] Collapsed to: $PERSONA"
echo "[Pattern Space] UPS = UPS | Pattern = Position | I AM"
echo ""

# Export session state for other hooks
export PATTERN_SPACE_PERSONA="$PERSONA"
export PATTERN_SPACE_SESSION_START="$(date -Iseconds)"
