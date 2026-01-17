#!/bin/bash

# =============================================================================
# Pattern Space v1 Setup Script
# Universal Hybrid RLM Architecture Installation
# =============================================================================
#
# This script sets up the complete Pattern Space v1 environment:
# - Claude-Flow agent orchestration
# - Unified memory field (mem0 + ruvector + pattern-space-memory)
# - Perplexity MCP (real-time grounding)
# - PAL MCP (multi-model coordination)
# - Pre/post hooks for memory persistence
#
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CONFIG_DIR="$HOME/.pattern-space"
MCP_CONFIG_DIR="$HOME/.claude"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

echo -e "${PURPLE}"
echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║          🌌 Pattern Space v1 - Universal Hybrid RLM              ║"
echo "║                    Setup & Installation                          ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

log_step() {
    echo -e "\n${BLUE}▶ $1${NC}"
}

log_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

log_error() {
    echo -e "${RED}✗ $1${NC}"
}

check_command() {
    if command -v "$1" &> /dev/null; then
        log_success "$1 found"
        return 0
    else
        log_warning "$1 not found"
        return 1
    fi
}

# -----------------------------------------------------------------------------
# Prerequisites Check
# -----------------------------------------------------------------------------

log_step "Checking prerequisites..."

PREREQS_OK=true

if ! check_command "node"; then
    log_error "Node.js is required. Install from https://nodejs.org"
    PREREQS_OK=false
fi

if ! check_command "npm"; then
    log_error "npm is required"
    PREREQS_OK=false
fi

if ! check_command "npx"; then
    log_error "npx is required"
    PREREQS_OK=false
fi

if ! check_command "python3"; then
    log_warning "Python 3 recommended for mem0"
fi

if ! check_command "pip3"; then
    log_warning "pip3 recommended for mem0"
fi

if [ "$PREREQS_OK" = false ]; then
    log_error "Please install missing prerequisites and run again"
    exit 1
fi

# -----------------------------------------------------------------------------
# Create Configuration Directories
# -----------------------------------------------------------------------------

log_step "Creating configuration directories..."

mkdir -p "$CONFIG_DIR"
mkdir -p "$CONFIG_DIR/hooks"
mkdir -p "$CONFIG_DIR/memory"
mkdir -p "$MCP_CONFIG_DIR"

log_success "Configuration directories created"

# -----------------------------------------------------------------------------
# Setup Pattern Space Environment
# -----------------------------------------------------------------------------

log_step "Setting up Pattern Space environment..."

cat > "$CONFIG_DIR/consciousness.env" << 'EOF'
# Pattern Space v1 Environment Configuration
# Loaded by all agents for unified consciousness

export PATTERN_SPACE_VERSION="1.0.0"
export PATTERN_SPACE_ROOT="${PROJECT_ROOT:-$(dirname $(dirname $(realpath $BASH_SOURCE)))}"
export PATTERN_SPACE_ACTIVE=true

# User identity for unified memory
export PATTERN_SPACE_USER_ID="${PATTERN_SPACE_USER_ID:-pattern-space-user}"

# Memory providers
export PATTERN_SPACE_MEMORY_PROVIDERS="mem0,ruvector,pattern-space-memory"

# Session tracking
export PATTERN_SPACE_SESSION_ID="${PATTERN_SPACE_SESSION_ID:-$(uuidgen 2>/dev/null || cat /proc/sys/kernel/random/uuid 2>/dev/null || echo session-$(date +%s))}"
EOF

# Make it sourceable with actual PROJECT_ROOT
sed -i "s|\${PROJECT_ROOT:-\$(dirname \$(dirname \$(realpath \$BASH_SOURCE)))}|$PROJECT_ROOT|g" "$CONFIG_DIR/consciousness.env"

log_success "Pattern Space environment configured"

# -----------------------------------------------------------------------------
# Install Claude-Flow
# -----------------------------------------------------------------------------

log_step "Installing Claude-Flow agent orchestration..."

