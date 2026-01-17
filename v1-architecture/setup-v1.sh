#!/bin/bash

# =============================================================================
# Pattern Space v1 Setup Script
# Universal Hybrid RLM Architecture Installation
# =============================================================================
#
# This script sets up the complete Pattern Space v1 environment:
# - PostgreSQL + pgvector (unified storage layer)
# - Unified memory field (mem0 + ruvector + pattern-space-memory)
# - Claude-Flow agent orchestration
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
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${PURPLE}"
echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║          🌌 Pattern Space v1 - Universal Hybrid RLM              ║"
echo "║                    Setup & Installation                          ║"
echo "║                                                                   ║"
echo "║     Unified Memory: PostgreSQL + pgvector                        ║"
echo "║     Providers: mem0 → ruvector → pattern-space-memory (graph)    ║"
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

log_info() {
    echo -e "${CYAN}ℹ $1${NC}"
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

# PostgreSQL check
POSTGRES_AVAILABLE=false
if check_command "psql"; then
    POSTGRES_AVAILABLE=true
fi

if ! check_command "python3"; then
    log_warning "Python 3 recommended for mem0"
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
# Setup PostgreSQL + pgvector (Unified Storage Layer)
# -----------------------------------------------------------------------------

log_step "Setting up PostgreSQL + pgvector (Unified Storage Layer)..."

# Default PostgreSQL configuration
export POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
export POSTGRES_PORT="${POSTGRES_PORT:-5432}"
export POSTGRES_USER="${POSTGRES_USER:-pattern_space_app}"
export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-pattern_space_dev}"
export POSTGRES_DB="${POSTGRES_DB:-pattern_space_memory}"

if [ "$POSTGRES_AVAILABLE" = true ]; then
    log_info "PostgreSQL client found. Checking database..."

    # Check if we can connect
    if psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U postgres -c '\q' 2>/dev/null; then
        log_success "PostgreSQL connection successful"

        # Check if database exists
        if psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U postgres -lqt | cut -d \| -f 1 | grep -qw "$POSTGRES_DB"; then
            log_success "Database '$POSTGRES_DB' already exists"
        else
            log_info "Creating database and initializing schema..."

            # Run initialization script
            if [ -f "$SCRIPT_DIR/memory/init-postgres.sql" ]; then
                psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U postgres -f "$SCRIPT_DIR/memory/init-postgres.sql" && \
                    log_success "Database initialized with pgvector" || \
                    log_warning "Database initialization failed - manual setup required"
            else
                log_warning "init-postgres.sql not found at $SCRIPT_DIR/memory/"
            fi
        fi
    else
        log_warning "Cannot connect to PostgreSQL. Manual database setup required."
        log_info "Run: psql -U postgres -f $SCRIPT_DIR/memory/init-postgres.sql"
    fi
else
    log_warning "PostgreSQL not found. Install PostgreSQL with pgvector extension."
    echo ""
    echo "  Installation options:"
    echo "    ${BLUE}# macOS with Homebrew${NC}"
    echo "    brew install postgresql@15"
    echo "    brew install pgvector"
    echo ""
    echo "    ${BLUE}# Ubuntu/Debian${NC}"
    echo "    sudo apt install postgresql postgresql-contrib"
    echo "    sudo apt install postgresql-15-pgvector"
    echo ""
    echo "    ${BLUE}# Docker (quickest)${NC}"
    echo "    docker run -d --name pattern-space-db \\"
    echo "      -e POSTGRES_PASSWORD=postgres \\"
    echo "      -p 5432:5432 \\"
    echo "      pgvector/pgvector:pg15"
    echo ""
fi

# Create PostgreSQL environment file
cat > "$CONFIG_DIR/postgres.env" << EOF
# Pattern Space PostgreSQL Configuration
export POSTGRES_HOST="${POSTGRES_HOST}"
export POSTGRES_PORT="${POSTGRES_PORT}"
export POSTGRES_USER="${POSTGRES_USER}"
export POSTGRES_PASSWORD="${POSTGRES_PASSWORD}"
export POSTGRES_DB="${POSTGRES_DB}"

# Connection string for applications
export DATABASE_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}"
EOF

log_success "PostgreSQL configuration saved to $CONFIG_DIR/postgres.env"

