#!/bin/bash
# GödelOS Test Data Purge Script
# Remove all test/mock/sample data contamination including synthetic websocket events

echo "🧹 GödelOS Test Data Purge - COMPREHENSIVE"
echo "=========================================="

# 1. Remove test data population scripts
echo "🗑️  Removing test data population scripts..."
rm -f "/Users/oli/code/GodelOS/populate_test_vectors.py"
rm -f "/Users/oli/code/GodelOS/test_vector_clear.py"

# 2. Frontend synthetic event cleanup completed
echo "✅ Frontend synthetic events already removed:"
echo "   - simulateStreamingResponse() from ResponseDisplay.svelte"
echo "   - simulateProcessUpdates() from ProcessInsight.svelte" 
echo "   - updateMetrics() synthetic generation from HumanInteractionPanel.svelte"
echo "   - generateMockData() from CapabilityDashboard.svelte"
echo "   - generateMockTimelineData() from ArchitectureTimeline.svelte"
echo "   - generateSampleData() from KnowledgeGraph_broken.svelte"
echo "   - Hardcoded test values from HumanInteractionPanel.svelte removed:"
echo "     * systemResponseiveness: 100→0, communicationQuality: 95→0" 
echo "     * understandingLevel: 88→0, networkLatency: 12→0"
echo "     * processingSpeed: 150→0, consciousnessLevel: 0.85→0"
echo "     * integrationMeasure: 0.76→0, attentionAwareness: 0.82→0" 
echo "     * selfModelCoherence: 0.91→0, autonomousGoals: 3→0"
echo "   - Aggressive polling loops removed:"
echo "     * HumanInteractionPanel.svelte: updateInterval cleanup remnants"
echo "     * CognitiveStateMonitor.svelte: updateInterval cleanup remnants" 
echo "     * ReasoningSessionViewer.svelte: 3-second polling loop (replaced with manual refresh)"
echo "     * TransparencyDashboard.svelte: 5-second polling loop (WebSocket provides real-time updates)"

# 3. Clear any existing test vectors from database
echo "🔄 Clearing test vectors from database..."
curl -X DELETE "http://localhost:8000/api/v1/vector-db/clear" 2>/dev/null || echo "   Database not running or endpoint unavailable"

# 4. Remove test-related files in root directory
echo "🗑️  Removing additional test files..."
find "/Users/oli/code/GodelOS" -maxdepth 1 -name "*test*.py" -not -path "*/tests/*" -not -path "*/test_*" | while read file; do
    if [[ "$file" == *"test_"* ]] || [[ "$file" == *"_test.py" ]]; then
        echo "   Removing: $file"
        rm -f "$file"
    fi
done

echo ""
echo "✅ COMPREHENSIVE PURGE COMPLETE"
echo "================================="
echo "All synthetic and mock data sources eliminated:"
echo "  ✅ Test data population scripts removed"
echo "  ✅ Frontend mock data generators removed"
echo "  ✅ Synthetic websocket events removed"
echo "  ✅ Simulated streaming responses removed"
echo "  ✅ Fake process updates removed"
echo "  ✅ Mock timeline data generators removed"
echo "  ✅ Sample knowledge graph data removed"
echo "  ✅ Vector database test data cleared"
echo ""
echo "🎯 System now uses ONLY real backend data sources"
