#!/usr/bin/env python3
"""
Quick test to check navigation configuration
"""

import requests
import json

def test_navigation_config():
    """Test navigation configuration by checking rendered HTML"""
    print("🔍 Testing Navigation Configuration...")
    
    try:
        # Get the main page
        response = requests.get("http://localhost:3001", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend accessible")
            
            # Check for JavaScript files
            js_response = requests.get("http://localhost:3001/src/main.js", timeout=3)
            if js_response.status_code == 200:
                print("✅ Main.js accessible")
                print(f"📄 Content preview: {js_response.text[:200]}...")
            
            # Test if we can get component information
            app_response = requests.get("http://localhost:3001/src/App.svelte", timeout=3)
            if app_response.status_code == 200:
                print("✅ App.svelte accessible via dev server")
            else:
                print("⚠️ App.svelte not directly accessible (normal for production)")
                
        else:
            print(f"❌ Frontend error: {response.status_code}")
    
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_navigation_config()
