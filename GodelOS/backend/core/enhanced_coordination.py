#!/usr/bin/env python3
"""
Enhanced Coordination System for Cognitive Components

This module provides advanced coordination capabilities including dynamic
policy learning, multi-component orchestration, and adaptive thresholds.
"""

import asyncio
import logging
import time
import json
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Any, Callable, Set
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum

# Import adaptive learning
from .adaptive_learning import adaptive_learning_engine, PolicyLearningEngine

logger = logging.getLogger(__name__)


class CoordinationAction(Enum):
    """Types of coordination actions."""
    PROCEED = "proceed"
    AUGMENT_CONTEXT = "augment_context"
    ESCALATE_PRIORITY = "escalate_priority"
    DEFER_PROCESSING = "defer_processing"
    ROUTE_TO_SPECIALIST = "route_to_specialist"
    MERGE_CONTEXTS = "merge_contexts"
    VALIDATE_CONFIDENCE = "validate_confidence"
    TRIGGER_REFLECTION = "trigger_reflection"


class ComponentType(Enum):
    """Types of cognitive components."""
    LLM_DRIVER = "llm_driver"
    KNOWLEDGE_PIPELINE = "knowledge_pipeline"
    CONSCIOUSNESS_ENGINE = "consciousness_engine"
    METACOGNITIVE_MONITOR = "metacognitive_monitor"
    AUTONOMOUS_LEARNING = "autonomous_learning"
    KNOWLEDGE_GRAPH = "knowledge_graph"
    PHENOMENAL_EXPERIENCE = "phenomenal_experience"
    TRANSPARENCY_ENGINE = "transparency_engine"


@dataclass
class ComponentStatus:
    """Status information for a cognitive component."""
    component_type: ComponentType
    name: str
    status: str = "active"  # active, degraded, offline, recovering
    health: float = 1.0  # 0.0 to 1.0
    load: float = 0.0  # 0.0 to 1.0
    last_activity: float = field(default_factory=time.time)
    error_count: int = 0
    success_count: int = 0
    average_response_time: float = 0.0
    capabilities: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CoordinationContext:
    """Context for coordination decisions."""
    session_id: str
    query: str
    confidence: float
    component_states: Dict[str, ComponentStatus]
    historical_data: Dict[str, Any]
    constraints: Dict[str, Any] = field(default_factory=dict)
    preferences: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CoordinationPolicy:
    """Policy for coordination decisions."""
    name: str
    conditions: List[Dict[str, Any]]
    actions: List[Dict[str, Any]]
    priority: int = 1
    enabled: bool = True
    learned: bool = False
    success_rate: float = 0.0
    usage_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EnhancedCoordinationEvent:
    """Enhanced coordination event with richer context."""
    name: str
    context: CoordinationContext
    timestamp: float = field(default_factory=time.time)
    component_source: Optional[str] = None
    urgency: str = "normal"  # low, normal, high, critical
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EnhancedCoordinationDecision:
    """Enhanced coordination decision with detailed reasoning."""
    action: CoordinationAction
    params: Dict[str, Any] = field(default_factory=dict)
    rationale: str = ""
    confidence: float = 1.0
    component_assignments: Dict[str, str] = field(default_factory=dict)
    expected_improvements: List[str] = field(default_factory=list)
    monitoring_points: List[str] = field(default_factory=list)
    fallback_actions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["action"] = self.action.value
        return result


