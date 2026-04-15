#!/usr/bin/env python3
"""
Simple Knowledge Integration Test

This script directly tests the knowledge import and retrieval to understand
how to connect the imported knowledge to the query system.
"""

import asyncio
import aiohttp
import json
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000/api"

async def test_knowledge_integration():
    """Test the knowledge integration and query processing."""
    
    async with aiohttp.ClientSession() as session:
        
        print("🔍 Testing Knowledge Import and Query Integration")
        print("=" * 60)
        
        # 1. Import some simple knowledge
        print("\n📚 Importing test knowledge...")
        
        test_knowledge = [
            {
                "content": "Dogs are mammals. They have four legs and bark. Dogs are loyal companions to humans.",
                "title": "Dogs Basic Facts",
                "category": "animals"
            },
            {
                "content": "Cats are mammals. They have four legs and meow. Cats are independent animals that like to hunt mice.",
                "title": "Cats Basic Facts", 
                "category": "animals"
            },
            {
                "content": "Python is a programming language. It is easy to learn and widely used for web development, data science, and artificial intelligence.",
                "title": "Python Programming",
                "category": "technology"
            }
        ]
        
        import_ids = []
        for knowledge in test_knowledge:
            try:
                url = f"{BASE_URL}/knowledge/import/text"
                async with session.post(url, json=knowledge) as response:
                    if response.status == 200:
                        result = await response.json()
                        import_ids.append(result.get('import_id'))
                        logger.info(f"✅ Imported: {knowledge['title']} - ID: {result.get('import_id')}")
                    else:
                        logger.error(f"❌ Import failed: {response.status}")
            except Exception as e:
                logger.error(f"❌ Exception: {e}")
        
        print(f"\n✅ Imported {len(import_ids)} knowledge items")
        
        # 2. Wait a moment for processing
        print("\n⏳ Waiting for knowledge processing...")
        await asyncio.sleep(3)
        
        # 3. Test queries to see if knowledge is being used
        print("\n🧠 Testing queries...")
        
        test_queries = [
            "What is a dog?",
            "Tell me about cats",
            "What is Python?",
            "How many legs do dogs have?",
            "Do cats bark?",
            "What is Python used for?"
        ]
        
        for query in test_queries:
            try:
                url = f"{BASE_URL}/query"
                payload = {
                    "query": query,
                    "include_reasoning": True,
                    "max_response_length": 200
                }
                
                print(f"\n📋 Query: {query}")
                
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"📝 Response: {result.get('response', 'No response')}")
                        print(f"🎯 Confidence: {result.get('confidence', 0)}")
                        knowledge_used = result.get('knowledge_used', [])
                        print(f"📚 Knowledge used: {len(knowledge_used)} items")
                        if knowledge_used:
                            for i, knowledge in enumerate(knowledge_used[:2]):  # Show first 2
                                print(f"   {i+1}. {knowledge}")
                    else:
                        error_text = await response.text()
                        print(f"❌ Query failed: {response.status} - {error_text}")
                
                await asyncio.sleep(1)  # Small delay between queries
                
            except Exception as e:
                print(f"❌ Exception during query: {e}")
        
        # 4. Test the knowledge search API if it exists
        print("\n🔍 Testing knowledge search...")
        try:
            url = f"{BASE_URL}/knowledge/search"
            payload = {
                "query_text": "dog",
                "max_results": 5
            }
            
            async with session.get(url, params=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Knowledge search works - found {len(result.get('results', []))} results")
                    for i, item in enumerate(result.get('results', [])[:2]):
                        print(f"   {i+1}. {item.get('title', 'Untitled')}")
                else:
                    print(f"❌ Knowledge search failed: {response.status}")
        except Exception as e:
            print(f"❌ Knowledge search exception: {e}")
        
        print("\n🎉 Knowledge integration test complete!")

if __name__ == "__main__":
    asyncio.run(test_knowledge_integration())
