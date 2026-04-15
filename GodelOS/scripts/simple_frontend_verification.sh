#!/bin/bash

# GödelOS Navigation & Layout Verification Script
# Simple verification without browser automation

echo "🚀 GödelOS Frontend Verification Script"
echo "========================================"

# Check if the frontend server is running
echo "📡 Checking if frontend server is running on localhost:3001..."

if curl -s -f http://localhost:3001 > /dev/null; then
    echo "✅ Frontend server is running"
    
    # Get the HTML content
    echo "📄 Fetching page content..."
    HTML_CONTENT=$(curl -s http://localhost:3001)
    
    # Check for key elements in the HTML
    echo "🔍 Verifying key interface elements..."
    
    # Check for navigation items
    NAVIGATION_COUNT=$(echo "$HTML_CONTENT" | grep -o "nav-item" | wc -l)
    echo "   📊 Navigation items found: $NAVIGATION_COUNT"
    
    # Check for key CSS classes
    if echo "$HTML_CONTENT" | grep -q "godelos-interface"; then
        echo "   ✅ Main interface container: Present"
    else
        echo "   ❌ Main interface container: Missing"
    fi
    
    if echo "$HTML_CONTENT" | grep -q "sidebar"; then
        echo "   ✅ Sidebar navigation: Present"
    else
        echo "   ❌ Sidebar navigation: Missing"
    fi
    
    if echo "$HTML_CONTENT" | grep -q "main-content"; then
        echo "   ✅ Main content area: Present"
    else
        echo "   ❌ Main content area: Missing"
    fi
    
    if echo "$HTML_CONTENT" | grep -q "interface-header"; then
        echo "   ✅ Header section: Present"
    else
        echo "   ❌ Header section: Missing"
    fi
    
    # Check for view configuration (should have all 11 items)
    EXPECTED_VIEWS=(
        "Dashboard"
        "Cognitive State" 
        "Knowledge Graph"
        "Query Interface"
        "Knowledge Import"
        "Reflection"
        "Capabilities"
        "Resources"
        "Transparency" 
        "Reasoning Sessions"
        "Provenance"
    )
    
    echo "🧭 Checking for expected navigation views..."
    FOUND_VIEWS=0
    for view in "${EXPECTED_VIEWS[@]}"; do
        if echo "$HTML_CONTENT" | grep -q "$view"; then
            echo "   ✅ $view: Found"
            ((FOUND_VIEWS++))
        else
            echo "   ❌ $view: Missing"
        fi
    done
    
    echo ""
    echo "📊 Summary:"
    echo "   Views found: $FOUND_VIEWS/${#EXPECTED_VIEWS[@]}"
    echo "   Navigation elements: $NAVIGATION_COUNT"
    
    if [ $FOUND_VIEWS -eq ${#EXPECTED_VIEWS[@]} ]; then
        echo "   🎉 All expected views are present!"
        echo "   ✅ VERIFICATION: PASS"
    elif [ $FOUND_VIEWS -ge 8 ]; then
        echo "   ⚠️  Most views present (acceptable)"
        echo "   🟡 VERIFICATION: MOSTLY PASS"
    else
        echo "   ❌ Too many views missing"
        echo "   ❌ VERIFICATION: FAIL"
    fi
    
else
    echo "❌ Frontend server is not responding on localhost:3001"
    echo "   Please ensure the Svelte development server is running"
    echo "   Run: npm run dev (in the svelte-frontend directory)"
fi

echo ""
echo "🏁 Verification complete!"
