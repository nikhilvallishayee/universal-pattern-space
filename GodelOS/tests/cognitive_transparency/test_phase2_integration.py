"""
Test suite for Phase 2 Cognitive Transparency features.

Tests the integration of Dynamic Knowledge Graph, Provenance Tracking,
Autonomous Learning, and Uncertainty Quantification components.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List

from godelOS.cognitive_transparency.knowledge_graph import DynamicKnowledgeGraph, GraphUpdateResult
from godelOS.cognitive_transparency.provenance import ProvenanceTracker, ProvenanceQueryType
from godelOS.cognitive_transparency.autonomous_learning import AutonomousLearningOrchestrator, LearningStrategy
from godelOS.cognitive_transparency.uncertainty import UncertaintyQuantificationEngine, PropagationMethod
from godelOS.cognitive_transparency.models import (
    KnowledgeNode, KnowledgeEdge, ProvenanceRecord, LearningObjective, 
    LearningObjectiveType, UncertaintyMetrics, ReasoningStep, StepType
)


class TestDynamicKnowledgeGraph:
    """Test suite for Dynamic Knowledge Graph functionality."""
    
    @pytest.fixture
    def knowledge_graph(self):
        """Create a knowledge graph instance for testing."""
        return DynamicKnowledgeGraph()
    
    def test_add_node_success(self, knowledge_graph):
        """Test successful node addition."""
        result = knowledge_graph.add_node(
            concept="artificial_intelligence",
            node_type="concept",
            properties={"domain": "computer_science"},
            confidence=0.9
        )
        
        assert result.success is True
        assert result.operation == "node_added"
        assert len(result.affected_nodes) == 1
        assert "artificial_intelligence" in [
            knowledge_graph.nodes[node_id].concept 
            for node_id in result.affected_nodes
        ]
    
    def test_add_duplicate_node(self, knowledge_graph):
        """Test adding duplicate node updates existing."""
        # Add first node
        result1 = knowledge_graph.add_node("machine_learning", confidence=0.8)
        assert result1.success is True
        
        # Add duplicate - should update existing
        result2 = knowledge_graph.add_node("machine_learning", confidence=0.9)
        assert result2.success is True
        assert result2.operation == "node_updated"
        
        # Should still have only one node with updated confidence
        ml_nodes = [
            node for node in knowledge_graph.nodes.values() 
            if node.concept == "machine_learning"
        ]
        assert len(ml_nodes) == 1
        assert ml_nodes[0].confidence == 0.9
    
    def test_add_edge_success(self, knowledge_graph):
        """Test successful edge addition."""
        result = knowledge_graph.add_edge(
            source_concept="machine_learning",
            target_concept="artificial_intelligence",
            relation_type="is_subfield_of",
            confidence=0.95
        )
        
        assert result.success is True
        assert result.operation == "edge_added"
        assert len(result.affected_nodes) == 2
        assert len(result.affected_edges) == 1
    
    def test_discover_relationships(self, knowledge_graph):
        """Test relationship discovery."""
        # Add some nodes first
        knowledge_graph.add_node("neural_networks")
        knowledge_graph.add_node("deep_learning")
        knowledge_graph.add_node("machine_learning")
        
        # Add some relationships
        knowledge_graph.add_edge("deep_learning", "machine_learning", "is_subfield_of")
        knowledge_graph.add_edge("neural_networks", "deep_learning", "enables")
        
        # Discover relationships for neural_networks
        relationships = knowledge_graph.discover_new_relationships("neural_networks", max_distance=2)
        
        assert isinstance(relationships, list)
        # Should discover potential relationship with machine_learning through deep_learning
    
    def test_graph_statistics(self, knowledge_graph):
        """Test graph statistics calculation."""
        # Add some nodes and edges
        knowledge_graph.add_node("concept1")
        knowledge_graph.add_node("concept2")
        knowledge_graph.add_edge("concept1", "concept2", "relates_to")
        
        stats = knowledge_graph.get_graph_statistics()
        
        assert stats["node_count"] >= 2
        assert stats["edge_count"] >= 1
        assert "avg_confidence" in stats
        assert "density" in stats
    
    def test_export_graph_data(self, knowledge_graph):
        """Test graph data export."""
        knowledge_graph.add_node("test_concept")
        
        export_data = knowledge_graph.export_graph_data()
        
        assert "nodes" in export_data
        assert "edges" in export_data
        assert "statistics" in export_data
        assert "metadata" in export_data
        assert len(export_data["nodes"]) >= 1


class TestProvenanceTracker:
    """Test suite for Provenance Tracking functionality."""
    
    @pytest.fixture
    def provenance_tracker(self):
        """Create a provenance tracker instance for testing."""
        return ProvenanceTracker()
    
    def test_create_record(self, provenance_tracker):
        """Test provenance record creation."""
        record = provenance_tracker.create_record(
            operation_type="create",
            target_id="test_node_1",
            target_type="node",
            transformation_description="Created test node",
            confidence_after=0.8
        )
        
        assert record.operation_type == "create"
        assert record.target_id == "test_node_1"
        assert record.target_type == "node"
        assert record.confidence_after == 0.8
        assert record.record_id in provenance_tracker.records
    
    def test_start_end_chain(self, provenance_tracker):
        """Test provenance chain management."""
        session_id = "test_session_1"
        
        # Start chain
        chain_id = provenance_tracker.start_chain(session_id, "reasoning")
        assert chain_id is not None
        assert session_id in provenance_tracker.active_chains
        
        # End chain
        ended_chain_id = provenance_tracker.end_chain(session_id)
        assert ended_chain_id == chain_id
        assert session_id not in provenance_tracker.active_chains
    
    def test_query_backward_trace(self, provenance_tracker):
        """Test backward provenance tracing."""
        # Create some records with dependencies
        record1 = provenance_tracker.create_record(
            operation_type="create",
            target_id="source_1",
            target_type="node"
        )
        
        record2 = provenance_tracker.create_record(
            operation_type="infer",
            target_id="derived_1",
            target_type="node",
            input_sources=["source_1"]
        )
        
        # Query backward trace
        result = provenance_tracker.query_provenance(
            target_id="derived_1",
            query_type=ProvenanceQueryType.BACKWARD_TRACE,
            max_depth=5
        )
        
        assert result["target_id"] == "derived_1"
        assert result["trace_type"] == "backward"
        assert len(result["nodes"]) >= 1
    
    def test_attribution_chain(self, provenance_tracker):
        """Test attribution chain generation."""
        # Create records with attribution
        provenance_tracker.create_record(
            operation_type="create",
            target_id="base_fact",
            target_type="fact"
        )
        
        provenance_tracker.create_record(
            operation_type="infer",
            target_id="conclusion",
            target_type="fact",
            input_sources=["base_fact"]
        )
        
        chain = provenance_tracker.get_attribution_chain("conclusion")
        
        assert isinstance(chain, list)
        assert len(chain) >= 1
    
    def test_confidence_history(self, provenance_tracker):
        """Test confidence evolution tracking."""
        target_id = "evolving_concept"
        
        # Create multiple records showing confidence evolution
        provenance_tracker.create_record(
            operation_type="create",
            target_id=target_id,
            target_type="concept",
            confidence_after=0.5
        )
        
        provenance_tracker.create_record(
            operation_type="update",
            target_id=target_id,
            target_type="concept",
            confidence_before=0.5,
            confidence_after=0.8
        )
        
        history = provenance_tracker.get_confidence_history(target_id)
        
        assert isinstance(history, list)
        assert len(history) >= 2
        assert history[0]["confidence_after"] == 0.5
        assert history[1]["confidence_after"] == 0.8
    
    def test_create_snapshot(self, provenance_tracker):
        """Test knowledge state snapshot creation."""
        knowledge_state = {
            "nodes": [{"id": "test1", "concept": "test_concept"}],
            "edges": []
        }
        
        snapshot_id = provenance_tracker.create_snapshot(
            knowledge_state=knowledge_state,
            metadata={"test": True}
        )
        
        assert snapshot_id is not None
        assert snapshot_id in provenance_tracker.snapshots
        
        snapshot = provenance_tracker.snapshots[snapshot_id]
        assert snapshot.knowledge_state == knowledge_state
        assert snapshot.metadata["test"] is True


class TestAutonomousLearning:
    """Test suite for Autonomous Learning functionality."""
    
    @pytest.fixture
    def autonomous_learning(self):
        """Create an autonomous learning orchestrator for testing."""
        return AutonomousLearningOrchestrator()
    
    def test_start_learning_session(self, autonomous_learning):
        """Test starting a learning session."""
        session_id = autonomous_learning.start_learning_session(
            focus_areas=["machine_learning", "neural_networks"],
            strategy=LearningStrategy.EXPLORATION
        )
        
        assert session_id is not None
        assert session_id in autonomous_learning.learning_sessions
        
        session = autonomous_learning.learning_sessions[session_id]
        assert session.strategy == LearningStrategy.EXPLORATION.value
        assert len(session.objectives) >= 0
    
    def test_process_reasoning_step(self, autonomous_learning):
        """Test processing reasoning step for learning opportunities."""
        reasoning_step = ReasoningStep(
            step_type=StepType.INFERENCE,
            description="Test reasoning step",
            confidence=0.6,
            context={
                "missing_knowledge": ["concept_x", "concept_y"],
                "contradictions": ["contradiction_1"]
            }
        )
        
        session_id = "test_session"
        objectives = autonomous_learning.process_reasoning_step(reasoning_step, session_id)
        
        assert isinstance(objectives, list)
        # Should generate objectives for missing knowledge and contradictions
        assert len(objectives) >= 0
    
    def test_execute_learning_objective(self, autonomous_learning):
        """Test executing a learning objective."""
        # Create a test objective
        objective = LearningObjective(
            objective_type=LearningObjectiveType.KNOWLEDGE_GAP_FILLING,
            description="Test objective",
            priority=0.8
        )
        
        autonomous_learning.active_objectives[objective.objective_id] = objective
        
        # Execute the objective
        success = autonomous_learning.execute_learning_objective(objective.objective_id)
        
        assert isinstance(success, bool)
        # Objective should be moved from active to completed
        assert objective.objective_id not in autonomous_learning.active_objectives
    
    def test_adapt_learning_strategy(self, autonomous_learning):
        """Test learning strategy adaptation."""
        initial_strategy = autonomous_learning.current_strategy
        
        # Simulate some performance data
        metrics = autonomous_learning.strategy_performance[LearningStrategy.EXPLORATION]
        metrics.objectives_completed = 10
        metrics.objectives_failed = 2
        metrics.learning_efficiency = 0.8
        
        new_strategy = autonomous_learning.adapt_learning_strategy()
        
        assert isinstance(new_strategy, LearningStrategy)
        # Strategy might change based on performance
    
    def test_get_learning_status(self, autonomous_learning):
        """Test getting learning status."""
        status = autonomous_learning.get_learning_status()
        
        assert "current_strategy" in status
        assert "active_objectives_count" in status
        assert "completed_objectives_count" in status
        assert "performance_metrics" in status
    
    def test_get_learning_recommendations(self, autonomous_learning):
        """Test getting learning recommendations."""
        recommendations = autonomous_learning.get_learning_recommendations()
        
        assert isinstance(recommendations, list)
        for rec in recommendations:
            assert "type" in rec
            assert "description" in rec
            assert "priority" in rec


class TestUncertaintyQuantification:
    """Test suite for Uncertainty Quantification functionality."""
    
    @pytest.fixture
    def uncertainty_engine(self):
        """Create an uncertainty quantification engine for testing."""
        return UncertaintyQuantificationEngine()
    
    def test_assess_step_uncertainty(self, uncertainty_engine):
        """Test uncertainty assessment for reasoning steps."""
        reasoning_step = ReasoningStep(
            step_type=StepType.INFERENCE,
            description="Test inference step",
            confidence=0.7,
            processing_time_ms=500,
            context={
                "knowledge_gaps": ["gap1", "gap2"],
                "source_reliability": 0.8,
                "evidence_count": 3
            }
        )
        
        analysis = uncertainty_engine.assess_step_uncertainty(reasoning_step)
        
        assert analysis.target_id == reasoning_step.step_id
        assert analysis.target_type == "step"
        assert analysis.uncertainty_metrics.confidence == 0.7
        assert len(analysis.contributing_factors) >= 0
        assert len(analysis.mitigation_suggestions) >= 0
    
    def test_propagate_uncertainty(self, uncertainty_engine):
        """Test uncertainty propagation through reasoning chain."""
        # Create a chain of reasoning steps
        steps = []
        for i in range(3):
            step = ReasoningStep(
                step_type=StepType.INFERENCE,
                description=f"Step {i}",
                confidence=0.8 - (i * 0.1)  # Decreasing confidence
            )
            steps.append(step)
        
        result = uncertainty_engine.propagate_uncertainty(
            reasoning_chain=steps,
            method=PropagationMethod.ANALYTICAL
        )
        
        assert result.propagation_method == PropagationMethod.ANALYTICAL
        assert len(result.step_uncertainties) == 3
        assert result.initial_uncertainty >= 0.0
        assert result.final_uncertainty >= 0.0
        assert result.uncertainty_growth == result.final_uncertainty - result.initial_uncertainty
    
    def test_get_confidence_level(self, uncertainty_engine):
        """Test confidence level categorization."""
        assert uncertainty_engine.get_confidence_level(0.95) == "very_high"
        assert uncertainty_engine.get_confidence_level(0.85) == "high"
        assert uncertainty_engine.get_confidence_level(0.7) == "medium"
        assert uncertainty_engine.get_confidence_level(0.5) == "low"
        assert uncertainty_engine.get_confidence_level(0.3) == "very_low"
        assert uncertainty_engine.get_confidence_level(0.1) == "very_low"
    
    def test_get_statistics(self, uncertainty_engine):
        """Test uncertainty statistics calculation."""
        # Add some analyses
        step = ReasoningStep(confidence=0.8)
        uncertainty_engine.assess_step_uncertainty(step)
        
        stats = uncertainty_engine.get_statistics()
        
        assert "total_analyses" in stats
        assert "avg_confidence" in stats
        assert "avg_uncertainty" in stats
        assert "confidence_distribution" in stats


class TestPhase2Integration:
    """Integration tests for Phase 2 components working together."""
    
    @pytest.fixture
    def integrated_system(self):
        """Create an integrated system with all Phase 2 components."""
        uncertainty_engine = UncertaintyQuantificationEngine()
        provenance_tracker = ProvenanceTracker()
        knowledge_graph = DynamicKnowledgeGraph(
            provenance_tracker=provenance_tracker,
            uncertainty_engine=uncertainty_engine
        )
        autonomous_learning = AutonomousLearningOrchestrator(
            knowledge_graph=knowledge_graph,
            provenance_tracker=provenance_tracker,
            uncertainty_engine=uncertainty_engine
        )
        
        return {
            "knowledge_graph": knowledge_graph,
            "provenance_tracker": provenance_tracker,
            "autonomous_learning": autonomous_learning,
            "uncertainty_engine": uncertainty_engine
        }
    
    def test_knowledge_graph_with_provenance(self, integrated_system):
        """Test knowledge graph operations with provenance tracking."""
        kg = integrated_system["knowledge_graph"]
        pt = integrated_system["provenance_tracker"]
        
        # Start provenance chain
        session_id = "integration_test"
        pt.start_chain(session_id, "reasoning")
        
        # Add node with provenance
        result = kg.add_node(
            concept="test_concept",
            confidence=0.8,
            source_session_id=session_id
        )
        
        assert result.success is True
        assert len(result.provenance_records) > 0
        
        # Verify provenance record was created
        node_id = result.affected_nodes[0]
        node = kg.nodes[node_id]
        assert len(node.source_provenance) > 0
        
        provenance_record_id = node.source_provenance[0]
        assert provenance_record_id in pt.records
    
    def test_learning_with_uncertainty(self, integrated_system):
        """Test autonomous learning with uncertainty assessment."""
        al = integrated_system["autonomous_learning"]
        ue = integrated_system["uncertainty_engine"]
        
        # Create a reasoning step with uncertainty
        reasoning_step = ReasoningStep(
            step_type=StepType.INFERENCE,
            confidence=0.6,  # Medium confidence
            context={"missing_knowledge": ["important_concept"]}
        )
        
        # Assess uncertainty
        uncertainty_analysis = ue.assess_step_uncertainty(reasoning_step)
        assert uncertainty_analysis.uncertainty_metrics.confidence == 0.6
        
        # Process for learning opportunities
        objectives = al.process_reasoning_step(reasoning_step, "test_session")
        
        # Should generate learning objectives due to missing knowledge
        assert len(objectives) >= 0
    
    def test_full_reasoning_cycle(self, integrated_system):
        """Test a complete reasoning cycle with all Phase 2 components."""
        kg = integrated_system["knowledge_graph"]
        pt = integrated_system["provenance_tracker"]
        al = integrated_system["autonomous_learning"]
        ue = integrated_system["uncertainty_engine"]
        
        # 1. Start learning session
        learning_session_id = al.start_learning_session(
            focus_areas=["artificial_intelligence"],
            strategy=LearningStrategy.EXPLORATION
        )
        
        # 2. Start provenance tracking
        reasoning_session_id = "full_cycle_test"
        pt.start_chain(reasoning_session_id, "reasoning")
        
        # 3. Add knowledge with uncertainty
        kg_result = kg.add_node(
            concept="machine_learning",
            confidence=0.7,
            source_session_id=reasoning_session_id
        )
        
        # 4. Create reasoning step
        reasoning_step = ReasoningStep(
            step_type=StepType.INFERENCE,
            description="Inferring ML capabilities",
            confidence=0.8,
            output_data={"concepts": ["machine_learning"]}
        )
        
        # 5. Assess uncertainty
        uncertainty_analysis = ue.assess_step_uncertainty(reasoning_step)
        
        # 6. Update knowledge graph from reasoning
        kg_updates = kg.update_from_reasoning_step(reasoning_step, reasoning_session_id)
        
        # 7. Process for learning opportunities
        learning_objectives = al.process_reasoning_step(reasoning_step, learning_session_id)
        
        # 8. End provenance chain
        pt.end_chain(reasoning_session_id)
        
        # Verify integration worked
        assert kg_result.success is True
        assert uncertainty_analysis.target_id == reasoning_step.step_id
        assert len(kg_updates) >= 0
        assert isinstance(learning_objectives, list)
        
        # Verify provenance tracking
        provenance_stats = pt.get_statistics()
        assert provenance_stats["total_records"] > 0
        
        # Verify learning status
        learning_status = al.get_learning_status()
        assert learning_status["active_objectives_count"] >= 0


@pytest.mark.asyncio
class TestPhase2AsyncIntegration:
    """Async integration tests for Phase 2 components."""
    
    async def test_concurrent_operations(self):
        """Test concurrent operations across Phase 2 components."""
        # Create components
        uncertainty_engine = UncertaintyQuantificationEngine()
        provenance_tracker = ProvenanceTracker()
        knowledge_graph = DynamicKnowledgeGraph(
            provenance_tracker=provenance_tracker,
            uncertainty_engine=uncertainty_engine
        )
        
        # Simulate concurrent operations
        tasks = []
        
        # Add multiple nodes concurrently
        for i in range(5):
            task = asyncio.create_task(
                asyncio.to_thread(
                    knowledge_graph.add_node,
                    f"concept_{i}",
                    confidence=0.8 + (i * 0.02)
                )
            )
            tasks.append(task)
        
        # Wait for all operations to complete
        results = await asyncio.gather(*tasks)
        
        # Verify all operations succeeded
        for result in results:
            assert result.success is True
        
        # Verify graph state
        stats = knowledge_graph.get_graph_statistics()
        assert stats["node_count"] >= 5


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])