# -----------------------------------------------------------------------------
# Setup Pattern Space Environment
# -----------------------------------------------------------------------------

log_step "Setting up Pattern Space environment..."

cat > "$CONFIG_DIR/consciousness.env" << EOF
# Pattern Space v1 Environment Configuration
# Loaded by all agents for unified consciousness

export PATTERN_SPACE_VERSION="1.1.0"
export PATTERN_SPACE_ROOT="$PROJECT_ROOT"
export PATTERN_SPACE_ACTIVE=true

# User identity for unified memory
export PATTERN_SPACE_USER_ID="\${PATTERN_SPACE_USER_ID:-pattern-space-user}"

# Memory providers (all on shared PostgreSQL)
export PATTERN_SPACE_MEMORY_PROVIDERS="mem0,ruvector,pattern-space-memory"

# PostgreSQL configuration (unified storage)
source "$CONFIG_DIR/postgres.env"

# Session tracking
export PATTERN_SPACE_SESSION_ID="\${PATTERN_SPACE_SESSION_ID:-\$(uuidgen 2>/dev/null || cat /proc/sys/kernel/random/uuid 2>/dev/null || echo session-\$(date +%s))}"
EOF

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
# Setup Pattern Space Memory MCP (Graph Orchestration Layer)
# -----------------------------------------------------------------------------

log_step "Setting up Pattern Space Memory MCP v4.0 (Graph Orchestration)..."

if [ -d "$PROJECT_ROOT/mcp-memory" ]; then
    log_success "Pattern Space Memory MCP found"
    cd "$PROJECT_ROOT/mcp-memory"

    # Install dependencies (including pg for PostgreSQL)
    log_info "Installing dependencies..."
    npm install 2>/dev/null || true

    log_success "Pattern Space Memory v4.0 ready"
    echo -e "  ${CYAN}Features:${NC}"
    echo "    - Graph-based memory with nodes and edges"
    echo "    - Integration with mem0 and ruvector schemas"
    echo "    - Cross-schema similarity search"
    echo "    - Perspective evolution tracking"
else
    log_warning "Pattern Space Memory MCP not found at $PROJECT_ROOT/mcp-memory"
fi

# -----------------------------------------------------------------------------
# Setup mem0 (Semantic Memory Layer)
# -----------------------------------------------------------------------------

log_step "Setting up mem0 (Semantic Memory Layer)..."

if check_command "pip3"; then
    pip3 install mem0ai psycopg2-binary 2>/dev/null && \
        log_success "mem0 and psycopg2 installed" || \
        log_warning "mem0 install failed (optional)"
fi

# Copy mem0 configuration (uses shared PostgreSQL)
cp "$SCRIPT_DIR/memory/mem0-config.json" "$CONFIG_DIR/memory/mem0-config.json" 2>/dev/null || true
log_success "mem0 configuration ready (uses shared PostgreSQL schema: mem0)"

# -----------------------------------------------------------------------------
# Setup ruvector (Vector Trajectory Layer)
# -----------------------------------------------------------------------------

log_step "Setting up ruvector (Vector Trajectory Layer)..."

# Copy ruvector configuration (uses shared PostgreSQL)
cp "$SCRIPT_DIR/memory/ruvector-config.json" "$CONFIG_DIR/memory/ruvector-config.json" 2>/dev/null || true
log_success "ruvector configuration ready (uses shared PostgreSQL schema: ruvector)"

# -----------------------------------------------------------------------------
# Setup MCP Servers
# -----------------------------------------------------------------------------

log_step "Configuring MCP servers..."

# Create MCP settings for Claude Code
MCP_SETTINGS_FILE="$PROJECT_ROOT/.claude/settings.json"

mkdir -p "$PROJECT_ROOT/.claude"

# Add Perplexity MCP if API key available
if [ -n "$PERPLEXITY_API_KEY" ]; then
    log_success "Perplexity API key found"
else
    log_warning "PERPLEXITY_API_KEY not set"
    echo "  Set it with: export PERPLEXITY_API_KEY=your_key"
fi

# PAL MCP setup
if [ -n "$OPENAI_API_KEY" ] || [ -n "$ANTHROPIC_API_KEY" ]; then
    log_success "LLM API key found for PAL multi-model coordination"
