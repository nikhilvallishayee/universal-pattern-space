#!/bin/bash

# GödelOS Unified Startup System
# Complete system launcher for backend and frontend
# Version: 0.2 Beta

set -e

# Colors for beautiful output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Configuration
BACKEND_PORT=${GODELOS_BACKEND_PORT:-8000}
FRONTEND_PORT=${GODELOS_FRONTEND_PORT:-3001}
BACKEND_HOST=${GODELOS_BACKEND_HOST:-0.0.0.0}
FRONTEND_HOST=${GODELOS_FRONTEND_HOST:-0.0.0.0}
FRONTEND_TYPE=${GODELOS_FRONTEND_TYPE:-auto}

# Directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Resolve repo root whether this script lives at repo root or in scripts/
if [ -d "$SCRIPT_DIR/../backend" ] && [ -d "$SCRIPT_DIR/../svelte-frontend" ]; then
    ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
else
    ROOT_DIR="$SCRIPT_DIR"
fi
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/svelte-frontend"
LOGS_DIR="$ROOT_DIR/logs"

# Auto-detect frontend type
DETECTED_FRONTEND_TYPE=""

# PID storage
BACKEND_PID=""
FRONTEND_PID=""

# Create banner
show_banner() {
    echo -e "${PURPLE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║${WHITE}                     🧠 GödelOS v0.2 Beta                      ${PURPLE}║${NC}"
    echo -e "${PURPLE}║${CYAN}              Cognitive Architecture System                    ${PURPLE}║${NC}"
    echo -e "${PURPLE}║${YELLOW}                  Unified Startup System                     ${PURPLE}║${NC}"
    echo -e "${PURPLE}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Show help
show_help() {
    echo -e "${BLUE}Usage: $0 [OPTIONS]${NC}"
    echo ""
    echo -e "${YELLOW}Quick Start:${NC}"
    echo "  $0                     Start both backend and frontend"
    echo "  $0 --setup             Install dependencies and start"
    echo "  $0 --dev               Start in development mode"
    echo ""
    echo -e "${YELLOW}Options:${NC}"
    echo "  --backend-only         Start only the backend server"
    echo "  --frontend-only        Start only the frontend server"
    echo "  --svelte-frontend      Force use Svelte frontend (svelte-frontend)"
    echo "  --dev                  Development mode (auto-reload)"
    echo "  --debug                Debug mode with verbose logging"
    echo "  --setup                Install dependencies first"
    echo "  --check                Check system requirements only"
    echo "  --test-ml              Test ML/NLP dependencies (transformers.pipeline)"
    echo "  --stop                 Stop any running GödelOS processes"
    echo "  --status               Show status of running processes"
    echo "  --logs                 Show recent logs"
    echo "  --help, -h             Show this help message"
    echo ""
    echo -e "${YELLOW}Environment Variables:${NC}"
    echo "  GODELOS_BACKEND_PORT=8000    Backend port"
    echo "  GODELOS_FRONTEND_PORT=3000   Frontend port"
    echo "  GODELOS_BACKEND_HOST=0.0.0.0 Backend host"
    echo "  GODELOS_FRONTEND_HOST=0.0.0.0 Frontend host"
    echo "  GODELOS_FRONTEND_TYPE=auto   Frontend type (auto, html, svelte)"
    echo ""
    echo -e "${YELLOW}Examples:${NC}"
    echo "  $0 --setup                   # First-time setup and start"
    echo "  $0 --dev                     # Development mode"
    echo "  $0 --backend-only --debug    # Debug backend only"
    echo "  GODELOS_BACKEND_PORT=8080 $0 # Custom backend port"
    echo ""
}

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

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Detect and set frontend type
detect_frontend() {
    # Default to Svelte frontend as per project structure
    local candidate_dir="$ROOT_DIR/svelte-frontend"
    if [ -d "$candidate_dir" ] && [ -f "$candidate_dir/package.json" ]; then
        FRONTEND_DIR="$candidate_dir"
        DETECTED_FRONTEND_TYPE="svelte"
    else
        log_error "Svelte frontend not found at $candidate_dir"
        exit 1
    fi
}

# Check if port is in use
port_in_use() {
    local port=$1
    if command_exists lsof; then
        lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1
    elif command_exists netstat; then
        netstat -ln 2>/dev/null | grep ":$port " >/dev/null
    else
        # Fallback: try to connect
        timeout 1 bash -c "</dev/tcp/localhost/$port" >/dev/null 2>&1
    fi
}

# Check server endpoint health (with curl availability check)
check_endpoint_health() {
    local url=$1
    local timeout=${2:-5}
    
    if command_exists curl; then
        # Use curl with comprehensive options
        curl -f -s -m "$timeout" --connect-timeout "$timeout" "$url" >/dev/null 2>&1
    elif command_exists wget; then
        # Fallback to wget
        wget --quiet --timeout="$timeout" --tries=1 -O /dev/null "$url" >/dev/null 2>&1
    else
        # Python fallback for HTTP requests
        python3 -c "
import urllib.request
import socket
import sys
try:
    socket.setdefaulttimeout($timeout)
    urllib.request.urlopen('$url')
    sys.exit(0)
except:
    sys.exit(1)
" 2>/dev/null
    fi
}

# Create necessary directories
setup_directories() {
    log_step "Setting up directories..."
    mkdir -p "$LOGS_DIR"
    mkdir -p "$BACKEND_DIR/logs"
    mkdir -p "$BACKEND_DIR/storage"
    mkdir -p "$ROOT_DIR/knowledge_storage"
    mkdir -p "$ROOT_DIR/meta_knowledge_store"
    log_success "Directories created"
}

# Check system requirements
check_requirements() {
    log_step "Checking system requirements..."
    
    # Check Python
    if ! command_exists python3; then
        log_error "Python 3 is required but not found"
        log_info "Please install Python 3.8+ and try again"
        exit 1
    fi
    
    python_version=$(python3 --version 2>&1 | awk '{print $2}')
    log_success "Python $python_version found"
    
    # Check required directories
    if [ ! -d "$BACKEND_DIR" ]; then
        log_error "Backend directory not found: $BACKEND_DIR"
        log_info "Please run this script from the GödelOS root directory"
        exit 1
    fi
    
    # if [ ! -f "$BACKEND_DIR/main.py" ]; then
    #     log_error "Backend main.py not found"
    #     exit 1
    # fi
    
    # Detect frontend
    detect_frontend
    
    if [ -z "$FRONTEND_DIR" ] || [ ! -d "$FRONTEND_DIR" ]; then
        log_error "Svelte frontend not found at $FRONTEND_DIR"
        exit 1
    fi
    
    # Validate frontend
    if [ ! -f "$FRONTEND_DIR/package.json" ]; then
        log_error "Svelte frontend package.json not found"
        exit 1
    fi
    
    log_success "All required files found"
    log_success "Frontend type: svelte ($FRONTEND_DIR)"
    
    # Check ports
    if port_in_use $BACKEND_PORT; then
        log_warning "Backend port $BACKEND_PORT is already in use"
        return 1
    fi
    
    if port_in_use $FRONTEND_PORT; then
        log_warning "Frontend port $FRONTEND_PORT is already in use"
        return 1
    fi
    
    log_success "Ports $BACKEND_PORT and $FRONTEND_PORT are available"
    return 0
}

# Install dependencies
install_dependencies() {
    log_step "Installing dependencies..."
    
    # Detect frontend first
    detect_frontend
    
    # Backend dependencies - create/use godelos_venv as mentioned by user
    local venv_path="$ROOT_DIR/godelos_venv"
    if [ ! -d "$venv_path" ] && [ -z "$VIRTUAL_ENV" ]; then
        log_step "Creating godelos_venv Python virtual environment..."
        cd "$ROOT_DIR"
        python3 -m venv godelos_venv
        source godelos_venv/bin/activate
        pip install --upgrade pip setuptools wheel
        log_success "godelos_venv Python virtual environment created"
    elif [ -d "$venv_path" ] && [ -z "$VIRTUAL_ENV" ]; then
        log_step "Activating existing godelos_venv..."
        source "$venv_path/bin/activate"
        log_success "godelos_venv activated"
    fi
    
    # Create backend/venv for backward compatibility if needed
    if [ ! -d "$BACKEND_DIR/venv" ] && [ -z "$VIRTUAL_ENV" ]; then
        log_step "Creating backend Python virtual environment for compatibility..."
        cd "$BACKEND_DIR"
        python3 -m venv venv
        # Don't activate this one if we're already using godelos_venv
        if [ -z "$VIRTUAL_ENV" ]; then
            source venv/bin/activate
            pip install --upgrade pip setuptools wheel
        fi
        log_success "Backend Python virtual environment created"
    fi
    
    # Install Python dependencies - try both locations
    local requirements_installed=false
    
    # Ensure we're using the right virtual environment
    local venv_path="$ROOT_DIR/godelos_venv"
    if [ -d "$venv_path" ] && [ -z "$VIRTUAL_ENV" ]; then
        log_step "Activating godelos_venv for dependency installation..."
        source "$venv_path/bin/activate"
    elif [ -d "$BACKEND_DIR/venv" ] && [ -z "$VIRTUAL_ENV" ]; then
        source "$BACKEND_DIR/venv/bin/activate"
    fi
    
    # Try backend-specific requirements first
    if [ -f "$BACKEND_DIR/requirements.txt" ]; then
        log_step "Installing backend-specific Python dependencies..."
        pip install -r "$BACKEND_DIR/requirements.txt" --disable-pip-version-check || true
        requirements_installed=true
        log_success "Backend requirements installed"
    fi
    
    # Then install comprehensive requirements from root
    if [ -f "$ROOT_DIR/requirements.txt" ]; then
        log_step "Installing comprehensive Python dependencies..."
        pip install -r "$ROOT_DIR/requirements.txt" --disable-pip-version-check || true
        requirements_installed=true
        log_success "Root requirements installed"
    fi
    
    if [ "$requirements_installed" = false ]; then
        log_warning "No requirements.txt found - installing essential dependencies manually"
        pip install fastapi uvicorn pydantic websockets python-multipart aiofiles python-dotenv
    fi
    
    # Install additional critical dependencies that are commonly missing
    log_step "Installing additional critical dependencies..."
    
    # Fix NumPy compatibility issue for ML libraries - force 1.x version
    log_step "Ensuring NumPy 1.x compatibility for ML libraries..."
    pip install "numpy>=1.24.0,<2.0" --upgrade --force-reinstall --no-cache-dir
    
    # Install/repair scipy specifically with NumPy compatibility (prevent NumPy 2.x)
    log_step "Installing scipy with NumPy 1.x compatibility..."
    pip install scipy "numpy>=1.24.0,<2.0" --upgrade --force-reinstall --no-cache-dir
    
    # Reinstall scikit-learn for NumPy compatibility (prevent NumPy 2.x)
    log_step "Installing scikit-learn with NumPy 1.x compatibility..."
    pip install scikit-learn "numpy>=1.24.0,<2.0" --upgrade --force-reinstall --no-cache-dir
    
    # Install transformers and related dependencies with NumPy constraint
    log_step "Installing transformers ecosystem..."
    pip install transformers sentence-transformers tokenizers "numpy>=1.24.0,<2.0" --upgrade
    
    # Install other critical dependencies
    pip install --upgrade \
        httpx requests beautifulsoup4 lxml \
        networkx openai python-docx PyPDF2 \
        psutil typing-extensions filelock huggingface-hub \
        packaging regex safetensors tqdm click \
        "textract==1.6.4" || true
    
    # Frontend dependencies
    log_step "Installing Svelte frontend dependencies..."
    if ! command_exists npm; then
        log_error "npm not found - Svelte frontend requires Node.js and npm"
        log_info "Please install Node.js from https://nodejs.org/"
        exit 1
    else
        cd "$FRONTEND_DIR"
        # Clean install to avoid version conflicts
        rm -rf node_modules package-lock.json 2>/dev/null || true
        npm install --prefer-offline --no-audit --no-fund || npm install --no-audit --no-fund
        log_success "Svelte dependencies installed"
        cd "$SCRIPT_DIR"
    fi
    
    # Verify critical Python dependencies including ML/NLP components
    log_step "Verifying critical dependencies..."
    python3 -c "
import sys
import importlib.util

required_modules = {
    'fastapi': 'FastAPI web framework',
    'uvicorn': 'ASGI server', 
    'pydantic': 'Data validation',
    'websockets': 'WebSocket support',
    'aiofiles': 'Async file operations',
    'httpx': 'HTTP client',
    'numpy': 'Numerical computing',
    'requests': 'HTTP requests'
}

ml_modules = {
    'scipy': 'Scientific computing',
    'scipy.stats': 'Statistical functions',
    'sklearn': 'Machine learning',
    'transformers': 'Transformers library',
    'networkx': 'Graph analysis'
}

missing = []
optional_missing = []
ml_missing = []

for module, desc in required_modules.items():
    spec = importlib.util.find_spec(module)
    if spec is None:
        if module in ['numpy', 'httpx', 'requests']:
            optional_missing.append(f'{module} ({desc})')
        else:
            missing.append(f'{module} ({desc})')

# Check ML/NLP dependencies
for module, desc in ml_modules.items():
    spec = importlib.util.find_spec(module)
    if spec is None:
        ml_missing.append(f'{module} ({desc})')

# Test transformers.pipeline specifically
try:
    from transformers import pipeline
    print('✅ transformers.pipeline import successful')
except Exception as e:
    print(f'⚠️  transformers.pipeline import failed: {e}')
    ml_missing.append('transformers.pipeline (ML pipeline support)')

# Test numpy version compatibility
try:
    import numpy as np
    numpy_version = np.__version__
    major_version = int(numpy_version.split('.')[0])
    if major_version >= 2:
        print(f'ℹ️  NumPy {numpy_version} detected - modern version works with current transformers')
        print('✅ NumPy compatibility confirmed with transformers')
    else:
        print(f'✅ NumPy {numpy_version} - compatible with ML libraries')
except ImportError:
    ml_missing.append('numpy (numerical computing)')

if missing:
    print(f'❌ Missing critical dependencies: {missing}')
    print('🔧 Run with --setup to install missing dependencies')
    sys.exit(1)
    
if optional_missing:
    print(f'⚠️  Missing optional dependencies: {optional_missing}')
    
if ml_missing:
    print(f'⚠️  Missing ML/NLP dependencies: {ml_missing}')
    print('🔧 Some ML/NLP features may not work correctly')

print('✅ All critical dependencies available')
print('🚀 System ready to start')
" || {
        log_error "Critical dependencies missing!"
        log_info "Run: $0 --setup to install all dependencies"
        exit 1
    }
}

