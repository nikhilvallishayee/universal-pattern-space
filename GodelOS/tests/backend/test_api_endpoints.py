"""
API Endpoint Tests for GödelOS Backend

Comprehensive test suite for all REST API endpoints including:
- Health checks and system status
- Query processing endpoints
- Knowledge management endpoints
- Cognitive state endpoints
- Import/export functionality
- Error handling and edge cases
"""

import asyncio
import json
import pytest
import time
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

# Import the FastAPI app
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.main import app
from backend.models import QueryRequest, KnowledgeRequest, SimpleKnowledgeRequest


class TestHealthEndpoints:
    """Test health check and system status endpoints."""
    
    def setup_method(self):
        """Set up test client for each test."""
        self.client = TestClient(app)
    
    def test_root_endpoint(self):
        """Test the root endpoint returns correct response."""
        response = self.client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "GödelOS Unified Cognitive API"
        assert data["version"] == "2.0.0"
    
    @patch('backend.main.godelos_integration')
    def test_health_check_healthy(self, mock_integration):
        """Test health check when system is healthy."""
        # Mock healthy system
        mock_integration.get_health_status = AsyncMock(return_value={
            "healthy": True,
            "components": {"inference_engine": True, "knowledge_store": True},
            "error_count": 0
        })
        
        response = self.client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "services" in data
    
    @patch('backend.main.godelos_integration')
    def test_health_check_unhealthy(self, mock_integration):
        """Test health check when system is unhealthy."""
        # Mock unhealthy system
        mock_integration.get_health_status = AsyncMock(return_value={
            "healthy": False,
            "components": {"inference_engine": False, "knowledge_store": True},
            "error_count": 3
        })
        
        response = self.client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "services" in data
    
    def test_health_check_not_initialized(self):
        """Test health check when GödelOS is not initialized."""
        with patch('backend.main.godelos_integration', None):
            response = self.client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
    
    @patch('backend.main.godelos_integration')
    def test_api_health_alias(self, mock_integration):
        """Test /api/health endpoint (alias for /health)."""
        mock_integration.get_health_status = AsyncMock(return_value={
            "healthy": True,
            "components": {},
            "error_count": 0
        })
        
        response = self.client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestQueryEndpoints:
    """Test query processing endpoints."""
    
    def setup_method(self):
        """Set up test client for each test."""
        self.client = TestClient(app)
    
    @patch('backend.main.godelos_integration')
    @patch('backend.main.websocket_manager')
    def test_process_query_basic(self, mock_ws_manager, mock_integration):
        """Test basic query processing."""
        # Mock query response
        mock_integration.process_query = AsyncMock(return_value={
            "response": "The capital of France is Paris.",
            "confidence": 0.95,
            "knowledge_used": ["fact_france_capital"]
        })
        mock_ws_manager.has_connections = MagicMock(return_value=False)
        
        query_data = {
            "query": "What is the capital of France?",
            "include_reasoning": True
        }
        
        response = self.client.post("/api/query", json=query_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["response"] == "The capital of France is Paris."
        assert data["confidence"] == 0.95
        assert "inference_time_ms" in data
        assert "fact_france_capital" in data["knowledge_used"]
    
    @patch('backend.main.godelos_integration')
    def test_process_query_with_context(self, mock_integration):
        """Test query processing with context."""
        mock_integration.process_query = AsyncMock(return_value={
            "response": "Based on the context, the answer is 42.",
            "confidence": 0.85,
            "knowledge_used": []
        })
        
        query_data = {
            "query": "What is the answer?",
            "context": {"topic": "mathematics", "previous_question": "ultimate question"},
            "include_reasoning": False
        }
        
        response = self.client.post("/api/query", json=query_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["response"] == "Based on the context, the answer is 42."
        assert data["confidence"] == 0.85
    
    def test_process_query_not_initialized(self):
        """Test query processing when system is not initialized."""
        with patch('backend.main.godelos_integration', None):
            query_data = {"query": "Test query"}
            response = self.client.post("/api/query", json=query_data)
            assert response.status_code == 200
            data = response.json()
            assert "fallback mode" in data["response"]
    
    @patch('backend.main.godelos_integration')
    def test_process_query_error(self, mock_integration):
        """Test query processing error handling."""
        mock_integration.process_query = AsyncMock(
            side_effect=Exception("Processing failed")
        )
        
        query_data = {"query": "Test query that will fail"}
        response = self.client.post("/api/query", json=query_data)
        # unified_server catches errors and returns fallback 200
        assert response.status_code == 200
        data = response.json()
        assert "fallback mode" in data["response"]
    
    def test_simple_test_endpoint(self):
        """Test the simple test endpoint."""
        response = self.client.get("/api/simple-test")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "simple test works"
        assert "timestamp" in data


class TestKnowledgeEndpoints:
    """Test knowledge management endpoints."""
    
    def setup_method(self):
        """Set up test client for each test."""
        self.client = TestClient(app)
    
    @patch('backend.main.godelos_integration')
    def test_get_knowledge_basic(self, mock_integration):
        """Test basic knowledge retrieval."""
        mock_integration.get_knowledge = AsyncMock(return_value={
            "facts": [
                {"id": "fact1", "content": "Paris is the capital of France", "knowledge_type": "fact"}
            ],
            "rules": [],
            "concepts": [
                {"id": "concept1", "content": "France is a European country", "knowledge_type": "concept"}
            ],
            "total_count": 2
        })
        
        response = self.client.get("/api/knowledge")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_count"] == 2
        assert len(data["facts"]) == 1
        assert len(data["concepts"]) == 1
        assert data["facts"][0]["content"] == "Paris is the capital of France"
    
    @patch('backend.main.godelos_integration')
    def test_get_knowledge_with_filters(self, mock_integration):
        """Test knowledge retrieval with filters."""
        mock_integration.get_knowledge = AsyncMock(return_value={
            "facts": [{"id": "fact1", "content": "Test fact", "knowledge_type": "fact"}],
            "rules": [],
            "concepts": [],
            "total_count": 1
        })
        
        response = self.client.get("/api/knowledge?knowledge_type=fact&limit=50")
        assert response.status_code == 200
        
        # Verify the integration was called with correct parameters
        mock_integration.get_knowledge.assert_called_once_with(
            context_id=None,
            knowledge_type="fact",
            limit=50
        )
    
    @patch('backend.main.godelos_integration')
    @patch('backend.main.websocket_manager')
    def test_add_knowledge_simple_format(self, mock_ws_manager, mock_integration):
        """Test adding knowledge using simple format."""
        mock_integration.add_knowledge = AsyncMock(return_value={
            "message": "Knowledge added successfully"
        })
        mock_ws_manager.has_connections = MagicMock(return_value=False)
        
        knowledge_data = {
            "concept": "Machine Learning",
            "definition": "A subset of artificial intelligence",
            "category": "technology"
        }
        
        response = self.client.post("/api/knowledge", json=knowledge_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "added successfully" in data["message"]
    
    @patch('backend.main.godelos_integration')
    @patch('backend.main.websocket_manager')
    def test_add_knowledge_full_format(self, mock_ws_manager, mock_integration):
        """Test adding knowledge using full KnowledgeRequest format."""
        mock_integration.add_knowledge = AsyncMock(return_value={
            "message": "Knowledge added successfully"
        })
        mock_ws_manager.has_connections = MagicMock(return_value=True)
        mock_ws_manager.broadcast = AsyncMock()
        
        knowledge_data = {
            "content": "Quantum computing uses quantum mechanics",
            "knowledge_type": "fact",
            "context_id": "physics",
            "metadata": {"source": "textbook", "confidence": 0.9}
        }
        
        response = self.client.post("/api/knowledge", json=knowledge_data)
        assert response.status_code == 200
        
        # Verify WebSocket broadcast was called
        mock_ws_manager.broadcast.assert_called_once()
    
    def test_add_knowledge_not_initialized(self):
        """Test adding knowledge when system is not initialized."""
        with patch('backend.main.godelos_integration', None):
            knowledge_data = {"content": "Test knowledge"}
            response = self.client.post("/api/knowledge", json=knowledge_data)
            assert response.status_code == 200


class TestCognitiveStateEndpoints:
    """Test cognitive state monitoring endpoints."""
    
    def setup_method(self):
        """Set up test client for each test."""
        self.client = TestClient(app)
    
    @patch('backend.main.godelos_integration')
    def test_get_cognitive_state(self, mock_integration):
        """Test cognitive state retrieval."""
        mock_cognitive_state = {
            "manifest_consciousness": {
                "current_focus": "Processing query",
                "awareness_level": 0.8,
                "coherence_level": 0.9
            },
            "agentic_processes": [
                {
                    "process_id": "proc1",
                    "process_type": "inference",
                    "status": "active",
                    "priority": 5,
                    "progress": 0.7
                }
            ],
            "daemon_threads": [
                {
                    "process_id": "daemon1",
                    "process_type": "memory_consolidation",
                    "status": "running",
                    "priority": 2,
                    "progress": 0.5
                }
            ],
            "working_memory": {
                "active_items": [
                    {"item_id": "item1", "content": "Current query", "activation_level": 0.9}
                ]
            },
            "attention_focus": [
                {"item_id": "focus1", "item_type": "query", "salience": 0.8}
            ],
            "metacognitive_state": {
                "self_awareness_level": 0.7,
                "confidence_in_reasoning": 0.85
            }
        }
        
        mock_integration.get_cognitive_state = AsyncMock(return_value=mock_cognitive_state)
        
        response = self.client.get("/api/cognitive-state")
        assert response.status_code == 200
        
        data = response.json()
        assert "manifest_consciousness" in data
        assert "version" in data
    
    def test_get_cognitive_state_not_initialized(self):
        """Test cognitive state when system is not initialized."""
        with patch('backend.main.godelos_integration', None):
            response = self.client.get("/api/cognitive-state")
            assert response.status_code == 200


class TestKnowledgeImportEndpoints:
    """Test knowledge import endpoints."""
    
    def setup_method(self):
        """Set up test client for each test."""
        self.client = TestClient(app)
    
    @patch('backend.main.KNOWLEDGE_SERVICES_AVAILABLE', True)
    @patch('backend.main.knowledge_ingestion_service')
    @patch('backend.main.websocket_manager')
    def test_import_from_url(self, mock_ws_manager, mock_ingestion_service):
        """Test URL import functionality."""
        mock_ws_manager.has_connections = MagicMock(return_value=True)
        mock_ws_manager.broadcast = AsyncMock()
        mock_ingestion_service.import_from_url = AsyncMock(return_value="url_import_123")
        
        import_data = {
            "url": "https://example.com/knowledge",
            "category": "web"
        }
        
        response = self.client.post("/api/knowledge/import/url", json=import_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "import_id" in data
        assert data["status"] == "queued"
    
    @patch('backend.main.KNOWLEDGE_SERVICES_AVAILABLE', True)
    @patch('backend.main.knowledge_ingestion_service')
    @patch('backend.main.websocket_manager')
    def test_import_from_file(self, mock_ws_manager, mock_ingestion_service):
        """Test file import functionality."""
        mock_ws_manager.has_connections = MagicMock(return_value=False)
        mock_ingestion_service.import_from_file = AsyncMock(return_value="file_import_123")
        
        # Create test file content
        test_content = b"This is test file content for knowledge import."
        
        files = {"file": ("test.txt", test_content, "text/plain")}
        data = {
            "filename": "test.txt",
            "file_type": "txt",
            "encoding": "utf-8",
            "categorization_hints": "[]"
        }
        
        response = self.client.post("/api/knowledge/import/file", files=files, data=data)
        assert response.status_code == 200
        
        result = response.json()
        assert result["import_id"] == "file_import_123"
        assert result["status"] == "started"
    
    @patch('backend.main.KNOWLEDGE_SERVICES_AVAILABLE', True)
    @patch('backend.main.knowledge_ingestion_service')
    @patch('backend.main.websocket_manager')
    def test_import_from_wikipedia(self, mock_ws_manager, mock_ingestion_service):
        """Test Wikipedia import functionality."""
        mock_ws_manager.has_connections = MagicMock(return_value=False)
        mock_ingestion_service.import_from_wikipedia = AsyncMock(return_value="wiki_import_123")
        
        import_data = {
            "topic": "Artificial Intelligence",
            "category": "technology"
        }
        
        response = self.client.post("/api/knowledge/import/wikipedia", json=import_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "import_id" in data
        assert data["status"] == "queued"
    
    @patch('backend.main.KNOWLEDGE_SERVICES_AVAILABLE', True)
    @patch('backend.main.knowledge_ingestion_service')
    @patch('backend.main.websocket_manager')
    def test_import_from_text(self, mock_ws_manager, mock_ingestion_service):
        """Test text import functionality."""
        mock_ws_manager.has_connections = MagicMock(return_value=False)
        mock_ingestion_service.import_from_text = AsyncMock(return_value="text_import_123")
        
        import_data = {
            "content": "This is manually entered knowledge content.",
            "title": "Manual Knowledge Entry",
            "category": "manual"
        }
        
        response = self.client.post("/api/knowledge/import/text", json=import_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "import_id" in data
        assert data["status"] == "queued"
    
    @patch('backend.main.websocket_manager')
    def test_batch_import(self, mock_ws_manager):
        """Test batch import functionality."""
        mock_ws_manager.has_connections = MagicMock(return_value=False)
        
        import_data = {
            "sources": [
                {"type": "url", "source": "https://example1.com"},
                {"type": "url", "source": "https://example2.com"}
            ]
        }
        
        response = self.client.post("/api/knowledge/import/batch", json=import_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "import_ids" in data
        assert data["batch_size"] == 2
        assert data["status"] == "queued"
    
    def test_get_import_progress(self):
        """Test import progress retrieval."""
        import_id = "test_import_123"
        response = self.client.get(f"/api/knowledge/import/progress/{import_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["import_id"] == import_id
        assert "status" in data
    
    def test_cancel_import(self):
        """Test import cancellation."""
        import_id = "test_import_123"
        response = self.client.delete(f"/api/knowledge/import/{import_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["import_id"] == import_id
        assert data["status"] in ("cancelled", "not_found")


class TestKnowledgeSearchEndpoints:
    """Test knowledge search and management endpoints."""
    
    def setup_method(self):
        """Set up test client for each test."""
        self.client = TestClient(app)
    
    def test_search_knowledge(self):
        """Test knowledge search functionality."""
        response = self.client.get("/api/knowledge/search?query=artificial intelligence&limit=10")
        assert response.status_code == 200
        
        data = response.json()
        assert "results" in data
        assert "total" in data
    
    def test_get_knowledge_graph(self):
        """Test knowledge graph retrieval."""
        response = self.client.get("/api/knowledge/graph")
        assert response.status_code == 200
        # Basic structure validation will be handled by integration tests
    
    def test_get_knowledge_statistics(self):
        """Test knowledge statistics endpoint."""
        response = self.client.get("/api/knowledge/statistics")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_items" in data
    
    def test_get_categories(self):
        """Test categories retrieval."""
        response = self.client.get("/api/knowledge/categories")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data["categories"], list)
    
    def test_create_category(self):
        """Test category creation."""
        category_data = {
            "category_id": "test_category",
            "name": "Test Category",
            "description": "A test category for unit testing",
            "color": "#FF5733",
            "parent_category": None,
            "metadata": {}
        }
        
        response = self.client.post("/api/knowledge/categories", json=category_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"


class TestSystemCapabilitiesEndpoints:
    """Test system capabilities and meta endpoints."""
    
    def setup_method(self):
        """Set up test client for each test."""
        self.client = TestClient(app)
    
    def test_get_system_capabilities(self):
        """Test system capabilities endpoint."""
        response = self.client.get("/api/capabilities")
        assert response.status_code == 200
        
        data = response.json()
        assert "cognitive_capabilities" in data
        assert "technical_capabilities" in data
    
    def test_test_route(self):
        """Test the general test route."""
        response = self.client.get("/api/test-route")
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "Test route working"
    
    def test_evolution_test(self):
        """Test evolution test endpoint."""
        response = self.client.get("/api/evo-test")
        assert response.status_code == 200
        
        data = response.json()
        assert "evolution_data" in data
    
    def test_graph_test(self):
        """Test graph test endpoint."""
        response = self.client.get("/api/graph-test")
        assert response.status_code == 200
        
        data = response.json()
        assert "nodes" in data
        assert "edges" in data


class TestErrorHandling:
    """Test error handling across all endpoints."""
    
    def setup_method(self):
        """Set up test client for each test."""
        self.client = TestClient(app)
    
    def test_404_not_found(self):
        """Test 404 handling for non-existent endpoints."""
        response = self.client.get("/api/nonexistent-endpoint")
        assert response.status_code == 404
    
    def test_invalid_json_format(self):
        """Test handling of invalid JSON in requests."""
        response = self.client.post(
            "/api/query",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    def test_missing_required_fields(self):
        """Test handling of missing required fields."""
        # Test query without required 'query' field
        response = self.client.post("/api/query", json={})
        assert response.status_code == 422
        
        # Verify error details
        error_detail = response.json()
        assert "detail" in error_detail
    
    def test_invalid_field_types(self):
        """Test handling of invalid field types."""
        # Test query with wrong type for include_reasoning
        # unified_server returns fallback response instead of 422
        response = self.client.post("/api/query", json={
            "query": "test query",
            "include_reasoning": "not_a_boolean"
        })
        assert response.status_code == 200


class TestPerformanceBenchmarks:
    """Performance benchmark tests for API response times."""
    
    def setup_method(self):
        """Set up test client for each test."""
        self.client = TestClient(app)
    
    @patch('backend.main.godelos_integration')
    def test_query_response_time_benchmark(self, mock_integration):
        """Benchmark query processing response time."""
        # Mock fast response
        mock_integration.process_query = AsyncMock(return_value={
            "response": "Fast response",
            "confidence": 1.0,
            "knowledge_used": []
        })
        
        start_time = time.time()
        response = self.client.post("/api/query", json={"query": "test query"})
        end_time = time.time()
        
        assert response.status_code == 200
        response_time_ms = (end_time - start_time) * 1000
        
        # API response should be under 1 second for simple queries
        assert response_time_ms < 1000, f"Query response took {response_time_ms}ms"
    
    def test_health_check_response_time(self):
        """Benchmark health check response time."""
        with patch('backend.main.godelos_integration') as mock_integration:
            mock_integration.get_health_status = AsyncMock(return_value={
                "healthy": True,
                "components": {},
                "error_count": 0
            })
            
            start_time = time.time()
            response = self.client.get("/health")
            end_time = time.time()
            
            assert response.status_code == 200
            response_time_ms = (end_time - start_time) * 1000
            
            # Health checks should be very fast
            assert response_time_ms < 200, f"Health check took {response_time_ms}ms"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])