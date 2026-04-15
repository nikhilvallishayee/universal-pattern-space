"""
GödelOS Integration Tests for Backend

Comprehensive test suite for GödelOS core system integration including:
- Cognitive architecture functionality
- Natural language processing
- Inference engine operations
- Knowledge base integration
- Metacognitive processes
- System health and monitoring
"""

import asyncio
import json
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch

# Import the modules to test
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.godelos_integration import GödelOSIntegration


class TestGödelOSIntegration:
    """Test GödelOS system integration functionality."""
    
    def setup_method(self):
        """Set up GödelOS integration for each test."""
        self.integration = GödelOSIntegration()
    
    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test GödelOS system initialization."""
        with patch.object(self.integration, '_initialize_cognitive_systems', AsyncMock()):
            with patch.object(self.integration, '_initialize_knowledge_base', AsyncMock()):
                with patch.object(self.integration, '_start_background_processes', AsyncMock()):
                    await self.integration.initialize()
                    
                    assert self.integration.initialized is True
                    assert self.integration.start_time is not None
    
    @pytest.mark.asyncio
    async def test_health_status_healthy(self):
        """Test health status when system is healthy."""
        # Mock healthy subsystems
        with patch.object(self.integration, '_check_inference_engine', AsyncMock(return_value=True)):
            with patch.object(self.integration, '_check_knowledge_base', AsyncMock(return_value=True)):
                with patch.object(self.integration, '_check_cognitive_layers', AsyncMock(return_value=True)):
                    
                    health_status = await self.integration.get_health_status()
                    
                    assert health_status["healthy"] is True
                    assert health_status["components"]["inference_engine"] is True
                    assert health_status["components"]["knowledge_base"] is True
                    assert health_status["components"]["cognitive_layers"] is True
                    assert health_status["error_count"] == 0
                    assert "uptime_seconds" in health_status
    
    @pytest.mark.asyncio
    async def test_health_status_unhealthy(self):
        """Test health status when system has issues."""
        # Mock unhealthy subsystems
        with patch.object(self.integration, '_check_inference_engine', AsyncMock(return_value=False)):
            with patch.object(self.integration, '_check_knowledge_base', AsyncMock(return_value=True)):
                with patch.object(self.integration, '_check_cognitive_layers', AsyncMock(return_value=True)):
                    
                    # Simulate some errors
                    self.integration.error_count = 3
                    
                    health_status = await self.integration.get_health_status()
                    
                    assert health_status["healthy"] is False
                    assert health_status["components"]["inference_engine"] is False
                    assert health_status["error_count"] == 3
    
    @pytest.mark.asyncio
    async def test_natural_language_query_processing(self):
        """Test natural language query processing."""
        query = "What is machine learning?"
        
        # Mock the various processing stages
        with patch.object(self.integration, '_parse_natural_language', AsyncMock(return_value={
            "intent": "definition_request",
            "entities": [{"text": "machine learning", "type": "concept"}],
            "confidence": 0.9
        })):
            with patch.object(self.integration, '_retrieve_relevant_knowledge', AsyncMock(return_value=[
                {"id": "ml_def", "content": "Machine learning is a subset of AI", "confidence": 0.95}
            ])):
                with patch.object(self.integration, '_generate_response', AsyncMock(return_value={
                    "response": "Machine learning is a subset of artificial intelligence that focuses on algorithms.",
                    "confidence": 0.92
                })):
                    
                    result = await self.integration.process_natural_language_query(
                        query, 
                        include_reasoning=True
                    )
                    
                    assert "response" in result
                    assert "confidence" in result
                    assert "reasoning_steps" in result
                    assert "inference_time_ms" in result
                    assert result["confidence"] > 0.0
                    assert len(result["response"]) > 0
    
    @pytest.mark.asyncio
    async def test_query_with_context(self):
        """Test query processing with context."""
        query = "How does it work?"
        context = {"previous_topic": "neural networks", "domain": "machine_learning"}
        
        with patch.object(self.integration, '_parse_natural_language', AsyncMock(return_value={
            "intent": "explanation_request",
            "entities": [],
            "confidence": 0.8,
            "context_resolved": True
        })):
            with patch.object(self.integration, '_retrieve_relevant_knowledge', AsyncMock(return_value=[
                {"id": "nn_explanation", "content": "Neural networks work by...", "confidence": 0.9}
            ])):
                with patch.object(self.integration, '_generate_response', AsyncMock(return_value={
                    "response": "Neural networks work by processing information through interconnected nodes.",
                    "confidence": 0.88
                })):
                    
                    result = await self.integration.process_natural_language_query(
                        query,
                        context=context,
                        include_reasoning=True
                    )
                    
                    assert result["response"] is not None
                    assert "neural networks" in result["response"].lower()
    
    @pytest.mark.asyncio
    async def test_knowledge_operations(self):
        """Test knowledge base operations."""
        # Test adding knowledge
        knowledge_content = "Python is a programming language"
        knowledge_type = "fact"
        
        with patch.object(self.integration, '_validate_knowledge', AsyncMock(return_value=True)):
            with patch.object(self.integration, '_store_knowledge', AsyncMock(return_value="fact_123")):
                with patch.object(self.integration, '_update_knowledge_graph', AsyncMock()):
                    
                    add_result = await self.integration.add_knowledge(
                        content=knowledge_content,
                        knowledge_type=knowledge_type,
                        context_id="programming"
                    )
                    
                    assert add_result["status"] == "success"
                    assert "knowledge_id" in add_result or "message" in add_result
        
        # Test retrieving knowledge
        with patch.object(self.integration, '_query_knowledge_base', AsyncMock(return_value={
            "facts": [{"id": "fact_123", "content": knowledge_content}],
            "rules": [],
            "concepts": [],
            "total_count": 1
        })):
            
            knowledge_result = await self.integration.get_knowledge(
                knowledge_type="fact",
                limit=10
            )
            
            assert "facts" in knowledge_result
            assert "total_count" in knowledge_result
            assert knowledge_result["total_count"] >= 0
    
    @pytest.mark.asyncio
    async def test_cognitive_state_monitoring(self):
        """Test cognitive state monitoring."""
        with patch.object(self.integration, '_get_manifest_consciousness', AsyncMock(return_value={
            "current_focus": "Processing query",
            "awareness_level": 0.8,
            "coherence_level": 0.9
        })):
            with patch.object(self.integration, '_get_agentic_processes', AsyncMock(return_value=[
                {
                    "process_id": "inference_1",
                    "process_type": "logical_inference",
                    "status": "active",
                    "priority": 5,
                    "progress": 0.7
                }
            ])):
                with patch.object(self.integration, '_get_daemon_threads', AsyncMock(return_value=[
                    {
                        "process_id": "memory_consolidation",
                        "process_type": "background_learning",
                        "status": "running",
                        "priority": 2,
                        "progress": 0.4
                    }
                ])):
                    
                    cognitive_state = await self.integration.get_cognitive_state()
                    
                    assert "manifest_consciousness" in cognitive_state
                    assert "agentic_processes" in cognitive_state
                    assert "daemon_threads" in cognitive_state
                    assert "working_memory" in cognitive_state
                    assert "attention_focus" in cognitive_state
                    assert "metacognitive_state" in cognitive_state
                    
                    # Verify structure
                    manifest = cognitive_state["manifest_consciousness"]
                    assert "awareness_level" in manifest
                    assert 0.0 <= manifest["awareness_level"] <= 1.0
    
    @pytest.mark.asyncio
    async def test_inference_engine_operations(self):
        """Test inference engine operations."""
        premises = ["All humans are mortal", "Socrates is human"]
        
        with patch.object(self.integration, '_parse_logical_statements', AsyncMock(return_value=[
            {"type": "universal", "subject": "humans", "predicate": "mortal"},
            {"type": "assertion", "subject": "Socrates", "predicate": "human"}
        ])):
            with patch.object(self.integration, '_apply_inference_rules', AsyncMock(return_value=[
                {
                    "rule": "modus_ponens",
                    "conclusion": "Socrates is mortal",
                    "confidence": 1.0,
                    "step": 1
                }
            ])):
                
                inference_result = await self.integration.perform_logical_inference(premises)
                
                assert "conclusions" in inference_result
                assert "reasoning_chain" in inference_result
                assert "confidence" in inference_result
                assert len(inference_result["conclusions"]) > 0
    
    @pytest.mark.asyncio
    async def test_metacognitive_monitoring(self):
        """Test metacognitive monitoring capabilities."""
        with patch.object(self.integration, '_assess_reasoning_quality', AsyncMock(return_value=0.85)):
            with patch.object(self.integration, '_monitor_cognitive_load', AsyncMock(return_value=0.6)):
                with patch.object(self.integration, '_evaluate_learning_progress', AsyncMock(return_value=0.7)):
                    
                    metacognitive_state = await self.integration.get_metacognitive_state()
                    
                    assert "self_awareness_level" in metacognitive_state
                    assert "confidence_in_reasoning" in metacognitive_state
                    assert "cognitive_load" in metacognitive_state
                    assert "learning_rate" in metacognitive_state
                    assert "adaptation_level" in metacognitive_state
                    
                    # All values should be between 0 and 1
                    for key, value in metacognitive_state.items():
                        if isinstance(value, (int, float)):
                            assert 0.0 <= value <= 1.0
    
    @pytest.mark.asyncio
    async def test_knowledge_graph_operations(self):
        """Test knowledge graph operations."""
        with patch.object(self.integration, '_build_knowledge_graph', AsyncMock(return_value={
            "nodes": [
                {"id": "python", "type": "concept", "label": "Python"},
                {"id": "programming", "type": "concept", "label": "Programming"}
            ],
            "edges": [
                {"source": "python", "target": "programming", "type": "is_a", "weight": 0.9}
            ]
        })):
            
            graph_data = await self.integration.get_knowledge_graph()
            
            assert "nodes" in graph_data
            assert "edges" in graph_data
            assert len(graph_data["nodes"]) > 0
            
            # Verify node structure
            node = graph_data["nodes"][0]
            assert "id" in node
            assert "type" in node
            assert "label" in node
            
            # Verify edge structure if edges exist
            if graph_data["edges"]:
                edge = graph_data["edges"][0]
                assert "source" in edge
                assert "target" in edge
                assert "type" in edge
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in various operations."""
        # Test query processing error
        with patch.object(self.integration, '_parse_natural_language', 
                         AsyncMock(side_effect=Exception("Parsing failed"))):
            
            with pytest.raises(Exception):
                await self.integration.process_natural_language_query("invalid query")
            
            # Error count should increase
            assert self.integration.error_count > 0
        
        # Test knowledge operation error
        with patch.object(self.integration, '_validate_knowledge',
                         AsyncMock(side_effect=Exception("Validation failed"))):
            
            with pytest.raises(Exception):
                await self.integration.add_knowledge("invalid content", "invalid_type")
    
    @pytest.mark.asyncio
    async def test_performance_monitoring(self):
        """Test performance monitoring and metrics."""
        # Mock performance data
        with patch.object(self.integration, '_get_performance_metrics', AsyncMock(return_value={
            "query_processing_time_avg": 250.5,
            "memory_usage_mb": 512.8,
            "cpu_usage_percent": 45.3,
            "active_processes": 8,
            "cache_hit_ratio": 0.85
        })):
            
            performance = await self.integration.get_performance_metrics()
            
            assert "query_processing_time_avg" in performance
            assert "memory_usage_mb" in performance
            assert "cpu_usage_percent" in performance
            assert "active_processes" in performance
            assert "cache_hit_ratio" in performance
            
            # Verify reasonable values
            assert performance["query_processing_time_avg"] > 0
            assert performance["memory_usage_mb"] > 0
            assert 0 <= performance["cpu_usage_percent"] <= 100
            assert performance["active_processes"] >= 0
            assert 0 <= performance["cache_hit_ratio"] <= 1
    
    @pytest.mark.asyncio
    async def test_learning_and_adaptation(self):
        """Test learning and adaptation capabilities."""
        feedback_data = {
            "query": "What is AI?",
            "response": "AI is artificial intelligence",
            "user_satisfaction": 0.8,
            "correctness": 0.9
        }
        
        with patch.object(self.integration, '_process_feedback', AsyncMock(return_value={
            "learning_applied": True,
            "adaptation_level": 0.1,
            "confidence_adjustment": 0.05
        })):
            
            learning_result = await self.integration.process_learning_feedback(feedback_data)
            
            assert "learning_applied" in learning_result
            assert "adaptation_level" in learning_result
            assert learning_result["learning_applied"] is True
    
    @pytest.mark.asyncio
    async def test_reasoning_transparency(self):
        """Test reasoning transparency and explainability."""
        query = "Why is the sky blue?"
        
        with patch.object(self.integration, '_generate_reasoning_explanation', AsyncMock(return_value={
            "reasoning_steps": [
                {
                    "step": 1,
                    "operation": "knowledge_retrieval",
                    "description": "Retrieved information about light scattering",
                    "confidence": 0.9
                },
                {
                    "step": 2,
                    "operation": "causal_reasoning",
                    "description": "Applied Rayleigh scattering principles",
                    "confidence": 0.85
                }
            ],
            "confidence_chain": [0.9, 0.85],
            "final_confidence": 0.87
        })):
            
            explanation = await self.integration.explain_reasoning(query)
            
            assert "reasoning_steps" in explanation
            assert "confidence_chain" in explanation
            assert "final_confidence" in explanation
            assert len(explanation["reasoning_steps"]) > 0
            
            # Verify reasoning step structure
            step = explanation["reasoning_steps"][0]
            assert "step" in step
            assert "operation" in step
            assert "description" in step
            assert "confidence" in step
    
    @pytest.mark.asyncio
    async def test_concurrent_query_handling(self):
        """Test handling of concurrent queries."""
        queries = [
            "What is Python?",
            "Explain machine learning",
            "How do neural networks work?",
            "What is deep learning?",
            "Define artificial intelligence"
        ]
        
        # Mock query processing
        async def mock_process_query(query, **kwargs):
            await asyncio.sleep(0.1)  # Simulate processing time
            return {
                "response": f"Response to: {query}",
                "confidence": 0.8,
                "reasoning_steps": [],
                "inference_time_ms": 100.0,
                "knowledge_used": []
            }
        
        with patch.object(self.integration, 'process_natural_language_query', 
                         side_effect=mock_process_query):
            
            start_time = time.time()
            
            # Process queries concurrently
            tasks = [
                self.integration.process_natural_language_query(query)
                for query in queries
            ]
            results = await asyncio.gather(*tasks)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Should process concurrently (faster than sequential)
            assert total_time < len(queries) * 0.1 * 0.8  # Allow some overhead
            assert len(results) == len(queries)
            
            # All results should be valid
            for result in results:
                assert "response" in result
                assert "confidence" in result
    
    @pytest.mark.asyncio
    async def test_system_shutdown(self):
        """Test proper system shutdown."""
        # Initialize first
        with patch.object(self.integration, '_initialize_cognitive_systems', AsyncMock()):
            with patch.object(self.integration, '_initialize_knowledge_base', AsyncMock()):
                with patch.object(self.integration, '_start_background_processes', AsyncMock()):
                    await self.integration.initialize()
        
        # Test shutdown
        with patch.object(self.integration, '_stop_background_processes', AsyncMock()):
            with patch.object(self.integration, '_cleanup_resources', AsyncMock()):
                await self.integration.shutdown()
                
                assert self.integration.initialized is False


