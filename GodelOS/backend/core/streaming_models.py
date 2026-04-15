"""
Unified Streaming Models for GödelOS

This module provides the core data models and schemas for the unified streaming architecture,
replacing the fragmented streaming implementations across multiple services.
"""

import asyncio
import time
import uuid
from collections import deque
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Deque
from pydantic import BaseModel, Field
from fastapi import WebSocket


class EventType(Enum):
    """Unified event types for all streaming services."""
    # Core cognitive events
    COGNITIVE_STATE = "cognitive_state"
    COGNITIVE_LOOP = "cognitive_loop"
    CONSCIOUSNESS_UPDATE = "consciousness_update"
    
    # Knowledge and learning events
    KNOWLEDGE_UPDATE = "knowledge_update"
    KNOWLEDGE_GRAPH_EVOLUTION = "knowledge_graph_evolution"
    LEARNING_PROGRESS = "learning_progress"
    
    # Transparency and observability
    TRANSPARENCY_EVENT = "transparency_event"
    REASONING_TRACE = "reasoning_trace"
    DECISION_LOG = "decision_log"
    
    # System events
    SYSTEM_STATUS = "system_status"
    HEALTH_UPDATE = "health_update"
    METRICS_UPDATE = "metrics_update"
    
    # Connection management
    CONNECTION_STATUS = "connection_status"
    PING = "ping"
    PONG = "pong"


class EventPriority(Enum):
    """Event priority levels for routing and delivery."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4
    SYSTEM = 5


class GranularityLevel(Enum):
    """Client-specific event granularity preferences."""
    MINIMAL = "minimal"      # Only critical events
    STANDARD = "standard"    # Normal operational events
    DETAILED = "detailed"    # Detailed cognitive processes
    DEBUG = "debug"         # Full debugging information


class CognitiveEvent(BaseModel):
    """Unified event model for all streaming services."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: EventType
    timestamp: datetime = Field(default_factory=datetime.now)
    data: Dict[str, Any]
    source: str = "godelos_system"
    priority: EventPriority = EventPriority.NORMAL
    target_clients: Optional[List[str]] = None
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None
    
    class Config:
        use_enum_values = True
    
    def to_websocket_message(self) -> Dict[str, Any]:
        """Convert event to WebSocket message format."""
        return {
            "id": self.id,
            "type": self.type.value,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "source": self.source,
            "priority": self.priority.value,
            "session_id": self.session_id,
            "correlation_id": self.correlation_id
        }


class ClientConnection(BaseModel):
    """Client connection state and preferences."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    websocket: Optional[WebSocket] = Field(exclude=True)  # Not serialized
    subscriptions: Set[EventType] = Field(default_factory=set)
    granularity: GranularityLevel = GranularityLevel.STANDARD
    connected_at: datetime = Field(default_factory=datetime.now)
    last_ping: datetime = Field(default_factory=datetime.now)
    events_sent: int = 0
    events_received: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        arbitrary_types_allowed = True
        use_enum_values = True
    
    def is_active(self) -> bool:
        """Check if connection is still active."""
        if not self.websocket:
            return False
        
        # Consider connection stale if no ping in last 60 seconds
        time_since_ping = (datetime.now() - self.last_ping).total_seconds()
        return time_since_ping < 60
    
    def should_receive_event(self, event: CognitiveEvent) -> bool:
        """Determine if this client should receive the given event."""
        # Check subscription filter
        if self.subscriptions and event.type not in self.subscriptions:
            return False
        
        # Check target client filter
        if event.target_clients and self.id not in event.target_clients:
            return False
        
        # Check granularity filter
        if self.granularity == GranularityLevel.MINIMAL:
            return event.priority in [EventPriority.CRITICAL, EventPriority.SYSTEM]
        elif self.granularity == GranularityLevel.STANDARD:
            return event.priority in [EventPriority.NORMAL, EventPriority.HIGH, EventPriority.CRITICAL, EventPriority.SYSTEM]
        # DETAILED and DEBUG receive all events
        
        return True
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_ping = datetime.now()


class StreamingState(BaseModel):
    """Unified state store for all streaming data."""
    cognitive_state: Dict[str, Any] = Field(default_factory=dict)
    consciousness_metrics: Dict[str, float] = Field(default_factory=dict)
    knowledge_graph_stats: Dict[str, Any] = Field(default_factory=dict)
    system_health: Dict[str, Any] = Field(default_factory=dict)
    
    # Event history (in-memory circular buffer)
    recent_events: Deque[CognitiveEvent] = Field(default_factory=lambda: deque(maxlen=1000))
    
    def update_cognitive_state(self, state: Dict[str, Any]):
        """Thread-safe update of cognitive state."""
        self.cognitive_state.update(state)
    
    def update_consciousness_metrics(self, metrics: Dict[str, float]):
        """Update consciousness assessment metrics."""
        self.consciousness_metrics.update(metrics)
    
    def add_event(self, event: CognitiveEvent):
        """Add event to history buffer."""
        self.recent_events.append(event)
    
    def get_recent_events(self, limit: int = 50, event_types: Optional[List[EventType]] = None) -> List[CognitiveEvent]:
        """Get recent events with optional filtering."""
        events = list(self.recent_events)
        
        if event_types:
            events = [e for e in events if e.type in event_types]
        
        return events[-limit:]
    
    def get_client_initial_state(self, client: ClientConnection) -> Dict[str, Any]:
        """Get initial state data for a new client connection."""
        return {
            "cognitive_state": self.cognitive_state,
            "consciousness_metrics": self.consciousness_metrics,
            "knowledge_graph_stats": self.knowledge_graph_stats,
            "system_health": self.system_health,
            "connection_info": {
                "client_id": client.id,
                "granularity": client.granularity.value,
                "subscriptions": [s.value for s in client.subscriptions]
            }
        }


class ClientMessage(BaseModel):
    """Messages sent from client to server."""
    type: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        use_enum_values = True


class SubscriptionRequest(BaseModel):
    """Client subscription management request."""
    action: str  # "subscribe" or "unsubscribe"
    event_types: List[EventType]
    granularity: Optional[GranularityLevel] = None


class ConnectionStats(BaseModel):
    """Statistics for the unified streaming service."""
    total_connections: int = 0
    active_connections: int = 0
    total_events_sent: int = 0
    events_per_second: float = 0.0
    average_latency_ms: float = 0.0
    connection_uptime_seconds: float = 0.0
    memory_usage_mb: float = 0.0
    
    # Per event type statistics
    event_type_counts: Dict[str, int] = Field(default_factory=dict)
    
    def update_event_stats(self, event_type: EventType):
        """Update event type statistics."""
        type_key = event_type.value
        self.event_type_counts[type_key] = self.event_type_counts.get(type_key, 0) + 1
        self.total_events_sent += 1
