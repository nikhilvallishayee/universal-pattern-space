"""
Metacognition Adapter for GodelOS

This module implements the MetacognitionAdapter class, which adapts the existing
MetacognitionManager to work with the new CognitiveEngine in the UnifiedAgentCore
architecture.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Callable, Tuple, Union

from godelOS.metacognition.manager import (
    MetacognitionManager,
    MetacognitivePhase,
    MetacognitiveMode,
    MetacognitiveEvent
)
from godelOS.metacognition.diagnostician import DiagnosticReport, DiagnosticFinding
from godelOS.metacognition.modification_planner import ModificationProposal, ModificationStatus

from godelOS.unified_agent_core.cognitive_engine.interfaces import (
    CognitiveEngineInterface,
    Thought,
    Reflection,
    Idea,
    CognitiveContext
)

logger = logging.getLogger(__name__)


class MetacognitionAdapter:
    """
    Adapter for connecting the existing MetacognitionManager with the new CognitiveEngine.
    
    This adapter implements the adapter pattern to allow the existing MetacognitionManager
    to work with the new CognitiveEngine in the UnifiedAgentCore architecture, ensuring
    backward compatibility while enabling the new architecture's capabilities.
    """
    
    def __init__(
        self,
        metacognition_manager: MetacognitionManager,
        cognitive_engine: Optional[CognitiveEngineInterface] = None
    ):
        """
        Initialize the metacognition adapter.
        
        Args:
            metacognition_manager: The existing metacognition manager
            cognitive_engine: Optional cognitive engine to connect to
        """
        self.metacognition_manager = metacognition_manager
        self.cognitive_engine = cognitive_engine
        
        # Event mapping from metacognition events to cognitive engine events
        self.event_mapping: Dict[str, str] = {
            "anomaly_detected": "cognitive_anomaly",
            "diagnostic_report_generated": "cognitive_diagnosis",
            "proposals_generated": "cognitive_planning",
            "modification_executed": "cognitive_adaptation"
        }
        
        # Event subscribers
        self.event_subscribers: Dict[str, List[Callable[[Dict[str, Any]], None]]] = {}
        
        # Initialize event subscriptions
        self._setup_event_subscriptions()
    
    def _setup_event_subscriptions(self) -> None:
        """Set up event subscriptions between components."""
        # Subscribe to relevant metacognition events
        for event_type in self.event_mapping.keys():
            self.metacognition_manager.subscribe_to_event(
                event_type, self._on_metacognition_event
            )
    
    def _on_metacognition_event(self, event: MetacognitiveEvent) -> None:
        """
        Handle metacognition events.
        
        Args:
            event: The metacognition event
        """
        # Map the metacognition event to a cognitive engine event
        if event.event_type in self.event_mapping:
            cognitive_event_type = self.event_mapping[event.event_type]
            
            # Convert the metacognition event to a cognitive engine event
            cognitive_event = self._convert_to_cognitive_event(event)
            
            # Notify subscribers
            self._notify_event_subscribers(cognitive_event_type, cognitive_event)
            
            # Forward to cognitive engine if available
            if self.cognitive_engine:
                asyncio.create_task(self._forward_to_cognitive_engine(
                    cognitive_event_type, cognitive_event
                ))
    
    def _convert_to_cognitive_event(self, event: MetacognitiveEvent) -> Dict[str, Any]:
        """
        Convert a metacognition event to a cognitive engine event.
        
        Args:
            event: The metacognition event
            
        Returns:
            The cognitive engine event
        """
        cognitive_event = {
            "id": str(id(event)),
            "type": self.event_mapping.get(event.event_type, "unknown"),
            "timestamp": event.timestamp,
            "source": "metacognition_adapter",
            "original_source": event.source_component,
            "details": {}
        }
        
        # Convert event-specific details
        if event.event_type == "anomaly_detected":
            cognitive_event["details"] = {
                "anomaly_type": event.details.get("anomaly_type", "unknown"),
                "severity": event.details.get("severity", 0.5),
                "affected_component": event.details.get("affected_component", "unknown"),
                "description": event.details.get("description", "")
            }
        elif event.event_type == "diagnostic_report_generated":
            cognitive_event["details"] = {
                "report_id": event.details.get("report_id", ""),
                "finding_count": event.details.get("finding_count", 0)
            }
        elif event.event_type == "proposals_generated":
            cognitive_event["details"] = {
                "proposal_count": event.details.get("proposal_count", 0),
                "approved_count": event.details.get("approved_count", 0)
            }
        elif event.event_type == "modification_executed":
            cognitive_event["details"] = {
                "proposal_id": event.details.get("proposal_id", ""),
                "plan_id": event.details.get("plan_id", ""),
                "result_id": event.details.get("result_id", ""),
                "success": event.details.get("success", False)
            }
        else:
            cognitive_event["details"] = event.details
        
        return cognitive_event
    
    async def _forward_to_cognitive_engine(self, event_type: str, event: Dict[str, Any]) -> None:
        """
        Forward an event to the cognitive engine.
        
        Args:
            event_type: The event type
            event: The event data
        """
        if not self.cognitive_engine:
            return
        
        try:
            # Convert to a thought
            thought = Thought(
                id=event["id"],
                content=f"Event: {event_type}",
                type="event",
                priority=self._get_priority_for_event(event_type),
                metadata={
                    "event_type": event_type,
                    "event_data": event
                }
            )
            
            # Create cognitive context
            context = CognitiveContext(
                attention_focus=event_type,
                cognitive_load=0.5,  # Default value
                metadata={
                    "source": "metacognition_adapter",
                    "event_type": event_type
                }
            )
            
            # Process the thought
            resources = {"priority": "high"}  # Simplified resource allocation
            await self.cognitive_engine.process_thought(
                {
                    "thought": thought.__dict__,
                    "context": context.__dict__
                },
                resources
            )
        except Exception as e:
            logger.error(f"Error forwarding event to cognitive engine: {e}")
    
    def _get_priority_for_event(self, event_type: str) -> float:
        """
        Get the priority for an event type.
        
        Args:
            event_type: The event type
            
        Returns:
            The priority (0.0 to 1.0)
        """
        priority_mapping = {
            "cognitive_anomaly": 0.9,
            "cognitive_diagnosis": 0.7,
            "cognitive_planning": 0.6,
            "cognitive_adaptation": 0.8
        }
        
        return priority_mapping.get(event_type, 0.5)
    
    def subscribe_to_event(self, event_type: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Subscribe to events.
        
        Args:
            event_type: Type of event to subscribe to, or "*" for all events
            callback: Function to call when the event occurs
        """
        if event_type not in self.event_subscribers:
            self.event_subscribers[event_type] = []
        
        self.event_subscribers[event_type].append(callback)
    
    def unsubscribe_from_event(self, event_type: str, callback: Callable[[Dict[str, Any]], None]) -> bool:
        """
        Unsubscribe from events.
        
        Args:
            event_type: Type of event to unsubscribe from
            callback: Function to remove from subscribers
            
        Returns:
            True if the callback was removed, False otherwise
        """
        if event_type not in self.event_subscribers:
            return False
        
        try:
            self.event_subscribers[event_type].remove(callback)
            return True
        except ValueError:
            return False
    
    def _notify_event_subscribers(self, event_type: str, event: Dict[str, Any]) -> None:
        """
        Notify subscribers of an event.
        
        Args:
            event_type: The event type
            event: The event data
        """
        # Notify subscribers for this event type
        if event_type in self.event_subscribers:
            for callback in self.event_subscribers[event_type]:
                try:
                    callback(event)
                except Exception as e:
                    logger.error(f"Error in event subscriber callback: {e}")
        
        # Notify subscribers for all events
        if "*" in self.event_subscribers:
            for callback in self.event_subscribers["*"]:
                try:
                    callback(event)
                except Exception as e:
                    logger.error(f"Error in event subscriber callback: {e}")
    
    async def convert_thought_to_diagnostic(self, thought: Thought) -> DiagnosticFinding:
        """
        Convert a thought to a diagnostic finding.
        
        Args:
            thought: The thought to convert
            
        Returns:
            The diagnostic finding
        """
        finding = DiagnosticFinding(
            finding_id=thought.id,
            finding_type="cognitive_insight",
            affected_component=thought.metadata.get("affected_component", "unknown"),
            severity=thought.priority,
            description=thought.content,
            metadata=thought.metadata
        )
        
        return finding
    
    async def convert_reflection_to_proposal(self, reflection: Reflection) -> ModificationProposal:
        """
        Convert a reflection to a modification proposal.
        
        Args:
            reflection: The reflection to convert
            
        Returns:
            The modification proposal
        """
        proposal = ModificationProposal(
            proposal_id=reflection.id,
            diagnostic_finding_ids=[reflection.thought_id],
            description=reflection.content,
            modification_type="cognitive_adaptation",
            risk_level="low",
            status=ModificationStatus.PROPOSED,
            metadata=reflection.metadata
        )
        
        return proposal
    
    async def get_cognitive_context_from_metacognition(self) -> CognitiveContext:
        """
        Get cognitive context from metacognition state.
        
        Returns:
            The cognitive context
        """
        status = self.metacognition_manager.get_current_status()
        
        context = CognitiveContext(
            attention_focus=status["current_phase"],
            cognitive_load=0.5,  # Default value
            metadata={
                "metacognition_mode": status["current_mode"],
                "metacognition_phase": status["current_phase"],
                "components": status["components"]
            }
        )
        
        return context
    
    async def set_cognitive_engine(self, cognitive_engine: CognitiveEngineInterface) -> None:
        """
        Set the cognitive engine reference.
        
        Args:
            cognitive_engine: The cognitive engine
        """
        self.cognitive_engine = cognitive_engine