class TestGödelOSIntegrationEdgeCases:
    """Test edge cases and error conditions for GödelOS integration."""
    
    def setup_method(self):
        """Set up for edge case tests."""
        self.integration = GödelOSIntegration()
    
    @pytest.mark.asyncio
    async def test_empty_query_handling(self):
        """Test handling of empty or malformed queries."""
        empty_queries = ["", "   ", None]
        
        for query in empty_queries:
            with patch.object(self.integration, '_validate_query', AsyncMock(return_value=False)):
                result = await self.integration.process_natural_language_query(query)
                
                assert "error" in result or result["response"] == ""
    
    @pytest.mark.asyncio
    async def test_memory_pressure_handling(self):
        """Test system behavior under memory pressure."""
        with patch.object(self.integration, '_check_memory_usage', AsyncMock(return_value=0.95)):  # 95% memory usage
            with patch.object(self.integration, '_trigger_memory_cleanup', AsyncMock()):
                
                health_status = await self.integration.get_health_status()
                
                # System should still be functional but may report issues
                assert "memory_pressure" in health_status.get("warnings", []) or \
                       health_status.get("memory_usage_percent", 0) > 90
    
    @pytest.mark.asyncio
    async def test_knowledge_base_corruption_handling(self):
        """Test handling of knowledge base corruption."""
        with patch.object(self.integration, '_check_knowledge_base', 
                         AsyncMock(side_effect=Exception("Knowledge base corrupted"))):
            
            health_status = await self.integration.get_health_status()
            
            assert health_status["healthy"] is False
            assert health_status["components"]["knowledge_base"] is False
    
    @pytest.mark.asyncio
    async def test_inference_timeout_handling(self):
        """Test handling of inference timeouts."""
        long_running_query = "Solve this extremely complex philosophical question about the nature of consciousness..."
        
        with patch.object(self.integration, '_parse_natural_language', AsyncMock(return_value={
            "intent": "complex_reasoning",
            "entities": [],
            "confidence": 0.7
        })):
            with patch.object(self.integration, '_perform_inference', 
                             AsyncMock(side_effect=asyncio.TimeoutError("Inference timeout"))):
                
                result = await self.integration.process_natural_language_query(
                    long_running_query, 
                    timeout=1.0
                )
                
                assert "timeout" in result.get("error", "").lower() or \
                       "timeout" in result.get("response", "").lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])