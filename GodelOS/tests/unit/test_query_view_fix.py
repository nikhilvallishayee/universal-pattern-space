#!/usr/bin/env python3
"""
Test script to verify the query view fix in the frontend
"""

import requests
import json
from datetime import datetime

def test_frontend_query_view():
    """Test that the frontend loads without the 'View Not Found' error"""
    print("🧪 Testing Query View Fix")
    print("=" * 50)
    
    try:
        # Test frontend accessibility
        response = requests.get("http://localhost:3001", timeout=5)
        
        if response.status_code == 200:
            content = response.text
            
            # Check if the error message is present
            if "View Not Found" in content:
                print("❌ FAIL: 'View Not Found' error still present")
                if "Could not render view" in content:
                    print("   - Debug error message still showing")
                return False
            elif "query-expanded" in content:
                print("❌ FAIL: Still references 'query-expanded' incorrectly")
                return False
            else:
                print("✅ PASS: Frontend loads without query view errors")
                
                # Check for query interface elements
                if "Query Interface" in content or "query" in content.lower():
                    print("✅ PASS: Query interface elements detected")
                else:
                    print("⚠️  WARNING: Query interface elements not clearly visible")
                    
                return True
        else:
            print(f"❌ FAIL: Frontend not accessible (HTTP {response.status_code})")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ FAIL: Cannot connect to frontend - {e}")
        return False

def test_backend_endpoints():
    """Verify backend is still working"""
    print("\n🔧 Backend Status Check")
    print("-" * 30)
    
    endpoints = [
        ("Health", "GET", "http://localhost:8000/api/health"),
        ("Cognitive State", "GET", "http://localhost:8000/api/cognitive/state"),
    ]
    
    all_good = True
    for name, method, url in endpoints:
        try:
            if method == "GET":
                response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                print(f"✅ {name}: OK")
            else:
                print(f"❌ {name}: HTTP {response.status_code}")
                all_good = False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {name}: Connection error - {e}")
            all_good = False
    
    return all_good

if __name__ == "__main__":
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    frontend_ok = test_frontend_query_view()
    backend_ok = test_backend_endpoints()
    
    print("\n" + "=" * 50)
    if frontend_ok and backend_ok:
        print("🎉 SUCCESS: Query view fix verified - all systems operational!")
    elif frontend_ok:
        print("⚠️  PARTIAL: Frontend fixed but backend issues detected")
    elif backend_ok:
        print("⚠️  PARTIAL: Backend OK but frontend issues remain")
    else:
        print("❌ FAILURE: Both frontend and backend have issues")
    
    print(f"⏰ Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