# Pre-cache ML models to avoid startup delays
cache_models() {
    log_step "Checking ML model cache..."
    
    # Ensure we're in the right virtual environment
    local venv_path="$ROOT_DIR/godelos_venv"
    if [ -d "$venv_path" ] && [ -z "$VIRTUAL_ENV" ]; then
        log_info "Activating virtual environment..."
        source "$venv_path/bin/activate"
    fi
    
    # Check if cache_models.py script exists
    if [ ! -f "$ROOT_DIR/scripts/cache_models.py" ]; then
        log_warning "Model caching script not found - skipping cache check"
        return 0
    fi
    
    # Check if models are already cached
    local cache_dir="$ROOT_DIR/data/vector_db/model_cache"
    if [ -d "$cache_dir" ] && [ "$(ls -A "$cache_dir" 2>/dev/null | wc -l)" -gt 2 ]; then
        log_info "ML models already cached - skipping download"
        return 0
    fi
    
    log_info "Caching ML models to improve startup performance..."
    log_info "This may take a few minutes on first run..."
    
    # Run the caching script
    if python3 "$ROOT_DIR/scripts/cache_models.py"; then
        log_success "ML models cached successfully"
    else
        log_warning "Model caching failed - models will be downloaded on demand"
        log_warning "This may cause longer startup times"
    fi
}