class ComponentHealthMonitor:
    """Monitors health and performance of cognitive components."""
    
    def __init__(self):
        self.component_statuses: Dict[str, ComponentStatus] = {}
        self.health_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.alert_thresholds = {
            "health": 0.5,
            "load": 0.9,
            "error_rate": 0.1,
            "response_time": 5.0
        }
        
    def register_component(self, component_type: ComponentType, name: str, 
                          capabilities: List[str] = None, dependencies: List[str] = None):
        """Register a cognitive component for monitoring."""
        self.component_statuses[name] = ComponentStatus(
            component_type=component_type,
            name=name,
            capabilities=capabilities or [],
            dependencies=dependencies or []
        )
        logger.info(f"📊 Registered component {name} for health monitoring")
    
    def update_component_status(self, name: str, **kwargs):
        """Update status information for a component."""
        if name not in self.component_statuses:
            logger.warning(f"Component {name} not registered for monitoring")
            return
        
        status = self.component_statuses[name]
        
        # Update provided fields
        for key, value in kwargs.items():
            if hasattr(status, key):
                setattr(status, key, value)
        
        status.last_activity = time.time()
        
        # Calculate health score
        health_factors = []
        if status.error_count > 0:
            error_rate = status.error_count / (status.error_count + status.success_count)
            health_factors.append(1.0 - min(error_rate * 10, 1.0))
        else:
            health_factors.append(1.0)
        
        # Load factor
        health_factors.append(1.0 - min(status.load, 1.0))
        
        # Response time factor (assuming target < 1s)
        if status.average_response_time > 0:
            time_factor = max(0.0, 1.0 - (status.average_response_time - 1.0) / 4.0)
            health_factors.append(time_factor)
        
        status.health = sum(health_factors) / len(health_factors) if health_factors else 1.0
        
        # Record health history
        self.health_history[name].append({
            "timestamp": time.time(),
            "health": status.health,
            "load": status.load,
            "error_count": status.error_count
        })
        
        # Check for alerts
        self._check_alerts(name, status)
    
    def _check_alerts(self, name: str, status: ComponentStatus):
        """Check if component status requires alerts."""
        alerts = []
        
        if status.health < self.alert_thresholds["health"]:
            alerts.append(f"Health below threshold: {status.health:.2f}")
        
        if status.load > self.alert_thresholds["load"]:
            alerts.append(f"Load above threshold: {status.load:.2f}")
        
        if status.average_response_time > self.alert_thresholds["response_time"]:
            alerts.append(f"Response time above threshold: {status.average_response_time:.2f}s")
        
        if alerts:
            logger.warning(f"🚨 Component {name} alerts: {', '.join(alerts)}")
    
    def get_component_recommendations(self, name: str) -> List[str]:
        """Get recommendations for improving component performance."""
        if name not in self.component_statuses:
            return []
        
        status = self.component_statuses[name]
        recommendations = []
        
        if status.health < 0.7:
            recommendations.append("Consider restarting or reinitializing component")
        
        if status.load > 0.8:
            recommendations.append("High load detected - consider load balancing or scaling")
        
        if status.error_count > status.success_count:
            recommendations.append("High error rate - investigate error patterns")
        
        if status.average_response_time > 3.0:
            recommendations.append("Slow response times - optimize processing or add caching")
        
        return recommendations


