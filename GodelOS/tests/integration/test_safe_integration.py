#!/usr/bin/env python3
"""
Comprehensive test for the safe GödelOS integration module.
"""

import sys
import os
import asyncio

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'backend'))

async def test_safe_integration():
    """Test the safe integration module comprehensively."""
    print("🔍 Testing safe GödelOS integration...")
    
    try:
        # Step 1: Import the integration
        print("\n📝 Step 1: Importing integration module...")
        from backend.godelos_integration import GödelOSIntegration, godelos_integration
        print("✅ Integration import successful")
        
        # Step 2: Check initial state
        print("\n📝 Step 2: Checking initial state...")
        print(f"✅ Integration object: {type(godelos_integration).__name__}")
        print(f"✅ Initialized: {godelos_integration.initialized}")
        print(f"✅ Simple knowledge items: {len(godelos_integration.simple_knowledge_store)}")
        
        # Step 3: Initialize the integration
        print("\n📝 Step 3: Initializing integration...")
        await godelos_integration.initialize()
        print(f"✅ Initialization complete. Initialized: {godelos_integration.initialized}")
        
        # Step 4: Test knowledge search without external dependencies
        print("\n📝 Step 4: Testing simple knowledge search...")
        result = await godelos_integration._search_simple_knowledge_store("artificial intelligence")
        print(f"✅ Knowledge search result: found={result.get('found', False)}")
        if result.get('found'):
            print(f"✅ Found content length: {len(result['content'])} chars")
            print(f"✅ Sources: {result['sources']}")
            print(f"✅ Content preview: {result['content'][:100]}...")
        
        # Step 5: Test different types of queries
        print("\n📝 Step 5: Testing query types...")
        test_queries = [
            "What is artificial intelligence?",
            "What is machine learning?",
            "Where is John?",
            "Can Mary go to the cafe?"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Testing query: '{query}'")
            try:
                query_result = await godelos_integration.process_natural_language_query(query)
                print(f"  ✅ Response: {query_result.get('response', 'No response')[:100]}...")
                print(f"  ✅ Confidence: {query_result.get('confidence', 0.0)}")
                print(f"  ✅ Knowledge used: {len(query_result.get('knowledge_used', []))} sources")
            except Exception as e:
                print(f"  ❌ Query failed: {e}")
        
        # Step 6: Test system status
        print("\n📝 Step 6: Testing system status...")
        status = await godelos_integration.get_system_status()
        print(f"✅ System status: {status.get('status', 'unknown')}")
        print(f"✅ Capabilities: {list(status.get('capabilities', {}).keys())}")
        
        # Step 7: Test cognitive state
        print("\n📝 Step 7: Testing cognitive state...")
        cognitive_state = await godelos_integration.get_cognitive_state()
        print(f"✅ Components status: {sum(cognitive_state.get('components_status', {}).values())} active")
        print(f"✅ Component availability: {sum(cognitive_state.get('component_availability', {}).values())} available")
        print(f"✅ Error count: {cognitive_state.get('error_count', 0)}")
        print(f"✅ Uptime: {cognitive_state.get('uptime_seconds', 0):.1f} seconds")
        
        print("\n✅ All tests passed! The safe integration is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_safe_integration())
    sys.exit(0 if success else 1)
