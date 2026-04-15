#!/usr/bin/env python3
"""
Quick Integration Test - GödelOS Backend/Frontend
Tests the key endpoints and verifies the system is working.
"""

import requests
import json
import sys
from datetime import datetime

def test_endpoint(url, name):
    """Test a single endpoint and return results."""
    try:
        response = requests.get(url, timeout=10)
        success = response.status_code == 200
        
        if success:
            try:
                data = response.json()
                return {
                    "name": name,
                    "status": "✅ PASS",
                    "code": response.status_code,
                    "response_size": len(json.dumps(data)),
                    "has_data": bool(data)
                }
            except:
                return {
                    "name": name,
                    "status": "⚠️  JSON_ERROR",
                    "code": response.status_code,
                    "response_size": len(response.text),
                    "has_data": False
                }
        else:
            return {
                "name": name,
                "status": "❌ FAIL",
                "code": response.status_code,
                "response_size": len(response.text),
                "has_data": False
            }
            
    except requests.exceptions.RequestException as e:
        return {
            "name": name,
            "status": "❌ ERROR",
            "code": "N/A",
            "response_size": 0,
            "has_data": False,
            "error": str(e)
        }

def main():
    # Test endpoints silently first
    endpoints = [
        ("http://localhost:8000/api/health", "Backend Health"),
        ("http://localhost:8000/api/cognitive/state", "Cognitive State"),
        ("http://localhost:8000/api/knowledge/concepts", "Knowledge Concepts"),
        ("http://localhost:8000/api/query", "Query Endpoint (GET)"),
        ("http://localhost:3001", "Frontend Accessibility"),
    ]
    
    results = []
    for url, name in endpoints:
        result = test_endpoint(url, name)
        results.append(result)
    
    # Now show results
    print("🧪 GödelOS Integration Test Results")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    for result in results:
        status = result["status"]
        name = result["name"]
        code = result["code"]
        size = result["response_size"]
        
        print(f"{status} {name}")
        print(f"    HTTP {code} | Response: {size} bytes")
        
        if "error" in result:
            print(f"    Error: {result['error']}")
        print()
    
    # Summary
    passed = sum(1 for r in results if "PASS" in r["status"])
    total = len(results)
    
    print(f"🎯 Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All systems operational!")
        return 0
    else:
        print("⚠️  Some issues detected.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