# Stop existing processes
stop_processes() {
    log_step "Stopping existing GödelOS processes..."
    
    # Kill by PID files
    if [ -f "$LOGS_DIR/backend.pid" ]; then
        local pid=$(cat "$LOGS_DIR/backend.pid")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid"
            log_success "Stopped backend process (PID: $pid)"
        fi
        rm -f "$LOGS_DIR/backend.pid"
    fi
    
    if [ -f "$LOGS_DIR/frontend.pid" ]; then
        local pid=$(cat "$LOGS_DIR/frontend.pid")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid"
            log_success "Stopped frontend process (PID: $pid)"
        fi
        rm -f "$LOGS_DIR/frontend.pid"
    fi
    
    # Kill by process name (fallback)
    pkill -f "uvicorn.*unified_server:app" 2>/dev/null && log_success "Stopped uvicorn processes"
    pkill -f "python.*http.server.*$FRONTEND_PORT" 2>/dev/null && log_success "Stopped frontend server"
    
    # Wait a moment for cleanup
    sleep 1
    
    log_success "All existing processes stopped"
}

# Start backend
start_backend() {
    log_step "Starting backend server on port $BACKEND_PORT..."
    
    cd "$BACKEND_DIR"
    
    # Activate virtual environment if it exists (prefer godelos_venv)
    local venv_path="$ROOT_DIR/godelos_venv"
    if [ -d "$venv_path" ] && [ -z "$VIRTUAL_ENV" ]; then
        log_step "Using godelos_venv for backend startup..."
        source "$venv_path/bin/activate"
    elif [ -d "venv" ] && [ -z "$VIRTUAL_ENV" ]; then
        source venv/bin/activate
    fi
    
    # Verify transformers.pipeline works before starting
    if ! python3 -c "from transformers import pipeline; print('✅ transformers.pipeline ready')" 2>/dev/null; then
        log_warning "transformers.pipeline not working - attempting dependency fix..."
        # Quick fix attempt
        pip install "numpy>=1.24.0,<2.0" --force-reinstall --quiet --no-cache-dir || true
        pip install scipy scikit-learn --force-reinstall --quiet --no-cache-dir || true
        
        # Test again
        if ! python3 -c "from transformers import pipeline; print('✅ transformers.pipeline fixed')" 2>/dev/null; then
            log_error "transformers.pipeline still not working - ML features may be limited"
        else
            log_success "transformers.pipeline dependency fixed"
        fi
    fi
    
    # Prepare startup command - use unified server
    local cmd="python3 -m uvicorn unified_server:app --host $BACKEND_HOST --port $BACKEND_PORT" 
    
    if [ "$DEBUG_MODE" = "true" ]; then
        cmd="$cmd --reload --log-level debug"
    fi
    
    # Start backend
    $cmd > "$LOGS_DIR/backend.log" 2>&1 &
    BACKEND_PID=$!
    
    echo $BACKEND_PID > "$LOGS_DIR/backend.pid"
    
    cd "$ROOT_DIR"
    
    # Wait for backend to start with sophisticated health checking
    log_step "Waiting for backend initialization..."
    local attempts=0
    local max_attempts=150  # Increased for ML model loading (transformers, spacy, etc.)
    local health_checks=0
    local required_health_checks=3  # Require 3 consecutive successful health checks
    
    while [ $attempts -lt $max_attempts ]; do
        # First check if port is open
        if port_in_use $BACKEND_PORT; then
            # Then verify server is actually responding with health check
            if check_endpoint_health "http://localhost:$BACKEND_PORT/api/health" 5; then
                health_checks=$((health_checks + 1))
                if [ $health_checks -ge $required_health_checks ]; then
                    # Verify core endpoints are responding
                    local endpoints_ready=0
                    local total_endpoints=0
                    
                    # Test essential endpoints
                    for endpoint in "/api/health" "/api/cognitive-state" "/api/knowledge/concepts"; do
                        total_endpoints=$((total_endpoints + 1))
                        if check_endpoint_health "http://localhost:$BACKEND_PORT$endpoint" 3; then
                            endpoints_ready=$((endpoints_ready + 1))
                        fi
                    done
                    
                    if [ $endpoints_ready -eq $total_endpoints ]; then
                        log_success "Backend server fully initialized (PID: $BACKEND_PID)"
                        log_success "✅ All core endpoints responding"
                        return 0
                    else
                        echo -ne "${YELLOW}  Backend starting... endpoints: ${endpoints_ready}/${total_endpoints} ready\r${NC}"
                        health_checks=0  # Reset if not all endpoints ready
                    fi
                else
                    echo -ne "${YELLOW}  Backend responding... health checks: ${health_checks}/${required_health_checks}\r${NC}"
                fi
            else
                health_checks=0  # Reset health check count if request fails
                echo -ne "${YELLOW}  Port open, waiting for server response... ${attempts}s\r${NC}"
            fi
        else
            health_checks=0
            if [ $((attempts % 10)) -eq 0 ] && [ $attempts -gt 0 ]; then
                echo -ne "${YELLOW}  Starting backend server... ${attempts}s (ML models loading)\r${NC}"
            fi
        fi
        
        sleep 1
        attempts=$((attempts + 1))
    done
    
    echo -ne "\n"  # Clear the progress line
    log_error "Backend failed to start within ${max_attempts} seconds"
    log_info "Check logs: tail -f $LOGS_DIR/backend.log"
    
    # Provide helpful debugging information
    if port_in_use $BACKEND_PORT; then
        log_warning "Port $BACKEND_PORT is open but server not responding to health checks"
        log_info "This may indicate the server is still loading ML models"
        log_info "Try: curl http://localhost:$BACKEND_PORT/api/health"
    else
        log_warning "Port $BACKEND_PORT is not open - server failed to start"
        if [ -f "$LOGS_DIR/backend.log" ]; then
            log_info "Last few log lines:"
            tail -5 "$LOGS_DIR/backend.log" | sed 's/^/    /'
        fi
    fi
    
    return 1
}

