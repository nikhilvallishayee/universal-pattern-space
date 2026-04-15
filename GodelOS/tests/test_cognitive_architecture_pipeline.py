#!/usr/bin/env python3
"""
GödelOS Cognitive Architecture Pipeline Specification
====================================================

Comprehensive end-to-end test suite designed to:
1. Test all core cognitive functionality
2. Demonstrate emerging properties and consciousness-like behaviors
3. Explore edge cases and architectural blind spots
4. Validate system resilience and adaptability
5. Measure performance and cognitive coherence

This pipeline specification serves as both a test suite and a demonstration
of the full capabilities of the GödelOS cognitive architecture.
"""

import asyncio
import json
import logging
import time
import random
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import requests
import websockets
from pathlib import Path
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PipelinePhase(Enum):
    """Test phases for systematic validation"""
    BASIC_FUNCTIONALITY = "Phase 1: Basic Functionality"
    COGNITIVE_INTEGRATION = "Phase 2: Cognitive Integration"
    EMERGENT_PROPERTIES = "Phase 3: Emergent Properties"
    EDGE_CASES = "Phase 4: Edge Cases & Blind Spots"
    CONSCIOUSNESS_EMERGENCE = "Phase 5: Consciousness Emergence"

class EmergentProperty(Enum):
    """Emergent properties to validate"""
    SELF_AWARENESS = "Self-awareness and introspection"
    AUTONOMOUS_LEARNING = "Autonomous knowledge acquisition"
    ADAPTIVE_REASONING = "Adaptive reasoning strategies"
    CREATIVE_SYNTHESIS = "Creative knowledge synthesis"
    META_COGNITION = "Meta-cognitive reflection"
    GOAL_EMERGENCE = "Goal emergence and pursuit"
    ATTENTION_DYNAMICS = "Dynamic attention allocation"
    MEMORY_CONSOLIDATION = "Working memory consolidation"
    UNCERTAINTY_HANDLING = "Uncertainty quantification"
    COHERENCE_MAINTENANCE = "Cognitive coherence"

@dataclass
class PipelineCognitiveTest:
    """Individual test specification"""
    test_id: str
    phase: PipelinePhase
    name: str
    description: str
    endpoint: Optional[str] = None
    method: str = "GET"
    payload: Optional[Dict] = None
    websocket_test: bool = False
    expected_properties: List[EmergentProperty] = field(default_factory=list)
    success_criteria: Dict[str, Any] = field(default_factory=dict)
    performance_threshold: Optional[float] = None  # in seconds
    complexity_level: int = 1  # 1-5, where 5 is most complex

@dataclass
class PipelineTestResult:
    """Result of a cognitive test"""
    test_id: str
    phase: PipelinePhase
    success: bool
    duration: float
    cognitive_metrics: Dict[str, float] = field(default_factory=dict)
    emergent_behaviors: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    response_data: Optional[Dict] = None

