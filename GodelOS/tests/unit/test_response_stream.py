#!/usr/bin/env python3
"""
Test the response stream functionality specifically
"""

import requests
import json
from datetime import datetime

def test_query_endpoint():
    """Test the query endpoint that the frontend should be calling"""
    print("🧪 Testing Query Response Stream Fix")
    print("=" * 50)
    
    try:
        # Test the exact query the frontend is making
        query_data = {
            "query": "What are the current agentic processes working on?",
            "context": {"type": "knowledge"},
            "include_reasoning": True
        }
        
        print(f"📤 Sending query: {query_data['query']}")
        
        response = requests.post(
            "http://localhost:8000/api/query", 
            json=query_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"📥 Response Status: HTTP {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Query successful!")
            print(f"   Response length: {len(str(result))} characters")
            
            # Check for expected fields that the frontend uses
            expected_fields = ['response', 'confidence', 'reasoning_steps', 'knowledge_used', 'inference_time_ms']
            found_fields = []
            
            for field in expected_fields:
                if field in result:
                    found_fields.append(field)
                    if isinstance(result[field], str):
                        print(f"   ✅ {field}: \"{result[field][:100]}{'...' if len(str(result[field])) > 100 else ''}\"")
                    else:
                        print(f"   ✅ {field}: {type(result[field]).__name__} ({len(str(result[field]))} chars)")
                else:
                    print(f"   ❌ {field}: Missing")
            
            print(f"\n📊 Found {len(found_fields)}/{len(expected_fields)} expected fields")
            
            if len(found_fields) >= 3:
                print("🎉 Response structure looks good for frontend integration!")
                return True
            else:
                print("⚠️  Response missing some expected fields")
                return False
                
        else:
            print(f"❌ Query failed: HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Query test error: {e}")
        return False

def test_cognitive_state_for_suggestions():
    """Test that cognitive state provides data for generating suggestions"""
    print("\n🧠 Testing Cognitive State for Suggestions")
    print("-" * 40)
    
    try:
        response = requests.get("http://localhost:8000/api/cognitive/state", timeout=5)
        
        if response.status_code == 200:
            cognitive_data = response.json()
            print("✅ Cognitive state accessible")
            
            # Check fields used by suggestions
            suggestion_fields = {
                'attention_focus': 'attention focus items',
                'agentic_processes': 'active processes', 
                'metacognitive_state': 'metacognitive data'
            }
            
            for field, description in suggestion_fields.items():
                if field in cognitive_data:
                    data = cognitive_data[field]
                    if isinstance(data, list):
                        print(f"   ✅ {field}: {len(data)} {description}")
                    elif isinstance(data, dict):
                        print(f"   ✅ {field}: {description} (dict)")
                    else:
                        print(f"   ✅ {field}: {description} ({type(data).__name__})")
                else:
                    print(f"   ❌ {field}: Missing")
            
            return True
        else:
            print(f"❌ Cognitive state failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Cognitive state test error: {e}")
        return False

if __name__ == "__main__":
    print(f"⏰ Test started: {datetime.now().strftime('%H:%M:%S')}")
    
    query_ok = test_query_endpoint()
    cognitive_ok = test_cognitive_state_for_suggestions()
    
    print("\n" + "=" * 50)
    if query_ok and cognitive_ok:
        print("🎉 SUCCESS: Response stream should now work!")
        print("   - Query endpoint returns proper data")
        print("   - Cognitive state provides suggestion data")
        print("   - Frontend should display responses correctly")
    else:
        print("⚠️  ISSUES DETECTED:")
        if not query_ok:
            print("   - Query endpoint has problems")
        if not cognitive_ok:
            print("   - Cognitive state has problems")
    
    print(f"⏰ Test completed: {datetime.now().strftime('%H:%M:%S')}")
