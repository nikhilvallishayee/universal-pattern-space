#!/bin/bash

# GödelOS Demo Setup Script
# Quickly sets up demonstration data for showcasing system capabilities

echo "🧠 GödelOS Demo Setup"
echo "======================"

# Check if demo data exists
if [ ! -d "demo-data" ]; then
    echo "❌ Demo data directory not found. Please run from GödelOS root directory."
    exit 1
fi

echo "📁 Demo data available:"
echo "  • GödelOS Research Paper (godelos_arxiv_paper_v2.pdf)"
echo "  • AI Overview Document (ai_overview.md)"  
echo "  • Quantum Computing Guide (quantum_computing.md)"
echo ""

# Check if system is running
if curl -s http://localhost:8000/health >/dev/null 2>&1; then
    echo "✅ GödelOS backend is running on port 8000"
else
    echo "⚠️  GödelOS backend not detected. Start with: ./start-godelos.sh"
fi

if curl -s http://localhost:3001 >/dev/null 2>&1; then
    echo "✅ Frontend is running on port 3001"
else
    echo "⚠️  Frontend not detected. It should start automatically with backend."
fi

echo ""
echo "🚀 Demo Instructions:"
echo "1. Open http://localhost:3001 in your browser"
echo "2. Navigate to Document Upload section"
echo "3. Upload demo-data/documents/godelos_arxiv_paper_v2.pdf"
echo "4. Watch the knowledge graph generate in real-time"
echo "5. Explore cognitive transparency features"
echo ""
echo "📖 For more details, see demo-data/README.md"