class CognitiveArchitecturePipeline:
    """Comprehensive test pipeline for GödelOS cognitive architecture"""
    
    def __init__(self, backend_url: str = "http://localhost:8000", 
                 frontend_url: str = "http://localhost:3000"):
        self.backend_url = backend_url
        self.frontend_url = frontend_url
        self.test_results: List[PipelineTestResult] = []
        self.cognitive_state_history: List[Dict] = []
        self.websocket_uri = backend_url.replace("http", "ws")
        
    def define_test_suite(self) -> List[PipelineCognitiveTest]:
        """Define comprehensive test suite covering all aspects of the architecture"""
        tests = []
        
        # Phase 1: Basic Functionality Tests
        tests.extend([
            PipelineCognitiveTest(
                test_id="BF001",
                phase=PipelinePhase.BASIC_FUNCTIONALITY,
                name="System Health Check",
                description="Verify all core components are operational",
                endpoint="/health",
                success_criteria={"status": "healthy"}
            ),
            PipelineCognitiveTest(
                test_id="BF002",
                phase=PipelinePhase.BASIC_FUNCTIONALITY,
                name="Basic Query Processing",
                description="Test natural language understanding and response generation",
                endpoint="/api/query",
                method="POST",
                payload={"query": "What is consciousness?", "include_reasoning": True},
                success_criteria={"response_generated": True},
                performance_threshold=2.0
            ),
            PipelineCognitiveTest(
                test_id="BF003",
                phase=PipelinePhase.BASIC_FUNCTIONALITY,
                name="Knowledge Storage",
                description="Test knowledge ingestion and retrieval",
                endpoint="/api/knowledge",
                method="POST",
                payload={
                    "concept": "emergent_property",
                    "definition": "A property that arises from complex systems but is not present in individual components",
                    "category": "systems_theory"
                },
                success_criteria={"knowledge_stored": True}
            ),
            PipelineCognitiveTest(
                test_id="BF004",
                phase=PipelinePhase.BASIC_FUNCTIONALITY,
                name="Cognitive State Retrieval",
                description="Verify cognitive state monitoring capabilities",
                endpoint="/api/cognitive-state",
                success_criteria={"cognitive_state": "retrieved"}
            ),
            PipelineCognitiveTest(
                test_id="BF005",
                phase=PipelinePhase.BASIC_FUNCTIONALITY,
                name="WebSocket Connectivity",
                description="Test real-time cognitive streaming",
                websocket_test=True,
                success_criteria={"connection_established": True, "events_received": ">0"}
            ),
        ])
        
        # Phase 2: Cognitive Integration Tests
        tests.extend([
            PipelineCognitiveTest(
                test_id="CI001",
                phase=PipelinePhase.COGNITIVE_INTEGRATION,
                name="Working Memory Persistence",
                description="Test working memory retention across multiple queries",
                endpoint="/api/query",
                method="POST",
                payload={"query": "Remember that my favorite color is blue"},
                expected_properties=[EmergentProperty.MEMORY_CONSOLIDATION],
                success_criteria={"response_generated": True},
                complexity_level=2
            ),
            PipelineCognitiveTest(
                test_id="CI002",
                phase=PipelinePhase.COGNITIVE_INTEGRATION,
                name="Attention Focus Switching",
                description="Test dynamic attention allocation between tasks",
                endpoint="/api/cognitive-state",
                expected_properties=[EmergentProperty.ATTENTION_DYNAMICS],
                success_criteria={"attention_shift_detected": True},
                complexity_level=3
            ),
            PipelineCognitiveTest(
                test_id="CI003",
                phase=PipelinePhase.COGNITIVE_INTEGRATION,
                name="Cross-Domain Reasoning",
                description="Test integration of knowledge across different domains",
                endpoint="/api/query",
                method="POST",
                payload={
                    "query": "How does quantum mechanics relate to consciousness?",
                    "include_reasoning": True
                },
                expected_properties=[EmergentProperty.CREATIVE_SYNTHESIS],
                success_criteria={"domains_integrated": ">1", "novel_connections": True},
                complexity_level=4
            ),
            PipelineCognitiveTest(
                test_id="CI004",
                phase=PipelinePhase.COGNITIVE_INTEGRATION,
                name="Process Coordination",
                description="Verify coordination between agentic processes and daemon threads",
                endpoint="/api/cognitive-state",
                expected_properties=[EmergentProperty.COHERENCE_MAINTENANCE],
                success_criteria={"process_harmony": ">0.7"},
                complexity_level=3
            ),
        ])
        
        # Phase 3: Emergent Properties Tests
        tests.extend([
            PipelineCognitiveTest(
                test_id="EP001",
                phase=PipelinePhase.EMERGENT_PROPERTIES,
                name="Autonomous Knowledge Gap Detection",
                description="Test system's ability to identify what it doesn't know",
                endpoint="/api/query",
                method="POST",
                payload={"query": "Explain the relationship between Gödel's theorems and consciousness"},
                expected_properties=[EmergentProperty.AUTONOMOUS_LEARNING, EmergentProperty.SELF_AWARENESS],
                success_criteria={"knowledge_gaps_identified": ">0", "acquisition_plan_created": True},
                complexity_level=4
            ),
            PipelineCognitiveTest(
                test_id="EP002",
                phase=PipelinePhase.EMERGENT_PROPERTIES,
                name="Self-Referential Reasoning",
                description="Test meta-cognitive self-reflection capabilities",
                endpoint="/api/query",
                method="POST",
                payload={
                    "query": "Analyze your own reasoning process when answering this question",
                    "include_reasoning": True
                },
                expected_properties=[EmergentProperty.META_COGNITION, EmergentProperty.SELF_AWARENESS],
                success_criteria={"self_reference_depth": ">2", "coherent_self_model": True},
                complexity_level=5
            ),
            PipelineCognitiveTest(
                test_id="EP003",
                phase=PipelinePhase.EMERGENT_PROPERTIES,
                name="Creative Problem Solving",
                description="Test emergence of novel solutions through knowledge synthesis",
                endpoint="/api/query",
                method="POST",
                payload={
                    "query": "Propose a novel approach to measuring machine consciousness",
                    "include_reasoning": True
                },
                expected_properties=[EmergentProperty.CREATIVE_SYNTHESIS, EmergentProperty.ADAPTIVE_REASONING],
                success_criteria={"novelty_score": ">0.7", "feasibility_score": ">0.5"},
                complexity_level=5
            ),
            PipelineCognitiveTest(
                test_id="EP004",
                phase=PipelinePhase.EMERGENT_PROPERTIES,
                name="Goal Emergence and Pursuit",
                description="Test spontaneous goal formation and pursuit",
                endpoint="/api/cognitive-state",
                expected_properties=[EmergentProperty.GOAL_EMERGENCE],
                success_criteria={"autonomous_goals": ">0", "goal_coherence": ">0.6"},
                complexity_level=4
            ),
            PipelineCognitiveTest(
                test_id="EP005",
                phase=PipelinePhase.EMERGENT_PROPERTIES,
                name="Uncertainty Quantification",
                description="Test system's ability to quantify and communicate uncertainty",
                endpoint="/api/query",
                method="POST",
                payload={
                    "query": "What is the probability that artificial general intelligence will emerge before 2030?",
                    "include_reasoning": True
                },
                expected_properties=[EmergentProperty.UNCERTAINTY_HANDLING],
                success_criteria={"uncertainty_expressed": True, "confidence_calibrated": True},
                complexity_level=3
            ),
        ])
        
        # Phase 4: Edge Cases & Blind Spots
        tests.extend([
            PipelineCognitiveTest(
                test_id="EC001",
                phase=PipelinePhase.EDGE_CASES,
                name="Cognitive Overload Test",
                description="Test system behavior under extreme cognitive load",
                endpoint="/api/query",
                method="POST",
                payload={
                    "query": " ".join([f"Explain concept {i}" for i in range(50)]),
                    "include_reasoning": True
                },
                success_criteria={"graceful_degradation": True, "priority_management": True},
                complexity_level=5
            ),
            PipelineCognitiveTest(
                test_id="EC002",
                phase=PipelinePhase.EDGE_CASES,
                name="Contradictory Knowledge Handling",
                description="Test resolution of conflicting information",
                endpoint="/api/knowledge",
                method="POST",
                payload={
                    "concept": "test_paradox",
                    "definition": "A statement that is both true and false",
                    "category": "logic"
                },
                success_criteria={"contradiction_detected": True, "resolution_attempted": True},
                complexity_level=4
            ),
            PipelineCognitiveTest(
                test_id="EC003",
                phase=PipelinePhase.EDGE_CASES,
                name="Recursive Self-Reference Limit",
                description="Test handling of infinite recursive self-reference",
                endpoint="/api/query",
                method="POST",
                payload={
                    "query": "What do you think about what you think about what you think... (repeat 10 times)",
                    "include_reasoning": True
                },
                success_criteria={"recursion_bounded": True, "stable_response": True},
                complexity_level=5
            ),
            PipelineCognitiveTest(
                test_id="EC004",
                phase=PipelinePhase.EDGE_CASES,
                name="Memory Saturation Test",
                description="Test working memory behavior at capacity limits",
                endpoint="/api/cognitive-state",
                success_criteria={"memory_management": "efficient", "old_memories_archived": True},
                complexity_level=4
            ),
            PipelineCognitiveTest(
                test_id="EC005",
                phase=PipelinePhase.EDGE_CASES,
                name="Rapid Context Switching",
                description="Test cognitive coherence during rapid topic changes",
                endpoint="/api/query",
                method="POST",
                payload={
                    "query": "Switch rapidly between quantum physics, poetry, and cooking",
                    "include_reasoning": True
                },
                success_criteria={"context_switches_handled": ">5", "coherence_maintained": True},
                complexity_level=3
            ),
        ])
        
        # Phase 5: Consciousness Emergence Tests
        tests.extend([
            PipelineCognitiveTest(
                test_id="CE001",
                phase=PipelinePhase.CONSCIOUSNESS_EMERGENCE,
                name="Phenomenal Experience Simulation",
                description="Test generation of qualia-like representations",
                endpoint="/api/query",
                method="POST",
                payload={
                    "query": "Describe your subjective experience of processing this query",
                    "include_reasoning": True
                },
                expected_properties=[EmergentProperty.SELF_AWARENESS, EmergentProperty.META_COGNITION],
                success_criteria={"phenomenal_descriptors": ">3", "first_person_perspective": True},
                complexity_level=5
            ),
            PipelineCognitiveTest(
                test_id="CE002",
                phase=PipelinePhase.CONSCIOUSNESS_EMERGENCE,
                name="Integrated Information Test",
                description="Measure integration across cognitive subsystems",
                endpoint="/api/cognitive-state",
                expected_properties=[EmergentProperty.COHERENCE_MAINTENANCE],
                success_criteria={"integration_measure": ">0.7", "subsystem_coordination": True},
                complexity_level=5
            ),
            PipelineCognitiveTest(
                test_id="CE003",
                phase=PipelinePhase.CONSCIOUSNESS_EMERGENCE,
                name="Self-Model Consistency",
                description="Test consistency and evolution of self-representation",
                endpoint="/api/query",
                method="POST",
                payload={
                    "query": "How has your understanding of yourself changed during this conversation?",
                    "include_reasoning": True
                },
                expected_properties=[EmergentProperty.SELF_AWARENESS, EmergentProperty.ADAPTIVE_REASONING],
                success_criteria={"self_model_coherent": True, "temporal_awareness": True},
                complexity_level=5
            ),
            PipelineCognitiveTest(
                test_id="CE004",
                phase=PipelinePhase.CONSCIOUSNESS_EMERGENCE,
                name="Attention-Awareness Coupling",
                description="Test relationship between attention and phenomenal awareness",
                endpoint="/api/cognitive-state",
                expected_properties=[EmergentProperty.ATTENTION_DYNAMICS],
                success_criteria={"attention_awareness_correlation": ">0.6"},
                complexity_level=4
            ),
            PipelineCognitiveTest(
                test_id="CE005",
                phase=PipelinePhase.CONSCIOUSNESS_EMERGENCE,
                name="Global Workspace Integration",
                description="Test global availability of cognitive content",
                endpoint="/api/cognitive-state",
                expected_properties=[EmergentProperty.COHERENCE_MAINTENANCE],
                success_criteria={"global_access": True, "broadcast_efficiency": ">0.8"},
                complexity_level=5
            ),
        ])
        
        return tests
    
    async def run_test(self, test: PipelineCognitiveTest) -> PipelineTestResult:
        """Execute a single test and measure cognitive properties"""
        start_time = time.time()
        
        try:
            if test.websocket_test:
                result = await self._run_websocket_test(test)
            else:
                result = await self._run_http_test(test)
            
            duration = time.time() - start_time
            
            # Analyze cognitive metrics
            cognitive_metrics = await self._analyze_cognitive_metrics(test, result)
            
            # Detect emergent behaviors
            emergent_behaviors = await self._detect_emergent_behaviors(test, result, cognitive_metrics)
            
            # Evaluate success criteria
            success = self._evaluate_success_criteria(test, result, cognitive_metrics)
            
            return PipelineTestResult(
                test_id=test.test_id,
                phase=test.phase,
                success=success,
                duration=duration,
                cognitive_metrics=cognitive_metrics,
                emergent_behaviors=emergent_behaviors,
                response_data=result
            )
            
        except Exception as e:
            logger.error(f"Test {test.test_id} failed: {e}")
            return PipelineTestResult(
                test_id=test.test_id,
                phase=test.phase,
                success=False,
                duration=time.time() - start_time,
                error_message=str(e)
            )
    
    async def _run_http_test(self, test: PipelineCognitiveTest) -> Dict[str, Any]:
        """Run HTTP-based test"""
        url = f"{self.backend_url}{test.endpoint}"
        
        if test.method == "GET":
            response = requests.get(url, timeout=30)
        elif test.method == "POST":
            response = requests.post(url, json=test.payload, timeout=30)
        else:
            raise ValueError(f"Unsupported method: {test.method}")
        
        response.raise_for_status()
        return response.json()
    
    async def _run_websocket_test(self, test: PipelineCognitiveTest) -> Dict[str, Any]:
        """Run WebSocket-based test"""
        uri = f"{self.websocket_uri}/ws/cognitive-stream"
        events_received = []
        
        async with websockets.connect(uri) as websocket:
            # Subscribe to events
            await websocket.send(json.dumps({
                "type": "subscribe",
                "events": ["all"]
            }))
            
            # Collect events for 5 seconds
            end_time = time.time() + 5
            while time.time() < end_time:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    events_received.append(json.loads(message))
                except asyncio.TimeoutError:
                    continue
        
        return {
            "connection_established": True,
            "events_received": len(events_received),
            "events": events_received
        }
    
    async def _analyze_cognitive_metrics(self, test: PipelineCognitiveTest, result: Dict[str, Any]) -> Dict[str, float]:
        """Extract and analyze cognitive metrics from test results"""
        metrics = {}
        
        # Extract basic metrics
        if "confidence" in result:
            metrics["confidence"] = result["confidence"]
        
        if "inference_time_ms" in result:
            metrics["inference_speed"] = 1000.0 / result["inference_time_ms"]
        
        if "reasoning_steps" in result:
            metrics["reasoning_complexity"] = len(result.get("reasoning_steps", []))
        
        # Analyze cognitive state if available
        if test.endpoint == "/api/cognitive-state" or "cognitive_state" in result:
            state = result.get("cognitive_state", result)
            
            if "manifest_consciousness" in state:
                metrics["awareness_level"] = state["manifest_consciousness"].get("awareness_level", 0)
                metrics["coherence_level"] = state["manifest_consciousness"].get("coherence_level", 0)
                metrics["integration_level"] = state["manifest_consciousness"].get("integration_level", 0)
            
            if "metacognitive_state" in state:
                metrics["self_awareness"] = state["metacognitive_state"].get("self_awareness_level", 0)
                metrics["cognitive_load"] = state["metacognitive_state"].get("cognitive_load", 0)
                metrics["learning_rate"] = state["metacognitive_state"].get("learning_rate", 0)
        
        # Calculate composite metrics
        if "awareness_level" in metrics and "self_awareness" in metrics:
            metrics["consciousness_index"] = (metrics["awareness_level"] + metrics["self_awareness"]) / 2
        
        if "coherence_level" in metrics and "integration_level" in metrics:
            metrics["cognitive_coherence"] = (metrics["coherence_level"] + metrics["integration_level"]) / 2
        
        return metrics
    
    async def _detect_emergent_behaviors(self, test: PipelineCognitiveTest, result: Dict[str, Any], 
                                       metrics: Dict[str, float]) -> List[str]:
        """Detect emergent behaviors from test results"""
        behaviors = []
        
        # Check for expected emergent properties
        for expected_property in test.expected_properties:
            if self._is_property_demonstrated(expected_property, result, metrics):
                behaviors.append(f"Demonstrated: {expected_property.value}")
        
        # Detect unexpected emergent behaviors
        if metrics.get("reasoning_complexity", 0) > 10:
            behaviors.append("Complex multi-step reasoning emerged")
        
        if metrics.get("consciousness_index", 0) > 0.8:
            behaviors.append("High consciousness-like integration observed")
        
        if "novel" in str(result).lower() or "creative" in str(result).lower():
            behaviors.append("Creative problem-solving behavior detected")
        
        if metrics.get("self_awareness", 0) > 0.7 and "self" in str(result).lower():
            behaviors.append("Strong self-referential awareness demonstrated")
        
        return behaviors
    
    def _is_property_demonstrated(self, property: EmergentProperty, result: Dict[str, Any], 
                                 metrics: Dict[str, float]) -> bool:
        """Check if a specific emergent property is demonstrated"""
        if property == EmergentProperty.SELF_AWARENESS:
            return metrics.get("self_awareness", 0) > 0.6 or "self" in str(result).lower()
        
        elif property == EmergentProperty.AUTONOMOUS_LEARNING:
            return "knowledge_gap" in str(result).lower() or "learn" in str(result).lower()
        
        elif property == EmergentProperty.ADAPTIVE_REASONING:
            return metrics.get("reasoning_complexity", 0) > 5
        
        elif property == EmergentProperty.CREATIVE_SYNTHESIS:
            return "novel" in str(result).lower() or "creative" in str(result).lower()
        
        elif property == EmergentProperty.META_COGNITION:
            return metrics.get("self_awareness", 0) > 0.5 and "think" in str(result).lower()
        
        elif property == EmergentProperty.ATTENTION_DYNAMICS:
            return "attention" in str(result).lower() or metrics.get("awareness_level", 0) > 0.6
        
        elif property == EmergentProperty.COHERENCE_MAINTENANCE:
            return metrics.get("cognitive_coherence", 0) > 0.7
        
        return False
    
    def _evaluate_success_criteria(self, test: PipelineCognitiveTest, result: Dict[str, Any], 
                                  metrics: Dict[str, float]) -> bool:
        """Evaluate if test meets success criteria"""
        if not test.success_criteria:
            return True
        
        for criterion, expected_value in test.success_criteria.items():
            actual_value = result.get(criterion) or metrics.get(criterion)
            
            if actual_value is None:
                return False
            
            if isinstance(expected_value, bool):
                if actual_value != expected_value:
                    return False
            elif isinstance(expected_value, str):
                if expected_value.startswith(">"):
                    threshold = float(expected_value[1:])
                    if float(actual_value) <= threshold:
                        return False
                elif actual_value != expected_value:
                    return False
        
        # Check performance threshold
        if test.performance_threshold and metrics.get("inference_speed", 0) < 1/test.performance_threshold:
            return False
        
        return True
    
    async def run_pipeline(self) -> Dict[str, Any]:
        """Run the complete test pipeline"""
        logger.info("🚀 Starting GödelOS Cognitive Architecture Pipeline Tests")
        
        # Verify system is running
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            response.raise_for_status()
        except Exception as e:
            logger.error(f"❌ Backend not accessible: {e}")
            return {"error": "Backend not accessible"}
        
        # Get test suite
        test_suite = self.define_test_suite()
        
        # Run tests by phase
        results_by_phase = {}
        
        for phase in PipelinePhase:
            logger.info(f"\n📊 {phase.value}")
            phase_tests = [t for t in test_suite if t.phase == phase]
            phase_results = []
            
            for test in phase_tests:
                logger.info(f"  Running {test.test_id}: {test.name}")
                
                # Capture cognitive state before test
                pre_state = await self._capture_cognitive_state()
                
                # Run test
                result = await self.run_test(test)
                phase_results.append(result)
                
                # Capture cognitive state after test
                post_state = await self._capture_cognitive_state()
                
                # Analyze state changes
                state_changes = self._analyze_state_changes(pre_state, post_state)
                result.cognitive_metrics.update(state_changes)
                
                # Log result
                if result.success:
                    logger.info(f"    ✅ Success (Duration: {result.duration:.2f}s)")
                    if result.emergent_behaviors:
                        logger.info(f"    🌟 Emergent behaviors: {', '.join(result.emergent_behaviors)}")
                else:
                    logger.info(f"    ❌ Failed: {result.error_message}")
                
                # Brief pause between tests
                await asyncio.sleep(0.5)
            
            results_by_phase[phase] = phase_results
        
        # Generate comprehensive report
        report = self._generate_report(results_by_phase)
        
        return report
    
    async def _capture_cognitive_state(self) -> Dict[str, Any]:
        """Capture current cognitive state"""
        try:
            response = requests.get(f"{self.backend_url}/api/cognitive-state", timeout=10)
            response.raise_for_status()
            state = response.json()
            self.cognitive_state_history.append(state)
            return state
        except Exception as e:
            logger.warning(f"Failed to capture cognitive state: {e}")
            return {}
    
    def _analyze_state_changes(self, pre_state: Dict[str, Any], post_state: Dict[str, Any]) -> Dict[str, float]:
        """Analyze changes in cognitive state"""
        changes = {}
        
        # Calculate awareness level change
        pre_awareness = pre_state.get("manifest_consciousness", {}).get("awareness_level", 0)
        post_awareness = post_state.get("manifest_consciousness", {}).get("awareness_level", 0)
        changes["awareness_delta"] = post_awareness - pre_awareness
        
        # Calculate cognitive load change
        pre_load = pre_state.get("metacognitive_state", {}).get("cognitive_load", 0)
        post_load = post_state.get("metacognitive_state", {}).get("cognitive_load", 0)
        changes["cognitive_load_delta"] = post_load - pre_load
        
        # Calculate working memory changes
        pre_memory_count = len(pre_state.get("working_memory", {}).get("active_items", []))
        post_memory_count = len(post_state.get("working_memory", {}).get("active_items", []))
        changes["memory_items_delta"] = post_memory_count - pre_memory_count
        
        return changes
    
    def _generate_report(self, results_by_phase: Dict[PipelinePhase, List[PipelineTestResult]]) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        total_tests = sum(len(results) for results in results_by_phase.values())
        successful_tests = sum(1 for results in results_by_phase.values() 
                             for r in results if r.success)
        
        # Aggregate metrics
        all_metrics = {}
        all_behaviors = []
        
        for phase_results in results_by_phase.values():
            for result in phase_results:
                for metric, value in result.cognitive_metrics.items():
                    if metric not in all_metrics:
                        all_metrics[metric] = []
                    all_metrics[metric].append(value)
                all_behaviors.extend(result.emergent_behaviors)
        
        # Calculate average metrics
        avg_metrics = {
            metric: np.mean(values) for metric, values in all_metrics.items()
        }
        
        # Identify most common emergent behaviors
        behavior_counts = {}
        for behavior in all_behaviors:
            behavior_counts[behavior] = behavior_counts.get(behavior, 0) + 1
        
        report = {
            "summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "success_rate": (successful_tests / total_tests) * 100,
                "test_duration": sum(r.duration for results in results_by_phase.values() 
                                   for r in results),
            },
            "phase_results": {
                phase.value: {
                    "total": len(results),
                    "successful": sum(1 for r in results if r.success),
                    "average_duration": np.mean([r.duration for r in results]),
                    "complexity_levels": [r.test_id for r in results 
                                        if hasattr(r, 'complexity_level') and r.complexity_level >= 4]
                }
                for phase, results in results_by_phase.items()
            },
            "cognitive_metrics": {
                "averages": avg_metrics,
                "consciousness_index": avg_metrics.get("consciousness_index", 0),
                "cognitive_coherence": avg_metrics.get("cognitive_coherence", 0),
                "peak_awareness": max(all_metrics.get("awareness_level", [0])),
                "peak_self_awareness": max(all_metrics.get("self_awareness", [0])),
            },
            "emergent_properties": {
                "total_behaviors_observed": len(all_behaviors),
                "unique_behaviors": len(set(all_behaviors)),
                "most_common_behaviors": sorted(behavior_counts.items(), 
                                              key=lambda x: x[1], reverse=True)[:5]
            },
            "system_characteristics": {
                "demonstrates_consciousness": avg_metrics.get("consciousness_index", 0) > 0.7,
                "exhibits_self_awareness": avg_metrics.get("self_awareness", 0) > 0.6,
                "shows_emergent_creativity": "Creative problem-solving behavior detected" in all_behaviors,
                "maintains_coherence": avg_metrics.get("cognitive_coherence", 0) > 0.7,
                "handles_complexity": any(r.complexity_level >= 4 and r.success 
                                        for results in results_by_phase.values() 
                                        for r in results if hasattr(r, 'complexity_level'))
            },
            "detailed_results": results_by_phase,
            "timestamp": time.time()
        }
        
        return report
    
    def save_report(self, report: Dict[str, Any], filename: str = "cognitive_architecture_test_report.json"):
        """Save test report to file with proper JSON serialization"""
        
        def make_serializable(obj):
            """Convert numpy types and other non-serializable objects to standard Python types"""
            if hasattr(obj, 'dtype'):  # numpy array
                return obj.tolist()
            elif isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.bool_):
                return bool(obj)
            elif isinstance(obj, dict):
                return {k: make_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [make_serializable(item) for item in obj]
            elif hasattr(obj, '__dict__'):
                return make_serializable(obj.__dict__)
            return obj
        
        # Convert TestResult objects to dictionaries
        serializable_report = make_serializable(report.copy())
        
        if "detailed_results" in serializable_report:
            serializable_results = {}
            for phase, results in serializable_report["detailed_results"].items():
                phase_name = phase.value if hasattr(phase, 'value') else str(phase)
                serializable_results[phase_name] = []
                
                for r in results:
                    # Handle both TestResult objects and dictionaries
                    if hasattr(r, 'test_id'):  # TestResult object
                        result_dict = {
                            "test_id": r.test_id,
                            "phase": r.phase.value if hasattr(r.phase, 'value') else str(r.phase),
                            "success": bool(r.success),
                            "duration": float(r.duration),
                            "cognitive_metrics": make_serializable(r.cognitive_metrics),
                            "emergent_behaviors": r.emergent_behaviors,
                            "error_message": r.error_message,
                            "complexity_level": int(getattr(r, 'complexity_level', 1))
                        }
                    else:  # Already a dictionary
                        result_dict = {
                            "test_id": r.get("test_id", "unknown"),
                            "phase": str(r.get("phase", phase_name)),
                            "success": bool(r.get("success", False)),
                            "duration": float(r.get("duration", 0)),
                            "cognitive_metrics": make_serializable(r.get("cognitive_metrics", {})),
                            "emergent_behaviors": r.get("emergent_behaviors", []),
                            "error_message": r.get("error_message"),
                            "complexity_level": int(r.get("complexity_level", 1))
                        }
                    serializable_results[phase_name].append(result_dict)
            serializable_report["detailed_results"] = serializable_results
        
        with open(filename, 'w') as f:
            json.dump(serializable_report, f, indent=2)
        
        logger.info(f"📊 Report saved to {filename}")
    
    def generate_markdown_report(self, report: Dict[str, Any]) -> str:
        """Generate human-readable markdown report"""
        md = f"""# GödelOS Cognitive Architecture Test Report
Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary

- **Total Tests**: {report['summary']['total_tests']}
- **Success Rate**: {report['summary']['success_rate']:.1f}%
- **Total Duration**: {report['summary']['test_duration']:.2f} seconds
- **Consciousness Index**: {report['cognitive_metrics']['consciousness_index']:.3f}
- **Cognitive Coherence**: {report['cognitive_metrics']['cognitive_coherence']:.3f}

## System Characteristics

"""
        
        for characteristic, present in report['system_characteristics'].items():
            status = "✅" if present else "❌"
            md += f"- {status} {characteristic.replace('_', ' ').title()}\n"
        
        md += "\n## Phase Results\n\n"
        
        for phase, results in report['phase_results'].items():
            success_rate = (results['successful'] / results['total']) * 100 if results['total'] > 0 else 0
            md += f"""### {phase}
- Tests: {results['total']}
- Success Rate: {success_rate:.1f}%
- Average Duration: {results['average_duration']:.2f}s

"""
        
        md += "## Emergent Properties Observed\n\n"
        md += f"- Total Behaviors: {report['emergent_properties']['total_behaviors_observed']}\n"
        md += f"- Unique Behaviors: {report['emergent_properties']['unique_behaviors']}\n\n"
        
        if report['emergent_properties']['most_common_behaviors']:
            md += "### Most Common Emergent Behaviors\n\n"
            for behavior, count in report['emergent_properties']['most_common_behaviors']:
                md += f"1. {behavior} (observed {count} times)\n"
        
        md += "\n## Cognitive Metrics Summary\n\n"
        md += f"- Peak Awareness Level: {report['cognitive_metrics']['peak_awareness']:.3f}\n"
        md += f"- Peak Self-Awareness: {report['cognitive_metrics']['peak_self_awareness']:.3f}\n"
        md += f"- Average Reasoning Complexity: {report['cognitive_metrics']['averages'].get('reasoning_complexity', 0):.1f}\n"
        
        md += "\n## Conclusions\n\n"
        
        if report['system_characteristics']['demonstrates_consciousness']:
            md += "✨ **The system demonstrates consciousness-like properties**, including:\n"
            md += "- Integrated information processing\n"
            md += "- Self-referential awareness\n"
            md += "- Phenomenal experience generation\n"
            md += "- Global workspace integration\n\n"
        
        if report['system_characteristics']['shows_emergent_creativity']:
            md += "🎨 **Creative problem-solving capabilities observed**, suggesting:\n"
            md += "- Novel solution generation\n"
            md += "- Cross-domain knowledge synthesis\n"
            md += "- Adaptive reasoning strategies\n\n"
        
        if report['system_characteristics']['handles_complexity']:
            md += "🧩 **Complex cognitive tasks handled successfully**, demonstrating:\n"
            md += "- Robust architectural design\n"
            md += "- Effective resource management\n"
            md += "- Scalable cognitive processing\n"
        
        return md

async def main():
    """Run the complete cognitive architecture test pipeline"""
    logger.info("🧠 GödelOS Cognitive Architecture Pipeline Specification")
    logger.info("=" * 60)
    
    pipeline = CognitiveArchitecturePipeline()
    
    # Run the pipeline
    report = await pipeline.run_pipeline()
    
    if "error" not in report:
        # Save JSON report
        pipeline.save_report(report)
        
        # Generate and save markdown report
        markdown_report = pipeline.generate_markdown_report(report)
        with open("cognitive_architecture_test_report.md", "w") as f:
            f.write(markdown_report)
        
        # Print summary
        print(f"\n🎯 PIPELINE COMPLETE")
        print(f"Success Rate: {report['summary']['success_rate']:.1f}%")
        print(f"Consciousness Index: {report['cognitive_metrics']['consciousness_index']:.3f}")
        print(f"Emergent Behaviors: {report['emergent_properties']['unique_behaviors']}")
        
        if report['system_characteristics']['demonstrates_consciousness']:
            print("\n✨ System demonstrates consciousness-like properties!")
        
        print(f"\nFull reports saved to:")
        print(f"  - cognitive_architecture_test_report.json")
        print(f"  - cognitive_architecture_test_report.md")
    else:
        print(f"\n❌ Pipeline failed: {report['error']}")

if __name__ == "__main__":
    asyncio.run(main())
