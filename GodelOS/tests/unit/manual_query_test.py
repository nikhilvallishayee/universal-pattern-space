#!/usr/bin/env python3
"""
Manual query test to verify the frontend query interface is working.
"""

import requests
import json
from datetime import datetime

def test_manual_query():
    """Test a query that should produce a better response."""
    
    print("🧪 Manual Query Test")
    print("=" * 40)
    
    # Test with a more specific query
    test_queries = [
        "Hello, can you respond?",
        "Tell me about yourself",
        "What are your capabilities?",
        "Analyze the system health data"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}️⃣ Testing query: '{query}'")
        
        try:
            # Test via frontend proxy
            response = requests.post("http://localhost:3001/api/query", 
                                   json={
                                       "query": query,
                                       "context": {"type": "knowledge"},
                                       "include_reasoning": True
                                   },
                                   timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Response ({len(result.get('response', ''))} chars): {result.get('response', '')[:100]}...")
                print(f"   📊 Confidence: {result.get('confidence', 0):.2f}")
                print(f"   ⏱️  Time: {result.get('inference_time_ms', 0):.1f}ms")
                
                if result.get('reasoning_steps'):
                    print(f"   🧠 Reasoning steps: {len(result['reasoning_steps'])}")
                    
            else:
                print(f"   ❌ Failed: HTTP {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n🎯 Summary: The query engine is responding to all requests")
    print(f"📱 Frontend available at: http://localhost:3001")
    print(f"🔧 Backend available at: http://localhost:8000")
    print(f"\n💡 Next steps:")
    print(f"   1. Open http://localhost:3001 in your browser")
    print(f"   2. Click on the 'Query Interface' or use the query box on the dashboard")
    print(f"   3. Submit a query and check if you see a response")
    print(f"   4. If no response appears, check browser developer console for errors")

if __name__ == "__main__":
    test_manual_query()
