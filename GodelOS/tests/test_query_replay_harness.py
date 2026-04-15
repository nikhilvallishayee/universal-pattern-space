"""
Comprehensive tests for Query Replay Harness functionality.

Tests recording, replay, comparison, and API functionality.
"""

import asyncio
import json
import pytest
import tempfile
import uuid
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock, patch

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.core.query_replay_harness import (
    QueryReplayHarness,
    ProcessingStep,
    RecordedStep,
    QueryRecording,
    ReplayResult,
    ReplayStatus,
    replay_harness
)


class TestQueryReplayHarness:
    """Test the core QueryReplayHarness functionality."""
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory for tests."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def harness(self, temp_storage):
        """Create a QueryReplayHarness instance for testing."""
        harness = QueryReplayHarness(storage_path=temp_storage)
        harness.enable_recording = True
        return harness
    
    @pytest.fixture
    def mock_cognitive_manager(self):
        """Create a mock cognitive manager."""
        manager = AsyncMock()
        manager.process_query = AsyncMock(return_value={
            "response": "Test response",
            "reasoning": "Test reasoning",
            "confidence": 0.85,
            "sources": ["source1", "source2"]
        })
        return manager
    
    def test_processing_step_enum(self):
        """Test ProcessingStep enum values."""
        assert ProcessingStep.QUERY_RECEIVED.value == "query_received"
        assert ProcessingStep.CONTEXT_GATHERING.value == "context_gathering"
        assert ProcessingStep.COGNITIVE_ANALYSIS.value == "cognitive_analysis"
        assert ProcessingStep.KNOWLEDGE_RETRIEVAL.value == "knowledge_retrieval"
        assert ProcessingStep.REASONING_PROCESS.value == "reasoning_process"
        assert ProcessingStep.RESPONSE_GENERATION.value == "response_generation"
        assert ProcessingStep.QUALITY_ASSURANCE.value == "quality_assurance"
        assert ProcessingStep.RESPONSE_COMPLETE.value == "response_complete"
    
    def test_harness_initialization(self, temp_storage):
        """Test harness initialization."""
        harness = QueryReplayHarness(storage_path=temp_storage)
        
        assert harness.storage_path == temp_storage
        assert harness.enable_recording is True
        assert harness.max_recordings == 1000
        assert harness.auto_cleanup_days == 30
        assert harness.active_recordings == {}
        assert harness.replay_results == {}
    
    @pytest.mark.asyncio
    async def test_start_recording(self, harness):
        """Test starting a new recording."""
        query = "What is consciousness?"
        correlation_id = str(uuid.uuid4())
        
        recording_id = await harness.start_recording(
            query=query,
            correlation_id=correlation_id,
            metadata={"test": True}
        )
        
        assert recording_id is not None
        assert recording_id in harness.active_recordings
        
        recording = harness.active_recordings[recording_id]
        assert recording.query == query
        assert recording.correlation_id == correlation_id
        assert recording.metadata["test"] is True
        assert len(recording.steps) == 0
    
    @pytest.mark.asyncio
    async def test_record_step(self, harness):
        """Test recording processing steps."""
        # Start recording
        recording_id = await harness.start_recording("Test query")
        
        # Record a step
        await harness.record_step(
            recording_id=recording_id,
            step_type=ProcessingStep.CONTEXT_GATHERING,
            data={"context": "test context"},
            duration_ms=150
        )
        
        recording = harness.active_recordings[recording_id]
        assert len(recording.steps) == 1
        
        step = recording.steps[0]
        assert step.step_type == ProcessingStep.CONTEXT_GATHERING
        assert step.data["context"] == "test context"
        assert step.duration_ms == 150
        assert step.error is None
    
    @pytest.mark.asyncio
    async def test_record_step_with_error(self, harness):
        """Test recording steps with errors."""
        recording_id = await harness.start_recording("Test query")
        
        error_msg = "Test error occurred"
        await harness.record_step(
            recording_id=recording_id,
            step_type=ProcessingStep.COGNITIVE_ANALYSIS,
            data={"analysis": "partial"},
            duration_ms=200,
            error=error_msg
        )
        
        recording = harness.active_recordings[recording_id]
        step = recording.steps[0]
        assert step.error == error_msg
    
    @pytest.mark.asyncio
    async def test_complete_recording(self, harness):
        """Test completing and saving a recording."""
        recording_id = await harness.start_recording("Test query")
        
        # Record some steps
        await harness.record_step(
            recording_id, ProcessingStep.CONTEXT_GATHERING, {"context": "test"}
        )
        await harness.record_step(
            recording_id, ProcessingStep.RESPONSE_GENERATION, {"response": "test response"}
        )
        
        # Complete recording
        final_result = {"response": "Final response", "confidence": 0.9}
        await harness.complete_recording(recording_id, final_result)
        
        # Recording should be saved and removed from active
        assert recording_id not in harness.active_recordings
        
        # Check saved file exists
        saved_files = list(harness.storage_path.glob(f"{recording_id}_*.json"))
        assert len(saved_files) == 1
        
        # Load and verify saved recording
        with open(saved_files[0], 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data["recording_id"] == recording_id
        assert saved_data["final_response"] == final_result
        assert len(saved_data["steps"]) == 2
    
    @pytest.mark.asyncio
    async def test_load_recording(self, harness):
        """Test loading a saved recording."""
        # Create and complete a recording
        recording_id = await harness.start_recording("Test query")
        await harness.record_step(recording_id, ProcessingStep.CONTEXT_GATHERING, {"test": "data"})
        await harness.complete_recording(recording_id, {"result": "test"})
        
        # Load the recording
        loaded_recording = harness.load_recording(recording_id)
        
        assert loaded_recording is not None
        assert loaded_recording.recording_id == recording_id
        assert loaded_recording.query == "Test query"
        assert len(loaded_recording.steps) == 1
        assert loaded_recording.final_response["result"] == "test"
    
    @pytest.mark.asyncio
    async def test_replay_query(self, harness, mock_cognitive_manager):
        """Test replaying a recorded query."""
        # Create a recording
        recording_id = await harness.start_recording("What is AI?")
        await harness.record_step(
            recording_id, ProcessingStep.CONTEXT_GATHERING, {"context": "AI context"}
        )
        original_result = {"response": "AI is artificial intelligence", "confidence": 0.8}
        await harness.complete_recording(recording_id, original_result)
        
        # Replay the query
        replay_result = await harness.replay_query(
            recording_id=recording_id,
            cognitive_manager=mock_cognitive_manager,
            compare_results=True
        )
        
        assert replay_result is not None
        assert replay_result.original_recording_id == recording_id
        assert replay_result.status == ReplayStatus.COMPLETED
        
        # Verify cognitive manager was called
        mock_cognitive_manager.process_query.assert_called_once()
        call_args = mock_cognitive_manager.process_query.call_args
        assert call_args[1]["query"] == "What is AI?"
    
    def test_list_recordings(self, harness):
        """Test listing recordings with filters."""
        # Create test recordings data
        recordings_data = [
            {
                "recording_id": "rec1",
                "query": "Test 1",
                "timestamp": "2024-01-01T10:00:00",
                "tags": ["test", "ai"],
                "duration_ms": 1000
            },
            {
                "recording_id": "rec2", 
                "query": "Test 2",
                "timestamp": "2024-01-01T11:00:00",
                "tags": ["test", "ml"],
                "duration_ms": 1500
            },
            {
                "recording_id": "rec3",
                "query": "Test 3", 
                "timestamp": "2024-01-01T12:00:00",
                "tags": ["production"],
                "duration_ms": 800
            }
        ]
        
        # Save test recordings
        for data in recordings_data:
            filepath = harness.storage_path / f"{data['recording_id']}_{data['timestamp'].replace(':', '-')}.json"
            with open(filepath, 'w') as f:
                json.dump(data, f)
        
        # Test listing all
        all_recordings = harness.list_recordings()
        assert len(all_recordings) == 3
        
        # Test filtering by tags
        test_recordings = harness.list_recordings(tags=["test"])
        assert len(test_recordings) == 2
        
        ai_recordings = harness.list_recordings(tags=["ai"])
        assert len(ai_recordings) == 1
        assert ai_recordings[0]["recording_id"] == "rec1"
        
        # Test limit
        limited = harness.list_recordings(limit=2)
        assert len(limited) == 2
    
    @pytest.mark.asyncio
    async def test_compare_results(self, harness):
        """Test result comparison functionality."""
        original = {
            "response": "Original response",
            "confidence": 0.8,
            "sources": ["source1", "source2"]
        }
        
        replay = {
            "response": "Modified response", 
            "confidence": 0.85,
            "sources": ["source1", "source3"]
        }
        
        comparison = harness._compare_results(original, replay)
        
        assert "response_similarity" in comparison
        assert "confidence_diff" in comparison
        assert "sources_overlap" in comparison
        assert "key_differences" in comparison
        
        assert comparison["confidence_diff"] == 0.05  # 0.85 - 0.8
        assert comparison["sources_overlap"] == 0.5  # 1/2 overlap
    
    @pytest.mark.asyncio 
    async def test_recording_disabled(self, harness):
        """Test that recording can be disabled."""
        harness.enable_recording = False
        
        recording_id = await harness.start_recording("Test query")
        assert recording_id is None
        
        # Should not raise error but do nothing
        await harness.record_step("fake_id", ProcessingStep.CONTEXT_GATHERING, {})
        await harness.complete_recording("fake_id", {})
    
    def test_cleanup_old_recordings(self, harness):
        """Test automatic cleanup of old recordings."""
        # This would need mock datetime to properly test
        # For now, just test the method exists and doesn't crash
        harness.cleanup_old_recordings()
        
        # Test with specific age
        harness.cleanup_old_recordings(max_age_days=7)


class TestReplayHarnessIntegration:
    """Test integration with other system components."""
    
    @pytest.fixture
    def mock_app(self):
        """Create a mock FastAPI app."""
        from fastapi import FastAPI
        return FastAPI()
    
    @pytest.mark.asyncio
    async def test_api_endpoints_setup(self, mock_app):
        """Test that API endpoints can be set up."""
        from backend.api.replay_endpoints import setup_replay_endpoints
        
        mock_cognitive_manager = AsyncMock()
        
        # Should not raise error
        setup_replay_endpoints(mock_app, mock_cognitive_manager)
        
        # Check that routes were added
        route_paths = [route.path for route in mock_app.routes]
        
        expected_paths = [
            "/api/v1/replay/recordings",
            "/api/v1/replay/recordings/{recording_id}",
            "/api/v1/replay/recordings/{recording_id}/replay",
            "/api/v1/replay/replays/{replay_id}/status",
            "/api/v1/replay/recordings/{recording_id}/analyze",
            "/api/v1/replay/stats",
            "/api/v1/replay/recordings/{recording_id}",  # DELETE
            "/api/v1/replay/settings"
        ]
        
        for expected_path in expected_paths:
            # Check if any route matches the expected pattern
            assert any(expected_path.replace("{recording_id}", "test").replace("{replay_id}", "test") 
                      in path.replace("{recording_id}", "test").replace("{replay_id}", "test") 
                      for path in route_paths), f"Missing route: {expected_path}"


class TestReplayHarnessErrors:
    """Test error handling in replay harness."""
    
    @pytest.fixture
    def temp_storage(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def harness(self, temp_storage):
        return QueryReplayHarness(storage_path=temp_storage)
    
    @pytest.mark.asyncio
    async def test_record_step_invalid_recording(self, harness):
        """Test recording step with invalid recording ID."""
        # Should not raise error, just log warning
        await harness.record_step(
            "invalid_id", ProcessingStep.CONTEXT_GATHERING, {"test": "data"}
        )
    
    @pytest.mark.asyncio
    async def test_complete_invalid_recording(self, harness):
        """Test completing invalid recording."""
        # Should not raise error, just log warning
        await harness.complete_recording("invalid_id", {"result": "test"})
    
    def test_load_nonexistent_recording(self, harness):
        """Test loading a recording that doesn't exist."""
        result = harness.load_recording("nonexistent_id")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_replay_nonexistent_recording(self, harness):
        """Test replaying a recording that doesn't exist."""
        mock_cognitive_manager = AsyncMock()
        
        result = await harness.replay_query(
            "nonexistent_id", mock_cognitive_manager
        )
        assert result is None


class TestGlobalReplayHarness:
    """Test the global replay harness instance."""
    
    def test_global_instance_exists(self):
        """Test that global replay harness instance exists."""
        from backend.core.query_replay_harness import replay_harness
        
        assert replay_harness is not None
        assert isinstance(replay_harness, QueryReplayHarness)
    
    @pytest.mark.asyncio
    async def test_global_instance_functional(self):
        """Test that global instance is functional."""
        from backend.core.query_replay_harness import replay_harness
        
        # Should be able to start recording
        recording_id = await replay_harness.start_recording("Global test")
        
        if recording_id:  # Only if recording is enabled
            assert recording_id in replay_harness.active_recordings
            
            # Clean up
            await replay_harness.complete_recording(recording_id, {"test": "cleanup"})


@pytest.mark.asyncio
async def test_end_to_end_workflow():
    """Test complete end-to-end replay workflow."""
    with tempfile.TemporaryDirectory() as temp_dir:
        harness = QueryReplayHarness(storage_path=Path(temp_dir))
        harness.enable_recording = True
        
        # Create mock cognitive manager
        mock_manager = AsyncMock()
        mock_manager.process_query = AsyncMock(return_value={
            "response": "Test response",
            "confidence": 0.9
        })
        
        # 1. Start recording
        recording_id = await harness.start_recording(
            query="What is machine learning?",
            correlation_id=str(uuid.uuid4()),
            metadata={"test": "e2e"}
        )
        assert recording_id is not None
        
        # 2. Record several steps
        await harness.record_step(
            recording_id, ProcessingStep.CONTEXT_GATHERING,
            {"context": "ML context"}, duration_ms=100
        )
        await harness.record_step(
            recording_id, ProcessingStep.COGNITIVE_ANALYSIS,
            {"analysis": "ML analysis"}, duration_ms=200
        )
        await harness.record_step(
            recording_id, ProcessingStep.RESPONSE_GENERATION,
            {"response": "ML is..."}, duration_ms=150
        )
        
        # 3. Complete recording
        original_result = {"response": "ML is machine learning", "confidence": 0.85}
        await harness.complete_recording(recording_id, original_result)
        
        # 4. Verify recording was saved
        saved_recording = harness.load_recording(recording_id)
        assert saved_recording is not None
        assert len(saved_recording.steps) == 3
        
        # 5. Replay the query
        replay_result = await harness.replay_query(
            recording_id, mock_manager, compare_results=True
        )
        assert replay_result is not None
        assert replay_result.status == ReplayStatus.COMPLETED
        
        # 6. Verify replay result has comparison
        assert replay_result.comparison is not None
        
        # 7. List recordings
        recordings = harness.list_recordings()
        assert len(recordings) >= 1
        assert any(r["recording_id"] == recording_id for r in recordings)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