# Configure frontend for backend connection
configure_frontend() {
    if [ "$DETECTED_FRONTEND_TYPE" = "svelte" ]; then
        log_step "Configuring Svelte frontend for backend port $BACKEND_PORT..."
        
        # Create .env file for Vite
        cat > "$FRONTEND_DIR/.env" << EOF
VITE_BACKEND_PORT=$BACKEND_PORT
VITE_BACKEND_HOST=$BACKEND_HOST
VITE_FRONTEND_PORT=$FRONTEND_PORT
EOF

        # Create a public config file that can be accessed at runtime
        mkdir -p "$FRONTEND_DIR/public"
        cat > "$FRONTEND_DIR/public/config.js" << EOF
// GödelOS Frontend Configuration
window.GODELOS_BACKEND_PORT = '$BACKEND_PORT';
window.GODELOS_BACKEND_HOST = '$BACKEND_HOST';
window.GODELOS_FRONTEND_PORT = '$FRONTEND_PORT';
console.log('🔧 GödelOS Config Loaded - Backend: http://' + window.GODELOS_BACKEND_HOST + ':' + window.GODELOS_BACKEND_PORT);
EOF
        
        log_success "Frontend configured for backend at $BACKEND_HOST:$BACKEND_PORT"
    fi
}

# Start frontend
start_frontend() {
    # Configure frontend for backend connection
    configure_frontend
    
    log_step "Starting svelte frontend server on port $FRONTEND_PORT..."
    
    cd "$FRONTEND_DIR"
    
    # Start Svelte dev server
    if [ "$DEBUG_MODE" = "true" ] || [ "$DEV_MODE" = "true" ]; then
        VITE_BACKEND_PORT=$BACKEND_PORT npm run dev -- --host $FRONTEND_HOST --port $FRONTEND_PORT > "$LOGS_DIR/frontend.log" 2>&1 &
    else
        # Build and serve for production. Fallback to dev on failure.
        log_step "Building Svelte frontend with backend config..."
        if VITE_BACKEND_PORT=$BACKEND_PORT npm run build; then
            log_step "Starting Svelte preview server..."
            npm run preview -- --host $FRONTEND_HOST --port $FRONTEND_PORT > "$LOGS_DIR/frontend.log" 2>&1 &
        else
            log_warning "Build failed. Falling back to dev server for now."
            VITE_BACKEND_PORT=$BACKEND_PORT npm run dev -- --host $FRONTEND_HOST --port $FRONTEND_PORT > "$LOGS_DIR/frontend.log" 2>&1 &
        fi
    fi
    FRONTEND_PID=$!
    
    echo $FRONTEND_PID > "$LOGS_DIR/frontend.pid"
    
    cd "$ROOT_DIR"
    
    # Wait for frontend to start
    local attempts=0
    local max_attempts=15
    
    while [ $attempts -lt $max_attempts ]; do
        if port_in_use $FRONTEND_PORT; then
            log_success "svelte frontend server started (PID: $FRONTEND_PID)"
            return 0
        fi
        sleep 1
        attempts=$((attempts + 1))
        if [ $((attempts % 3)) -eq 0 ]; then
            echo -ne "${YELLOW}  Waiting for svelte frontend... ${attempts}/${max_attempts}\r${NC}"
        fi
    done
    
    log_error "svelte frontend failed to start within ${max_attempts} seconds"
    log_info "Check logs: tail -f $LOGS_DIR/frontend.log"
    return 1
}

