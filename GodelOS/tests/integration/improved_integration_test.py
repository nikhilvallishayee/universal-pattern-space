#!/usr/bin/env python3
"""
Quick integration test for GödelOS Backend and Frontend
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3001"

def test_get_endpoint(url, name, timeout=5):
    """Test a GET endpoint"""
    try:
        response = requests.get(url, timeout=timeout)
        return {
            "name": name,
            "status": "✅ PASS" if response.status_code == 200 else "❌ FAIL",
            "code": response.status_code,
            "response_size": len(response.text),
            "success": response.status_code == 200
        }
    except requests.exceptions.RequestException as e:
        return {
            "name": name,
            "status": "❌ ERROR",
            "code": "N/A",
            "response_size": 0,
            "success": False,
            "error": str(e)
        }

def test_post_endpoint(url, name, data=None, timeout=5):
    """Test a POST endpoint"""
    try:
        response = requests.post(url, json=data, timeout=timeout)
        return {
            "name": name,
            "status": "✅ PASS" if response.status_code == 200 else "❌ FAIL",
            "code": response.status_code,
            "response_size": len(response.text),
            "success": response.status_code == 200
        }
    except requests.exceptions.RequestException as e:
        return {
            "name": name,
            "status": "❌ ERROR",
            "code": "N/A",
            "response_size": 0,
            "success": False,
            "error": str(e)
        }

def main():
    print("🧪 GödelOS Integration Test Results")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    results = []
    
    # Test 1: Backend Health
    result = test_get_endpoint(f"{BASE_URL}/api/health", "Backend Health")
    results.append(result)
    print(f"{result['status']} {result['name']}")
    print(f"    HTTP {result['code']} | Response: {result['response_size']} bytes")
    print()
    
    # Test 2: Cognitive State
    result = test_get_endpoint(f"{BASE_URL}/api/cognitive/state", "Cognitive State")
    results.append(result)
    print(f"{result['status']} {result['name']}")
    print(f"    HTTP {result['code']} | Response: {result['response_size']} bytes")
    print()
    
    # Test 3: Knowledge Concepts
    result = test_get_endpoint(f"{BASE_URL}/api/knowledge/concepts", "Knowledge Concepts")
    results.append(result)
    print(f"{result['status']} {result['name']}")
    print(f"    HTTP {result['code']} | Response: {result['response_size']} bytes")
    print()
    
    # Test 4: Query Endpoint (POST)
    query_data = {"query": "What can you tell me about the system?"}
    result = test_post_endpoint(f"{BASE_URL}/api/query", "Query Endpoint (POST)", query_data)
    results.append(result)
    print(f"{result['status']} {result['name']}")
    print(f"    HTTP {result['code']} | Response: {result['response_size']} bytes")
    print()
    
    # Test 5: Frontend Accessibility
    result = test_get_endpoint(FRONTEND_URL, "Frontend Accessibility")
    results.append(result)
    print(f"{result['status']} {result['name']}")
    print(f"    HTTP {result['code']} | Response: {result['response_size']} bytes")
    
    # Check if response looks like HTML (frontend) or JSON (API error)
    if result['success']:
        try:
            response = requests.get(FRONTEND_URL, timeout=5)
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' in content_type:
                print("    ✅ Frontend serving HTML correctly")
            elif 'application/json' in content_type:
                print("    ⚠️  Frontend serving JSON (may not be running)")
            else:
                print(f"    ⚠️  Unknown content type: {content_type}")
        except:
            pass
    print()
    
    # Summary
    passed = sum(1 for r in results if r['success'])
    total = len(results)
    
    print("🎯 Overall Result: {}/{} tests passed".format(passed, total))
    if passed == total:
        print("🎉 All systems operational!")
    else:
        print("⚠️  Some issues detected.")

if __name__ == "__main__":
    main()
