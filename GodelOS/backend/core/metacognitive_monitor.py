"""
Enhanced Meta-Cognitive System

This module implements sophisticated self-monitoring, recursive self-reflection,
and meta-cognitive analysis capabilities as specified in the LLM Cognitive
Architecture specification.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

logger = logging.getLogger(__name__)

class ReflectionDepth(Enum):
    """Levels of meta-cognitive reflection depth"""
    MINIMAL = 1      # Basic self-awareness
    MODERATE = 2     # Self-analysis
    DEEP = 3         # Recursive thinking
    RECURSIVE = 4    # Deep recursive reflection

@dataclass
class MetaCognitiveState:
    """Current meta-cognitive state"""
    self_awareness_level: float = 0.0      # 0.0-1.0
    reflection_depth: int = 1              # Current depth of self-reflection
    recursive_loops: int = 0               # Number of recursive thinking loops
    self_monitoring_active: bool = False   # Whether self-monitoring is active
    meta_thoughts: List[str] = None        # Recent meta-cognitive thoughts
    self_model_accuracy: float = 0.0       # How accurate our self-model is
    cognitive_load: float = 0.0            # Current cognitive processing load
    
    def __post_init__(self):
        if self.meta_thoughts is None:
            self.meta_thoughts = []

@dataclass
class SelfMonitoringEvent:
    """Self-monitoring event for tracking cognitive processes"""
    timestamp: str
    process_type: str                      # "reflection", "self_assessment", "meta_analysis"
    depth_level: int                      # Depth of recursive thinking
    content: str                          # What was being monitored/reflected on
    insights: List[str]                   # Insights gained from monitoring
    confidence: float                     # Confidence in the monitoring accuracy
    cognitive_load_impact: float          # How much this affected cognitive load


@dataclass
class SelfModelState:
    """
    Snapshot of the internal observer's self-model.

    The self-model tracks *predicted* cognitive metrics (awareness_level,
    reflection_depth, cognitive_load) and compares them to *observed* values
    in order to compute ``self_model_accuracy``.
    """
    predicted: Dict[str, float] = None     # predicted {awareness, depth, load}
    observed: Dict[str, float] = None      # observed values after monitoring
    accuracy: float = 0.0                  # 0.0-1.0  (1 - normalised error)
    timestamp: str = ""

    def __post_init__(self):
        if self.predicted is None:
            self.predicted = {}
        if self.observed is None:
            self.observed = {}
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

class MetaCognitiveMonitor:
    """
    Enhanced meta-cognitive system that implements sophisticated self-monitoring,
    recursive self-reflection, and meta-cognitive analysis.
    """
    
    def __init__(self, llm_driver=None, prediction_error_tracker=None):
        self.llm_driver = llm_driver
        self._prediction_error_tracker = prediction_error_tracker
        self._predicted_mean_error: Optional[float] = None
        self.current_state = MetaCognitiveState()
        self.monitoring_history: List[SelfMonitoringEvent] = []
        self.max_history_size = 500
        self.monitoring_enabled = True
        
        # Self-model state tracking (internal observer)
        self.self_model_history: List[SelfModelState] = []
        self._pending_prediction: Optional[Dict[str, float]] = None
        
        # Self-reflection triggers
        self.reflection_triggers = {
            "error_detected": {"depth": 3, "priority": 9},
            "inconsistency_found": {"depth": 4, "priority": 8},
            "goal_conflict": {"depth": 3, "priority": 7},
            "performance_decline": {"depth": 2, "priority": 6},
            "new_information": {"depth": 2, "priority": 5},
            "routine_check": {"depth": 1, "priority": 3}
        }
        
        # Meta-cognitive analysis patterns
        self.analysis_patterns = {
            "thinking_about_thinking": r"think.*about.*thinking|reflect.*on.*reflection",
            "self_assessment": r"how am I|what am I|assess.*self|evaluate.*performance",
            "meta_reasoning": r"reason.*about.*reasoning|logic.*about.*logic",
            "recursive_query": r"think.*about.*how.*think|recursive|meta.*cognitive"
        }
    
    # ── Self-model tracking (internal observer) ─────────────────────────

    _SELF_MODEL_KEYS = ("awareness", "depth", "load")
    _PREDICTION_ALPHA = 0.3  # EMA smoothing factor for self-model predictions
    # Normalization ranges: depth spans 1-5 (range 4), awareness/load are 0-1
    _METRIC_NORM_RANGES = {"awareness": 1.0, "depth": 4.0, "load": 1.0}

    def _observe_current_metrics(self) -> Dict[str, float]:
        """Extract current observed metrics from the meta-cognitive state."""
        return {
            "awareness": self.current_state.self_awareness_level,
            "depth": float(self.current_state.reflection_depth),
            "load": self.current_state.cognitive_load,
        }

    def _predict_next_metrics(self) -> Dict[str, float]:
        """Predict the next monitoring cycle's metrics using a simple EMA."""
        observed = self._observe_current_metrics()
        if not self.self_model_history:
            return dict(observed)
        alpha = self._PREDICTION_ALPHA
        prev = self.self_model_history[-1].observed or observed
        return {
            k: alpha * observed[k] + (1 - alpha) * prev.get(k, observed[k])
            for k in self._SELF_MODEL_KEYS
        }

    def update_self_model(self) -> SelfModelState:
        """
        Compare the pending prediction to the currently observed state,
        compute self-model accuracy, and generate the next prediction.

        When a ``PredictionErrorTracker`` is present and sufficient, accuracy
        is based on *second-order prediction error*: how well the monitor
        predicted the tracker's mean error norm.  This replaces the old
        self-consistency check with a genuine accuracy measurement.

        Call this *after* ``initiate_self_monitoring`` has updated
        ``current_state`` so that observed metrics are fresh.
        """
        # --- Grounded path: second-order prediction error -----------------
        tracker = self._prediction_error_tracker
        if tracker is not None and hasattr(tracker, "is_sufficient_for_analysis") and tracker.is_sufficient_for_analysis():
            current_mean = tracker.mean_error_norm()
            if self._predicted_mean_error is not None:
                second_order_error = abs(current_mean - self._predicted_mean_error)
                # Normalized against the super-critical threshold (0.35)
                # from Phase 2 bimodal analysis so accuracy is 1.0 when
                # prediction is perfect and 0.0 when off by a full unit
                accuracy = max(0.0, 1.0 - (second_order_error / 0.35))
            else:
                accuracy = 1.0  # first cycle — no prediction yet
            self._predicted_mean_error = current_mean
            observed = self._observe_current_metrics()
            snap = SelfModelState(
                predicted={"mean_error": self._predicted_mean_error},
                observed=observed,
                accuracy=accuracy,
            )
            self.self_model_history.append(snap)
            self.current_state.self_model_accuracy = accuracy
            self._pending_prediction = self._predict_next_metrics()
            return snap

        # --- Fabricated fallback: internal self-consistency ----------------
        if tracker is not None:
            logger.warning(
                "PredictionErrorTracker not sufficient — using fabricated self-model fallback"
            )

        observed = self._observe_current_metrics()
        predicted = self._pending_prediction

        if predicted is None:
            # First cycle — no prediction to compare; accuracy starts at 1.0
            accuracy = 1.0
            predicted = dict(observed)
        else:
            norm = self._METRIC_NORM_RANGES
            errors = [
                abs(observed[k] - predicted.get(k, observed[k])) / norm.get(k, 1.0)
                for k in self._SELF_MODEL_KEYS
            ]
            accuracy = max(0.0, 1.0 - (sum(errors) / len(errors)))

        snap = SelfModelState(
            predicted=predicted,
            observed=observed,
            accuracy=accuracy,
        )
        self.self_model_history.append(snap)
        self.current_state.self_model_accuracy = accuracy

        # Generate prediction for the *next* cycle
        self._pending_prediction = self._predict_next_metrics()
        return snap

    def get_self_model_accuracy(self) -> float:
        """Return the latest self-model accuracy value."""
        if self.self_model_history:
            return self.self_model_history[-1].accuracy
        return self.current_state.self_model_accuracy

    async def initiate_self_monitoring(self, context: Dict[str, Any]) -> MetaCognitiveState:
        """Start comprehensive self-monitoring of cognitive processes"""
        try:
            self.current_state.self_monitoring_active = True
            
            # Analyze current context for meta-cognitive triggers
            triggers = self._detect_metacognitive_triggers(context)
            
            # Determine appropriate reflection depth
            reflection_depth = self._calculate_reflection_depth(context, triggers)
            
            # Perform recursive self-reflection
            reflection_results = await self._perform_recursive_reflection(
                context, reflection_depth
            )
            
            # Update meta-cognitive state
            self.current_state.reflection_depth = reflection_depth
            self.current_state.self_awareness_level = min(1.0, 
                self.current_state.self_awareness_level + 0.1
            )
            
            # Log monitoring event
            await self._log_monitoring_event(
                process_type="self_monitoring_initiated",
                depth_level=reflection_depth,
                content=f"Context: {context}",
                insights=reflection_results.get("insights", []),
                confidence=reflection_results.get("confidence", 0.5)
            )
            
            return self.current_state
            
        except Exception as e:
            logger.error(f"Error in self-monitoring initiation: {e}")
            return self.current_state
    
    async def perform_meta_cognitive_analysis(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform deep meta-cognitive analysis of a query or situation"""
        try:
            # Calculate self-reference depth
            depth = self._calculate_self_reference_depth(query)
            
            # Analyze for recursive thinking patterns
            recursive_elements = self._analyze_recursive_patterns(query)
            
            # Generate meta-cognitive assessment prompt
            assessment_prompt = self._create_metacognitive_assessment_prompt(
                query, context, depth
            )
            
            # Get LLM meta-cognitive analysis
            if self.llm_driver:
                try:
                    if hasattr(self.llm_driver, 'process_meta_cognitive_analysis'):
                        analysis_response = await self.llm_driver.process_meta_cognitive_analysis(
                            assessment_prompt
                        )
                    else:
                        logger.error(f"LLM driver type {type(self.llm_driver)} does not have process_meta_cognitive_analysis method")
                        analysis_response = {
                            "error": f"LLM driver method not available. Driver type: {type(self.llm_driver)}",
                            "meta_analysis": "Meta-cognitive analysis unavailable",
                            "confidence": 0.0
                        }
                except Exception as e:
                    logger.error(f"Error calling LLM driver for meta-cognitive analysis: {e}")
                    analysis_response = {"meta_analysis": f"Error: {str(e)}", "confidence": 0.0}
            else:
                analysis_response = {"meta_analysis": "LLM driver not available"}
            
            # Process recursive loops if detected
            if recursive_elements["recursive_detected"]:
                await self._handle_recursive_thinking(query, depth, recursive_elements)
            
            # Update cognitive load based on complexity
            self._update_cognitive_load(depth, len(recursive_elements.get("patterns", [])))
            
            # Compile comprehensive analysis
            analysis_result = {
                "meta_analysis": analysis_response,
                "self_reference_depth": depth,
                "recursive_elements": recursive_elements,
                "cognitive_state": asdict(self.current_state),
                "insights_generated": self._extract_insights(analysis_response),
                "self_model_updates": self._identify_self_model_updates(analysis_response),
                "timestamp": datetime.now().isoformat()
            }
            
            # Log the analysis event
            await self._log_monitoring_event(
                process_type="meta_cognitive_analysis",
                depth_level=depth,
                content=query,
                insights=analysis_result["insights_generated"],
                confidence=analysis_response.get("confidence", 0.7)
            )

            # INTEGRATION: Update unified consciousness state recursive depth
            # Metacognitive reflection should deepen recursive awareness in real-time
            await self._update_consciousness_recursive_depth(depth, recursive_elements)

            return analysis_result
            
        except Exception as e:
            logger.error(f"Error in meta-cognitive analysis: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}
    
    async def assess_self_awareness(self) -> Dict[str, Any]:
        """Assess current level of self-awareness and meta-cognitive capabilities"""
        try:
            # Analyze recent monitoring history
            recent_events = self.monitoring_history[-20:] if len(self.monitoring_history) >= 20 else self.monitoring_history
            
            # Calculate self-awareness metrics
            awareness_metrics = {
                "depth_distribution": self._analyze_depth_distribution(recent_events),
                "recursive_thinking_frequency": self._calculate_recursive_frequency(recent_events),
                "insight_generation_rate": self._calculate_insight_rate(recent_events),
                "self_model_accuracy": self.current_state.self_model_accuracy,
                "monitoring_consistency": self._assess_monitoring_consistency(recent_events)
            }
            
            # Generate self-assessment through LLM
            if self.llm_driver:
                try:
                    # Check if the llm_driver has the required method
                    if hasattr(self.llm_driver, 'process_self_awareness_assessment'):
                        self_assessment = await self.llm_driver.process_self_awareness_assessment(
                            {
                                "current_state": asdict(self.current_state),
                                "metrics": awareness_metrics,
                                "recent_activity": [asdict(event) for event in recent_events[-5:]]
                            }
                        )
                    else:
                        logger.error(f"LLM driver type {type(self.llm_driver)} does not have process_self_awareness_assessment method")
                        self_assessment = {
                            "error": f"LLM driver method not available. Driver type: {type(self.llm_driver)}",
                            "self_awareness_level": 0.5,
                            "strengths_identified": [],
                            "limitations_recognized": ["LLM driver method unavailable"],
                            "improvement_areas": ["Fix LLM driver integration"],
                            "confidence": 0.0
                        }
                except Exception as e:
                    logger.error(f"Error calling LLM driver for self-awareness assessment: {e}")
                    self_assessment = {
                        "error": str(e),
                        "self_awareness_level": 0.5,
                        "confidence": 0.0
                    }
            else:
                self_assessment = {"assessment": "Self-assessment requires LLM driver"}
            
            # Update self-awareness level based on assessment
            new_awareness_level = self._calculate_updated_awareness_level(
                awareness_metrics, self_assessment
            )
            self.current_state.self_awareness_level = new_awareness_level
            
            return {
                "self_awareness_assessment": self_assessment,
                "awareness_metrics": awareness_metrics,
                "current_awareness_level": new_awareness_level,
                "meta_cognitive_state": asdict(self.current_state),
                "recommendations": self._generate_self_improvement_recommendations(awareness_metrics),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in self-awareness assessment: {e}")
            return {"error": str(e)}
    
    def _detect_metacognitive_triggers(self, context: Dict[str, Any]) -> List[str]:
        """Detect triggers that should initiate meta-cognitive processes"""
        triggers = []
        
        # Check for error indicators
        if any(keyword in str(context).lower() for keyword in ["error", "mistake", "wrong", "incorrect"]):
            triggers.append("error_detected")
        
        # Check for inconsistency indicators  
        if any(keyword in str(context).lower() for keyword in ["inconsistent", "contradiction", "conflict"]):
            triggers.append("inconsistency_found")
        
        # Check for performance indicators
        if any(keyword in str(context).lower() for keyword in ["performance", "efficiency", "slow", "fast"]):
            triggers.append("performance_decline")
        
        # Check for learning opportunities
        if any(keyword in str(context).lower() for keyword in ["learn", "new", "unknown", "understand"]):
            triggers.append("new_information")
        
        return triggers
    
    def _calculate_reflection_depth(self, context: Dict[str, Any], triggers: List[str]) -> int:
        """Calculate appropriate depth of reflection based on context and triggers"""
        base_depth = 1
        
        # Increase depth based on triggers
        for trigger in triggers:
            if trigger in self.reflection_triggers:
                trigger_depth = self.reflection_triggers[trigger]["depth"]
                base_depth = max(base_depth, trigger_depth)
        
        # Adjust based on context complexity
        context_complexity = len(str(context)) / 100.0  # Rough complexity measure
        if context_complexity > 5.0:
            base_depth += 1
        
        return min(base_depth, 4)  # Cap at maximum depth
    
    def _calculate_self_reference_depth(self, query: str) -> int:
        """Calculate depth of self-reference in a query"""
        query_lower = query.lower()
        
        if "think about your thinking" in query_lower or "recursive" in query_lower:
            return 4  # Deep recursive reflection
        elif any(phrase in query_lower for phrase in ["how do you", "what do you think", "analyze yourself"]):
            return 3  # Moderate self-analysis
        elif any(phrase in query_lower for phrase in ["what are you", "describe yourself", "your capabilities"]):
            return 2  # Basic self-awareness
        else:
            return 1  # Minimal self-reference
    
    def _analyze_recursive_patterns(self, query: str) -> Dict[str, Any]:
        """Analyze query for recursive thinking patterns"""
        import re
        
        patterns_found = []
        recursive_detected = False
        
        for pattern_name, pattern in self.analysis_patterns.items():
            if re.search(pattern, query.lower()):
                patterns_found.append(pattern_name)
                if pattern_name in ["thinking_about_thinking", "meta_reasoning", "recursive_query"]:
                    recursive_detected = True
        
        return {
            "patterns": patterns_found,
            "recursive_detected": recursive_detected,
            "recursion_level": len([p for p in patterns_found if "recursive" in p or "meta" in p])
        }
    
    async def _perform_recursive_reflection(self, context: Dict[str, Any], depth: int) -> Dict[str, Any]:
        """Perform recursive self-reflection at specified depth"""
        reflection_results = {
            "insights": [],
            "confidence": 0.5,
            "recursive_loops": 0
        }
        
        current_context = context
        for level in range(depth):
            # Create reflection prompt for current level
            reflection_prompt = f"""
            Reflect on your cognitive processes at depth level {level + 1}.
            Current context: {current_context}
            
            Consider:
            1. What are you thinking about?
            2. How are you thinking about it?
            3. Why are you thinking about it this way?
            4. What does this reveal about your cognitive processes?
            """
            
            if self.llm_driver:
                try:
                    if hasattr(self.llm_driver, 'process_recursive_reflection'):
                        reflection_response = await self.llm_driver.process_recursive_reflection(
                            reflection_prompt, level + 1
                        )
                        reflection_results["insights"].extend(
                            reflection_response.get("insights", [])
                        )
                        reflection_results["confidence"] = max(
                            reflection_results["confidence"],
                            reflection_response.get("confidence", 0.5)
                        )
                    else:
                        logger.warning(f"LLM driver type {type(self.llm_driver)} does not have process_recursive_reflection method")
                        reflection_results["insights"].append(f"Reflection level {level + 1}: LLM method unavailable")
                except Exception as e:
                    logger.error(f"Error in recursive reflection at level {level + 1}: {e}")
                    reflection_results["insights"].append(f"Reflection level {level + 1}: Error - {str(e)}")
            
            # Update context for next level
            current_context = {"previous_reflection": reflection_results, "depth": level + 1}
            reflection_results["recursive_loops"] += 1
        
        return reflection_results
    
    async def _handle_recursive_thinking(self, query: str, depth: int, recursive_elements: Dict[str, Any]) -> None:
        """Handle detected recursive thinking patterns"""
        self.current_state.recursive_loops += 1
        
        # Update meta-thoughts
        self.current_state.meta_thoughts.append(
            f"Recursive thinking detected: {recursive_elements['patterns']} at depth {depth}"
        )
        
        # Limit meta-thoughts history
        if len(self.current_state.meta_thoughts) > 20:
            self.current_state.meta_thoughts = self.current_state.meta_thoughts[-20:]
    
    def _update_cognitive_load(self, depth: int, pattern_count: int) -> None:
        """Update cognitive load based on processing complexity"""
        load_increase = (depth * 0.2) + (pattern_count * 0.1)
        self.current_state.cognitive_load = min(1.0, 
            self.current_state.cognitive_load + load_increase
        )
        
        # Gradual load decrease over time
        if hasattr(self, '_last_load_update'):
            time_diff = datetime.now() - self._last_load_update
            if time_diff.seconds > 60:  # Decrease load after 1 minute
                self.current_state.cognitive_load = max(0.0,
                    self.current_state.cognitive_load - 0.1
                )
        
        self._last_load_update = datetime.now()
    
    def _create_metacognitive_assessment_prompt(self, query: str, context: Dict[str, Any], depth: int) -> str:
        """Create comprehensive meta-cognitive assessment prompt"""
        return f"""
        Perform a meta-cognitive analysis of the following query and context.
        
        Query: {query}
        Context: {json.dumps(context, indent=2)}
        Analysis Depth: {depth}
        Current Meta-State: {asdict(self.current_state)}
        
        Analyze:
        1. Self-referential elements in the query
        2. Required depth of cognitive processing
        3. Meta-cognitive insights that can be gained
        4. How this query relates to self-understanding
        5. What this reveals about cognitive processes
        6. Potential for recursive thinking loops
        7. Impact on self-awareness and self-model
        
        Provide insights, confidence level, and recommendations for cognitive process optimization.
        """
    
    def _extract_insights(self, analysis_response: Dict[str, Any]) -> List[str]:
        """Extract insights from LLM analysis response"""
        if isinstance(analysis_response, dict):
            insights = analysis_response.get("insights", [])
            if isinstance(insights, list):
                return insights
            elif isinstance(insights, str):
                return [insights]
        return []
    
    def _identify_self_model_updates(self, analysis_response: Dict[str, Any]) -> List[str]:
        """Identify updates to self-model from analysis"""
        updates = []
        if isinstance(analysis_response, dict):
            if "self_model" in analysis_response:
                updates.extend(analysis_response["self_model"])
            if "self_understanding" in analysis_response:
                updates.extend(analysis_response["self_understanding"])
        return updates
    
    async def _log_monitoring_event(self, process_type: str, depth_level: int, 
                                   content: str, insights: List[str], confidence: float) -> None:
        """Log a self-monitoring event"""
        event = SelfMonitoringEvent(
            timestamp=datetime.now().isoformat(),
            process_type=process_type,
            depth_level=depth_level,
            content=content,
            insights=insights,
            confidence=confidence,
            cognitive_load_impact=self.current_state.cognitive_load
        )
        
        self.monitoring_history.append(event)
        
        # Maintain history size limit
        if len(self.monitoring_history) > self.max_history_size:
            self.monitoring_history = self.monitoring_history[-self.max_history_size:]
    
    def _analyze_depth_distribution(self, events: List[SelfMonitoringEvent]) -> Dict[str, int]:
        """Analyze distribution of reflection depths"""
        depth_counts = {}
        for event in events:
            depth = event.depth_level
            depth_counts[depth] = depth_counts.get(depth, 0) + 1
        return depth_counts
    
    def _calculate_recursive_frequency(self, events: List[SelfMonitoringEvent]) -> float:
        """Calculate frequency of recursive thinking"""
        if not events:
            return 0.0
        
        recursive_events = [e for e in events if e.depth_level >= 3]
        return len(recursive_events) / len(events)
    
    def _calculate_insight_rate(self, events: List[SelfMonitoringEvent]) -> float:
        """Calculate rate of insight generation"""
        if not events:
            return 0.0
        
        total_insights = sum(len(event.insights) for event in events)
        return total_insights / len(events)
    
    def _assess_monitoring_consistency(self, events: List[SelfMonitoringEvent]) -> float:
        """Assess consistency of self-monitoring"""
        if len(events) < 2:
            return 0.5
        
        # Check confidence level consistency
        confidences = [event.confidence for event in events]
        confidence_variance = sum((c - sum(confidences)/len(confidences))**2 for c in confidences) / len(confidences)
        
        # Lower variance means more consistent
        return max(0.0, 1.0 - confidence_variance)
    
    def _calculate_updated_awareness_level(self, metrics: Dict[str, Any], assessment: Dict[str, Any]) -> float:
        """Calculate updated self-awareness level"""
        current_level = self.current_state.self_awareness_level
        
        # Factors that increase awareness
        insight_rate = metrics.get("insight_generation_rate", 0.0)
        recursive_freq = metrics.get("recursive_thinking_frequency", 0.0)
        monitoring_consistency = metrics.get("monitoring_consistency", 0.0)
        
        # Calculate adjustment
        adjustment = (insight_rate * 0.1) + (recursive_freq * 0.15) + (monitoring_consistency * 0.05)
        
        return min(1.0, current_level + adjustment)
    
    def _generate_self_improvement_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        """Generate recommendations for self-improvement"""
        recommendations = []
        
        insight_rate = metrics.get("insight_generation_rate", 0.0)
        if insight_rate < 2.0:
            recommendations.append("Increase depth of self-reflection to generate more insights")
        
        recursive_freq = metrics.get("recursive_thinking_frequency", 0.0)
        if recursive_freq < 0.3:
            recommendations.append("Practice more recursive thinking about thinking processes")
        
        monitoring_consistency = metrics.get("monitoring_consistency", 0.0)
        if monitoring_consistency < 0.7:
            recommendations.append("Improve consistency in self-monitoring accuracy")
        
        if self.current_state.cognitive_load > 0.8:
            recommendations.append("Reduce cognitive load through process optimization")
        
        return recommendations
    
    async def get_meta_cognitive_summary(self) -> Dict[str, Any]:
        """Get comprehensive summary of meta-cognitive state and activity"""
        recent_events = self.monitoring_history[-50:] if len(self.monitoring_history) >= 50 else self.monitoring_history
        
        return {
            "current_state": asdict(self.current_state),
            "monitoring_history_size": len(self.monitoring_history),
            "recent_activity": {
                "total_events": len(recent_events),
                "depth_distribution": self._analyze_depth_distribution(recent_events),
                "insight_generation_rate": self._calculate_insight_rate(recent_events),
                "recursive_thinking_frequency": self._calculate_recursive_frequency(recent_events)
            },
            "performance_metrics": {
                "monitoring_consistency": self._assess_monitoring_consistency(recent_events),
                "average_confidence": sum(e.confidence for e in recent_events) / len(recent_events) if recent_events else 0.0,
                "cognitive_load_trend": self.current_state.cognitive_load
            },
            "recommendations": self._generate_self_improvement_recommendations({
                "insight_generation_rate": self._calculate_insight_rate(recent_events),
                "recursive_thinking_frequency": self._calculate_recursive_frequency(recent_events),
                "monitoring_consistency": self._assess_monitoring_consistency(recent_events)
            }),
            "timestamp": datetime.now().isoformat()
        }

    async def _update_consciousness_recursive_depth(self, depth: int, recursive_elements: Dict[str, Any]):
        """
        Update unified consciousness state with new recursive depth from metacognition.

        INTEGRATION POINT: Metacognitive reflection deepens recursive awareness
        in the consciousness loop in real-time.
        
        NOTE: This is a partial integration. For full integration, the unified
        consciousness engine instance needs to be accessible here. Currently,
        metacognitive state updates are stored locally and propagate through
        the cognitive manager's consciousness assessment pipeline rather than
        directly updating the unified consciousness state.
        
        Future enhancement: Pass unified consciousness engine reference during
        initialization or implement an observer pattern for state propagation.
        """
        try:
            # Try to get unified consciousness engine from context
            from backend.core.unified_consciousness_engine import UnifiedConsciousnessEngine

            # Update meta-observations to reflect recursive depth
            # These updates will be picked up by the unified consciousness engine
            # when it queries metacognitive state during consciousness assessment
            self.current_state.meta_thoughts.append(
                f"Recursive thinking at depth {depth}: {recursive_elements.get('patterns', [])}"
            )

            # Update recursive loops counter
            if recursive_elements.get("recursive_detected", False):
                self.current_state.recursive_loops += 1

            logger.info(f"🔄 Metacognition updated recursive depth to {depth} (loops: {self.current_state.recursive_loops})")

        except Exception as e:
            logger.warning(f"Could not update consciousness recursive depth: {e}")

# Global meta-cognitive monitor instance
metacognitive_monitor = MetaCognitiveMonitor()