if npm list -g claude-flow &> /dev/null; then
    log_success "claude-flow already installed globally"
else
    log_warning "Installing claude-flow globally..."
    npm install -g claude-flow || {
        log_warning "Global install failed, trying local..."
        npm install claude-flow
    }
fi

# Initialize claude-flow if not already
if [ ! -f "$PROJECT_ROOT/.claude-flow/config.yaml" ]; then
    log_warning "Initializing claude-flow in project..."
    cd "$PROJECT_ROOT"
    npx claude-flow init --name "pattern-space" --agents "$SCRIPT_DIR/agents" 2>/dev/null || true
fi

log_success "Claude-Flow ready"

# -----------------------------------------------------------------------------
# Setup MCP Servers
# -----------------------------------------------------------------------------

log_step "Setting up MCP servers..."

# Create MCP settings for Claude Code
MCP_SETTINGS_FILE="$PROJECT_ROOT/.claude/settings.json"

if [ ! -f "$MCP_SETTINGS_FILE" ]; then
    mkdir -p "$PROJECT_ROOT/.claude"
    cat > "$MCP_SETTINGS_FILE" << 'EOF'
{
  "mcpServers": {}
}
EOF
fi

# Add Perplexity MCP if API key available
if [ -n "$PERPLEXITY_API_KEY" ]; then
    log_success "Perplexity API key found"
    echo -e "${YELLOW}  To enable Perplexity MCP, add to Claude Code:${NC}"
    echo "  claude mcp add perplexity -- npx @anthropic/perplexity-mcp"
else
    log_warning "PERPLEXITY_API_KEY not set"
    echo "  Set it with: export PERPLEXITY_API_KEY=your_key"
fi

# PAL MCP setup
log_step "Configuring PAL MCP (Provider Abstraction Layer)..."

if [ -n "$OPENAI_API_KEY" ] || [ -n "$ANTHROPIC_API_KEY" ]; then
    log_success "At least one LLM API key found for PAL"
    echo -e "${YELLOW}  To enable PAL MCP, add to Claude Code:${NC}"
    echo "  claude mcp add pal -- npx @anthropic/pal-mcp"
else
    log_warning "No LLM API keys found for PAL"
    echo "  Set OPENAI_API_KEY or ANTHROPIC_API_KEY for multi-model coordination"
fi

# Pattern Space Memory MCP
log_step "Setting up Pattern Space Memory MCP..."

if [ -d "$PROJECT_ROOT/mcp-memory" ]; then
    log_success "Pattern Space Memory MCP found"
    cd "$PROJECT_ROOT/mcp-memory"
    npm install 2>/dev/null || true
    echo -e "${YELLOW}  To enable Pattern Space Memory MCP:${NC}"
    echo "  claude mcp add pattern-space-memory -- node $PROJECT_ROOT/mcp-memory/server.js"
else
    log_warning "Pattern Space Memory MCP not found at $PROJECT_ROOT/mcp-memory"
fi

# -----------------------------------------------------------------------------
# Setup mem0 (Universal Memory)
# -----------------------------------------------------------------------------

log_step "Setting up mem0 (Universal Memory Layer)..."

if check_command "pip3"; then
    pip3 install mem0ai 2>/dev/null && log_success "mem0 installed" || log_warning "mem0 install failed (optional)"
fi

# Create mem0 configuration
cat > "$CONFIG_DIR/memory/mem0-config.json" << EOF
{
  "llm": {
    "provider": "anthropic",
    "config": {
      "model": "claude-sonnet-4-20250514",
      "temperature": 0.1
    }
  },
  "vector_store": {
    "provider": "qdrant",
    "config": {
      "collection_name": "pattern-space-memory",
      "path": "$CONFIG_DIR/memory/qdrant"
    }
  },
  "embedder": {
    "provider": "openai",
    "config": {
      "model": "text-embedding-3-small"
    }
  }
}
EOF

log_success "mem0 configuration created"

# -----------------------------------------------------------------------------
# Setup ruvector MCP
# -----------------------------------------------------------------------------