class PolicyLearningEngine:
    """Learns and adapts coordination policies based on outcomes."""
    
    def __init__(self):
        self.policies: Dict[str, CoordinationPolicy] = {}
        self.policy_outcomes: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.learning_rate = 0.1
        self.success_threshold = 0.7
        
        # Initialize default policies
        self._initialize_default_policies()
    
    def _initialize_default_policies(self):
        """Initialize default coordination policies."""
        policies = [
            CoordinationPolicy(
                name="low_confidence_augmentation",
                conditions=[
                    {"field": "confidence", "operator": "<", "value": 0.6}
                ],
                actions=[
                    {"action": "augment_context", "params": {"sources": ["knowledge_graph", "web_search"]}}
                ],
                priority=1
            ),
            CoordinationPolicy(
                name="high_load_deferral",
                conditions=[
                    {"field": "component_load", "operator": ">", "value": 0.9}
                ],
                actions=[
                    {"action": "defer_processing", "params": {"delay": 5.0}}
                ],
                priority=2
            ),
            CoordinationPolicy(
                name="expertise_routing",
                conditions=[
                    {"field": "query_domain", "operator": "in", "value": ["science", "mathematics"]}
                ],
                actions=[
                    {"action": "route_to_specialist", "params": {"specialist": "scientific_reasoning"}}
                ],
                priority=1
            ),
            CoordinationPolicy(
                name="reflection_trigger",
                conditions=[
                    {"field": "confidence", "operator": "<", "value": 0.5},
                    {"field": "complexity", "operator": ">", "value": 0.8}
                ],
                actions=[
                    {"action": "trigger_reflection", "params": {"depth": "deep"}}
                ],
                priority=1
            )
        ]
        
        for policy in policies:
            self.policies[policy.name] = policy
            logger.info(f"📜 Initialized policy: {policy.name}")
    
    def add_policy(self, policy: CoordinationPolicy):
        """Add a new coordination policy."""
        self.policies[policy.name] = policy
        logger.info(f"📜 Added policy: {policy.name}")
    
    def evaluate_policies(self, context: CoordinationContext) -> List[CoordinationPolicy]:
        """Evaluate which policies apply to the given context with ML predictions."""
        applicable_policies = []
        
        for policy in self.policies.values():
            if not policy.enabled:
                continue
            
            if self._policy_matches(policy, context):
                # Get ML prediction for this policy
                predicted_outcome = adaptive_learning_engine.predict_policy_outcome(
                    policy.name, context
                )
                
                # Add prediction confidence to policy metadata
                policy.metadata["predicted_outcome"] = predicted_outcome
                policy.metadata["ml_confidence"] = predicted_outcome
                
                applicable_policies.append(policy)
        
        # Sort by priority, predicted outcome, and historical success rate
        applicable_policies.sort(key=lambda p: (
            -p.priority, 
            -p.metadata.get("predicted_outcome", 0.5),
            -p.success_rate
        ))
        
        return applicable_policies
    
    def _policy_matches(self, policy: CoordinationPolicy, context: CoordinationContext) -> bool:
        """Check if a policy matches the given context."""
        for condition in policy.conditions:
            if not self._evaluate_condition(condition, context):
                return False
        return True
    
    def _evaluate_condition(self, condition: Dict[str, Any], context: CoordinationContext) -> bool:
        """Evaluate a single policy condition."""
        field = condition["field"]
        operator = condition["operator"]
        value = condition["value"]
        
        # Get field value from context
        if field == "confidence":
            context_value = context.confidence
        elif field == "component_load":
            context_value = max(status.load for status in context.component_states.values())
        elif field == "query_domain":
            # Simple domain detection based on keywords
            query_lower = context.query.lower()
            domains = []
            if any(word in query_lower for word in ["science", "physics", "chemistry", "biology"]):
                domains.append("science")
            if any(word in query_lower for word in ["math", "equation", "formula", "calculate"]):
                domains.append("mathematics")
            context_value = domains
        elif field == "complexity":
            # Simple complexity estimation
            context_value = min(1.0, len(context.query.split()) / 50.0)
        else:
            context_value = context.metadata.get(field)
        
        # Evaluate condition
        if operator == "<":
            return context_value < value
        elif operator == ">":
            return context_value > value
        elif operator == "<=":
            return context_value <= value
        elif operator == ">=":
            return context_value >= value
        elif operator == "==":
            return context_value == value
        elif operator == "!=":
            return context_value != value
        elif operator == "in":
            return context_value in value if isinstance(value, list) else context_value == value
        else:
            return False
    
    def record_outcome(self, policy_name: str, success: bool, improvement: float = 0.0, 
                      metadata: Dict[str, Any] = None):
        """Record the outcome of applying a policy with ML learning."""
        if policy_name not in self.policies:
            return
        
        policy = self.policies[policy_name]
        policy.usage_count += 1
        
        outcome = {
            "timestamp": time.time(),
            "success": success,
            "improvement": improvement,
            "metadata": metadata or {}
        }
        self.policy_outcomes[policy_name].append(outcome)
        
        # Update success rate
        recent_outcomes = self.policy_outcomes[policy_name][-10:]  # Last 10 outcomes
        success_count = sum(1 for o in recent_outcomes if o["success"])
        policy.success_rate = success_count / len(recent_outcomes)
        
        # Record outcome in adaptive learning system
        adaptive_learning_engine.record_outcome(
            policy_name=policy_name,
            context=getattr(self, '_last_context', None),
            action=policy.actions[0]["action"] if policy.actions else "unknown",
            success=success,
            improvement=improvement,
            execution_time=metadata.get("execution_time", 0.0) if metadata else 0.0,
            error_message=metadata.get("error_message") if metadata else None
        )
        
        # Learn from outcomes
        if policy.learned and policy.success_rate < self.success_threshold:
            self._adapt_policy(policy, recent_outcomes)
    
    def _adapt_policy(self, policy: CoordinationPolicy, outcomes: List[Dict[str, Any]]):
        """Adapt a policy based on outcomes."""
        # Simple adaptation: adjust thresholds based on success/failure patterns
        logger.info(f"📈 Adapting policy {policy.name} (success rate: {policy.success_rate:.2f})")
        
        # For now, just disable poorly performing learned policies
        if policy.success_rate < 0.3 and policy.usage_count > 5:
            policy.enabled = False
            logger.warning(f"🚫 Disabled underperforming policy: {policy.name}")


