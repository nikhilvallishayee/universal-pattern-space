#!/usr/bin/env python3
import requests
import json

print('🧪 Real User Workflow Test')
print('=' * 40)

# Test 1: Import knowledge
print('1. Testing knowledge import...')
try:
    import_response = requests.post('http://localhost:8000/api/knowledge/import/text', 
        json={'content': 'JavaScript D3.js force simulation is working correctly in the knowledge graph visualization.', 
              'title': 'KnowledgeGraph Fix Verification', 
              'category': 'system_test'})
    if import_response.status_code in [200, 201, 202]:
        print('✅ Knowledge import successful')
        import_data = import_response.json()
        print(f'   Import ID: {import_data.get("import_id", "N/A")}')
    else:
        print(f'❌ Knowledge import failed: {import_response.status_code}')
except Exception as e:
    print(f'❌ Knowledge import error: {e}')

# Test 2: Create reasoning session  
print('2. Testing reasoning session...')
try:
    session_response = requests.post('http://localhost:8000/api/transparency/session/start',
        json={'query': 'How is the knowledge graph visualization working?', 
              'transparency_level': 'detailed'})
    if session_response.status_code in [200, 201]:
        print('✅ Reasoning session created')
        session_data = session_response.json()
        print(f'   Session ID: {session_data.get("session_id", "N/A")}')
    else:
        print(f'❌ Reasoning session failed: {session_response.status_code}')
except Exception as e:
    print(f'❌ Reasoning session error: {e}')

# Test 3: Query provenance
print('3. Testing provenance tracking...')
try:
    prov_response = requests.post('http://localhost:8000/api/transparency/provenance/query',
        json={'target_id': 'KnowledgeGraph Fix', 'query_type': 'backward_trace'})
    if prov_response.status_code in [200, 201]:
        print('✅ Provenance query successful')
        prov_data = prov_response.json()
        print(f'   Results: {len(prov_data.get("results", {}).get("nodes", []))} nodes found')
    else:
        print(f'❌ Provenance query failed: {prov_response.status_code}')
except Exception as e:
    print(f'❌ Provenance query error: {e}')

print('\n🎉 Real User Workflow Test Complete!')
