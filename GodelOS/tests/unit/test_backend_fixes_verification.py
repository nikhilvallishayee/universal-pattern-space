#!/usr/bin/env python3
"""
Test the Backend API Fixes
Quick verification that our fixes resolve the 422 validation errors
"""

import requests
import json
import time

def test_fixed_endpoints():
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Backend API Fixes")
    print("=" * 50)
    
    tests = [
        {
            "name": "Knowledge POST (Simple Format)",
            "method": "POST",
            "endpoint": "/api/knowledge",
            "payload": {"concept": "test_concept", "definition": "test definition", "category": "test"}
        },
        {
            "name": "Knowledge POST (Standard Format)", 
            "method": "POST",
            "endpoint": "/api/knowledge",
            "payload": {"content": "Test knowledge content", "knowledge_type": "concept", "category": "test"}
        },
        {
            "name": "Knowledge Search",
            "method": "GET", 
            "endpoint": "/api/knowledge/search",
            "params": {"query": "test search", "category": "general", "limit": 5}
        },
        {
            "name": "Knowledge Item Details",
            "method": "GET",
            "endpoint": "/api/knowledge/test_item",
            "params": {}
        },
        {
            "name": "URL Import (Simple Format)",
            "method": "POST",
            "endpoint": "/api/knowledge/import/url", 
            "payload": {"url": "https://example.com", "category": "web"}
        },
        {
            "name": "Wikipedia Import",
            "method": "POST",
            "endpoint": "/api/knowledge/import/wikipedia",
            "payload": {"topic": "artificial intelligence", "category": "encyclopedia"}
        },
        {
            "name": "Text Import",
            "method": "POST", 
            "endpoint": "/api/knowledge/import/text",
            "payload": {"content": "Sample text content", "title": "Test Document", "category": "document"}
        },
        {
            "name": "Batch Import",
            "method": "POST",
            "endpoint": "/api/knowledge/import/batch",
            "payload": {"sources": [{"type": "text", "content": "Test content"}]}
        },
        {
            "name": "Import Progress",
            "method": "GET",
            "endpoint": "/api/knowledge/import/progress/test_import_123",
            "params": {}
        },
        {
            "name": "Cancel Import", 
            "method": "DELETE",
            "endpoint": "/api/knowledge/import/test_import_123",
            "params": {}
        }
    ]
    
    results = []
    
    for test in tests:
        print(f"\n🔍 Testing {test['name']}...")
        
        try:
            url = f"{base_url}{test['endpoint']}"
            
            if test['method'] == 'GET':
                response = requests.get(url, params=test.get('params', {}), timeout=5)
            elif test['method'] == 'POST':
                response = requests.post(url, json=test.get('payload', {}), timeout=5)
            elif test['method'] == 'DELETE':
                response = requests.delete(url, timeout=5)
            else:
                print(f"❌ Unsupported method: {test['method']}")
                continue
            
            success = (200 <= response.status_code < 300)
            status_icon = "✅" if success else "❌"
            
            print(f"{status_icon} {test['name']}: {response.status_code}")
            
            if success:
                try:
                    data = response.json()
                    if test['name'] == "Knowledge Search" and 'results' in data:
                        print(f"   📊 Found {len(data['results'])} results")
                    elif test['name'].endswith("Import") and 'import_id' in data:
                        print(f"   🔄 Import ID: {data['import_id']}")
                    elif 'status' in data:
                        print(f"   📌 Status: {data['status']}")
                except:
                    pass
            else:
                print(f"   ❌ Error: {response.text[:100]}...")
            
            results.append({
                'test': test['name'],
                'status_code': response.status_code,
                'success': success
            })
            
        except Exception as e:
            print(f"❌ {test['name']}: ERROR - {e}")
            results.append({
                'test': test['name'], 
                'status_code': 0,
                'success': False,
                'error': str(e)
            })
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r['success'])
    failed_tests = total_tests - successful_tests
    
    print(f"Total Tests: {total_tests}")
    print(f"Successful: {successful_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success Rate: {(successful_tests/total_tests)*100:.1f}%")
    
    if failed_tests > 0:
        print(f"\n❌ FAILED TESTS:")
        for result in results:
            if not result['success']:
                error_msg = result.get('error', f"Status {result['status_code']}")
                print(f"  - {result['test']}: {error_msg}")
    
    if successful_tests == total_tests:
        print(f"\n🎉 ALL TESTS PASSED! Backend fixes successful!")
    else:
        print(f"\n⚠️ {failed_tests} tests still failing. Check backend logs.")

def main():
    print("🚀 Backend API Fix Verification")
    print(f"⏰ Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # First check if backend is running
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running")
            test_fixed_endpoints()
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Backend not accessible: {e}")
        print("\n💡 Start the backend first:")
        print("   cd /Users/oli/code/GödelOS.md/backend")
        print("   python main.py")

if __name__ == "__main__":
    main()
