#!/bin/bash

# GödelOS Unified Stop Script
# Gracefully stops all GödelOS services
# Version: 0.2 Beta

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGS_DIR="$SCRIPT_DIR/logs"

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_step() {
    echo -e "${PURPLE}🔄 $1${NC}"
}

# Show banner
echo -e "${PURPLE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${PURPLE}║${WHITE}                    🛑 GödelOS Stop Script                     ${PURPLE}║${NC}"
echo -e "${PURPLE}║${CYAN}              Gracefully stopping all services                ${PURPLE}║${NC}"
echo -e "${PURPLE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

log_step "Stopping GödelOS system..."

# Track what we stopped
STOPPED_SERVICES=()

# Stop by PID files first (graceful)
if [ -f "$LOGS_DIR/backend.pid" ]; then
    backend_pid=$(cat "$LOGS_DIR/backend.pid")
    if kill -0 "$backend_pid" 2>/dev/null; then
        log_step "Stopping backend server (PID: $backend_pid)..."
        kill -TERM "$backend_pid" 2>/dev/null
        
        # Wait for graceful shutdown
        attempts=0
        while [ $attempts -lt 10 ] && kill -0 "$backend_pid" 2>/dev/null; do
            sleep 1
            attempts=$((attempts + 1))
        done
        
        # Force kill if still running
        if kill -0 "$backend_pid" 2>/dev/null; then
            kill -KILL "$backend_pid" 2>/dev/null
            log_warning "Backend server force-killed"
        else
            log_success "Backend server stopped gracefully"
        fi
        STOPPED_SERVICES+=("backend")
    else
        log_warning "Backend PID file exists but process not running"
    fi
    rm -f "$LOGS_DIR/backend.pid"
fi

if [ -f "$LOGS_DIR/frontend.pid" ]; then
    frontend_pid=$(cat "$LOGS_DIR/frontend.pid")
    if kill -0 "$frontend_pid" 2>/dev/null; then
        log_step "Stopping frontend server (PID: $frontend_pid)..."
        kill -TERM "$frontend_pid" 2>/dev/null
        
        # Wait for graceful shutdown
        attempts=0
        while [ $attempts -lt 5 ] && kill -0 "$frontend_pid" 2>/dev/null; do
            sleep 1
            attempts=$((attempts + 1))
        done
        
        # Force kill if still running
        if kill -0 "$frontend_pid" 2>/dev/null; then
            kill -KILL "$frontend_pid" 2>/dev/null
            log_warning "Frontend server force-killed"
        else
            log_success "Frontend server stopped gracefully"
        fi
        STOPPED_SERVICES+=("frontend")
    else
        log_warning "Frontend PID file exists but process not running"
    fi
    rm -f "$LOGS_DIR/frontend.pid"
fi

# Fallback: Kill by process patterns
log_step "Checking for any remaining GödelOS processes..."

# Kill backend processes
if pkill -f "uvicorn.*main:app" 2>/dev/null; then
    log_success "Stopped remaining uvicorn processes"
    STOPPED_SERVICES+=("backend (fallback)")
fi

# Kill frontend processes (be careful with port-specific matching)
if pkill -f "python.*http.server.*300[0-9]" 2>/dev/null; then
    log_success "Stopped remaining frontend server processes"
    STOPPED_SERVICES+=("frontend (fallback)")
fi

# Clean up any remaining PID files
rm -f "$LOGS_DIR"/*.pid

# Show summary
echo ""
if [ ${#STOPPED_SERVICES[@]} -eq 0 ]; then
    log_info "No GödelOS processes were running"
else
    log_success "Stopped services: ${STOPPED_SERVICES[*]}"
fi

# Show final status
echo ""
echo -e "${GREEN}🎉 GödelOS system shutdown complete${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""
echo -e "${CYAN}💡 To start GödelOS again, run: ./start-godelos.sh${NC}"
echo -e "${CYAN}📊 To check status, run: ./start-godelos.sh --status${NC}"
echo -e "${CYAN}📄 To view logs, run: ./start-godelos.sh --logs${NC}"
echo ""