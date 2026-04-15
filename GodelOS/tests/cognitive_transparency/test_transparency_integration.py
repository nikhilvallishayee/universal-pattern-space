"""
Integration tests for the cognitive transparency system.

Tests the complete flow from transparency manager through to API endpoints.
"""

import asyncio
import pytest
import time
from unittest.mock import Mock, AsyncMock

from godelOS.cognitive_transparency.manager import CognitiveTransparencyManager
from godelOS.cognitive_transparency.stream_tracker import ReasoningStreamTracker
from godelOS.cognitive_transparency.models import (
    ReasoningStep, StepType, TransparencyLevel, ReasoningStepBuilder
)
from backend.cognitive_transparency_integration import CognitiveTransparencyAPI


class TestCognitiveTransparencyIntegration:
    """Test suite for cognitive transparency integration."""
    
    @pytest.fixture
    async def transparency_manager(self):
        """Create a transparency manager for testing."""
        manager = CognitiveTransparencyManager()
        await manager.initialize()
        yield manager
        await manager.shutdown()
    
    @pytest.fixture
    def mock_websocket_manager(self):
        """Create a mock WebSocket manager."""
        mock_manager = Mock()
        mock_manager.broadcast_to_session = AsyncMock()
        mock_manager.broadcast_global = AsyncMock()
        return mock_manager
    
    @pytest.fixture
    async def transparency_api(self, mock_websocket_manager):
        """Create a transparency API for testing."""
        api = CognitiveTransparencyAPI()
        
        # Mock the websocket manager
        api.websocket_manager = mock_websocket_manager
        
        # Mock GödelOS integration
        mock_godelos = Mock()
        mock_godelos.kr_interface = Mock()
        mock_godelos.type_system = Mock()
        mock_godelos.metacognition_manager = Mock()
        
        await api.initialize(mock_godelos)
        yield api
        await api.shutdown()
    
    @pytest.mark.asyncio
    async def test_transparency_manager_initialization(self, transparency_manager):
        """Test that transparency manager initializes correctly."""
        assert transparency_manager.is_initialized
        assert transparency_manager.is_running
        assert transparency_manager.stream_tracker is not None
        assert transparency_manager.global_transparency_level == TransparencyLevel.STANDARD
    
    @pytest.mark.asyncio
    async def test_reasoning_session_lifecycle(self, transparency_manager):
        """Test the complete lifecycle of a reasoning session."""
        # Start a session
        session_id = await transparency_manager.start_reasoning_session(
            query="Test query",
            transparency_level=TransparencyLevel.DETAILED,
            context={"test": True}
        )
        
        assert session_id is not None
        assert session_id in transparency_manager.active_sessions
        
        # Get session info
        session_info = await transparency_manager.get_session_statistics(session_id)
        assert session_info is not None
        assert session_info["session_id"] == session_id
        
        # Emit some reasoning steps
        step1 = ReasoningStepBuilder() \
            .with_type(StepType.INFERENCE) \
            .with_description("Test inference step") \
            .with_confidence(0.8) \
            .build()
        
        await transparency_manager.emit_reasoning_step(step1, session_id)
        
        step2 = ReasoningStepBuilder() \
            .with_type(StepType.DECISION_MAKING) \
            .with_description("Test decision step") \
            .with_confidence(0.9) \
            .build()
        
        await transparency_manager.emit_reasoning_step(step2, session_id)
        
        # Complete the session
        await transparency_manager.complete_reasoning_session(session_id)
        
        # Verify session is completed
        assert session_id not in transparency_manager.active_sessions
        assert session_id in transparency_manager.completed_sessions
        
        # Get the trace
        trace = await transparency_manager.get_reasoning_trace(session_id)
        assert trace is not None
        assert len(trace["trace"]["steps"]) == 2
        assert trace["trace"]["summary"] is not None
    
    @pytest.mark.asyncio
    async def test_reasoning_step_importance_calculation(self, transparency_manager):
        """Test that reasoning step importance is calculated correctly."""
        session_id = await transparency_manager.start_reasoning_session(
            query="Importance test"
        )
        
        # High importance step (novel inference)
        high_importance_step = ReasoningStepBuilder() \
            .with_type(StepType.NOVEL_INFERENCE) \
            .with_description("Novel discovery") \
            .with_confidence(0.7) \
            .build()
        
        await transparency_manager.emit_reasoning_step(high_importance_step, session_id)
        
        # Low importance step (cache hit)
        low_importance_step = ReasoningStepBuilder() \
            .with_type(StepType.CACHE_HIT) \
            .with_description("Cache retrieval") \
            .with_confidence(1.0) \
            .build()
        
        await transparency_manager.emit_reasoning_step(low_importance_step, session_id)
        
        await transparency_manager.complete_reasoning_session(session_id)
        
        # Verify importance scores were calculated
        trace = await transparency_manager.get_reasoning_trace(session_id)
        steps = trace["trace"]["steps"]
        
        # Find the steps by type
        novel_step = next(s for s in steps if s["step_type"] == "novel_inference")
        cache_step = next(s for s in steps if s["step_type"] == "cache_hit")
        
        assert novel_step["importance_score"] > cache_step["importance_score"]
        assert novel_step["detail_level"] == "high"
        assert cache_step["detail_level"] == "low"
    
    @pytest.mark.asyncio
    async def test_transparency_level_configuration(self, transparency_manager):
        """Test transparency level configuration."""
        # Change global transparency level
        await transparency_manager.configure_transparency_level(TransparencyLevel.MAXIMUM)
        assert transparency_manager.global_transparency_level == TransparencyLevel.MAXIMUM
        
        # Start session with different level
        session_id = await transparency_manager.start_reasoning_session(
            query="Level test",
            transparency_level=TransparencyLevel.MINIMAL
        )
        
        session = transparency_manager.active_sessions[session_id]
        assert session.transparency_level == TransparencyLevel.MINIMAL
        
        await transparency_manager.complete_reasoning_session(session_id)
    
    @pytest.mark.asyncio
    async def test_stream_tracker_buffering(self, transparency_manager):
        """Test that stream tracker properly buffers and flushes steps."""
        session_id = await transparency_manager.start_reasoning_session(
            query="Buffering test"
        )
        
        # Emit multiple low-importance steps quickly
        for i in range(5):
            step = ReasoningStepBuilder() \
                .with_type(StepType.SIMPLE_UNIFICATION) \
                .with_description(f"Simple step {i}") \
                .with_confidence(1.0) \
                .build()
            
            await transparency_manager.emit_reasoning_step(step, session_id)
        
        # Emit one high-importance step (should flush immediately)
        important_step = ReasoningStepBuilder() \
            .with_type(StepType.CONTRADICTION_RESOLUTION) \
            .with_description("Critical step") \
            .with_confidence(0.6) \
            .build()
        
        await transparency_manager.emit_reasoning_step(important_step, session_id)
        
        await transparency_manager.complete_reasoning_session(session_id)
        
        # Verify all steps were tracked
        trace = await transparency_manager.get_reasoning_trace(session_id)
        assert len(trace["trace"]["steps"]) == 6
    
    @pytest.mark.asyncio
    async def test_api_session_management(self, transparency_api):
        """Test API session management endpoints."""
        from backend.cognitive_transparency_integration import (
            ReasoningSessionRequest, TransparencyConfigRequest
        )
        
        # Test session start
        request = ReasoningSessionRequest(
            query="API test query",
            transparency_level="detailed",
            context={"api_test": True}
        )
        
        response = await transparency_api._start_reasoning_session(request)
        assert response.status == "started"
        session_id = response.session_id
        
        # Test getting active sessions
        active_sessions = await transparency_api._get_active_sessions()
        assert active_sessions["count"] == 1
        assert any(s["session_id"] == session_id for s in active_sessions["active_sessions"])
        
        # Test session statistics
        stats = await transparency_api._get_session_statistics(session_id)
        assert stats["session_id"] == session_id
        
        # Test session completion
        completion_response = await transparency_api._complete_reasoning_session(session_id)
        assert completion_response["success"] is True
        
        # Verify session is no longer active
        active_sessions = await transparency_api._get_active_sessions()
        assert active_sessions["count"] == 0
    
    @pytest.mark.asyncio
    async def test_api_transparency_configuration(self, transparency_api):
        """Test API transparency configuration."""
        from backend.cognitive_transparency_integration import TransparencyConfigRequest
        
        # Test global configuration
        config_request = TransparencyConfigRequest(
            transparency_level="maximum",
            session_specific=False
        )
        
        response = await transparency_api._configure_transparency(config_request)
        assert response["success"] is True
        assert response["transparency_level"] == "maximum"
        
        # Test statistics
        stats_response = await transparency_api._get_transparency_statistics()
        assert stats_response.transparency_level == "maximum"
        assert stats_response.active_sessions == 0
    
    @pytest.mark.asyncio
    async def test_websocket_broadcasting(self, transparency_api, mock_websocket_manager):
        """Test WebSocket broadcasting functionality."""
        # Start a session
        from backend.cognitive_transparency_integration import ReasoningSessionRequest
        
        request = ReasoningSessionRequest(query="WebSocket test")
        response = await transparency_api._start_reasoning_session(request)
        session_id = response.session_id
        
        # Simulate emitting a step (this would trigger WebSocket broadcast)
        step = ReasoningStepBuilder() \
            .with_type(StepType.INFERENCE) \
            .with_description("WebSocket test step") \
            .build()
        
        await transparency_api.transparency_manager.emit_reasoning_step(step, session_id)
        
        # Complete session
        await transparency_api._complete_reasoning_session(session_id)
        
        # Verify WebSocket manager was called
        assert mock_websocket_manager.broadcast_to_session.called
    
    def test_reasoning_step_builder(self):
        """Test the ReasoningStepBuilder functionality."""
        step = ReasoningStepBuilder() \
            .with_type(StepType.ANALOGICAL_REASONING) \
            .with_description("Test analogical reasoning") \
            .with_input({"source": "A", "target": "B"}) \
            .with_output({"mapping": "A->B"}) \
            .with_confidence(0.85) \
            .with_importance(0.7) \
            .with_context({"domain": "mathematics"}) \
            .build()
        
        assert step.step_type == StepType.ANALOGICAL_REASONING
        assert step.description == "Test analogical reasoning"
        assert step.confidence == 0.85
        assert step.importance_score == 0.7
        assert step.input_data["source"] == "A"
        assert step.output_data["mapping"] == "A->B"
        assert step.context["domain"] == "mathematics"
    
    @pytest.mark.asyncio
    async def test_performance_metrics(self, transparency_manager):
        """Test that performance metrics are collected correctly."""
        session_id = await transparency_manager.start_reasoning_session(
            query="Performance test"
        )
        
        # Emit steps with different processing times
        for i in range(3):
            step = ReasoningStepBuilder() \
                .with_type(StepType.INFERENCE) \
                .with_description(f"Performance step {i}") \
                .build()
            
            # Simulate processing time
            step.processing_time_ms = (i + 1) * 10
            
            await transparency_manager.emit_reasoning_step(step, session_id)
        
        await transparency_manager.complete_reasoning_session(session_id)
        
        # Check global statistics
        global_stats = transparency_manager.get_global_statistics()
        assert global_stats["total_sessions"] >= 1
        assert global_stats["total_steps_tracked"] >= 3
        
        # Check session statistics
        session_stats = await transparency_manager.get_session_statistics(session_id)
        assert session_stats["total_steps"] == 3


if __name__ == "__main__":
    # Run a simple test
    async def run_simple_test():
        """Run a simple integration test."""
        print("Running cognitive transparency integration test...")
        
        manager = CognitiveTransparencyManager()
        await manager.initialize()
        
        try:
            # Start session
            session_id = await manager.start_reasoning_session(
                query="Simple test query",
                transparency_level=TransparencyLevel.STANDARD
            )
            print(f"Started session: {session_id}")
            
            # Emit some steps
            step1 = ReasoningStepBuilder() \
                .with_type(StepType.INFERENCE) \
                .with_description("Test inference") \
                .with_confidence(0.9) \
                .build()
            
            await manager.emit_reasoning_step(step1, session_id)
            print("Emitted reasoning step")
            
            # Complete session
            await manager.complete_reasoning_session(session_id)
            print("Completed session")
            
            # Get trace
            trace = await manager.get_reasoning_trace(session_id)
            print(f"Retrieved trace with {len(trace['trace']['steps'])} steps")
            
            print("✅ Integration test passed!")
            
        finally:
            await manager.shutdown()
    
    asyncio.run(run_simple_test())