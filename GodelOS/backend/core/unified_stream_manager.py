"""
Unified Streaming Manager for GödelOS

This module provides the central streaming service that consolidates all WebSocket
connections and event distribution, replacing the fragmented streaming implementations.
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Set
from fastapi import WebSocket, WebSocketDisconnect

from .streaming_models import (
    CognitiveEvent, ClientConnection, StreamingState, ConnectionStats,
    EventType, EventPriority, GranularityLevel, ClientMessage, SubscriptionRequest
)

logger = logging.getLogger(__name__)


class EventRouter:
    """Efficient event routing with subscription-based filtering."""
    
    def __init__(self):
        self.subscription_index: Dict[EventType, Set[str]] = {}
        self.stats = ConnectionStats()
    
    def register_subscription(self, client_id: str, event_type: EventType):
        """Register a client subscription for an event type."""
        if event_type not in self.subscription_index:
            self.subscription_index[event_type] = set()
        self.subscription_index[event_type].add(client_id)
    
    def unregister_subscription(self, client_id: str, event_type: EventType):
        """Remove a client subscription for an event type."""
        if event_type in self.subscription_index:
            self.subscription_index[event_type].discard(client_id)
            if not self.subscription_index[event_type]:
                del self.subscription_index[event_type]
    
    def unregister_client(self, client_id: str):
        """Remove all subscriptions for a client."""
        for event_type in list(self.subscription_index.keys()):
            self.subscription_index[event_type].discard(client_id)
            if not self.subscription_index[event_type]:
                del self.subscription_index[event_type]
    
    def get_target_clients(self, event: CognitiveEvent) -> Set[str]:
        """Get client IDs that should receive this event based on subscriptions."""
        if event.target_clients:
            return set(event.target_clients)
        
        # If no specific targets, use subscription index
        return self.subscription_index.get(event.type, set())
    
    def update_stats(self, event: CognitiveEvent, delivered_count: int):
        """Update routing statistics."""
        self.stats.update_event_stats(event.type)


class UnifiedStreamingManager:
    """
    Central streaming service that consolidates all WebSocket connections
    and event distribution for GödelOS cognitive architecture.
    
    Replaces:
    - WebSocketManager (1400+ lines)
    - Continuous cognitive streaming background task
    - Enhanced cognitive API streaming
    - Transparency streaming endpoints
    """
    
    def __init__(self):
        self.connections: Dict[str, ClientConnection] = {}
        self.event_router = EventRouter()
        self.state_store = StreamingState()
        self.stats = ConnectionStats()
        
        # Background tasks
        self._keepalive_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # Performance tracking
        self._start_time = time.time()
        self._last_stats_update = time.time()
        
        logger.info("🔗 Unified Streaming Manager initialized")
    
    async def start_background_tasks(self):
        """Start background maintenance tasks."""
        if not self._keepalive_task:
            self._keepalive_task = asyncio.create_task(self._keepalive_loop())
        if not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        logger.info("✅ Background tasks started")
    
    async def stop_background_tasks(self):
        """Stop background maintenance tasks."""
        if self._keepalive_task:
            self._keepalive_task.cancel()
            try:
                await self._keepalive_task
            except asyncio.CancelledError:
                pass
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        logger.info("🛑 Background tasks stopped")
    
    async def connect_client(self, 
                           websocket: WebSocket,
                           subscriptions: Optional[List[str]] = None,
                           granularity: str = "standard",
                           client_id: Optional[str] = None) -> str:
        """
        Connect a new client to the unified streaming service.
        
        Args:
            websocket: FastAPI WebSocket connection
            subscriptions: List of event types to subscribe to
            granularity: Event granularity level (minimal, standard, detailed, debug)
            client_id: Optional client identifier
            
        Returns:
            Client ID for the connection
        """
        try:
            # Accept WebSocket connection
            await websocket.accept()
            
            # Create client connection
            connection = ClientConnection(
                id=client_id,
                websocket=websocket,
                granularity=GranularityLevel(granularity),
                subscriptions=set()
            )
            
            # Process subscriptions
            if subscriptions:
                for sub in subscriptions:
                    try:
                        event_type = EventType(sub)
                        connection.subscriptions.add(event_type)
                        self.event_router.register_subscription(connection.id, event_type)
                    except ValueError:
                        logger.warning(f"Invalid subscription type: {sub}")
            else:
                # Default subscriptions for new clients
                default_subs = [
                    EventType.COGNITIVE_STATE,
                    EventType.SYSTEM_STATUS,
                    EventType.CONNECTION_STATUS
                ]
                for event_type in default_subs:
                    connection.subscriptions.add(event_type)
                    self.event_router.register_subscription(connection.id, event_type)
            
            # Store connection
            self.connections[connection.id] = connection
            self.stats.total_connections += 1
            self.stats.active_connections += 1
            
            # Send initial state and connection confirmation
            await self._send_initial_state(connection)
            await self._send_connection_event(connection.id, "connected")
            
            logger.info(f"🔗 Client connected: {connection.id} with {len(connection.subscriptions)} subscriptions")
            return connection.id
            
        except Exception as e:
            logger.error(f"❌ Error connecting client: {e}")
            raise
    
    async def disconnect_client(self, client_id: str):
        """
        Disconnect a client and clean up resources.
        
        Args:
            client_id: Client identifier to disconnect
        """
        try:
            if client_id not in self.connections:
                logger.warning(f"⚠️ Attempted to disconnect unknown client: {client_id}")
                return
            
            connection = self.connections[client_id]
            
            # Clean up subscriptions
            self.event_router.unregister_client(client_id)
            
            # Close WebSocket if still open
            if connection.websocket:
                try:
                    await connection.websocket.close()
                except Exception as e:
                    logger.debug(f"WebSocket already closed: {e}")
            
            # Remove from connections
            del self.connections[client_id]
            self.stats.active_connections -= 1
            
            # Send disconnection event to other clients
            await self._send_connection_event(client_id, "disconnected")
            
            logger.info(f"🔌 Client disconnected: {client_id}")
            
        except Exception as e:
            logger.error(f"❌ Error disconnecting client {client_id}: {e}")
    
    async def handle_client_message(self, client_id: str, message: str):
        """
        Handle incoming message from a client.
        
        Args:
            client_id: Client identifier
            message: JSON message from client
        """
        try:
            if client_id not in self.connections:
                logger.warning(f"⚠️ Message from unknown client: {client_id}")
                return
            
            connection = self.connections[client_id]
            connection.events_received += 1
            connection.update_activity()
            
            # Parse message
            data = json.loads(message)
            client_msg = ClientMessage(**data)
            
            # Handle different message types
            if client_msg.type == "ping":
                await self._handle_ping(client_id)
            elif client_msg.type == "subscribe" or client_msg.type == "unsubscribe":
                await self._handle_subscription(client_id, client_msg)
            elif client_msg.type == "request_state":
                await self._send_current_state(client_id)
            else:
                logger.warning(f"⚠️ Unknown message type from {client_id}: {client_msg.type}")
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON from client {client_id}: {e}")
        except Exception as e:
            logger.error(f"❌ Error handling message from {client_id}: {e}")
    
    async def broadcast_event(self, event: CognitiveEvent):
        """
        Broadcast an event to relevant clients.
        
        Args:
            event: CognitiveEvent to broadcast
        """
        try:
            # Add to state store
            self.state_store.add_event(event)
            
            # Get target clients
            target_clients = self.event_router.get_target_clients(event)
            
            if not target_clients:
                logger.debug(f"No clients subscribed to event type: {event.type}")
                return
            
            # Send to each target client
            delivered_count = 0
            for client_id in target_clients:
                if await self._send_event_to_client(client_id, event):
                    delivered_count += 1
            
            # Update statistics
            self.event_router.update_stats(event, delivered_count)
            
            logger.debug(f"📡 Event {event.type} delivered to {delivered_count}/{len(target_clients)} clients")
            
        except Exception as e:
            logger.error(f"❌ Error broadcasting event: {e}")
    
    async def update_cognitive_state(self, state: Dict[str, any]):
        """Update cognitive state and broadcast to subscribers."""
        self.state_store.update_cognitive_state(state)
        
        event = CognitiveEvent(
            type=EventType.COGNITIVE_STATE,
            data={"cognitive_state": state},
            priority=EventPriority.NORMAL
        )
        await self.broadcast_event(event)
    
    async def update_consciousness_metrics(self, metrics: Dict[str, float]):
        """Update consciousness metrics and broadcast to subscribers."""
        self.state_store.update_consciousness_metrics(metrics)
        
        event = CognitiveEvent(
            type=EventType.CONSCIOUSNESS_UPDATE,
            data={"consciousness_metrics": metrics},
            priority=EventPriority.HIGH
        )
        await self.broadcast_event(event)
    
    def get_connection_stats(self) -> Dict[str, any]:
        """Get current connection and performance statistics."""
        current_time = time.time()
        uptime = current_time - self._start_time
        
        return {
            "total_connections": self.stats.total_connections,
            "active_connections": self.stats.active_connections,
            "total_events_sent": self.stats.total_events_sent,
            "uptime_seconds": uptime,
            "event_type_counts": dict(self.stats.event_type_counts),
            "recent_events_count": len(self.state_store.recent_events),
            "subscription_index_size": len(self.event_router.subscription_index)
        }
    
    def has_connections(self) -> bool:
        """Check if there are any active connections."""
        return len(self.connections) > 0
    
    # Private methods
    
    async def _send_initial_state(self, connection: ClientConnection):
        """Send initial state to a newly connected client."""
        initial_state = self.state_store.get_client_initial_state(connection)
        
        event = CognitiveEvent(
            type=EventType.CONNECTION_STATUS,
            data={
                "status": "initial_state",
                "state": initial_state
            },
            target_clients=[connection.id],
            priority=EventPriority.SYSTEM
        )
        
        await self._send_event_to_client(connection.id, event)
    
    async def _send_connection_event(self, client_id: str, status: str):
        """Send connection status event."""
        event = CognitiveEvent(
            type=EventType.CONNECTION_STATUS,
            data={
                "client_id": client_id,
                "status": status,
                "timestamp": time.time()
            },
            priority=EventPriority.SYSTEM
        )
        
        await self.broadcast_event(event)
    
    async def _send_event_to_client(self, client_id: str, event: CognitiveEvent) -> bool:
        """Send event to a specific client. Returns True if successful."""
        if client_id not in self.connections:
            return False
        
        connection = self.connections[client_id]
        
        # Check if client should receive this event
        if not connection.should_receive_event(event):
            return False
        
        try:
            message = event.to_websocket_message()
            await connection.websocket.send_text(json.dumps(message))
            connection.events_sent += 1
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to send event to client {client_id}: {e}")
            # Schedule disconnection for failed clients
            asyncio.create_task(self.disconnect_client(client_id))
            return False
    
    async def _handle_ping(self, client_id: str):
        """Handle ping message from client."""
        if client_id in self.connections:
            pong_event = CognitiveEvent(
                type=EventType.PONG,
                data={"timestamp": time.time()},
                target_clients=[client_id],
                priority=EventPriority.SYSTEM
            )
            await self._send_event_to_client(client_id, pong_event)
    
    async def _handle_subscription(self, client_id: str, message: ClientMessage):
        """Handle subscription/unsubscription requests."""
        try:
            if not message.data:
                return
            
            sub_request = SubscriptionRequest(**message.data)
            connection = self.connections[client_id]
            
            for event_type in sub_request.event_types:
                if message.type == "subscribe":
                    connection.subscriptions.add(event_type)
                    self.event_router.register_subscription(client_id, event_type)
                elif message.type == "unsubscribe":
                    connection.subscriptions.discard(event_type)
                    self.event_router.unregister_subscription(client_id, event_type)
            
            # Update granularity if provided
            if sub_request.granularity:
                connection.granularity = sub_request.granularity
            
            # Send confirmation
            event = CognitiveEvent(
                type=EventType.CONNECTION_STATUS,
                data={
                    "status": f"subscription_{message.type}d",
                    "subscriptions": [s.value if hasattr(s, 'value') else str(s) for s in connection.subscriptions],
                    "granularity": connection.granularity.value if hasattr(connection.granularity, 'value') else str(connection.granularity)
                },
                target_clients=[client_id],
                priority=EventPriority.SYSTEM
            )
            await self._send_event_to_client(client_id, event)
            
            logger.info(f"📋 Client {client_id} {message.type}d to {len(sub_request.event_types)} event types")
            
        except Exception as e:
            logger.error(f"❌ Error handling subscription for {client_id}: {e}")
    
    async def _send_current_state(self, client_id: str):
        """Send current system state to client."""
        if client_id not in self.connections:
            return
        
        connection = self.connections[client_id]
        current_state = self.state_store.get_client_initial_state(connection)
        
        event = CognitiveEvent(
            type=EventType.SYSTEM_STATUS,
            data={
                "status": "current_state",
                "state": current_state,
                "stats": self.get_connection_stats()
            },
            target_clients=[client_id],
            priority=EventPriority.NORMAL
        )
        
        await self._send_event_to_client(client_id, event)
    
    async def _keepalive_loop(self):
        """Background task to maintain connection health."""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                # Send keepalive pings to all clients
                for client_id in list(self.connections.keys()):
                    if client_id in self.connections:
                        await self._handle_ping(client_id)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Error in keepalive loop: {e}")
    
    async def _cleanup_loop(self):
        """Background task to clean up stale connections."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                # Find and remove stale connections
                stale_clients = []
                for client_id, connection in self.connections.items():
                    if not connection.is_active():
                        stale_clients.append(client_id)
                
                for client_id in stale_clients:
                    logger.info(f"🧹 Cleaning up stale connection: {client_id}")
                    await self.disconnect_client(client_id)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Error in cleanup loop: {e}")


# Global instance
unified_stream_manager: Optional[UnifiedStreamingManager] = None


def get_unified_stream_manager() -> UnifiedStreamingManager:
    """Get the global unified streaming manager instance."""
    global unified_stream_manager
    if unified_stream_manager is None:
        unified_stream_manager = UnifiedStreamingManager()
    return unified_stream_manager


async def initialize_unified_streaming():
    """Initialize the unified streaming service."""
    manager = get_unified_stream_manager()
    await manager.start_background_tasks()
    logger.info("🚀 Unified streaming service initialized")


async def shutdown_unified_streaming():
    """Shutdown the unified streaming service."""
    global unified_stream_manager
    if unified_stream_manager:
        await unified_stream_manager.stop_background_tasks()
        logger.info("🛑 Unified streaming service shutdown")