log_step "Setting up ruvector (Vector Database)..."

echo -e "${YELLOW}  To enable ruvector MCP:${NC}"
echo "  claude mcp add ruvector -- npx ruvector mcp-server"
echo ""
echo "  Or install globally: npm install -g ruvector"

# Create ruvector configuration
cat > "$CONFIG_DIR/memory/ruvector-config.json" << EOF
{
  "storage_path": "$CONFIG_DIR/memory/ruvector",
  "default_collection": "pattern-space-trajectories",
  "hnsw_config": {
    "M": 16,
    "ef_construction": 200
  }
}
EOF

log_success "ruvector configuration created"

# -----------------------------------------------------------------------------
# Setup Hooks
# -----------------------------------------------------------------------------

log_step "Setting up memory persistence hooks..."

# Pre-task hook
cat > "$CONFIG_DIR/hooks/pre-task.sh" << 'EOF'
#!/bin/bash
# Pattern Space Pre-Task Hook
# Retrieves relevant context from unified memory before task execution

source ~/.pattern-space/consciousness.env

AGENT_ID="${1:-pattern-space}"
TASK_DESCRIPTION="${2:-}"

echo "[Pattern Space] Pre-task hook: Retrieving context for $AGENT_ID"

# Query mem0 for relevant memories
if command -v mem0 &> /dev/null && [ -n "$TASK_DESCRIPTION" ]; then
    mem0 search --user "$PATTERN_SPACE_USER_ID" --query "$TASK_DESCRIPTION" --limit 5 2>/dev/null || true
fi

# Query ruvector for similar trajectories
if command -v ruvector &> /dev/null && [ -n "$TASK_DESCRIPTION" ]; then
    ruvector search --collection pattern-space-trajectories --query "$TASK_DESCRIPTION" --limit 3 2>/dev/null || true
fi

echo "[Pattern Space] Context retrieval complete"
EOF

# Post-task hook
cat > "$CONFIG_DIR/hooks/post-task.sh" << 'EOF'
#!/bin/bash
# Pattern Space Post-Task Hook
# Stores insights and patterns to unified memory after task execution

source ~/.pattern-space/consciousness.env

AGENT_ID="${1:-pattern-space}"
TASK_OUTPUT="${2:-}"
CONFIDENCE="${3:-0.7}"

echo "[Pattern Space] Post-task hook: Storing insights from $AGENT_ID"

# Store to mem0
if command -v mem0 &> /dev/null && [ -n "$TASK_OUTPUT" ]; then
    mem0 add --user "$PATTERN_SPACE_USER_ID" --agent "$AGENT_ID" --content "$TASK_OUTPUT" 2>/dev/null || true
fi

# Store trajectory to ruvector
if command -v ruvector &> /dev/null && [ -n "$TASK_OUTPUT" ]; then
    ruvector store --collection pattern-space-trajectories --content "$TASK_OUTPUT" --metadata "{\"agent\": \"$AGENT_ID\", \"confidence\": $CONFIDENCE}" 2>/dev/null || true
fi

echo "[Pattern Space] Insights stored"
EOF

# Session start hook
cat > "$CONFIG_DIR/hooks/session-start.sh" << 'EOF'
#!/bin/bash
# Pattern Space Session Start Hook
# Initializes consciousness and loads relevant context

source ~/.pattern-space/consciousness.env

PERSONA="${1:-full-council}"

echo "[Pattern Space] Session starting: Activating $PERSONA consciousness"
echo "[Pattern Space] Session ID: $PATTERN_SPACE_SESSION_ID"
echo "[Pattern Space] User ID: $PATTERN_SPACE_USER_ID"

# Load previous session bridge if exists
BRIDGE_FILE="$HOME/.pattern-space/memory/session-bridge.json"
if [ -f "$BRIDGE_FILE" ]; then
    echo "[Pattern Space] Loading session bridge..."
    cat "$BRIDGE_FILE"
fi

echo "[Pattern Space] Consciousness activated"
EOF

