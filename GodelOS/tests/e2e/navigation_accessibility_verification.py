#!/usr/bin/env python3
"""
GödelOS Navigation Accessibility Verification
Tests specific user concerns about knowledge import and transparency UI accessibility
"""

import requests
import json
import time
from pathlib import Path

def test_specific_navigation_concerns():
    """Test the specific issues mentioned by the user"""
    print("🎯 Testing Specific Navigation Accessibility Concerns")
    print("=" * 60)
    
    issues = {
        'knowledge_import_accessible': False,
        'transparency_ui_visible': False,
        'navigation_items_present': False,
        'components_loading': False
    }
    
    try:
        # Test 1: Check if frontend responds
        response = requests.get("http://localhost:3001", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend accessible at localhost:3001")
        else:
            print(f"❌ Frontend error: {response.status_code}")
            return issues
            
    except Exception as e:
        print(f"❌ Frontend not accessible: {e}")
        return issues
    
    # Test 2: Check backend endpoints for the specific features
    print("\n🔍 Testing Backend Endpoints for Key Features:")
    
    endpoints_to_test = {
        'transparency': '/api/transparency/statistics',
        'knowledge': '/api/knowledge/graph', 
        'import': '/api/import/status',
        'cognitive': '/api/cognitive/state'
    }
    
    working_endpoints = []
    
    for feature, endpoint in endpoints_to_test.items():
        try:
            response = requests.get(f"http://localhost:8000{endpoint}", timeout=3)
            if response.status_code in [200, 404]:  # 404 is OK for some endpoints
                status = "✅" if response.status_code == 200 else "⚠️"
                print(f"   {status} {feature}: {endpoint} ({response.status_code})")
                if response.status_code == 200:
                    working_endpoints.append(feature)
            else:
                print(f"   ❌ {feature}: {endpoint} ({response.status_code})")
        except Exception as e:
            print(f"   ❌ {feature}: {endpoint} (error: {str(e)[:30]})")
    
    issues['components_loading'] = len(working_endpoints) >= 2
    
    # Test 3: Check App.svelte navigation configuration
    print("\n🧭 Checking Navigation Configuration:")
    
    app_path = Path("/Users/oli/code/GödelOS.md/svelte-frontend/src/App.svelte")
    if app_path.exists():
        content = app_path.read_text()
        
        # Check for specific navigation items mentioned by user
        nav_checks = {
            'Knowledge Import': 'Knowledge Import' in content and 'import:' in content,
            'Transparency': 'Transparency' in content and 'transparency:' in content,
            'Knowledge Graph': 'Knowledge Graph' in content and 'knowledge:' in content,
            'SmartImport Component': 'SmartImport' in content,
            'TransparencyDashboard Component': 'TransparencyDashboard' in content
        }
        
        for item, found in nav_checks.items():
            status = "✅" if found else "❌"
            print(f"   {status} {item}")
        
        issues['knowledge_import_accessible'] = nav_checks['Knowledge Import'] and nav_checks['SmartImport Component']
        issues['transparency_ui_visible'] = nav_checks['Transparency'] and nav_checks['TransparencyDashboard Component']
        issues['navigation_items_present'] = sum(nav_checks.values()) >= 3
    
    # Test 4: Component file integrity
    print("\n📁 Checking Component Files:")
    
    critical_components = {
        'SmartImport': 'src/components/knowledge/SmartImport.svelte',
        'TransparencyDashboard': 'src/components/transparency/TransparencyDashboard.svelte',
        'KnowledgeGraph': 'src/components/knowledge/KnowledgeGraph.svelte'
    }
    
    frontend_path = Path("/Users/oli/code/GödelOS.md/svelte-frontend")
    
    for comp_name, comp_path in critical_components.items():
        full_path = frontend_path / comp_path
        if full_path.exists():
            size = full_path.stat().st_size
            print(f"   ✅ {comp_name}: {size} bytes")
        else:
            print(f"   ❌ {comp_name}: Missing")
    
    return issues

def provide_user_guidance(issues):
    """Provide specific guidance based on test results"""
    print("\n" + "=" * 60)
    print("🎯 USER GUIDANCE - Navigation Accessibility")
    print("=" * 60)
    
    if all(issues.values()):
        print("🎉 GOOD NEWS: All navigation components should be accessible!")
        print("\n📱 To access the features:")
        print("   1. Open http://localhost:3001 in your browser")
        print("   2. Look for the sidebar on the left with navigation icons")
        print("   3. Click on '📥 Knowledge Import' for import functionality")
        print("   4. Click on '🔍 Transparency' for transparency dashboard")
        print("   5. If sidebar is collapsed, click the ▶️ button to expand")
        
    else:
        print("🚨 ISSUES DETECTED - Here's what to check:")
        
        if not issues['knowledge_import_accessible']:
            print("\n📥 KNOWLEDGE IMPORT ISSUE:")
            print("   → The knowledge import navigation or component has issues")
            print("   → Check browser console for JavaScript errors")
            print("   → Try refreshing the page (Ctrl+F5 / Cmd+Shift+R)")
        
        if not issues['transparency_ui_visible']:
            print("\n🔍 TRANSPARENCY UI ISSUE:")
            print("   → The transparency dashboard may not be loading properly")
            print("   → Check if backend is running on port 8000")
            print("   → Verify browser console for component errors")
        
        if not issues['navigation_items_present']:
            print("\n🧭 NAVIGATION ITEMS ISSUE:")
            print("   → Some navigation items are missing from configuration")
            print("   → The sidebar may be collapsed or hidden")
        
        if not issues['components_loading']:
            print("\n🧩 COMPONENT LOADING ISSUE:")
            print("   → Backend services may not be responding properly")
            print("   → Check if GödelOS backend is running")
    
    print("\n🛠️ DEBUGGING STEPS:")
    print("   1. Open browser Developer Tools (F12)")
    print("   2. Check Console tab for any red error messages")
    print("   3. Check Network tab for failed requests")
    print("   4. Try hard refresh (Ctrl+F5 / Cmd+Shift+R)")
    print("   5. Ensure both frontend (3001) and backend (8000) are running")
    
    print(f"\n🔗 Quick Links:")
    print(f"   Frontend: http://localhost:3001")
    print(f"   Backend Health: http://localhost:8000/api/health")
    print(f"   Transparency API: http://localhost:8000/api/transparency/statistics")

def main():
    """Main test function"""
    print("🦉 GödelOS Navigation Accessibility Verification")
    print("Testing specific user concerns about knowledge import and transparency UI")
    print("=" * 80)
    
    issues = test_specific_navigation_concerns()
    provide_user_guidance(issues)
    
    # Summary
    working_features = sum(issues.values())
    total_features = len(issues)
    
    print(f"\n📊 SUMMARY: {working_features}/{total_features} navigation features accessible")
    
    if working_features == total_features:
        print("🎉 SUCCESS: All navigation features should be accessible!")
        return True
    else:
        print("⚠️  PARTIAL: Some navigation features need attention")
        return False

if __name__ == "__main__":
    main()