class EnhancedCoordinator:
    """
    Enhanced coordinator with advanced decision-making, component monitoring,
    and adaptive policy learning.
    """
    
    def __init__(self, min_confidence: float = 0.6, websocket_manager=None):
        self.min_confidence = min_confidence
        self.websocket_manager = websocket_manager
        self.health_monitor = ComponentHealthMonitor()
        self.policy_engine = PolicyLearningEngine()
        self.adaptive_learning = adaptive_learning_engine
        self.decision_history: deque = deque(maxlen=1000)
        self.context_cache: Dict[str, Any] = {}
        
        # Performance metrics
        self.coordination_metrics = {
            "decisions_made": 0,
            "successful_outcomes": 0,
            "average_decision_time": 0.0,
            "policy_adaptations": 0,
            "component_alerts": 0,
            "adaptive_predictions_made": 0,
            "adaptive_accuracy": 0.0
        }
        
        logger.info("🎯 Enhanced coordinator initialized")
    
    def register_component(self, component_type: ComponentType, name: str, 
                          instance: Any = None, capabilities: List[str] = None):
        """Register a cognitive component for coordination."""
        self.health_monitor.register_component(
            component_type, name, capabilities or [], []
        )
        
        if instance:
            # Store reference for direct interaction
            setattr(self, f"_{name}_instance", instance)
        
        logger.info(f"🔗 Registered component {name} for coordination")
    
    async def notify(self, event: EnhancedCoordinationEvent) -> EnhancedCoordinationDecision:
        """Process coordination event and make enhanced decision with ML guidance."""
        start_time = time.time()
        
        try:
            # Store context for learning
            self._last_context = event.context
            
            # Update component statuses
            await self._update_component_statuses(event.context)
            
            # Evaluate applicable policies with ML predictions
            applicable_policies = self.policy_engine.evaluate_policies(event.context)
            
            if not applicable_policies:
                # No specific policies apply, use default logic
                decision = await self._make_default_decision(event)
            else:
                # Apply best matching policy (now ML-guided)
                best_policy = applicable_policies[0]
                decision = await self._apply_policy(best_policy, event)
                
                # Record ML prediction metrics
                predicted_outcome = best_policy.metadata.get("predicted_outcome", 0.5)
                self.coordination_metrics["adaptive_predictions_made"] += 1
                
                # Store prediction for later accuracy calculation
                decision.metadata["predicted_outcome"] = predicted_outcome
                decision.metadata["policy_used"] = best_policy.name
            
            # Record decision
            decision_time = time.time() - start_time
            self.coordination_metrics["decisions_made"] += 1
            self.coordination_metrics["average_decision_time"] = (
                (self.coordination_metrics["average_decision_time"] * 
                 (self.coordination_metrics["decisions_made"] - 1) + decision_time) / 
                self.coordination_metrics["decisions_made"]
            )
            
            decision_record = {
                "timestamp": time.time(),
                "event": event.to_dict(),
                "decision": decision.to_dict(),
                "policies_evaluated": len(applicable_policies),
                "decision_time": decision_time,
                "ml_predictions": [
                    {
                        "policy": p.name,
                        "predicted_outcome": p.metadata.get("predicted_outcome", 0.5)
                    }
                    for p in applicable_policies
                ]
            }
            self.decision_history.append(decision_record)
            
            # Broadcast coordination decision
            if self.websocket_manager:
                await self.websocket_manager.broadcast_cognitive_update({
                    "type": "coordination_decision",
                    "event_name": event.name,
                    "action": decision.action.value,
                    "confidence": decision.confidence,
                    "rationale": decision.rationale,
                    "ml_guidance": len(applicable_policies) > 0,
                    "predicted_outcome": decision.metadata.get("predicted_outcome"),
                    "timestamp": time.time()
                })
            
            logger.info(f"🎯 Coordination decision: {decision.action.value} (confidence: {decision.confidence:.2f})")
            if "predicted_outcome" in decision.metadata:
                logger.info(f"🤖 ML predicted outcome: {decision.metadata['predicted_outcome']:.2f}")
            
            return decision
            
        except Exception as e:
            logger.error(f"❌ Error in coordination decision: {e}")
            # Return safe fallback decision
            return EnhancedCoordinationDecision(
                action=CoordinationAction.PROCEED,
                rationale=f"Fallback due to error: {e}",
                confidence=0.5
            )
    
    async def _update_component_statuses(self, context: CoordinationContext):
        """Update component status information."""
        # Simple status updates based on available information
        current_time = time.time()
        
        for name, status in context.component_states.items():
            self.health_monitor.update_component_status(
                name,
                last_activity=current_time,
                status=status.status,
                health=status.health,
                load=status.load
            )
    
    async def _make_default_decision(self, event: EnhancedCoordinationEvent) -> EnhancedCoordinationDecision:
        """Make a default coordination decision when no policies apply."""
        context = event.context
        
        if context.confidence < self.min_confidence:
            return EnhancedCoordinationDecision(
                action=CoordinationAction.AUGMENT_CONTEXT,
                params={"sources": ["knowledge_graph"], "depth": "shallow"},
                rationale=f"Confidence {context.confidence:.2f} below threshold {self.min_confidence:.2f}",
                confidence=0.8,
                expected_improvements=["increased_confidence", "better_context"]
            )
        
        # Check component health
        unhealthy_components = [
            name for name, status in context.component_states.items()
            if status.health < 0.7
        ]
        
        if unhealthy_components:
            return EnhancedCoordinationDecision(
                action=CoordinationAction.ROUTE_TO_SPECIALIST,
                params={"avoid_components": unhealthy_components},
                rationale=f"Unhealthy components detected: {unhealthy_components}",
                confidence=0.7,
                monitoring_points=["component_recovery"]
            )
        
        return EnhancedCoordinationDecision(
            action=CoordinationAction.PROCEED,
            rationale="No coordination changes required",
            confidence=1.0
        )
    
    async def _apply_policy(self, policy: CoordinationPolicy, 
                           event: EnhancedCoordinationEvent) -> EnhancedCoordinationDecision:
        """Apply a coordination policy to make a decision."""
        if not policy.actions:
            return await self._make_default_decision(event)
        
        # For now, use the first action
        action_config = policy.actions[0]
        action = CoordinationAction(action_config["action"])
        
        decision = EnhancedCoordinationDecision(
            action=action,
            params=action_config.get("params", {}),
            rationale=f"Applied policy: {policy.name}",
            confidence=min(1.0, policy.success_rate + 0.2),
            metadata={"policy": policy.name, "policy_priority": policy.priority}
        )
        
        return decision
    
    async def record_decision_outcome(self, decision_id: str, success: bool, 
                                     improvement: float = 0.0, metadata: Dict[str, Any] = None):
        """Record the outcome of a coordination decision for learning."""
        # Find the decision in history
        for record in reversed(self.decision_history):
            if record.get("decision", {}).get("metadata", {}).get("id") == decision_id:
                policy_name = record.get("decision", {}).get("metadata", {}).get("policy")
                if policy_name:
                    self.policy_engine.record_outcome(policy_name, success, improvement, metadata)
                
                if success:
                    self.coordination_metrics["successful_outcomes"] += 1
                
                break
    
    async def get_coordination_insights(self) -> Dict[str, Any]:
        """Get insights about coordination performance and patterns including ML metrics."""
        # Analyze decision patterns
        recent_decisions = list(self.decision_history)[-50:]  # Last 50 decisions
        
        action_counts = defaultdict(int)
        success_by_action = defaultdict(list)
        
        for record in recent_decisions:
            action = record.get("decision", {}).get("action")
            if action:
                action_counts[action] += 1
        
        # Component health summary
        component_health = {
            name: status.health 
            for name, status in self.health_monitor.component_statuses.items()
        }
        
        # Policy performance
        policy_performance = {}
        for name, policy in self.policy_engine.policies.items():
            policy_performance[name] = {
                "success_rate": policy.success_rate,
                "usage_count": policy.usage_count,
                "enabled": policy.enabled,
                "learned": policy.learned
            }
        
        # Calculate ML prediction accuracy
        predictions_with_outcomes = []
        for record in self.decision_history:
            if "ml_predictions" in record and "outcome" in record:
                predicted = record["decision"].get("metadata", {}).get("predicted_outcome")
                actual = record.get("outcome", {}).get("success", False)
                if predicted is not None:
                    predictions_with_outcomes.append((predicted, 1.0 if actual else 0.0))
        
        ml_accuracy = 0.0
        if predictions_with_outcomes:
            # Calculate accuracy within 0.2 threshold
            correct = sum(1 for pred, actual in predictions_with_outcomes 
                         if abs(pred - actual) < 0.2)
            ml_accuracy = correct / len(predictions_with_outcomes)
            self.coordination_metrics["adaptive_accuracy"] = ml_accuracy
        
        # Get adaptive learning insights
        learning_insights = adaptive_learning_engine.get_learning_insights()
        
        return {
            "coordination_metrics": self.coordination_metrics,
            "recent_action_distribution": dict(action_counts),
            "component_health": component_health,
            "policy_performance": policy_performance,
            "decision_history_size": len(self.decision_history),
            "ml_prediction_accuracy": ml_accuracy,
            "adaptive_learning": learning_insights,
            "circuit_breaker_metrics": self._get_circuit_breaker_summary(),
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_circuit_breaker_summary(self) -> Dict[str, Any]:
        """Get summary of circuit breaker status."""
        try:
            # Import here to avoid circular imports
            from .circuit_breaker import circuit_breaker_manager
            return circuit_breaker_manager.get_all_metrics()
        except Exception as e:
            logger.warning(f"Could not get circuit breaker metrics: {e}")
            return {"error": str(e)}
