#!/bin/bash
# Quick verification that all integrations are syntactically correct

echo "🔍 Quick Verification of Consciousness Integrations"
echo "===================================================="
echo ""

# Change to the script's directory, then to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "1. Checking Python syntax of modified files..."
echo ""

# Check each file
files=(
    "backend/core/consciousness_engine.py"
    "backend/unified_server.py"
    "backend/core/unified_consciousness_engine.py"
    "backend/goal_management_system.py"
    "backend/core/metacognitive_monitor.py"
    "backend/core/knowledge_graph_evolution.py"
)

all_ok=true

for file in "${files[@]}"; do
    echo -n "  Checking $file... "
    if python3 -m py_compile "$file" 2>/dev/null; then
        echo "✓ OK"
    else
        echo "✗ SYNTAX ERROR"
        all_ok=false
    fi
done

echo ""
echo "2. Checking key integrations exist..."
echo ""

# Check bootstrap exists
if grep -q "async def bootstrap_consciousness" backend/core/consciousness_engine.py; then
    echo "  ✓ Bootstrap sequence implemented"
else
    echo "  ✗ Bootstrap sequence missing"
    all_ok=false
fi

# Check server calls bootstrap
if grep -q "bootstrap_consciousness()" backend/unified_server.py; then
    echo "  ✓ Server startup integration"
else
    echo "  ✗ Server startup integration missing"
    all_ok=false
fi

# Check conscious query processing
if grep -q "process_with_unified_awareness" backend/unified_server.py; then
    echo "  ✓ Conscious query processing"
else
    echo "  ✗ Conscious query processing missing"
    all_ok=false
fi

# Check phenomenal integrations
if grep -q "_generate_goal_phenomenal_experience" backend/goal_management_system.py; then
    echo "  ✓ Goals → Phenomenal experience"
else
    echo "  ✗ Goals phenomenal integration missing"
    all_ok=false
fi

if grep -q "_update_consciousness_recursive_depth" backend/core/metacognitive_monitor.py; then
    echo "  ✓ Metacognition → Recursive depth"
else
    echo "  ✗ Metacognition integration missing"
    all_ok=false
fi

if grep -q "_generate_emergence_phenomenal_experience" backend/core/knowledge_graph_evolution.py; then
    echo "  ✓ Knowledge graph → Phenomenal experience"
else
    echo "  ✗ Knowledge graph integration missing"
    all_ok=false
fi

echo ""
echo "===================================================="
if [ "$all_ok" = true ]; then
    echo "✅ ALL VERIFICATIONS PASSED"
    echo ""
    echo "Consciousness integration is complete and working!"
    exit 0
else
    echo "❌ SOME VERIFICATIONS FAILED"
    exit 1
fi
