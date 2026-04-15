"""
Stream of Consciousness Coordinator for real-time cognitive event streaming.

This module manages real-time streaming of cognitive events through WebSocket
connections with configurable granularity levels and performance optimization.
"""

import asyncio
import logging
import json
import time
from typing import Any, Dict, List, Optional, Set
from collections import deque
from datetime import datetime
import weakref

from .cognitive_models import (
    CognitiveEvent, CognitiveEventType, GranularityLevel,
    StreamingMetrics, serialize_cognitive_event, filter_events_by_granularity
)

logger = logging.getLogger(__name__)


class StreamOfConsciousnessCoordinator:
    """
    Coordinates real-time streaming of cognitive events with:
    - Configurable granularity filtering
    - Performance optimization
    - Client connection management
    - Event buffering and rate limiting
    """
    
    def __init__(
        self,
        websocket_manager=None,
        config=None
    ):
        """
        Initialize the stream coordinator.
        
        Args:
            websocket_manager: WebSocket manager for connections
            config: Streaming configuration
        """
        self.websocket_manager = websocket_manager
        self.config = config or self._default_config()
        
        # Event streaming state
        self.is_streaming = False
        self.event_sequence = 0
        
        # Event buffering
        self.event_buffer = deque(maxlen=self.config.buffer_size)
        self.event_history = deque(maxlen=self.config.buffer_size * 2)
        
        # Client management
        self.connected_clients: Dict[str, Dict[str, Any]] = {}
        self.client_subscriptions: Dict[str, Set[CognitiveEventType]] = {}
        self.client_granularity: Dict[str, GranularityLevel] = {}
        
        # Performance tracking
        self.metrics = StreamingMetrics()
        self.last_metrics_update = time.time()
        
        # Rate limiting
        self.events_this_second = 0
        self.current_second = int(time.time())
        
        # Background tasks
        self.background_tasks: Set[asyncio.Task] = set()
        
        logger.info("StreamOfConsciousnessCoordinator initialized")
    
    async def start(self) -> None:
        """Start the stream coordinator."""
        if self.is_streaming:
            logger.warning("Stream coordinator already running")
            return
        
        self.is_streaming = True
        
        # Start background tasks
        metrics_task = asyncio.create_task(self._metrics_update_loop())
        self.background_tasks.add(metrics_task)
        
        buffer_cleanup_task = asyncio.create_task(self._buffer_cleanup_loop())
        self.background_tasks.add(buffer_cleanup_task)
        
        logger.info("Stream coordinator started")
    
    async def stop(self) -> None:
        """Stop the stream coordinator."""
        if not self.is_streaming:
            return
        
        self.is_streaming = False
        
        # Cancel background tasks
        for task in self.background_tasks:
            if not task.done():
                task.cancel()
        
        # Wait for tasks to complete
        if self.background_tasks:
            await asyncio.gather(*self.background_tasks, return_exceptions=True)
        
        # Clear client connections
        self.connected_clients.clear()
        self.client_subscriptions.clear()
        self.client_granularity.clear()
        
        logger.info("Stream coordinator stopped")
    
    async def emit_event(self, event: CognitiveEvent) -> None:
        """
        Emit a cognitive event to all subscribed clients.
        
        Args:
            event: The cognitive event to emit
        """
        if not self.is_streaming:
            return
        
        # Check rate limiting
        current_second = int(time.time())
        if current_second != self.current_second:
            self.current_second = current_second
            self.events_this_second = 0
        
        if self.events_this_second >= self.config.max_event_rate:
            self.metrics.total_events_dropped += 1
            logger.debug("Event dropped due to rate limiting")
            return
        
        self.events_this_second += 1
        
        # Assign sequence number
        event.sequence_number = self.event_sequence
        self.event_sequence += 1
        
        # Add to buffers
        self.event_buffer.append(event)
        self.event_history.append(event)
        
        # Update metrics
        self.metrics.total_events_sent += 1
        
        # Broadcast to clients
        await self._broadcast_event(event)
    
    async def register_client(
        self,
        client_id: str,
        websocket,
        granularity: GranularityLevel = GranularityLevel.STANDARD,
        subscriptions: Optional[Set[CognitiveEventType]] = None
    ) -> bool:
        """
        Register a new client for cognitive event streaming.
        
        Args:
            client_id: Unique client identifier
            websocket: WebSocket connection
            granularity: Event granularity level
            subscriptions: Set of event types to subscribe to
            
        Returns:
            True if registration successful
        """
        try:
            self.connected_clients[client_id] = {
                'websocket': websocket,
                'connected_at': datetime.now(),
                'events_sent': 0,
                'last_ping': time.time()
            }
            
            self.client_granularity[client_id] = granularity
            self.client_subscriptions[client_id] = (
                subscriptions or set(CognitiveEventType)
            )
            
            # Update metrics
            self.metrics.connected_clients = len(self.connected_clients)
            
            # Send welcome event
            welcome_event = CognitiveEvent(
                type=CognitiveEventType.SYSTEM_STARTUP,
                timestamp=datetime.now(),
                data={
                    'message': 'Connected to cognitive stream',
                    'client_id': client_id,
                    'granularity': granularity.value
                },
                source='StreamCoordinator',
                granularity_level=GranularityLevel.MINIMAL
            )
            
            await self._send_event_to_client(client_id, welcome_event)
            
            logger.info(f"Client {client_id} registered for cognitive streaming")
            return True
            
        except Exception as e:
            logger.error(f"Error registering client {client_id}: {e}")
            return False
    
    async def unregister_client(self, client_id: str) -> None:
        """
        Unregister a client from cognitive event streaming.
        
        Args:
            client_id: Client identifier to unregister
        """
        if client_id in self.connected_clients:
            del self.connected_clients[client_id]
        
        if client_id in self.client_granularity:
            del self.client_granularity[client_id]
        
        if client_id in self.client_subscriptions:
            del self.client_subscriptions[client_id]
        
        # Update metrics
        self.metrics.connected_clients = len(self.connected_clients)
        
        logger.info(f"Client {client_id} unregistered from cognitive streaming")
    
    async def configure_client(
        self,
        client_id: str,
        granularity: Optional[GranularityLevel] = None,
        subscriptions: Optional[Set[CognitiveEventType]] = None
    ) -> bool:
        """
        Configure streaming settings for a client.
        
        Args:
            client_id: Client identifier
            granularity: New granularity level
            subscriptions: New event subscriptions
            
        Returns:
            True if configuration successful
        """
        if client_id not in self.connected_clients:
            logger.warning(f"Cannot configure unknown client: {client_id}")
            return False
        
        try:
            if granularity is not None:
                self.client_granularity[client_id] = granularity
            
            if subscriptions is not None:
                self.client_subscriptions[client_id] = subscriptions
            
            # Send configuration update event
            config_event = CognitiveEvent(
                type=CognitiveEventType.CONFIGURATION_CHANGED,
                timestamp=datetime.now(),
                data={
                    'client_id': client_id,
                    'granularity': self.client_granularity[client_id].value,
                    'subscriptions': [sub.value for sub in self.client_subscriptions[client_id]]
                },
                source='StreamCoordinator',
                granularity_level=GranularityLevel.MINIMAL
            )
            
            await self._send_event_to_client(client_id, config_event)
            
            logger.info(f"Updated configuration for client {client_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error configuring client {client_id}: {e}")
            return False
    
    async def get_event_history(
        self,
        client_id: str,
        limit: int = 100,
        event_types: Optional[Set[CognitiveEventType]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent event history for a client.
        
        Args:
            client_id: Client identifier
            limit: Maximum number of events to return
            event_types: Filter by specific event types
            
        Returns:
            List of event dictionaries
        """
        if client_id not in self.connected_clients:
            return []
        
        # Get client configuration
        granularity = self.client_granularity.get(client_id, GranularityLevel.STANDARD)
        subscriptions = self.client_subscriptions.get(client_id, set(CognitiveEventType))
        
        # Filter events
        filtered_events = []
        for event in reversed(self.event_history):
            # Check subscriptions
            if event.type not in subscriptions:
                continue
            
            # Check event type filter
            if event_types and event.type not in event_types:
                continue
            
            # Check granularity
            if not self._should_send_event_to_client(event, granularity):
                continue
            
            filtered_events.append(event.to_dict())
            
            if len(filtered_events) >= limit:
                break
        
        return list(reversed(filtered_events))
    
    async def get_client_count(self) -> int:
        """Get the number of connected clients."""
        return len(self.connected_clients)
    
    async def get_event_rate(self) -> float:
        """Get the current event rate (events per second)."""
        return self.metrics.events_per_second
    
    async def get_streaming_metrics(self) -> Dict[str, Any]:
        """Get comprehensive streaming metrics."""
        return self.metrics.to_dict()
    
    async def configure(self, config) -> None:
        """Update streaming configuration."""
        self.config = config
        logger.info("Stream coordinator configuration updated")
    
    async def broadcast_external_event(
        self, 
        event_type: str, 
        data: Dict[str, Any],
        source: str = "ExternalAPI",
        granularity_level: GranularityLevel = GranularityLevel.STANDARD
    ) -> None:
        """
        Broadcast an external event to all connected clients.
        
        Args:
            event_type: Type of the event
            data: Event data
            source: Source of the event
            granularity_level: Event granularity level
        """
        if not self.is_streaming:
            logger.warning("Cannot broadcast event: stream coordinator not running")
            return
        
        try:
            # Create a CognitiveEvent from the external data
            cognitive_event = CognitiveEvent(
                type=CognitiveEventType.EXTERNAL_EVENT,  # We'll use a generic type
                timestamp=datetime.now(),
                data={
                    "event_type": event_type,
                    **data
                },
                source=source,
                granularity_level=granularity_level,
                processing_context={
                    "external_api": True,
                    "original_type": event_type
                }
            )
            
            # Add to event buffer and history
            self.event_buffer.append(cognitive_event)
            self.event_history.append(cognitive_event)
            
            # Broadcast to all clients
            await self._broadcast_event(cognitive_event)
            
            # Update metrics
            self.metrics.total_events_sent += 1
            
            logger.debug(f"Broadcasted external event: {event_type}")
            
        except Exception as e:
            logger.error(f"Error broadcasting external event: {e}")

    # Private methods
    
    def _default_config(self):
        """Create default streaming configuration."""
        from .enhanced_metacognition_manager import CognitiveStreamingConfig
        return CognitiveStreamingConfig()
    
    async def _broadcast_event(self, event: CognitiveEvent) -> None:
        """Broadcast an event to all appropriate clients."""
        if not self.connected_clients:
            return
        
        # Create broadcast tasks for eligible clients
        broadcast_tasks = []
        
        for client_id in list(self.connected_clients.keys()):
            # Check if client should receive this event
            if self._should_send_event_to_client_id(client_id, event):
                task = asyncio.create_task(
                    self._send_event_to_client(client_id, event)
                )
                broadcast_tasks.append(task)
        
        # Execute broadcasts
        if broadcast_tasks:
            results = await asyncio.gather(*broadcast_tasks, return_exceptions=True)
            
            # Handle any connection errors
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.metrics.connection_errors += 1
                    logger.warning(f"Error broadcasting to client: {result}")
    
    def _should_send_event_to_client_id(self, client_id: str, event: CognitiveEvent) -> bool:
        """Check if an event should be sent to a specific client."""
        # Check subscriptions
        subscriptions = self.client_subscriptions.get(client_id, set())
        if event.type not in subscriptions:
            return False
        
        # Check granularity
        granularity = self.client_granularity.get(client_id, GranularityLevel.STANDARD)
        return self._should_send_event_to_client(event, granularity)
    
    def _should_send_event_to_client(
        self, event: CognitiveEvent, granularity: GranularityLevel
    ) -> bool:
        """Check if an event should be sent based on granularity."""
        granularity_order = {
            GranularityLevel.MINIMAL: 0,
            GranularityLevel.STANDARD: 1,
            GranularityLevel.DETAILED: 2,
            GranularityLevel.DEBUG: 3
        }
        
        max_level = granularity_order[granularity]
        event_level = granularity_order[event.granularity_level]
        
        return event_level <= max_level
    
    async def _send_event_to_client(self, client_id: str, event: CognitiveEvent) -> None:
        """Send an event to a specific client."""
        if client_id not in self.connected_clients:
            return
        
        client_info = self.connected_clients[client_id]
        websocket = client_info['websocket']
        
        try:
            # Serialize event
            event_data = serialize_cognitive_event(event)
            
            # Send to client
            if hasattr(websocket, 'send_text'):
                await websocket.send_text(event_data)
            elif hasattr(websocket, 'send'):
                await websocket.send(event_data)
            else:
                # Generic send method
                await websocket.send_text(event_data)
            
            # Update client metrics
            client_info['events_sent'] += 1
            client_info['last_ping'] = time.time()
            
        except Exception as e:
            logger.warning(f"Error sending event to client {client_id}: {e}")
            
            # Remove disconnected client
            await self.unregister_client(client_id)
            
            self.metrics.connection_errors += 1
    
    async def _metrics_update_loop(self) -> None:
        """Background loop to update streaming metrics."""
        while self.is_streaming:
            try:
                current_time = time.time()
                time_diff = current_time - self.last_metrics_update
                
                if time_diff >= 1.0:  # Update every second
                    # Calculate events per second
                    events_in_buffer = len(self.event_buffer)
                    self.metrics.events_per_second = events_in_buffer / time_diff
                    
                    # Update buffer utilization
                    self.metrics.buffer_utilization = events_in_buffer / self.config.buffer_size
                    
                    # Update connected clients count
                    self.metrics.connected_clients = len(self.connected_clients)
                    
                    # Update timestamp
                    self.metrics.last_updated = datetime.now()
                    self.last_metrics_update = current_time
                
                await asyncio.sleep(1.0)
                
            except Exception as e:
                logger.error(f"Error in metrics update loop: {e}")
                await asyncio.sleep(5.0)
    
    async def _buffer_cleanup_loop(self) -> None:
        """Background loop to clean up old events from buffers."""
        while self.is_streaming:
            try:
                # Cleanup is handled automatically by deque maxlen
                # This loop can be used for additional cleanup logic
                
                # Remove stale client connections
                current_time = time.time()
                stale_clients = []
                
                for client_id, client_info in self.connected_clients.items():
                    # Check if client hasn't received events recently
                    if current_time - client_info['last_ping'] > self.config.websocket_timeout:
                        stale_clients.append(client_id)
                
                # Remove stale clients
                for client_id in stale_clients:
                    await self.unregister_client(client_id)
                    logger.info(f"Removed stale client: {client_id}")
                
                await asyncio.sleep(30.0)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in buffer cleanup loop: {e}")
                await asyncio.sleep(60.0)
