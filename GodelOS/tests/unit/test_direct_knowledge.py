#!/usr/bin/env python3
"""
Direct Knowledge Store Test

This script will directly add knowledge to the knowledge management service
to bypass the import processing and test if the search functionality works.
"""

import asyncio
import sys
import os

# Add the project to the path
sys.path.insert(0, os.path.abspath('.'))

from backend.knowledge_models import ImportSource, KnowledgeItem
from backend.knowledge_management import knowledge_management_service

async def test_direct_knowledge_add():
    """Test adding knowledge directly to the knowledge management service."""
    
    print("🔍 Testing direct knowledge addition...")
    
    # Create a test knowledge item
    test_source = ImportSource(
        source_type="text",
        source_identifier="direct_test",
        metadata={"test": True}
    )
    
    test_knowledge = KnowledgeItem(
        id="direct_test_ai",
        content="Artificial Intelligence (AI) is the simulation of human intelligence in machines that are programmed to think and act like humans. It includes machine learning, natural language processing, computer vision, and robotics.",
        knowledge_type="fact",
        title="AI Direct Test",
        source=test_source,
        import_id="direct_test_001",
        confidence=0.95,
        quality_score=0.90,
        categories=["technology", "ai"],
        auto_categories=[],
        manual_categories=["technology"]
    )
    
    print(f"✅ Created knowledge item: {test_knowledge.title}")
    
    # Add it to the knowledge management service
    try:
        knowledge_management_service.add_item(test_knowledge)
        print(f"✅ Added knowledge item to management service")
        
        # Check the knowledge store size
        store_size = len(knowledge_management_service.search_engine.knowledge_store)
        print(f"📊 Knowledge store now has {store_size} items")
        
        # Test search
        from backend.knowledge_models import SearchQuery
        
        search_query = SearchQuery(
            query_text="artificial intelligence",
            search_type="full_text",
            max_results=5,
            include_snippets=True
        )
        
        print(f"🔍 Searching for: {search_query.query_text}")
        search_result = await knowledge_management_service.search_engine.search(search_query)
        
        print(f"📋 Search results:")
        print(f"   Total matches: {search_result.total_matches}")
        print(f"   Results returned: {len(search_result.results)}")
        
        for i, result in enumerate(search_result.results):
            print(f"   {i+1}. {result.knowledge_item.title} (score: {result.relevance_score})")
            print(f"      Content: {result.knowledge_item.content[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_direct_knowledge_add())
    if result:
        print("\n🎉 Direct knowledge addition test PASSED!")
    else:
        print("\n❌ Direct knowledge addition test FAILED!")