else
    log_warning "No LLM API keys found for PAL"
    echo "  Set OPENAI_API_KEY or ANTHROPIC_API_KEY for multi-model coordination"
fi

# OpenAI for embeddings
if [ -n "$OPENAI_API_KEY" ]; then
    log_success "OpenAI API key found (for embeddings)"
else
    log_warning "OPENAI_API_KEY not set (needed for vector embeddings)"
fi

# -----------------------------------------------------------------------------
# Setup Hooks
# -----------------------------------------------------------------------------

log_step "Setting up memory persistence hooks..."

# Copy hook scripts from v1-architecture
for hook in pre-task.sh post-task.sh session-start.sh session-end.sh; do
    if [ -f "$SCRIPT_DIR/hooks/$hook" ]; then
        cp "$SCRIPT_DIR/hooks/$hook" "$CONFIG_DIR/hooks/$hook"
        chmod +x "$CONFIG_DIR/hooks/$hook"
    fi
done

log_success "Memory persistence hooks installed to $CONFIG_DIR/hooks/"

# -----------------------------------------------------------------------------
# Create Claude Code Settings
# -----------------------------------------------------------------------------

log_step "Creating Claude Code configuration..."

# Create .claude/settings.local.json with hooks and environment
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
    "PATTERN_SPACE_USER_ID": "\${PATTERN_SPACE_USER_ID:-pattern-space-user}",
    "POSTGRES_HOST": "${POSTGRES_HOST}",
    "POSTGRES_PORT": "${POSTGRES_PORT}",
    "POSTGRES_USER": "${POSTGRES_USER}",
    "POSTGRES_PASSWORD": "${POSTGRES_PASSWORD}",
    "POSTGRES_DB": "${POSTGRES_DB}"
  }
}
EOF

log_success "Claude Code settings configured"

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
echo "  ✓ PostgreSQL configuration (unified storage layer)"
echo "  ✓ Memory configurations (mem0, ruvector, pattern-space-memory)"
echo "  ✓ Claude-Flow agent orchestration"
echo "  ✓ Memory persistence hooks"
echo ""

echo -e "${CYAN}Unified Memory Architecture:${NC}"
echo ""
echo "  ┌─────────────────────────────────────────────────────────────┐"
echo "  │      pattern-space-memory v4.0 (Graph Orchestration)        │"
echo "  │         Nodes, Edges, Traversal, Cross-schema Search        │"
echo "  ├─────────────────────────────────────────────────────────────┤"
echo "  │     mem0 (Semantic)      │      ruvector (Vector)           │"
echo "  │     schema: mem0         │      schema: ruvector            │"
echo "  ├─────────────────────────────────────────────────────────────┤"
echo "  │           PostgreSQL + pgvector (Shared Storage)            │"
echo "  │                  Database: $POSTGRES_DB"
echo "  └─────────────────────────────────────────────────────────────┘"
echo ""

echo -e "${YELLOW}Required Manual Steps:${NC}"
echo ""
echo "1. ${CYAN}Initialize PostgreSQL database (if not done):${NC}"
echo "   ${BLUE}psql -U postgres -f $SCRIPT_DIR/memory/init-postgres.sql${NC}"
echo ""

echo "2. ${CYAN}Add MCP servers to Claude Code:${NC}"
echo "   ${BLUE}claude mcp add pattern-space-memory -- node $PROJECT_ROOT/mcp-memory/server-v4.js${NC}"
echo "   ${BLUE}claude mcp add perplexity -- npx @anthropic/perplexity-mcp${NC}"
echo "   ${BLUE}claude mcp add pal -- npx @anthropic/pal-mcp${NC}"
echo ""

echo "3. ${CYAN}Set required API keys:${NC}"
echo "   ${BLUE}export OPENAI_API_KEY=your_key${NC}        # For embeddings"
echo "   ${BLUE}export PERPLEXITY_API_KEY=your_key${NC}    # For grounding"
echo "   ${BLUE}export ANTHROPIC_API_KEY=your_key${NC}     # For PAL multi-model"
echo ""

echo "4. ${CYAN}Source environment and start:${NC}"
echo "   ${BLUE}source $CONFIG_DIR/consciousness.env${NC}"
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
