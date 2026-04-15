#!/usr/bin/env python3
"""
Quick Frontend Integration Test
Tests the Svelte frontend integration with the backend
"""

import requests
import time
import json

def test_backend_health():
    """Test if backend is responding"""
    try:
        response = requests.get('http://localhost:8000/api/health', timeout=5)
        if response.status_code == 200:
            print("✅ Backend health check passed")
            return True
    except Exception as e:
        print(f"❌ Backend health check failed: {e}")
    return False

def test_frontend_accessibility():
    """Test if frontend is accessible"""
    try:
        response = requests.get('http://localhost:3001', timeout=5)
        if response.status_code == 200:
            print("✅ Frontend is accessible")
            return True
    except Exception as e:
        print(f"❌ Frontend accessibility test failed: {e}")
    return False

def test_api_endpoints():
    """Test key API endpoints"""
    endpoints = [
        '/api/health',
        '/api/knowledge/graph',
        '/api/knowledge/concepts',
        '/api/cognitive/state'
    ]
    
    results = {}
    for endpoint in endpoints:
        try:
            response = requests.get(f'http://localhost:8000{endpoint}', timeout=5)
            results[endpoint] = response.status_code == 200
            status = "✅" if results[endpoint] else "❌"
            print(f"{status} {endpoint}: {response.status_code}")
        except Exception as e:
            results[endpoint] = False
            print(f"❌ {endpoint}: {e}")
    
    return results

def main():
    print("🧪 Running Quick Frontend Integration Test")
    print("=" * 50)
    
    # Test backend
    backend_ok = test_backend_health()
    
    # Test frontend
    frontend_ok = test_frontend_accessibility()
    
    # Test API endpoints
    if backend_ok:
        api_results = test_api_endpoints()
        api_ok = any(api_results.values())
    else:
        api_ok = False
        print("⚠️ Skipping API tests - backend not available")
    
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"Backend: {'✅ OK' if backend_ok else '❌ FAIL'}")
    print(f"Frontend: {'✅ OK' if frontend_ok else '❌ FAIL'}")
    print(f"API Endpoints: {'✅ OK' if api_ok else '❌ FAIL'}")
    
    if backend_ok and frontend_ok:
        print("\n🎉 System is ready! Visit http://localhost:3001")
    else:
        print("\n⚠️ Some components are not running. Check the logs.")

if __name__ == '__main__':
    main()