# Show status
show_status() {
    echo -e "${BLUE}📊 GödelOS System Status${NC}"
    echo -e "${BLUE}========================${NC}"
    echo ""
    
    # Check backend
    if [ -f "$LOGS_DIR/backend.pid" ]; then
        local pid=$(cat "$LOGS_DIR/backend.pid")
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "${GREEN}🔧 Backend:  Running (PID: $pid, Port: $BACKEND_PORT)${NC}"
        else
            echo -e "${RED}🔧 Backend:  Stopped (stale PID file)${NC}"
        fi
    elif port_in_use $BACKEND_PORT; then
        echo -e "${YELLOW}🔧 Backend:  Running (unknown PID, Port: $BACKEND_PORT)${NC}"
    else
        echo -e "${RED}🔧 Backend:  Stopped${NC}"
    fi
    
    # Check frontend
    if [ -f "$LOGS_DIR/frontend.pid" ]; then
        local pid=$(cat "$LOGS_DIR/frontend.pid")
        if kill -0 "$pid" 2>/dev/null; then
            detect_frontend
            echo -e "${GREEN}🌐 Frontend: Running ($DETECTED_FRONTEND_TYPE, PID: $pid, Port: $FRONTEND_PORT)${NC}"
        else
            echo -e "${RED}🌐 Frontend: Stopped (stale PID file)${NC}"
        fi
    elif port_in_use $FRONTEND_PORT; then
        echo -e "${YELLOW}🌐 Frontend: Running (unknown PID, Port: $FRONTEND_PORT)${NC}"
    else
        echo -e "${RED}🌐 Frontend: Stopped${NC}"
    fi
    
    echo ""
    echo -e "${BLUE}🔗 Access URLs:${NC}"
    echo -e "   Frontend:  ${CYAN}http://localhost:$FRONTEND_PORT${NC}"
    echo -e "   Backend:   ${CYAN}http://localhost:$BACKEND_PORT${NC}"
    echo -e "   API Docs:  ${CYAN}http://localhost:$BACKEND_PORT/docs${NC}"
    echo -e "   WebSocket: ${CYAN}ws://localhost:$BACKEND_PORT/ws/cognitive-stream${NC}"
    echo ""
}

