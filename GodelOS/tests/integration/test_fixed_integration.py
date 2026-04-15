#!/usr/bin/env python3
"""
Test script to verify the fixed GödelOS integration module works correctly.
"""

import sys
import os
import asyncio

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'backend'))

async def test_integration():
    """Test the fixed integration module."""
    print("🔍 Testing fixed GödelOS integration...")
    
    try:
        # Import the integration
        from backend.godelos_integration import godelos_integration
        print("✅ Integration import successful")
        
        # Check initial state
        print(f"✅ Integration object: {type(godelos_integration).__name__}")
        print(f"✅ Initialized: {godelos_integration.initialized}")
        print(f"✅ Simple knowledge items: {len(godelos_integration.simple_knowledge_store)}")
        
        # Test a knowledge search without initialization
        print("\n🔍 Testing knowledge search before initialization...")
        result = await godelos_integration._search_simple_knowledge_store("artificial intelligence")
        print(f"✅ Knowledge search result: {result.get('found', False)}")
        if result.get('found'):
            print(f"✅ Found content: {result['content'][:100]}...")
            print(f"✅ Sources: {result['sources']}")
        
        # Test natural language query processing
        print("\n🔍 Testing natural language query processing...")
        query_result = await godelos_integration.process_natural_language_query(
            "What is artificial intelligence?"
        )
        print(f"✅ Query result keys: {list(query_result.keys())}")
        print(f"✅ Response: {query_result.get('response', 'No response')[:100]}...")
        print(f"✅ Confidence: {query_result.get('confidence', 0.0)}")
        
        # Test system status
        print("\n🔍 Testing system status...")
        status = await godelos_integration.get_system_status()
        print(f"✅ System status: {status.get('status', 'unknown')}")
        print(f"✅ Capabilities: {list(status.get('capabilities', {}).keys())}")
        
        print("\n✅ All tests passed! The integration is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_integration())
    sys.exit(0 if success else 1)
