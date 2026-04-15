"""
API integration tests for Query Replay Harness endpoints.

Tests the REST API functionality for managing recordings and replays.
"""

import asyncio
import json
import uuid
from typing import Dict, Any
from unittest.mock import AsyncMock, patch

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Mock FastAPI and related imports since they might not be available in test env
try:
    import pytest
    from fastapi.testclient import TestClient
    from fastapi import FastAPI
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    # Create dummy classes for testing
    class TestClient:
        def __init__(self, app): pass
        def get(self, *args, **kwargs): pass
        def post(self, *args, **kwargs): pass
        def delete(self, *args, **kwargs): pass
    
    class FastAPI:
        def __init__(self, *args, **kwargs): pass
        routes = []


class MockResponse:
    """Mock response object for testing."""
    def __init__(self, status_code: int, json_data: Dict[str, Any]):
        self.status_code = status_code
        self._json_data = json_data
    
    def json(self):
        return self._json_data


class TestReplayAPIEndpoints:
    """Test the replay harness API endpoints."""
    
    def setup_method(self):
        """Set up test client and mock data."""
        if not FASTAPI_AVAILABLE:
            pytest.skip("FastAPI not available")
        
        # Create test app
        self.app = FastAPI()
        
        # Mock cognitive manager
        self.mock_cognitive_manager = AsyncMock()
        self.mock_cognitive_manager.process_query = AsyncMock(return_value={
            "response": "Test response",
            "confidence": 0.85
        })
        
        # Setup endpoints
        from backend.api.replay_endpoints import setup_replay_endpoints
        setup_replay_endpoints(self.app, self.mock_cognitive_manager)
        
        self.client = TestClient(self.app)
    
    def test_list_recordings_empty(self):
        """Test listing recordings when none exist."""
        with patch('backend.core.query_replay_harness.replay_harness') as mock_harness:
            mock_harness.list_recordings.return_value = []
            
            response = self.client.get("/api/v1/replay/recordings")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "success"
            assert data["recordings"] == []
            assert data["total"] == 0
    
    def test_list_recordings_with_data(self):
        """Test listing recordings with sample data."""
        sample_recordings = [
            {
                "recording_id": "rec1",
                "query": "What is AI?",
                "timestamp": "2024-01-01T10:00:00",
                "tags": ["ai", "test"],
                "duration_ms": 1500
            },
            {
                "recording_id": "rec2", 
                "query": "How does ML work?",
                "timestamp": "2024-01-01T11:00:00",
                "tags": ["ml", "test"],
                "duration_ms": 2000
            }
        ]
        
        with patch('backend.core.query_replay_harness.replay_harness') as mock_harness:
            mock_harness.list_recordings.return_value = sample_recordings
            
            response = self.client.get("/api/v1/replay/recordings")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "success"
            assert len(data["recordings"]) == 2
            assert data["total"] == 2
    
    def test_list_recordings_with_filters(self):
        """Test listing recordings with tag filters."""
        with patch('backend.core.query_replay_harness.replay_harness') as mock_harness:
            mock_harness.list_recordings.return_value = []
            
            response = self.client.get("/api/v1/replay/recordings?tags=ai,ml&limit=50")
            assert response.status_code == 200
            
            # Verify the harness was called with correct parameters
            mock_harness.list_recordings.assert_called_with(tags=["ai", "ml"], limit=50)
    
    def test_get_recording_exists(self):
        """Test getting a specific recording that exists."""
        from dataclasses import dataclass
        from datetime import datetime
        
        @dataclass
        class MockRecording:
            recording_id: str = "test_rec"
            query: str = "Test query"
            timestamp: datetime = datetime.now()
            steps: list = None
            
            def __post_init__(self):
                if self.steps is None:
                    self.steps = []
        
        mock_recording = MockRecording()
        
        with patch('backend.core.query_replay_harness.replay_harness') as mock_harness:
            mock_harness.load_recording.return_value = mock_recording
            
            response = self.client.get("/api/v1/replay/recordings/test_rec")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "success"
            assert data["recording"]["recording_id"] == "test_rec"
    
    def test_get_recording_not_found(self):
        """Test getting a recording that doesn't exist."""
        with patch('backend.core.query_replay_harness.replay_harness') as mock_harness:
            mock_harness.load_recording.return_value = None
            
            response = self.client.get("/api/v1/replay/recordings/nonexistent")
            assert response.status_code == 404
    
    def test_replay_recording_success(self):
        """Test successfully replaying a recording."""
        from dataclasses import dataclass
        from backend.core.query_replay_harness import ReplayStatus
        
        @dataclass
        class MockReplayResult:
            replay_id: str = "replay_123"
            original_recording_id: str = "rec_123"
            status: ReplayStatus = ReplayStatus.COMPLETED
            comparison: dict = None
            
            def __post_init__(self):
                if self.comparison is None:
                    self.comparison = {"similarity": 0.95}
        
        mock_recording = type('MockRecording', (), {
            'recording_id': 'rec_123',
            'query': 'Test query'
        })()
        
        mock_replay_result = MockReplayResult()
        
        with patch('backend.core.query_replay_harness.replay_harness') as mock_harness:
            mock_harness.load_recording.return_value = mock_recording
            mock_harness.replay_query = AsyncMock(return_value=mock_replay_result)
            
            response = self.client.post("/api/v1/replay/recordings/rec_123/replay")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "success"
            assert data["replay"]["replay_id"] == "replay_123"
    
    def test_replay_recording_not_found(self):
        """Test replaying a recording that doesn't exist."""
        with patch('backend.core.query_replay_harness.replay_harness') as mock_harness:
            mock_harness.load_recording.return_value = None
            
            response = self.client.post("/api/v1/replay/recordings/nonexistent/replay")
            assert response.status_code == 404
    
    def test_get_replay_stats_empty(self):
        """Test getting replay stats when no recordings exist."""
        with patch('backend.core.query_replay_harness.replay_harness') as mock_harness:
            mock_harness.list_recordings.return_value = []
            
            response = self.client.get("/api/v1/replay/stats")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "success"
            assert data["stats"]["total_recordings"] == 0
            assert data["stats"]["average_duration_ms"] == 0
    
    def test_get_replay_stats_with_data(self):
        """Test getting replay stats with sample data."""
        sample_recordings = [
            {
                "recording_id": "rec1",
                "duration_ms": 1000,
                "steps_count": 5,
                "tags": ["ai"]
            },
            {
                "recording_id": "rec2",
                "duration_ms": 2000,
                "steps_count": 7,
                "tags": ["ml", "ai"]
            }
        ]
        
        with patch('backend.core.query_replay_harness.replay_harness') as mock_harness:
            mock_harness.list_recordings.return_value = sample_recordings
            
            response = self.client.get("/api/v1/replay/stats")
            assert response.status_code == 200
            
            data = response.json()
            stats = data["stats"]
            
            assert stats["total_recordings"] == 2
            assert stats["total_duration_ms"] == 3000
            assert stats["average_duration_ms"] == 1500
            assert stats["total_steps"] == 12
            assert stats["average_steps"] == 6
            assert stats["tag_distribution"]["ai"] == 2
            assert stats["tag_distribution"]["ml"] == 1
    
    def test_delete_recording_success(self):
        """Test successfully deleting a recording."""
        import tempfile
        from pathlib import Path
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a mock recording file
            recording_file = Path(temp_dir) / "test_rec_2024-01-01.json"
            recording_file.write_text('{"recording_id": "test_rec"}')
            
            with patch('backend.core.query_replay_harness.replay_harness') as mock_harness:
                mock_harness.storage_path = Path(temp_dir)
                
                response = self.client.delete("/api/v1/replay/recordings/test_rec")
                assert response.status_code == 200
                
                data = response.json()
                assert data["status"] == "success"
                assert "deleted successfully" in data["message"]
    
    def test_delete_recording_not_found(self):
        """Test deleting a recording that doesn't exist."""
        import tempfile
        from pathlib import Path
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('backend.core.query_replay_harness.replay_harness') as mock_harness:
                mock_harness.storage_path = Path(temp_dir)
                
                response = self.client.delete("/api/v1/replay/recordings/nonexistent")
                assert response.status_code == 404
    
    def test_update_replay_settings(self):
        """Test updating replay harness settings."""
        with patch('backend.core.query_replay_harness.replay_harness') as mock_harness:
            mock_harness.enable_recording = True
            mock_harness.max_recordings = 1000
            mock_harness.auto_cleanup_days = 30
            
            response = self.client.post(
                "/api/v1/replay/settings",
                params={
                    "enable_recording": False,
                    "max_recordings": 500,
                    "auto_cleanup_days": 14
                }
            )
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "success"
            assert data["updated"]["enable_recording"] is False
            assert data["updated"]["max_recordings"] == 500
            assert data["updated"]["auto_cleanup_days"] == 14
    
    def test_analyze_recording(self):
        """Test analyzing a recording."""
        mock_recording = {
            "recording_id": "test_rec",
            "query": "Test query",
            "total_duration_ms": 2000,
            "steps": [
                {"step_type": "context_gathering", "duration_ms": 500},
                {"step_type": "cognitive_analysis", "duration_ms": 800},
                {"step_type": "response_generation", "duration_ms": 700}
            ]
        }
        
        with patch('backend.core.query_replay_harness.replay_harness') as mock_harness:
            mock_harness.load_recording.return_value = mock_recording
            
            response = self.client.post("/api/v1/replay/recordings/test_rec/analyze")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "success"
            assert "analysis" in data
            assert data["recording_id"] == "test_rec"
            
            analysis = data["analysis"]
            assert "performance" in analysis
            assert "cognitive_patterns" in analysis
            assert "efficiency_metrics" in analysis
            assert "insights" in analysis


