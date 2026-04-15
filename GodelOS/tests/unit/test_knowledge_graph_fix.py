#!/usr/bin/env python3
"""
Test script to verify that the Knowledge Graph is populated after knowledge ingestion.
"""

import asyncio
import json
import logging
import requests
import time
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BACKEND_URL = "http://localhost:8000"
API_BASE = f"{BACKEND_URL}/api"

async def test_knowledge_graph_population():
    """Test that knowledge ingestion populates the knowledge graph."""
    
    print("🧪 Testing Knowledge Graph Population After Ingestion")
    print("=" * 60)
    
    # Step 1: Check initial knowledge graph state
    print("\n1. Checking initial knowledge graph state...")
    try:
        response = requests.get(f"{API_BASE}/transparency/knowledge-graph/export")
        if response.status_code == 200:
            initial_data = response.json()
            initial_nodes = len(initial_data.get("graph_data", {}).get("nodes", []))
            initial_edges = len(initial_data.get("graph_data", {}).get("edges", []))
            print(f"   ✅ Initial graph: {initial_nodes} nodes, {initial_edges} edges")
        else:
            print(f"   ⚠️ Knowledge graph not available (status: {response.status_code})")
            initial_nodes = 0
            initial_edges = 0
    except Exception as e:
        print(f"   ⚠️ Could not access knowledge graph: {e}")
        initial_nodes = 0
        initial_edges = 0
    
    # Step 2: Ingest some test knowledge
    print("\n2. Ingesting test knowledge...")
    test_data = {
        "content": "Artificial Intelligence is a branch of computer science that deals with creating intelligent machines. Machine Learning is a subset of AI that focuses on algorithms that can learn from data. Deep Learning uses neural networks with multiple layers.",
        "title": "Introduction to AI and Machine Learning",
        "source": {
            "source_type": "text",
            "source_id": "test-knowledge-graph",
            "source_identifier": "test-ai-ml-intro",
            "metadata": {
                "test": True,
                "created_by": "knowledge_graph_test"
            }
        },
        "categorization_hints": ["artificial-intelligence", "machine-learning", "technology"]
    }
    
    try:
        response = requests.post(f"{API_BASE}/knowledge/import/text", json=test_data)
        if response.status_code == 200:
            import_id = response.json().get("import_id")
            print(f"   ✅ Knowledge ingestion started (ID: {import_id})")
            
            # Wait for ingestion to complete
            print("   ⏳ Waiting for ingestion to complete...")
            for i in range(10):  # Wait up to 10 seconds
                time.sleep(1)
                try:
                    progress_response = requests.get(f"{API_BASE}/knowledge/import/{import_id}/progress")
                    if progress_response.status_code == 200:
                        progress = progress_response.json()
                        status = progress.get("status", "unknown")
                        print(f"   📊 Progress: {status} ({progress.get('progress_percentage', 0):.1f}%)")
                        if status == "completed":
                            print("   ✅ Ingestion completed successfully!")
                            break
                        elif status == "failed":
                            print(f"   ❌ Ingestion failed: {progress.get('error_message', 'Unknown error')}")
                            return False
                except Exception as e:
                    print(f"   ⚠️ Could not check progress: {e}")
            else:
                print("   ⚠️ Ingestion did not complete within timeout")
        else:
            print(f"   ❌ Failed to start ingestion (status: {response.status_code})")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Error during ingestion: {e}")
        return False
    
    # Step 3: Check knowledge graph after ingestion
    print("\n3. Checking knowledge graph after ingestion...")
    try:
        # Wait a bit more for graph updates to propagate
        time.sleep(2)
        
        response = requests.get(f"{API_BASE}/transparency/knowledge-graph/export")
        if response.status_code == 200:
            final_data = response.json()
            final_nodes = len(final_data.get("graph_data", {}).get("nodes", []))
            final_edges = len(final_data.get("graph_data", {}).get("edges", []))
            
            print(f"   📊 Final graph: {final_nodes} nodes, {final_edges} edges")
            print(f"   📈 Change: +{final_nodes - initial_nodes} nodes, +{final_edges - initial_edges} edges")
            
            if final_nodes > initial_nodes:
                print("   ✅ SUCCESS: Knowledge graph was populated with new nodes!")
                
                # Show some sample nodes
                nodes = final_data.get("graph_data", {}).get("nodes", [])
                if nodes:
                    print("   📋 Sample nodes in graph:")
                    for node in nodes[-3:]:  # Show last 3 nodes
                        concept = node.get("concept", "Unknown")
                        node_type = node.get("node_type", "Unknown")
                        print(f"      - {concept} (type: {node_type})")
                
                return True
            else:
                print("   ❌ FAILURE: Knowledge graph was not populated with new nodes")
                return False
        else:
            print(f"   ❌ Could not access knowledge graph after ingestion (status: {response.status_code})")
            return False
    except Exception as e:
        print(f"   ❌ Error checking final graph state: {e}")
        return False

def main():
    """Main test function."""
    print("🚀 Starting Knowledge Graph Population Test")
    print(f"Backend URL: {BACKEND_URL}")
    
    # Check if backend is running
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ Backend not responding correctly (status: {response.status_code})")
            return
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        print("   Make sure the backend is running on http://localhost:8000")
        return
    
    # Run the test
    try:
        success = asyncio.run(test_knowledge_graph_population())
        
        print("\n" + "=" * 60)
        if success:
            print("🎉 TEST PASSED: Knowledge Graph is being populated correctly!")
        else:
            print("❌ TEST FAILED: Knowledge Graph is not being populated")
        
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()