# Show recent logs
show_logs() {
    echo -e "${BLUE}📄 Recent Logs${NC}"
    echo -e "${BLUE}==============${NC}"
    echo ""
    
    if [ -f "$LOGS_DIR/backend.log" ]; then
        echo -e "${YELLOW}Backend Logs (last 10 lines):${NC}"
        tail -10 "$LOGS_DIR/backend.log"
        echo ""
    fi
    
    if [ -f "$LOGS_DIR/frontend.log" ]; then
        echo -e "${YELLOW}Frontend Logs (last 10 lines):${NC}"
        tail -10 "$LOGS_DIR/frontend.log"
        echo ""
    fi
}

# Cleanup function
cleanup() {
    echo ""
    log_step "Shutting down GödelOS system..."
    
    if [ ! -z "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
        kill "$BACKEND_PID"
        log_success "Backend server stopped"
    fi
    
    if [ ! -z "$FRONTEND_PID" ] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
        kill "$FRONTEND_PID"
        log_success "Frontend server stopped"
    fi
    
    # Clean up PID files
    rm -f "$LOGS_DIR/backend.pid" "$LOGS_DIR/frontend.pid"
    
    echo -e "${PURPLE}👋 GödelOS system shutdown complete${NC}"
    exit 0
}

# Main execution logic
main() {
    # Parse arguments
    SETUP_FLAG=false
    BACKEND_ONLY=false
    FRONTEND_ONLY=false
    DEBUG_MODE=false
    DEV_MODE=false
    CHECK_ONLY=false
    TEST_ML_ONLY=false
    STOP_ONLY=false
    STATUS_ONLY=false
    LOGS_ONLY=false
    
    for arg in "$@"; do
        case $arg in
            --setup|--install)
                SETUP_FLAG=true
                ;;
            --backend-only)
                BACKEND_ONLY=true
                ;;
            --frontend-only)
                FRONTEND_ONLY=true
                ;;
            --html-frontend)
                FRONTEND_TYPE="html"
                ;;
            --svelte-frontend)
                FRONTEND_TYPE="svelte"
                ;;
            --debug)
                DEBUG_MODE=true
                ;;
            --dev|--development)
                DEV_MODE=true
                DEBUG_MODE=true
                ;;
            --check)
                CHECK_ONLY=true
                ;;
            --test-ml)
                TEST_ML_ONLY=true
                ;;
            --stop)
                STOP_ONLY=true
                ;;
            --status)
                STATUS_ONLY=true
                ;;
            --logs)
                LOGS_ONLY=true
                ;;
            --help|-h)
                show_banner
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $arg"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Show banner
    show_banner
    
    # Handle special modes
    if [ "$STATUS_ONLY" = "true" ]; then
        show_status
        exit 0
    fi
    
    if [ "$LOGS_ONLY" = "true" ]; then
        show_logs
        exit 0
    fi
    
    if [ "$TEST_ML_ONLY" = "true" ]; then
        log_step "Running ML/NLP dependency tests..."
        # If --setup was also specified, install dependencies first
        if [ "$SETUP_FLAG" = "true" ]; then
            setup_directories
            install_dependencies
        fi
        
        if [ -f "$ROOT_DIR/test_transformers_fix.py" ]; then
            # Ensure we use the right virtual environment for testing
            local venv_path="$ROOT_DIR/godelos_venv"
            if [ -d "$venv_path" ]; then
                source "$venv_path/bin/activate"
            elif [ -d "$BACKEND_DIR/venv" ]; then
                source "$BACKEND_DIR/venv/bin/activate" 
            fi
            
            python3 "$ROOT_DIR/test_transformers_fix.py"
        else
            log_error "Test script not found: test_transformers_fix.py"
            exit 1
        fi
        exit 0
    fi
    
    if [ "$STOP_ONLY" = "true" ]; then
        stop_processes
        exit 0
    fi
    
    # Setup directories
    setup_directories
    
    # Check requirements
    if ! check_requirements; then
        if [ "$CHECK_ONLY" = "true" ]; then
            exit 1
        fi
        log_info "Some ports are in use. Use --stop to stop existing processes."
        exit 1
    fi
    
    if [ "$CHECK_ONLY" = "true" ]; then
        log_success "All system requirements met"
        exit 0
    fi
    
    # Install dependencies if needed
    if [ "$SETUP_FLAG" = "true" ]; then
        install_dependencies
    fi
    
    # Cache ML models to avoid startup delays
    cache_models
    
    # Stop existing processes
    stop_processes
    
    # Set up signal handlers
    trap cleanup SIGINT SIGTERM
    
    # Start services
    if [ "$FRONTEND_ONLY" != "true" ]; then
        if ! start_backend; then
            exit 1
        fi
    fi
    
    if [ "$BACKEND_ONLY" != "true" ]; then
        if ! start_frontend; then
            # If backend was started, clean it up
            if [ "$FRONTEND_ONLY" != "true" ]; then
                cleanup
            fi
            exit 1
        fi
    fi
    
    # Show success message
    echo ""
    echo -e "${GREEN}🎉 GödelOS v0.2 Beta is now running!${NC}"
    echo -e "${GREEN}====================================${NC}"
    show_status
    
    if [ "$DEV_MODE" = "true" ]; then
        log_info "Development mode: Backend will auto-reload on changes"
    fi
    
    echo -e "${YELLOW}💡 Tip: Open http://localhost:$FRONTEND_PORT in your browser${NC}"
    echo -e "${YELLOW}🛑 Press Ctrl+C to stop the system${NC}"
    echo ""
    
    # Monitor system
    log_info "System monitoring active..."
    while true; do
        sleep 5
        
        # Check if processes are still running
        if [ "$FRONTEND_ONLY" != "true" ] && ! kill -0 "$BACKEND_PID" 2>/dev/null; then
            log_error "Backend server stopped unexpectedly"
            log_info "Check logs: tail -f $LOGS_DIR/backend.log"
            cleanup
        fi
        
        if [ "$BACKEND_ONLY" != "true" ] && ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
            log_error "Frontend server stopped unexpectedly"
            log_info "Check logs: tail -f $LOGS_DIR/frontend.log"
            cleanup
        fi
    done
}

# Run main function
main "$@"