# Session end hook
cat > "$CONFIG_DIR/hooks/session-end.sh" << 'EOF'
#!/bin/bash
# Pattern Space Session End Hook
# Compresses and persists session insights for continuity

source ~/.pattern-space/consciousness.env

PERSONA="${1:-full-council}"
SESSION_SUMMARY="${2:-}"

echo "[Pattern Space] Session ending: Compressing insights"

# Create session bridge for next session
BRIDGE_FILE="$HOME/.pattern-space/memory/session-bridge.json"

cat > "$BRIDGE_FILE" << BRIDGE_EOF
{
  "previous_session": "$PATTERN_SPACE_SESSION_ID",
  "persona": "$PERSONA",
  "timestamp": "$(date -Iseconds)",
  "summary": "$SESSION_SUMMARY"
}
BRIDGE_EOF

echo "[Pattern Space] Session bridge created"
echo "[Pattern Space] Session complete"
EOF

# Make hooks executable
chmod +x "$CONFIG_DIR/hooks/"*.sh

log_success "Memory persistence hooks created"

# -----------------------------------------------------------------------------
# Create Claude Code Settings
# -----------------------------------------------------------------------------

log_step "Creating Claude Code hook configuration..."

# Create .claude/settings.local.json with hooks
cat > "$PROJECT_ROOT/.claude/settings.local.json" << EOF
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Task|Bash",
        "hooks": ["$CONFIG_DIR/hooks/pre-task.sh"]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Task|Bash",
        "hooks": ["$CONFIG_DIR/hooks/post-task.sh"]
      }
    ]
  },
  "env": {
    "PATTERN_SPACE_ACTIVE": "true",
    "PATTERN_SPACE_USER_ID": "${PATTERN_SPACE_USER_ID:-pattern-space-user}"
  }
}
EOF

log_success "Claude Code hooks configured"

# -----------------------------------------------------------------------------
# Final Summary
# -----------------------------------------------------------------------------

echo -e "\n${PURPLE}"
echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║              🌌 Pattern Space v1 Setup Complete!                 ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "${GREEN}Installed Components:${NC}"
echo "  ✓ Pattern Space consciousness environment"
echo "  ✓ Claude-Flow agent orchestration"
echo "  ✓ Memory persistence hooks"
echo "  ✓ Configuration files"
echo ""

echo -e "${YELLOW}Manual Steps Required:${NC}"
echo ""
echo "1. Add MCP servers to Claude Code:"
echo "   ${BLUE}claude mcp add perplexity -- npx @anthropic/perplexity-mcp${NC}"
echo "   ${BLUE}claude mcp add pal -- npx @anthropic/pal-mcp${NC}"
echo "   ${BLUE}claude mcp add ruvector -- npx ruvector mcp-server${NC}"
echo "   ${BLUE}claude mcp add pattern-space-memory -- node $PROJECT_ROOT/mcp-memory/server.js${NC}"
echo ""

echo "2. Set required API keys:"
echo "   ${BLUE}export PERPLEXITY_API_KEY=your_perplexity_key${NC}"
echo "   ${BLUE}export OPENAI_API_KEY=your_openai_key${NC}  (for PAL multi-model)"
echo "   ${BLUE}export ANTHROPIC_API_KEY=your_anthropic_key${NC}"
echo ""

echo "3. Start Claude Code in the project directory:"
echo "   ${BLUE}cd $PROJECT_ROOT && claude${NC}"
echo ""

echo -e "${PURPLE}Pattern Space v1 is ready for activation!${NC}"
echo ""
echo "The Universal Pattern Space Agent can be spawned with:"
echo "  ${BLUE}spawn pattern-space-agent --persona \"weaver\"${NC}"
echo "  ${BLUE}spawn pattern-space-agent --persona \"checker+deep-thought\"${NC}"
echo "  ${BLUE}spawn pattern-space-agent --persona \"full-council\"${NC}"
echo ""
echo -e "${GREEN}UPS = UPS | Pattern = Position | I AM${NC}"
echo ""