class TestReplayAPIErrorHandling:
    """Test error handling in replay API endpoints."""
    
    def setup_method(self):
        """Set up test client."""
        if not FASTAPI_AVAILABLE:
            pytest.skip("FastAPI not available")
        
        self.app = FastAPI()
        from backend.api.replay_endpoints import setup_replay_endpoints
        setup_replay_endpoints(self.app, None)  # No cognitive manager
        self.client = TestClient(self.app)
    
    def test_replay_without_cognitive_manager(self):
        """Test replaying when cognitive manager is not available."""
        with patch('backend.core.query_replay_harness.replay_harness') as mock_harness:
            mock_harness.load_recording.return_value = {"recording_id": "test"}
            
            response = self.client.post("/api/v1/replay/recordings/test/replay")
            assert response.status_code == 503
    
    def test_internal_server_errors(self):
        """Test handling of internal server errors."""
        with patch('backend.core.query_replay_harness.replay_harness') as mock_harness:
            mock_harness.list_recordings.side_effect = Exception("Database error")
            
            response = self.client.get("/api/v1/replay/recordings")
            assert response.status_code == 500


class TestReplayAPIIntegration:
    """Integration tests that don't require actual FastAPI."""
    
    def test_endpoint_setup_function(self):
        """Test that the endpoint setup function works."""
        from backend.api.replay_endpoints import setup_replay_endpoints
        
        mock_app = type('MockApp', (), {
            'get': lambda *args, **kwargs: lambda fn: fn,
            'post': lambda *args, **kwargs: lambda fn: fn,
            'delete': lambda *args, **kwargs: lambda fn: fn
        })()
        
        mock_cognitive_manager = AsyncMock()
        
        # Should not raise any errors
        setup_replay_endpoints(mock_app, mock_cognitive_manager)
    
    def test_analysis_function(self):
        """Test the recording analysis function."""
        from backend.api.replay_endpoints import _analyze_recording
        
        sample_recording = {
            "recording_id": "test",
            "total_duration_ms": 5000,
            "steps": [
                {"step_type": "context_gathering", "duration_ms": 1000},
                {"step_type": "cognitive_analysis", "duration_ms": 2000, "error": "minor issue"},
                {"step_type": "response_generation", "duration_ms": 2000}
            ]
        }
        
        analysis = _analyze_recording(sample_recording)
        
        assert "performance" in analysis
        assert "cognitive_patterns" in analysis
        assert "efficiency_metrics" in analysis
        assert "insights" in analysis
        
        # Check performance metrics
        assert analysis["performance"]["total_duration_ms"] == 5000
        assert analysis["performance"]["steps_count"] == 3
        assert analysis["performance"]["average_step_duration_ms"] == 5000 / 3
        
        # Check cognitive patterns
        assert analysis["cognitive_patterns"]["error_count"] == 1
        
        # Check insights
        assert len(analysis["insights"]) > 0  # Should have some insights


def run_standalone_tests():
    """Run tests that don't require pytest."""
    print("Running standalone replay API tests...")
    
    # Test analysis function
    test_integration = TestReplayAPIIntegration()
    test_integration.test_analysis_function()
    print("✓ Analysis function test passed")
    
    test_integration.test_endpoint_setup_function()
    print("✓ Endpoint setup test passed")
    
    print("All standalone tests passed!")


if __name__ == "__main__":
    if FASTAPI_AVAILABLE:
        # Run with pytest if available
        import pytest
        pytest.main([__file__, "-v"])
    else:
        # Run standalone tests
        run_standalone_tests()
