#!/usr/bin/env python3
"""
Test script for knowledge ingestion API endpoints
"""

import asyncio
import aiohttp
import json

async def test_endpoints():
    """Test the knowledge ingestion endpoints."""
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        print("🧪 Testing Knowledge Ingestion API Endpoints")
        print("=" * 50)
        
        # Test 1: Text Import
        print("\n1. Testing Text Import...")
        text_data = {
            "source": {
                "source_type": "text",
                "source_identifier": "Test Text",
                "metadata": {"source": "test_script"}
            },
            "content": "This is a test knowledge item for the GödelOS system.",
            "title": "Test Knowledge Item",
            "format_type": "plain",
            "categorization_hints": ["test", "api"]
        }
        
        try:
            async with session.post(f"{base_url}/api/knowledge/import/text", 
                                  json=text_data) as response:
                result = await response.json()
                if response.status == 200:
                    print(f"✅ Text import successful: {result}")
                else:
                    print(f"❌ Text import failed: {response.status} - {result}")
        except Exception as e:
            print(f"❌ Text import error: {e}")
        
        # Test 2: Wikipedia Import
        print("\n2. Testing Wikipedia Import...")
        wiki_data = {
            "source": {
                "source_type": "wikipedia",
                "source_identifier": "Artificial Intelligence",
                "metadata": {"source": "test_script"}
            },
            "page_title": "Artificial Intelligence",
            "language": "en",
            "include_references": True,
            "section_filter": []
        }
        
        try:
            async with session.post(f"{base_url}/api/knowledge/import/wikipedia", 
                                  json=wiki_data) as response:
                result = await response.json()
                if response.status == 200:
                    print(f"✅ Wikipedia import successful: {result}")
                else:
                    print(f"❌ Wikipedia import failed: {response.status} - {result}")
        except Exception as e:
            print(f"❌ Wikipedia import error: {e}")
        
        # Test 3: URL Import
        print("\n3. Testing URL Import...")
        url_data = {
            "source": {
                "source_type": "url",
                "source_identifier": "https://example.com",
                "metadata": {"source": "test_script"}
            },
            "url": "https://example.com",
            "max_depth": 1,
            "follow_links": False,
            "content_selectors": [],
            "categorization_hints": ["web", "test"]
        }
        
        try:
            async with session.post(f"{base_url}/api/knowledge/import/url", 
                                  json=url_data) as response:
                result = await response.json()
                if response.status == 200:
                    print(f"✅ URL import successful: {result}")
                else:
                    print(f"❌ URL import failed: {response.status} - {result}")
        except Exception as e:
            print(f"❌ URL import error: {e}")
        
        # Test 4: File Upload (create a test file)
        print("\n4. Testing File Upload...")
        test_content = "This is test file content for knowledge ingestion."
        
        # Create form data for file upload
        data = aiohttp.FormData()
        data.add_field('file', test_content, filename='test.txt', content_type='text/plain')
        data.add_field('filename', 'test.txt')
        data.add_field('file_type', 'text/plain')
        data.add_field('encoding', 'utf-8')
        data.add_field('categorization_hints', json.dumps(['test', 'file']))
        
        try:
            async with session.post(f"{base_url}/api/knowledge/import/file", 
                                  data=data) as response:
                result = await response.json()
                if response.status == 200:
                    print(f"✅ File upload successful: {result}")
                else:
                    print(f"❌ File upload failed: {response.status} - {result}")
        except Exception as e:
            print(f"❌ File upload error: {e}")
        
        print("\n" + "=" * 50)
        print("🏁 Testing completed!")

if __name__ == "__main__":
    asyncio.run(test_endpoints())