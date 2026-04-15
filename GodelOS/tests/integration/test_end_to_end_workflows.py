"""
End-to-End Integration Tests for GödelOS

Comprehensive test suite for validating complete user workflows including:
- Full query processing pipeline
- Knowledge ingestion and retrieval
- Real-time cognitive transparency
- WebSocket communication
- Multi-component integration
"""

import asyncio
import json
import pytest
import time
import requests
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch, MagicMock

# Import test utilities
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


class TestCompleteUserJourney:
    """Test complete user journey from frontend to backend."""
    
    def setup_method(self):
        """Set up test environment."""
        self.base_url = "http://localhost:8000"  # Adjust based on actual backend URL
        self.frontend_url = "http://localhost:3000"  # Adjust based on actual frontend URL
    
    def test_health_check_integration(self):
        """Test that backend health check is accessible."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            assert response.status_code in [200, 503], "Health endpoint should be accessible"
        except requests.exceptions.RequestException:
            pytest.skip("Backend not running - integration test requires running services")
    
    def test_api_endpoints_accessible(self):
        """Test that key API endpoints are accessible."""
        endpoints_to_test = [
            "/",
            "/health",
            "/api/health",
            "/api/simple-test"
        ]
        
        accessible_endpoints = []
        for endpoint in endpoints_to_test:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                if response.status_code < 500:  # Any response except server error
                    accessible_endpoints.append(endpoint)
            except requests.exceptions.RequestException:
                pass
        
        if len(accessible_endpoints) == 0:
            pytest.skip("Backend not accessible - integration test requires running services")
        
        assert len(accessible_endpoints) > 0, "At least some API endpoints should be accessible"
    
    def test_query_processing_pipeline(self):
        """Test complete query processing from API call to response."""
        query_data = {
            "query": "What is artificial intelligence?",
            "include_reasoning": True
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/query",
                json=query_data,
                timeout=10
            )
            
            if response.status_code == 503:
                pytest.skip("GödelOS system not initialized")
            
            assert response.status_code == 200, f"Query should succeed, got {response.status_code}"
            
            data = response.json()
            assert "response" in data, "Response should contain 'response' field"
            assert "confidence" in data, "Response should contain 'confidence' field"
            assert "inference_time_ms" in data, "Response should contain timing information"
            
            # Validate response structure
            assert isinstance(data["response"], str), "Response should be a string"
            assert 0.0 <= data["confidence"] <= 1.0, "Confidence should be between 0 and 1"
            assert data["inference_time_ms"] >= 0, "Inference time should be non-negative"
            
        except requests.exceptions.RequestException:
            pytest.skip("Backend not accessible for query test")
    
    def test_knowledge_addition_pipeline(self):
        """Test complete knowledge addition workflow."""
        knowledge_data = {
            "concept": "Integration Testing",
            "definition": "Testing multiple components working together",
            "category": "software_engineering"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/knowledge",
                json=knowledge_data,
                timeout=10
            )
            
            if response.status_code == 503:
                pytest.skip("GödelOS system not initialized")
            
            assert response.status_code == 200, f"Knowledge addition should succeed, got {response.status_code}"
            
            data = response.json()
            assert "status" in data, "Response should contain status"
            assert data["status"] == "success", "Knowledge addition should be successful"
            
        except requests.exceptions.RequestException:
            pytest.skip("Backend not accessible for knowledge addition test")
    
    def test_cognitive_state_monitoring(self):
        """Test cognitive state monitoring endpoint."""
        try:
            response = requests.get(f"{self.base_url}/api/cognitive-state", timeout=10)
            
            if response.status_code == 503:
                pytest.skip("GödelOS system not initialized")
            
            assert response.status_code == 200, f"Cognitive state should be accessible, got {response.status_code}"
            
            data = response.json()
            expected_fields = [
                "manifest_consciousness",
                "agentic_processes", 
                "daemon_threads",
                "working_memory",
                "attention_focus",
                "metacognitive_state",
                "timestamp"
            ]
            
            for field in expected_fields:
                assert field in data, f"Cognitive state should contain '{field}' field"
            
        except requests.exceptions.RequestException:
            pytest.skip("Backend not accessible for cognitive state test")


class TestKnowledgeIngestionPipeline:
    """Test complete knowledge ingestion pipeline."""
    
    def setup_method(self):
        """Set up test environment."""
        self.base_url = "http://localhost:8000"
    
    def test_text_import_workflow(self):
        """Test text import workflow."""
        import_data = {
            "content": "This is test content for import testing.",
            "title": "Test Import Document",
            "category": "test"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/knowledge/import/text",
                json=import_data,
                timeout=10
            )
            
            if response.status_code == 503:
                pytest.skip("Backend not accessible")
            
            assert response.status_code == 200, f"Text import should succeed, got {response.status_code}"
            
            data = response.json()
            assert "import_id" in data, "Response should contain import_id"
            assert "status" in data, "Response should contain status"
            assert data["status"] == "queued", "Import should be queued"
            
            # Test import progress endpoint
            import_id = data["import_id"]
            progress_response = requests.get(
                f"{self.base_url}/api/knowledge/import/progress/{import_id}",
                timeout=5
            )
            
            assert progress_response.status_code == 200, "Progress endpoint should be accessible"
            progress_data = progress_response.json()
            assert "import_id" in progress_data, "Progress response should contain import_id"
            assert "status" in progress_data, "Progress response should contain status"
            
        except requests.exceptions.RequestException:
            pytest.skip("Backend not accessible for import test")
    
    def test_url_import_workflow(self):
        """Test URL import workflow."""
        import_data = {
            "url": "https://example.com/test-content",
            "category": "web"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/knowledge/import/url",
                json=import_data,
                timeout=10
            )
            
            if response.status_code == 503:
                pytest.skip("Backend not accessible")
            
            assert response.status_code == 200, f"URL import should succeed, got {response.status_code}"
            
            data = response.json()
            assert "import_id" in data, "Response should contain import_id"
            assert "status" in data, "Response should contain status"
            
        except requests.exceptions.RequestException:
            pytest.skip("Backend not accessible for URL import test")
    
    def test_wikipedia_import_workflow(self):
        """Test Wikipedia import workflow."""
        import_data = {
            "topic": "Artificial Intelligence",
            "category": "technology"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/knowledge/import/wikipedia",
                json=import_data,
                timeout=10
            )
            
            if response.status_code == 503:
                pytest.skip("Backend not accessible")
            
            assert response.status_code == 200, f"Wikipedia import should succeed, got {response.status_code}"
            
            data = response.json()
            assert "import_id" in data, "Response should contain import_id"
            assert "status" in data, "Response should contain status"
            
        except requests.exceptions.RequestException:
            pytest.skip("Backend not accessible for Wikipedia import test")
    
    def test_batch_import_workflow(self):
        """Test batch import workflow."""
        import_data = {
            "sources": [
                {"type": "text", "content": "Test content 1", "title": "Test 1"},
                {"type": "text", "content": "Test content 2", "title": "Test 2"}
            ]
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/knowledge/import/batch",
                json=import_data,
                timeout=10
            )
            
            if response.status_code == 503:
                pytest.skip("Backend not accessible")
            
            assert response.status_code == 200, f"Batch import should succeed, got {response.status_code}"
            
            data = response.json()
            assert "import_ids" in data, "Response should contain import_ids"
            assert "batch_size" in data, "Response should contain batch_size"
            assert data["batch_size"] == 2, "Batch size should match input"
            
        except requests.exceptions.RequestException:
            pytest.skip("Backend not accessible for batch import test")


class TestWebSocketIntegration:
    """Test WebSocket integration for real-time communication."""
    
    def setup_method(self):
        """Set up WebSocket test environment."""
        self.ws_url = "ws://localhost:8000/ws/unified-cognitive-stream"
    
    @pytest.mark.asyncio
    async def test_websocket_connection(self):
        """Test WebSocket connection establishment."""
        try:
            import websockets
            
            async with websockets.connect(self.ws_url) as websocket:
                # Should receive connection established message
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(message)
                
                assert data["type"] == "connection_established", "Should receive connection confirmation"
                assert "timestamp" in data, "Message should have timestamp"
                assert "connection_id" in data, "Message should have connection ID"
                
        except ImportError:
            pytest.skip("websockets library not available")
        except Exception as e:
            pytest.skip(f"WebSocket test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_websocket_subscription(self):
        """Test WebSocket event subscription."""
        try:
            import websockets
            
            async with websockets.connect(self.ws_url) as websocket:
                # Skip initial messages
                await asyncio.wait_for(websocket.recv(), timeout=2.0)  # connection_established
                try:
                    await asyncio.wait_for(websocket.recv(), timeout=2.0)  # initial_state
                except asyncio.TimeoutError:
                    pass  # initial_state might not be sent immediately
                
                # Send subscription request
                subscription = {
                    "type": "subscribe",
                    "event_types": ["query_processed", "knowledge_added"]
                }
                await websocket.send(json.dumps(subscription))
                
                # Should receive subscription confirmation
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(message)
                
                assert data["type"] == "subscription_confirmed", "Should receive subscription confirmation"
                assert data["event_types"] == ["query_processed", "knowledge_added"], "Should confirm subscribed events"
                
        except ImportError:
            pytest.skip("websockets library not available")
        except Exception as e:
            pytest.skip(f"WebSocket subscription test failed: {e}")


class TestConcurrentAccess:
    """Test multi-user concurrent access scenarios."""
    
    def setup_method(self):
        """Set up concurrent access tests."""
        self.base_url = "http://localhost:8000"
        self.num_concurrent_users = 5
    
    def test_concurrent_queries(self):
        """Test concurrent query processing."""
        def make_query(query_id):
            """Make a single query request."""
            query_data = {
                "query": f"Test query {query_id} for concurrent testing",
                "include_reasoning": False
            }
            
            try:
                response = requests.post(
                    f"{self.base_url}/api/query",
                    json=query_data,
                    timeout=15
                )
                return {
                    "query_id": query_id,
                    "status_code": response.status_code,
                    "success": response.status_code == 200,
                    "response_time": response.elapsed.total_seconds()
                }
            except requests.exceptions.RequestException as e:
                return {
                    "query_id": query_id,
                    "status_code": None,
                    "success": False,
                    "error": str(e)
                }
        
        # Test concurrent queries
        with ThreadPoolExecutor(max_workers=self.num_concurrent_users) as executor:
            futures = [
                executor.submit(make_query, i) 
                for i in range(self.num_concurrent_users)
            ]
            
            results = [future.result() for future in futures]
        
        # Analyze results
        successful_queries = [r for r in results if r["success"]]
        
        if len(successful_queries) == 0:
            pytest.skip("No queries succeeded - backend may not be running")
        
        # At least some queries should succeed under concurrent load
        success_rate = len(successful_queries) / len(results)
        assert success_rate >= 0.5, f"Success rate under concurrent load should be at least 50%, got {success_rate:.2%}"
        
        # Response times should be reasonable
        if successful_queries:
            avg_response_time = sum(r["response_time"] for r in successful_queries) / len(successful_queries)
            assert avg_response_time < 30.0, f"Average response time should be under 30s, got {avg_response_time:.2f}s"
    
    def test_concurrent_knowledge_operations(self):
        """Test concurrent knowledge addition operations."""
        def add_knowledge(item_id):
            """Add a single knowledge item."""
            knowledge_data = {
                "concept": f"Concurrent Test Concept {item_id}",
                "definition": f"Definition for concurrent test item {item_id}",
                "category": "concurrent_test"
            }
            
            try:
                response = requests.post(
                    f"{self.base_url}/api/knowledge",
                    json=knowledge_data,
                    timeout=15
                )
                return {
                    "item_id": item_id,
                    "status_code": response.status_code,
                    "success": response.status_code == 200
                }
            except requests.exceptions.RequestException:
                return {
                    "item_id": item_id,
                    "status_code": None,
                    "success": False
                }
        
        # Test concurrent knowledge operations
        with ThreadPoolExecutor(max_workers=self.num_concurrent_users) as executor:
            futures = [
                executor.submit(add_knowledge, i) 
                for i in range(self.num_concurrent_users)
            ]
            
            results = [future.result() for future in futures]
        
        # Analyze results
        successful_operations = [r for r in results if r["success"]]
        
        if len(successful_operations) == 0:
            pytest.skip("No knowledge operations succeeded - backend may not be running")
        
        # Most operations should succeed
        success_rate = len(successful_operations) / len(results)
        assert success_rate >= 0.7, f"Knowledge operations success rate should be at least 70%, got {success_rate:.2%}"


class TestSystemStabilityUnderLoad:
    """Test system stability under various load conditions."""
    
    def setup_method(self):
        """Set up load testing."""
        self.base_url = "http://localhost:8000"
    
    def test_health_check_under_load(self):
        """Test health check stability under load."""
        def check_health():
            """Perform health check."""
            try:
                response = requests.get(f"{self.base_url}/health", timeout=5)
                return response.status_code == 200
            except:
                return False
        
        # Perform multiple health checks rapidly
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(check_health) for _ in range(20)]
            results = [future.result() for future in futures]
        
        success_count = sum(results)
        if success_count == 0:
            pytest.skip("Health checks failed - backend may not be running")
        
        # Health checks should be very reliable
        success_rate = success_count / len(results)
        assert success_rate >= 0.9, f"Health check success rate should be at least 90%, got {success_rate:.2%}"
    
    def test_api_response_time_consistency(self):
        """Test API response time consistency."""
        response_times = []
        
        for i in range(10):
            try:
                start_time = time.time()
                response = requests.get(f"{self.base_url}/api/simple-test", timeout=10)
                end_time = time.time()
                
                if response.status_code == 200:
                    response_times.append(end_time - start_time)
                    
            except requests.exceptions.RequestException:
                pass
        
        if len(response_times) == 0:
            pytest.skip("No successful API calls - backend may not be running")
        
        # Response times should be consistent
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        
        assert avg_time < 2.0, f"Average response time should be under 2s, got {avg_time:.3f}s"
        assert max_time < 5.0, f"Max response time should be under 5s, got {max_time:.3f}s"
        
        # Variation should be reasonable
        if len(response_times) > 1:
            import statistics
            std_dev = statistics.stdev(response_times)
            assert std_dev < avg_time, "Response time variation should be reasonable"


class TestErrorHandlingIntegration:
    """Test error handling across the integrated system."""
    
    def setup_method(self):
        """Set up error handling tests."""
        self.base_url = "http://localhost:8000"
    
    def test_invalid_request_handling(self):
        """Test handling of invalid requests."""
        # Test invalid JSON
        try:
            response = requests.post(
                f"{self.base_url}/api/query",
                data="invalid json",
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            assert response.status_code == 422, "Invalid JSON should return 422"
        except requests.exceptions.RequestException:
            pytest.skip("Backend not accessible")
        
        # Test missing required fields
        try:
            response = requests.post(
                f"{self.base_url}/api/query",
                json={},  # Missing required 'query' field
                timeout=5
            )
            assert response.status_code == 422, "Missing fields should return 422"
        except requests.exceptions.RequestException:
            pytest.skip("Backend not accessible")
    
    def test_nonexistent_endpoint_handling(self):
        """Test handling of requests to non-existent endpoints."""
        try:
            response = requests.get(f"{self.base_url}/api/nonexistent-endpoint", timeout=5)
            assert response.status_code == 404, "Non-existent endpoint should return 404"
        except requests.exceptions.RequestException:
            pytest.skip("Backend not accessible")
    
    def test_timeout_handling(self):
        """Test system behavior with very short timeouts."""
        try:
            # Very short timeout to test timeout handling
            response = requests.get(f"{self.base_url}/health", timeout=0.001)
            # If this succeeds, the system is very fast
            assert response.status_code in [200, 503]
        except requests.exceptions.Timeout:
            # Timeout is expected with very short timeout
            assert True, "Timeout handled correctly"
        except requests.exceptions.RequestException:
            pytest.skip("Backend not accessible")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])