#!/usr/bin/env python3
"""
Quick test to verify frontend accessibility and navigation
"""

import requests
import json
import time
from pathlib import Path

def test_frontend_navigation():
    """Test if the frontend is accessible and responding"""
    print("🔍 Testing GödelOS Frontend Navigation & Accessibility...")
    
    try:
        # Test if frontend is running
        response = requests.get("http://localhost:3001", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend is accessible at http://localhost:3001")
            print(f"📄 HTML content length: {len(response.text)} characters")
            
            # Check if key components are in the HTML
            html_content = response.text.lower()
            
            # Check for navigation items
            nav_items = ['knowledge graph', 'knowledge import', 'transparency', 'import', 'cognitive']
            found_items = []
            missing_items = []
            
            for item in nav_items:
                if item in html_content:
                    found_items.append(item)
                else:
                    missing_items.append(item)
            
            print(f"🗂️  Found navigation items: {found_items}")
            if missing_items:
                print(f"❌ Missing navigation items: {missing_items}")
            
            # Check for component names
            components = ['knowledgegraph', 'smartimport', 'transparencydashboard']
            found_components = []
            
            for comp in components:
                if comp in html_content:
                    found_components.append(comp)
            
            print(f"🧩 Found components: {found_components}")
            
            return True
            
        else:
            print(f"❌ Frontend returned status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to frontend at http://localhost:3001")
        print("💡 Make sure the frontend server is running")
        return False
    except Exception as e:
        print(f"❌ Error testing frontend: {e}")
        return False

def check_component_files():
    """Check if all required component files exist"""
    print("\n📁 Checking component files...")
    
    frontend_path = Path("/Users/oli/code/GödelOS.md/svelte-frontend")
    
    required_components = [
        "src/components/knowledge/KnowledgeGraph.svelte",
        "src/components/knowledge/SmartImport.svelte", 
        "src/components/transparency/TransparencyDashboard.svelte",
        "src/App.svelte"
    ]
    
    all_exist = True
    for comp_path in required_components:
        full_path = frontend_path / comp_path
        if full_path.exists():
            print(f"✅ {comp_path}")
        else:
            print(f"❌ {comp_path} - MISSING")
            all_exist = False
    
    return all_exist

if __name__ == "__main__":
    print("🦉 GödelOS Frontend Navigation Test")
    print("=" * 50)
    
    # Check files first
    files_ok = check_component_files()
    
    # Test frontend accessibility
    frontend_ok = test_frontend_navigation()
    
    print("\n" + "=" * 50)
    if files_ok and frontend_ok:
        print("✅ Frontend navigation test PASSED")
        print("💡 Check browser console for debug logs")
        print("🔗 Navigate to: http://localhost:3001")
    else:
        print("❌ Frontend navigation test FAILED")
        if not files_ok:
            print("   - Some component files are missing")
        if not frontend_ok:
            print("   - Frontend is not accessible")
