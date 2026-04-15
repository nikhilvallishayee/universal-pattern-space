"""
Real-Time Cognitive Transparency System

This module implements real-time streaming of cognitive processes through WebSocket
connections, providing transparency into the LLM cognitive architecture's decision
making, self-reflection, and consciousness simulation.
"""

import asyncio
import json
import logging
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Set
from fastapi import WebSocket, WebSocketDisconnect
import weakref

logger = logging.getLogger(__name__)

@dataclass
class CognitiveEvent:
    """Real-time cognitive event for transparency streaming"""
    timestamp: str
    event_type: str         # "reflection", "decision", "goal_creation", "consciousness_assessment"
    component: str          # Source cognitive component
    details: Dict           # Event-specific data
    llm_reasoning: str      # LLM's internal reasoning
    priority: int = 1       # Event priority (1-10)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)

@dataclass 
class CognitiveMetrics:
    """Cognitive transparency metrics"""
    events_streamed: int = 0
    active_connections: int = 0
    transparency_level: float = 0.0  # 0.0-1.0 visibility into processes
    decision_visibility: float = 0.0
    reasoning_depth: int = 0
    process_coverage: float = 0.0

class CognitiveTransparencyEngine:
    """
    Real-time cognitive transparency system that streams cognitive events
    and provides visibility into the LLM cognitive architecture's processes.
    """
    
    def __init__(self, websocket_manager=None):
        self.active_connections: Set[WebSocket] = set()
        self.event_buffer: List[CognitiveEvent] = []
        self.metrics = CognitiveMetrics()
        self.max_buffer_size = 1000
        self.transparency_enabled = True
        self.websocket_manager = websocket_manager  # Add reference to main websocket manager
        
        # Event type configurations
        self.event_types = {
            "consciousness_assessment": {"priority": 10, "stream": True},
            "meta_cognitive_reflection": {"priority": 9, "stream": True},
            "autonomous_goal_creation": {"priority": 8, "stream": True},
            "decision_making": {"priority": 7, "stream": True},
            "knowledge_integration": {"priority": 6, "stream": True},
            "self_monitoring": {"priority": 5, "stream": True},
            "component_coordination": {"priority": 4, "stream": True},
            "learning_progress": {"priority": 3, "stream": True},
            "state_transition": {"priority": 2, "stream": True},
            "routine_processing": {"priority": 1, "stream": False}
        }
    
    async def connect_client(self, websocket: WebSocket) -> None:
        """Connect new WebSocket client for cognitive transparency"""
        try:
            await websocket.accept()
            self.active_connections.add(websocket)
            self.metrics.active_connections = len(self.active_connections)
            
            logger.info(f"New cognitive transparency client connected. Total: {self.metrics.active_connections}")
            
            # Send initial state
            await self._send_initial_state(websocket)
            
        except Exception as e:
            logger.error(f"Error connecting transparency client: {e}")
            await self.disconnect_client(websocket)
    
    async def disconnect_client(self, websocket: WebSocket) -> None:
        """Disconnect WebSocket client"""
        try:
            self.active_connections.discard(websocket)
            self.metrics.active_connections = len(self.active_connections)
            logger.info(f"Cognitive transparency client disconnected. Remaining: {self.metrics.active_connections}")
        except Exception as e:
            logger.error(f"Error disconnecting transparency client: {e}")
    
    async def stream_cognitive_event(self, event: CognitiveEvent) -> None:
        """Stream cognitive event to all connected clients"""
        if not self.transparency_enabled:
            return
            
        # Add to buffer
        self.event_buffer.append(event)
        if len(self.event_buffer) > self.max_buffer_size:
            self.event_buffer.pop(0)
        
        # Check if event should be streamed
        event_config = self.event_types.get(event.event_type, {"stream": True})
        if not event_config.get("stream", True):
            return
        
        # Update metrics
        self.metrics.events_streamed += 1
        self._update_transparency_metrics(event)
        
        # Stream to all connected clients
        # Always try to broadcast through main websocket manager first, then fallback to direct connections
        message = {
            "type": "cognitive_event",
            "data": event.to_dict()
        }
        await self._broadcast_message(message)
    
    async def log_consciousness_assessment(self, assessment_data: Dict, reasoning: str) -> None:
        """Log consciousness assessment event"""
        event = CognitiveEvent(
            timestamp=datetime.now().isoformat(),
            event_type="consciousness_assessment",
            component="consciousness_engine",
            details=assessment_data,
            llm_reasoning=reasoning,
            priority=10
        )
        await self.stream_cognitive_event(event)
    
    async def log_meta_cognitive_reflection(self, reflection_data: Dict, depth: int, reasoning: str) -> None:
        """Log meta-cognitive reflection event"""
        event = CognitiveEvent(
            timestamp=datetime.now().isoformat(),
            event_type="meta_cognitive_reflection",
            component="cognitive_manager",
            details={
                "reflection_depth": depth,
                "self_analysis": reflection_data,
                "recursive_level": depth
            },
            llm_reasoning=reasoning,
            priority=9
        )
        await self.stream_cognitive_event(event)
    
    async def log_autonomous_goal_creation(self, goals: List[str], context: Dict, reasoning: str) -> None:
        """Log autonomous goal creation event"""
        event = CognitiveEvent(
            timestamp=datetime.now().isoformat(),
            event_type="autonomous_goal_creation",
            component="goal_system",
            details={
                "generated_goals": goals,
                "goal_count": len(goals),
                "context": context,
                "autonomous": True
            },
            llm_reasoning=reasoning,
            priority=8
        )
        await self.stream_cognitive_event(event)
    
    async def log_decision_making(self, decision: str, reasoning: str, confidence: float, alternatives: List[str] = None) -> None:
        """Log decision making process"""
        event = CognitiveEvent(
            timestamp=datetime.now().isoformat(),
            event_type="decision_making",
            component="llm_cognitive_driver",
            details={
                "decision": decision,
                "confidence": confidence,
                "alternatives_considered": alternatives or [],
                "decision_factors": []
            },
            llm_reasoning=reasoning,
            priority=7
        )
        await self.stream_cognitive_event(event)
    
    async def log_knowledge_integration(self, domains: List[str], connections: int, novel_insights: List[str], reasoning: str) -> None:
        """Log knowledge graph integration event"""
        event = CognitiveEvent(
            timestamp=datetime.now().isoformat(),
            event_type="knowledge_integration",
            component="knowledge_graph",
            details={
                "domains_integrated": domains,
                "connections_made": connections,
                "novel_insights": novel_insights,
                "cross_domain": len(domains) > 1
            },
            llm_reasoning=reasoning,
            priority=6
        )
        await self.stream_cognitive_event(event)
    
    async def log_component_coordination(self, components: List[str], coordination_type: str, success: bool, reasoning: str) -> None:
        """Log component coordination event"""
        event = CognitiveEvent(
            timestamp=datetime.now().isoformat(),
            event_type="component_coordination",
            component="cognitive_manager",
            details={
                "components_involved": components,
                "coordination_type": coordination_type,
                "coordination_success": success,
                "integration_level": len(components)
            },
            llm_reasoning=reasoning,
            priority=4
        )
        await self.stream_cognitive_event(event)
    
    async def log_cognitive_event(self, event_type: str, content: str, metadata: Dict[str, Any] = None, reasoning: str = "") -> None:
        """Generic cognitive event logging method"""
        event = CognitiveEvent(
            timestamp=datetime.now().isoformat(),
            event_type=event_type,
            component="cognitive_manager",
            details={
                "content": content,
                "metadata": metadata or {},
                "context": "knowledge_graph_evolution"
            },
            llm_reasoning=reasoning,
            priority=5
        )
        await self.stream_cognitive_event(event)
    
    async def get_transparency_metrics(self) -> Dict:
        """Get current transparency metrics"""
        return {
            "transparency_metrics": asdict(self.metrics),
            "event_buffer_size": len(self.event_buffer),
            "recent_events": [event.to_dict() for event in self.event_buffer[-10:]],
            "event_type_counts": self._get_event_type_counts(),
            "transparency_status": "active" if self.transparency_enabled else "disabled"
        }
    
    async def get_cognitive_activity_summary(self) -> Dict:
        """Get summary of recent cognitive activity"""
        recent_events = self.event_buffer[-50:] if len(self.event_buffer) >= 50 else self.event_buffer
        
        return {
            "total_events": len(self.event_buffer),
            "recent_activity": len(recent_events),
            "consciousness_assessments": len([e for e in recent_events if e.event_type == "consciousness_assessment"]),
            "meta_cognitive_reflections": len([e for e in recent_events if e.event_type == "meta_cognitive_reflection"]),
            "autonomous_goals_created": len([e for e in recent_events if e.event_type == "autonomous_goal_creation"]),
            "decisions_made": len([e for e in recent_events if e.event_type == "decision_making"]),
            "knowledge_integrations": len([e for e in recent_events if e.event_type == "knowledge_integration"]),
            "average_reasoning_depth": self._calculate_average_reasoning_depth(recent_events),
            "transparency_level": self.metrics.transparency_level
        }
    
    def _update_transparency_metrics(self, event: CognitiveEvent) -> None:
        """Update transparency metrics based on event"""
        # Update reasoning depth
        reasoning_words = len(event.llm_reasoning.split()) if event.llm_reasoning else 0
        self.metrics.reasoning_depth = max(self.metrics.reasoning_depth, reasoning_words)
        
        # Update transparency level based on event priority and detail richness
        detail_richness = len(str(event.details)) / 100.0  # Rough measure
        event_contribution = (event.priority / 10.0) * min(detail_richness, 1.0)
        
        # Exponential moving average
        alpha = 0.1
        self.metrics.transparency_level = (alpha * event_contribution + 
                                         (1 - alpha) * self.metrics.transparency_level)
        
        # Update decision visibility for decision-related events
        if event.event_type in ["decision_making", "consciousness_assessment", "meta_cognitive_reflection"]:
            self.metrics.decision_visibility = min(1.0, self.metrics.decision_visibility + 0.1)
    
    def _get_event_type_counts(self) -> Dict[str, int]:
        """Get count of each event type in buffer"""
        counts = {}
        for event in self.event_buffer:
            counts[event.event_type] = counts.get(event.event_type, 0) + 1
        return counts
    
    def _calculate_average_reasoning_depth(self, events: List[CognitiveEvent]) -> float:
        """Calculate average reasoning depth from events"""
        if not events:
            return 0.0
        
        total_words = sum(len(event.llm_reasoning.split()) if event.llm_reasoning else 0 
                         for event in events)
        return total_words / len(events)
    
    async def _send_initial_state(self, websocket: WebSocket) -> None:
        """Send initial state to newly connected client"""
        try:
            initial_message = {
                "type": "initial_state",
                "data": {
                    "transparency_enabled": self.transparency_enabled,
                    "metrics": await self.get_transparency_metrics(),
                    "activity_summary": await self.get_cognitive_activity_summary(),
                    "message": "Connected to GödelOS cognitive transparency stream"
                }
            }
            await websocket.send_text(json.dumps(initial_message))
        except Exception as e:
            logger.error(f"Error sending initial state: {e}")
    
    async def _broadcast_message(self, message: Dict) -> None:
        """Broadcast message to all connected clients"""
        logger.info(f"🔍 TRANSPARENCY: Broadcasting {message.get('type', 'unknown')} event")
        
        # Use main websocket manager if available
        if self.websocket_manager:
            try:
                # Check if the websocket manager has connections using the has_connections method
                if hasattr(self.websocket_manager, 'has_connections') and self.websocket_manager.has_connections():
                    # Use broadcast_cognitive_update for proper cognitive event formatting.
                    # Pass raw inner event payload when possible to avoid double wrapping.
                    if hasattr(self.websocket_manager, 'broadcast_cognitive_update'):
                        payload = message
                        if isinstance(message, dict) and message.get('type') == 'cognitive_event' and isinstance(message.get('data'), dict):
                            payload = message.get('data')
                        await self.websocket_manager.broadcast_cognitive_update(payload)
                        logger.info(f"✅ TRANSPARENCY: Event broadcast successful: {message.get('type', 'unknown')}")
                        return
                    # Fallback to regular broadcast
                    elif hasattr(self.websocket_manager, 'broadcast'):
                        await self.websocket_manager.broadcast(message)
                        logger.info(f"✅ TRANSPARENCY: Event broadcast successful (fallback): {message.get('type', 'unknown')}")
                        return
                else:
                    logger.info("🔍 TRANSPARENCY: No active WebSocket connections")
            except Exception as e:
                logger.error(f"TRANSPARENCY broadcast error: {e}")
        else:
            logger.info("🔍 TRANSPARENCY: No WebSocket manager")
        
        # Fallback to direct connections
        if not self.active_connections:
            logger.info("🔍 TRANSPARENCY: No direct connections, event not broadcast")
            return
            logger.debug("No direct connections available for transparency broadcast")
            return
        
        message_json = json.dumps(message)
        disconnected_clients = set()
        
        for websocket in self.active_connections.copy():
            try:
                await websocket.send_text(message_json)
            except WebSocketDisconnect:
                disconnected_clients.add(websocket)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected_clients.add(websocket)
        
        # Clean up disconnected clients
        for websocket in disconnected_clients:
            await self.disconnect_client(websocket)

# Global transparency engine instance - will be initialized with websocket_manager later
transparency_engine = None

def initialize_transparency_engine(websocket_manager=None):
    """Initialize the global transparency engine with websocket manager"""
    global transparency_engine
    transparency_engine = CognitiveTransparencyEngine(websocket_manager=websocket_manager)
    return transparency_engine
