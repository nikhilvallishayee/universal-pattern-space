"""
Cognitive Transparency Integration for the GödelOS Backend.

This module provides API endpoints and WebSocket handlers for the cognitive
transparency system, enabling real-time streaming of reasoning processes
and detailed post-completion analysis.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Query
from pydantic import BaseModel

from godelOS.cognitive_transparency.manager import CognitiveTransparencyManager
from godelOS.cognitive_transparency.enhanced_metacognition import EnhancedMetacognitionManager
from godelOS.cognitive_transparency.knowledge_graph import DynamicKnowledgeGraph
from godelOS.cognitive_transparency.provenance import ProvenanceTracker, ProvenanceQueryType
from godelOS.cognitive_transparency.autonomous_learning import AutonomousLearningOrchestrator, LearningStrategy
from godelOS.cognitive_transparency.uncertainty import UncertaintyQuantificationEngine, PropagationMethod
from godelOS.cognitive_transparency.models import TransparencyLevel, StepType, DetailLevel

logger = logging.getLogger(__name__)


# Pydantic models for API requests/responses
class TransparencyConfigRequest(BaseModel):
    transparency_level: str
    session_specific: bool = False
    session_id: Optional[str] = None


class ReasoningSessionRequest(BaseModel):
    query: str
    transparency_level: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class ReasoningSessionResponse(BaseModel):
    session_id: str
    status: str
    message: str


class ReasoningTraceResponse(BaseModel):
    session_id: str
    trace: Dict[str, Any]
    statistics: Optional[Dict[str, Any]] = None


class TransparencyStatisticsResponse(BaseModel):
    global_stats: Dict[str, Any]
    active_sessions: int
    transparency_level: str


# Phase 2 API Models
class KnowledgeGraphRequest(BaseModel):
    concept: str
    node_type: str = "concept"
    properties: Optional[Dict[str, Any]] = None
    confidence: float = 1.0


class KnowledgeRelationshipRequest(BaseModel):
    source_concept: str
    target_concept: str
    relation_type: str
    properties: Optional[Dict[str, Any]] = None
    confidence: float = 1.0
    strength: float = 1.0


class ProvenanceQueryRequest(BaseModel):
    target_id: str
    query_type: str  # backward_trace, forward_trace, influence_analysis, etc.
    max_depth: int = 10
    time_window_start: Optional[float] = None
    time_window_end: Optional[float] = None


class LearningSessionRequest(BaseModel):
    focus_areas: Optional[List[str]] = None
    strategy: Optional[str] = None


class UncertaintyAnalysisRequest(BaseModel):
    target_id: str
    target_type: str  # step, node, edge, fact
    context: Optional[Dict[str, Any]] = None


class KnowledgeGraphResponse(BaseModel):
    success: bool
    operation: str
    affected_nodes: List[str]
    affected_edges: List[str]
    message: str


class ProvenanceResponse(BaseModel):
    query_type: str
    target_id: str
    results: Dict[str, Any]


class LearningStatusResponse(BaseModel):
    session_id: str
    status: str
    current_strategy: str
    active_objectives_count: int
    performance_metrics: Dict[str, Any]


class UncertaintyResponse(BaseModel):
    target_id: str
    uncertainty_metrics: Dict[str, Any]
    contributing_factors: List[str]
    mitigation_suggestions: List[str]


class WebSocketConnectionManager:
    """Manages WebSocket connections for real-time transparency streaming."""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.session_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, session_id: Optional[str] = None):
        """Connect a WebSocket client."""
        await websocket.accept()
        
        if session_id:
            if session_id not in self.session_connections:
                self.session_connections[session_id] = []
            self.session_connections[session_id].append(websocket)
        else:
            # Global connection
            if "global" not in self.active_connections:
                self.active_connections["global"] = []
            self.active_connections["global"].append(websocket)
    
    def disconnect(self, websocket: WebSocket, session_id: Optional[str] = None):
        """Disconnect a WebSocket client."""
        if session_id and session_id in self.session_connections:
            if websocket in self.session_connections[session_id]:
                self.session_connections[session_id].remove(websocket)
                if not self.session_connections[session_id]:
                    del self.session_connections[session_id]
        else:
            # Remove from global connections
            if "global" in self.active_connections:
                if websocket in self.active_connections["global"]:
                    self.active_connections["global"].remove(websocket)
    
    async def broadcast_to_session(self, session_id: str, message: Dict[str, Any]):
        """Broadcast a message to all clients connected to a specific session."""
        if session_id not in self.session_connections:
            return
        
        disconnected = []
        for websocket in self.session_connections[session_id]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send message to WebSocket: {e}")
                disconnected.append(websocket)
        
        # Remove disconnected clients
        for websocket in disconnected:
            self.disconnect(websocket, session_id)
    
    async def broadcast_global(self, message: Dict[str, Any]):
        """Broadcast a message to all global connections."""
        if "global" not in self.active_connections:
            return
        
        disconnected = []
        for websocket in self.active_connections["global"]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send message to WebSocket: {e}")
                disconnected.append(websocket)
        
        # Remove disconnected clients
        for websocket in disconnected:
            self.disconnect(websocket)


class CognitiveTransparencyAPI:
    """API handler for cognitive transparency endpoints."""
    
    def __init__(self):
        self.transparency_manager: Optional[CognitiveTransparencyManager] = None
        self.enhanced_metacognition: Optional[EnhancedMetacognitionManager] = None
        
        # Phase 2 components
        self.knowledge_graph: Optional[DynamicKnowledgeGraph] = None
        self.provenance_tracker: Optional[ProvenanceTracker] = None
        self.autonomous_learning: Optional[AutonomousLearningOrchestrator] = None
        self.uncertainty_engine: Optional[UncertaintyQuantificationEngine] = None
        
        self.websocket_manager = WebSocketConnectionManager()
        self.router = APIRouter(prefix="/api/transparency", tags=["cognitive-transparency"])
        self.is_initialized = False
        
        # Setup routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup API routes for cognitive transparency."""
        
        @self.router.post("/configure", response_model=dict)
        async def configure_transparency(config: TransparencyConfigRequest):
            """Configure transparency level."""
            return await self._configure_transparency(config)
        
        @self.router.post("/session/start", response_model=ReasoningSessionResponse)
        async def start_reasoning_session(request: ReasoningSessionRequest):
            """Start a new reasoning session with transparency tracking."""
            return await self._start_reasoning_session(request)
        
        @self.router.post("/session/{session_id}/complete")
        async def complete_reasoning_session(session_id: str):
            """Complete a reasoning session."""
            return await self._complete_reasoning_session(session_id)
        
        @self.router.get("/session/{session_id}/trace", response_model=ReasoningTraceResponse)
        async def get_reasoning_trace(session_id: str, include_stats: bool = Query(True)):
            """Get complete reasoning trace for a session."""
            return await self._get_reasoning_trace(session_id, include_stats)
        
        @self.router.get("/sessions/active")
        async def get_active_sessions():
            """Get all active reasoning sessions."""
            return await self._get_active_sessions()
        
        @self.router.get("/statistics", response_model=TransparencyStatisticsResponse)
        async def get_transparency_statistics():
            """Get transparency system statistics."""
            return await self._get_transparency_statistics()
        
        @self.router.get("/session/{session_id}/statistics")
        async def get_session_statistics(session_id: str):
            """Get statistics for a specific session."""
            return await self._get_session_statistics(session_id)
        
        @self.router.websocket("/ws/stream/{session_id}")
        async def reasoning_stream_websocket(websocket: WebSocket, session_id: str):
            """WebSocket endpoint for real-time reasoning stream."""
            await self._handle_reasoning_stream_websocket(websocket, session_id)
        
        @self.router.websocket("/ws/global")
        async def global_transparency_websocket(websocket: WebSocket):
            """WebSocket endpoint for global transparency events."""
            await self._handle_global_transparency_websocket(websocket)
        
        # Phase 2 Routes - Knowledge Graph
        @self.router.post("/knowledge-graph/node", response_model=KnowledgeGraphResponse)
        async def add_knowledge_node(request: KnowledgeGraphRequest):
            """Add a new node to the knowledge graph."""
            return await self._add_knowledge_node(request)
        
        @self.router.post("/knowledge-graph/relationship", response_model=KnowledgeGraphResponse)
        async def add_knowledge_relationship(request: KnowledgeRelationshipRequest):
            """Add a new relationship to the knowledge graph."""
            return await self._add_knowledge_relationship(request)
        
        @self.router.get("/knowledge-graph/export")
        async def export_knowledge_graph():
            """Export the complete knowledge graph."""
            return await self._export_knowledge_graph()
        
        @self.router.get("/knowledge-graph/statistics")
        async def get_knowledge_graph_statistics():
            """Get knowledge graph statistics."""
            return await self._get_knowledge_graph_statistics()
        
        @self.router.get("/knowledge-graph/discover/{concept}")
        async def discover_relationships(concept: str, max_distance: int = Query(2)):
            """Discover potential relationships for a concept."""
            return await self._discover_relationships(concept, max_distance)

        @self.router.get("/knowledge/categories")
        async def get_knowledge_categories():
            """Get available knowledge categories."""
            return await self._get_knowledge_categories()

        @self.router.get("/knowledge/statistics")
        async def get_knowledge_statistics():
            """Get knowledge management statistics."""
            return await self._get_knowledge_statistics()
        
        # Phase 2 Routes - Provenance Tracking
        @self.router.post("/provenance/query", response_model=ProvenanceResponse)
        async def query_provenance(request: ProvenanceQueryRequest):
            """Query provenance information."""
            return await self._query_provenance(request)
        
        @self.router.get("/provenance/attribution/{target_id}")
        async def get_attribution_chain(target_id: str):
            """Get attribution chain for a knowledge item."""
            return await self._get_attribution_chain(target_id)
        
        @self.router.get("/provenance/confidence-history/{target_id}")
        async def get_confidence_history(target_id: str):
            """Get confidence evolution history."""
            return await self._get_confidence_history(target_id)
        
        @self.router.get("/provenance/statistics")
        async def get_provenance_statistics():
            """Get provenance tracking statistics."""
            return await self._get_provenance_statistics()
        
        @self.router.post("/provenance/snapshot")
        async def create_knowledge_snapshot():
            """Create a knowledge state snapshot."""
            return await self._create_knowledge_snapshot()
        
        @self.router.get("/provenance/rollback/{snapshot_id}")
        async def get_rollback_info(snapshot_id: str):
            """Get rollback information for a snapshot."""
            return await self._get_rollback_info(snapshot_id)
        
        # Phase 2 Routes - Autonomous Learning
        @self.router.post("/learning/session/start", response_model=LearningStatusResponse)
        async def start_learning_session(request: LearningSessionRequest):
            """Start an autonomous learning session."""
            return await self._start_learning_session(request)
        
        @self.router.get("/learning/status")
        async def get_learning_status():
            """Get autonomous learning status."""
            return await self._get_learning_status()
        
        @self.router.post("/learning/strategy/adapt")
        async def adapt_learning_strategy():
            """Trigger learning strategy adaptation."""
            return await self._adapt_learning_strategy()
        
        @self.router.get("/learning/recommendations")
        async def get_learning_recommendations():
            """Get learning performance recommendations."""
            return await self._get_learning_recommendations()
        
        @self.router.post("/learning/objective/{objective_id}/execute")
        async def execute_learning_objective(objective_id: str):
            """Execute a specific learning objective."""
            return await self._execute_learning_objective(objective_id)
        
        # Phase 2 Routes - Uncertainty Quantification
        @self.router.post("/uncertainty/analyze", response_model=UncertaintyResponse)
        async def analyze_uncertainty(request: UncertaintyAnalysisRequest):
            """Analyze uncertainty for a target."""
            return await self._analyze_uncertainty(request)
        
        @self.router.get("/uncertainty/visualization/{target_ids}")
        async def get_uncertainty_visualization(target_ids: str):
            """Get uncertainty visualization data."""
            return await self._get_uncertainty_visualization(target_ids)
        
        @self.router.get("/uncertainty/statistics")
        async def get_uncertainty_statistics():
            """Get uncertainty quantification statistics."""
            return await self._get_uncertainty_statistics()
        
        @self.router.post("/uncertainty/propagate")
        async def propagate_uncertainty(session_id: str, method: str = "analytical"):
            """Propagate uncertainty through a reasoning chain."""
            return await self._propagate_uncertainty(session_id, method)
        
        # Phase 2 WebSocket Routes
        @self.router.websocket("/ws/knowledge-graph")
        async def knowledge_graph_websocket(websocket: WebSocket):
            """WebSocket for real-time knowledge graph updates."""
            await self._handle_knowledge_graph_websocket(websocket)
        
        @self.router.websocket("/ws/learning")
        async def learning_websocket(websocket: WebSocket):
            """WebSocket for autonomous learning updates."""
            await self._handle_learning_websocket(websocket)
    
    async def initialize(self, godelos_integration):
        """Initialize the transparency API with GödelOS integration."""
        try:
            logger.info("🔍 CT_API_INIT: Starting CognitiveTransparencyAPI initialization")
            
            # Create transparency manager
            logger.info("🔍 CT_API_INIT: Creating transparency manager")
            self.transparency_manager = CognitiveTransparencyManager(
                websocket_manager=self.websocket_manager,
                config={
                    'default_transparency_level': 'standard',
                    'max_concurrent_sessions': 50,
                    'session_timeout_seconds': 1800  # 30 minutes
                }
            )
            
            # Initialize transparency manager
            logger.info("🔍 CT_API_INIT: Initializing transparency manager")
            await self.transparency_manager.initialize()
            logger.info("🔍 CT_API_INIT: Transparency manager initialized successfully")
            
            # Phase 2: Initialize components
            logger.info("🔍 CT_API_INIT: Starting Phase 2 component initialization")
            
            # Create uncertainty quantification engine
            logger.info("🔍 CT_API_INIT: Creating uncertainty quantification engine")
            self.uncertainty_engine = UncertaintyQuantificationEngine(
                event_callback=self._handle_uncertainty_event
            )
            logger.info("🔍 CT_API_INIT: Uncertainty engine created successfully")
            
            # Create provenance tracker
            logger.info("🔍 CT_API_INIT: Creating provenance tracker")
            self.provenance_tracker = ProvenanceTracker(
                event_callback=self._handle_provenance_event
            )
            logger.info("🔍 CT_API_INIT: Provenance tracker created successfully")
            
            # Create dynamic knowledge graph
            logger.info("🔍 CT_API_INIT: Creating dynamic knowledge graph")
            self.knowledge_graph = DynamicKnowledgeGraph(
                provenance_tracker=self.provenance_tracker,
                uncertainty_engine=self.uncertainty_engine,
                event_callback=self._handle_knowledge_graph_event
            )
            logger.info(f"🔍 CT_API_INIT: Dynamic knowledge graph created successfully, instance: {self.knowledge_graph}")
            logger.info(f"🔍 CT_API_INIT: knowledge_graph type: {type(self.knowledge_graph)}")
            
            # Create autonomous learning orchestrator
            logger.info("🔍 CT_API_INIT: Creating autonomous learning orchestrator")
            self.autonomous_learning = AutonomousLearningOrchestrator(
                knowledge_graph=self.knowledge_graph,
                provenance_tracker=self.provenance_tracker,
                uncertainty_engine=self.uncertainty_engine,
                event_callback=self._handle_learning_event
            )
            logger.info("🔍 CT_API_INIT: Autonomous learning orchestrator created successfully")
                
            # Create enhanced metacognition manager if available
            if hasattr(godelos_integration, 'metacognition_manager'):
                logger.info("🔍 CT_API_INIT: Creating enhanced metacognition manager")
                self.enhanced_metacognition = EnhancedMetacognitionManager(
                    kr_system_interface=godelos_integration.knowledge_store,
                    type_system=godelos_integration.type_system,
                    transparency_manager=self.transparency_manager
                )
                    
                # Replace the original metacognition manager
                godelos_integration.metacognition_manager = self.enhanced_metacognition
                logger.info("🔍 CT_API_INIT: Enhanced metacognition manager created and replaced")
            
            self.is_initialized = True
            logger.info("✅ CognitiveTransparencyAPI with Phase 2 components initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ CT_API_INIT: Failed to initialize CognitiveTransparencyAPI: {e}")
            logger.error(f"❌ CT_API_INIT: Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"❌ CT_API_INIT: Traceback: {traceback.format_exc()}")
            raise
    
    async def shutdown(self):
        """Shutdown the transparency API."""
        if self.transparency_manager:
            await self.transparency_manager.shutdown()
        
        if self.enhanced_metacognition:
            await self.enhanced_metacognition.stop_with_transparency()
        
        logger.info("CognitiveTransparencyAPI shutdown complete")
    
    async def _configure_transparency(self, config: TransparencyConfigRequest) -> Dict[str, Any]:
        """Configure transparency level."""
        if not self.is_initialized:
            raise HTTPException(status_code=503, detail="Transparency system not initialized")
        
        try:
            transparency_level = TransparencyLevel(config.transparency_level)
            
            if config.session_specific and config.session_id:
                # Configure for specific session (would need session-specific config)
                message = f"Session-specific transparency configuration not yet implemented"
                success = False
            else:
                # Configure global transparency level
                await self.transparency_manager.configure_transparency_level(transparency_level)
                message = f"Global transparency level set to {transparency_level.value}"
                success = True
            
            return {
                "success": success,
                "message": message,
                "transparency_level": transparency_level.value
            }
            
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid transparency level: {e}")
        except Exception as e:
            logger.error(f"Error configuring transparency: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    async def _start_reasoning_session(self, request: ReasoningSessionRequest) -> ReasoningSessionResponse:
        """Start a new reasoning session."""
        if not self.is_initialized:
            raise HTTPException(status_code=503, detail="Transparency system not initialized")
        
        try:
            transparency_level = None
            if request.transparency_level:
                transparency_level = TransparencyLevel(request.transparency_level)
            
            session_id = await self.transparency_manager.start_reasoning_session(
                transparency_level=transparency_level,
                query=request.query,
                context=request.context
            )
            
            return ReasoningSessionResponse(
                session_id=session_id,
                status="started",
                message="Reasoning session started successfully"
            )
            
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid request: {e}")
        except Exception as e:
            logger.error(f"Error starting reasoning session: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    async def _complete_reasoning_session(self, session_id: str) -> Dict[str, Any]:
        """Complete a reasoning session."""
        if not self.is_initialized:
            raise HTTPException(status_code=503, detail="Transparency system not initialized")
        
        try:
            await self.transparency_manager.complete_reasoning_session(session_id)
            
            return {
                "success": True,
                "message": f"Session {session_id} completed successfully",
                "session_id": session_id
            }
            
        except Exception as e:
            logger.error(f"Error completing reasoning session: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    async def _get_reasoning_trace(self, session_id: str, include_stats: bool) -> ReasoningTraceResponse:
        """Get reasoning trace for a session."""
        if not self.is_initialized:
            raise HTTPException(status_code=503, detail="Transparency system not initialized")
        
        try:
            trace = await self.transparency_manager.get_reasoning_trace(session_id)
            if not trace:
                raise HTTPException(status_code=404, detail="Session not found")
            
            statistics = None
            if include_stats:
                statistics = await self.transparency_manager.get_session_statistics(session_id)
            
            return ReasoningTraceResponse(
                session_id=session_id,
                trace=trace,
                statistics=statistics
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting reasoning trace: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    async def _get_active_sessions(self) -> Dict[str, Any]:
        """Get all active sessions."""
        if not self.is_initialized:
            raise HTTPException(status_code=503, detail="Transparency system not initialized")
        
        try:
            sessions = await self.transparency_manager.get_active_sessions()
            
            return {
                "active_sessions": sessions,
                "count": len(sessions),
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Error getting active sessions: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    async def _get_transparency_statistics(self) -> TransparencyStatisticsResponse:
        """Get transparency system statistics."""
        if not self.is_initialized:
            raise HTTPException(status_code=503, detail="Transparency system not initialized")
        
        try:
            global_stats = self.transparency_manager.get_global_statistics()
            
            return TransparencyStatisticsResponse(
                global_stats=global_stats,
                active_sessions=global_stats.get("active_sessions", 0),
                transparency_level=global_stats.get("global_transparency_level", "standard")
            )
            
        except Exception as e:
            logger.error(f"Error getting transparency statistics: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    async def _get_session_statistics(self, session_id: str) -> Dict[str, Any]:
        """Get statistics for a specific session."""
        if not self.is_initialized:
            raise HTTPException(status_code=503, detail="Transparency system not initialized")
        
        try:
            statistics = await self.transparency_manager.get_session_statistics(session_id)
            if not statistics:
                raise HTTPException(status_code=404, detail="Session not found")
            
            return {
                "session_id": session_id,
                "statistics": statistics,
                "timestamp": time.time()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting session statistics: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    async def _handle_reasoning_stream_websocket(self, websocket: WebSocket, session_id: str):
        """Handle WebSocket connection for reasoning stream."""
        await self.websocket_manager.connect(websocket, session_id)
        
        try:
            # Send initial connection confirmation
            await websocket.send_json({
                "type": "connection_established",
                "session_id": session_id,
                "timestamp": time.time()
            })
            
            # Keep connection alive and handle client messages
            while True:
                try:
                    # Wait for client messages (e.g., configuration changes)
                    message = await websocket.receive_json()
                    
                    # Handle client requests
                    if message.get("type") == "ping":
                        await websocket.send_json({
                            "type": "pong",
                            "timestamp": time.time()
                        })
                    elif message.get("type") == "get_session_info":
                        session_info = await self.transparency_manager.get_session_statistics(session_id)
                        await websocket.send_json({
                            "type": "session_info",
                            "data": session_info,
                            "timestamp": time.time()
                        })
                    
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.warning(f"Error in WebSocket message handling: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e),
                        "timestamp": time.time()
                    })
        
        except WebSocketDisconnect:
            pass
        except Exception as e:
            logger.error(f"Error in reasoning stream WebSocket: {e}")
        finally:
            self.websocket_manager.disconnect(websocket, session_id)
    
    async def _handle_global_transparency_websocket(self, websocket: WebSocket):
        """Handle WebSocket connection for global transparency events."""
        try:
            await self.websocket_manager.connect(websocket)
            logger.info("WebSocket connection accepted for global transparency")
        except Exception as e:
            logger.error(f"Failed to accept WebSocket connection: {e}")
            await websocket.close(code=1011, reason="Internal server error")
            return
        
        try:
            # Send initial connection confirmation
            await websocket.send_json({
                "type": "global_connection_established",
                "timestamp": time.time()
            })
            
            # Keep connection alive
            while True:
                try:
                    message = await websocket.receive_json()
                    
                    if message.get("type") == "ping":
                        await websocket.send_json({
                            "type": "pong",
                            "timestamp": time.time()
                        })
                    elif message.get("type") == "get_global_stats":
                        stats = self.transparency_manager.get_global_statistics()
                        await websocket.send_json({
                            "type": "global_stats",
                            "data": stats,
                            "timestamp": time.time()
                        })
                
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.warning(f"Error in global WebSocket message handling: {e}")
        
        except WebSocketDisconnect:
            pass
        except Exception as e:
            logger.error(f"Error in global transparency WebSocket: {e}")
        finally:
            self.websocket_manager.disconnect(websocket)

    async def _handle_uncertainty_event(self, event_data: dict):
        """Handle uncertainty quantification events."""
        try:
            # Process uncertainty event and broadcast to connected clients
            await self.websocket_manager.broadcast({
                "type": "uncertainty_update",
                "data": event_data,
                "timestamp": time.time()
            })
        except Exception as e:
            logger.error(f"Error handling uncertainty event: {e}")

    async def _handle_provenance_event(self, event_data: dict):
        """Handle provenance tracking events."""
        try:
            # Process provenance event and broadcast to connected clients
            await self.websocket_manager.broadcast({
                "type": "provenance_update",
                "data": event_data,
                "timestamp": time.time()
            })
        except Exception as e:
            logger.error(f"Error handling provenance event: {e}")

    async def _handle_knowledge_graph_event(self, event_data: dict):
        """Handle knowledge graph evolution events."""
        try:
            # Process knowledge graph event and broadcast to connected clients
            await self.websocket_manager.broadcast({
                "type": "knowledge_graph_update",
                "data": event_data,
                "timestamp": time.time()
            })
        except Exception as e:
            logger.error(f"Error handling knowledge graph event: {e}")

    async def _handle_learning_event(self, event_data: dict):
        """Handle autonomous learning events."""
        try:
            # Process learning event and broadcast to connected clients
            await self.websocket_manager.broadcast({
                "type": "learning_update",
                "data": event_data,
                "timestamp": time.time()
            })
        except Exception as e:
            logger.error(f"Error handling learning event: {e}")


    # Phase 2 Implementation Methods - Knowledge Graph
    async def _add_knowledge_node(self, request: KnowledgeGraphRequest) -> KnowledgeGraphResponse:
        """Add a new node to the knowledge graph."""
        if not self.knowledge_graph:
            raise HTTPException(status_code=503, detail="Knowledge graph not initialized")
        
        try:
            node_id = await self.knowledge_graph.add_node(
                concept=request.concept,
                node_type=request.node_type,
                properties=request.properties or {},
                confidence=request.confidence
            )
            
            return KnowledgeGraphResponse(
                success=True,
                operation="add_node",
                affected_nodes=[node_id],
                affected_edges=[],
                message=f"Node '{request.concept}' added successfully"
            )
            
        except Exception as e:
            logger.error(f"Error adding knowledge node: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to add node: {str(e)}")
    
    async def _add_knowledge_relationship(self, request: KnowledgeRelationshipRequest) -> KnowledgeGraphResponse:
        """Add a new relationship to the knowledge graph."""
        if not self.knowledge_graph:
            raise HTTPException(status_code=503, detail="Knowledge graph not initialized")
        
        try:
            edge_id = await self.knowledge_graph.add_relationship(
                source_concept=request.source_concept,
                target_concept=request.target_concept,
                relation_type=request.relation_type,
                properties=request.properties or {},
                confidence=request.confidence,
                strength=request.strength
            )
            
            return KnowledgeGraphResponse(
                success=True,
                operation="add_relationship",
                affected_nodes=[request.source_concept, request.target_concept],
                affected_edges=[edge_id],
                message=f"Relationship '{request.relation_type}' added successfully"
            )
            
        except Exception as e:
            logger.error(f"Error adding knowledge relationship: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to add relationship: {str(e)}")
    
    async def _export_knowledge_graph(self) -> Dict[str, Any]:
        """Export the complete knowledge graph."""
        if not self.knowledge_graph:
            raise HTTPException(status_code=503, detail="Knowledge graph not initialized")
        
        try:
            graph_data = await self.knowledge_graph.export_graph()
            return {
                "success": True,
                "graph_data": graph_data,
                "export_timestamp": time.time(),
                "node_count": len(graph_data.get("nodes", [])),
                "edge_count": len(graph_data.get("edges", []))
            }
            
        except Exception as e:
            logger.error(f"Error exporting knowledge graph: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to export graph: {str(e)}")
    
    async def _get_knowledge_graph_statistics(self) -> Dict[str, Any]:
        """Get knowledge graph statistics."""
        if not self.knowledge_graph:
            raise HTTPException(status_code=503, detail="Knowledge graph not initialized")
        
        try:
            stats = await self.knowledge_graph.get_statistics()
            return {
                "success": True,
                "statistics": stats,
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Error getting knowledge graph statistics: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")
    
    async def _discover_relationships(self, concept: str, max_distance: int) -> Dict[str, Any]:
        """Discover potential relationships for a concept."""
        if not self.knowledge_graph:
            raise HTTPException(status_code=503, detail="Knowledge graph not initialized")
        
        try:
            relationships = await self.knowledge_graph.discover_relationships(
                concept=concept,
                max_distance=max_distance
            )
            
            return {
                "success": True,
                "concept": concept,
                "discovered_relationships": relationships,
                "max_distance": max_distance,
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Error discovering relationships: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to discover relationships: {str(e)}")
    
    # Phase 2 Implementation Methods - Provenance Tracking
    async def _query_provenance(self, request: ProvenanceQueryRequest) -> ProvenanceResponse:
        """Query provenance information."""
        if not self.provenance_tracker:
            raise HTTPException(status_code=503, detail="Provenance tracker not initialized")
        
        try:
            query_type = ProvenanceQueryType(request.query_type)
            
            # Convert separate time window parameters to tuple if provided
            time_window = None
            if request.time_window_start is not None and request.time_window_end is not None:
                time_window = (request.time_window_start, request.time_window_end)
            
            results = self.provenance_tracker.query_provenance(
                target_id=request.target_id,
                query_type=query_type,
                max_depth=request.max_depth,
                time_window=time_window
            )
            
            return ProvenanceResponse(
                query_type=request.query_type,
                target_id=request.target_id,
                results=results
            )
            
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid query type: {e}")
        except Exception as e:
            logger.error(f"Error querying provenance: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to query provenance: {str(e)}")
    
    async def _get_attribution_chain(self, target_id: str) -> Dict[str, Any]:
        """Get attribution chain for a knowledge item."""
        if not self.provenance_tracker:
            raise HTTPException(status_code=503, detail="Provenance tracker not initialized")
        
        try:
            attribution_chain = self.provenance_tracker.get_attribution_chain(target_id)
            return {
                "success": True,
                "target_id": target_id,
                "attribution_chain": attribution_chain,
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Error getting attribution chain: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get attribution chain: {str(e)}")
    
    async def _get_confidence_history(self, target_id: str) -> Dict[str, Any]:
        """Get confidence evolution history."""
        if not self.provenance_tracker:
            raise HTTPException(status_code=503, detail="Provenance tracker not initialized")
        
        try:
            confidence_history = self.provenance_tracker.get_confidence_history(target_id)
            return {
                "success": True,
                "target_id": target_id,
                "confidence_history": confidence_history,
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Error getting confidence history: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get confidence history: {str(e)}")
    
    async def _get_provenance_statistics(self) -> Dict[str, Any]:
        """Get provenance tracking statistics."""
        if not self.provenance_tracker:
            raise HTTPException(status_code=503, detail="Provenance tracker not initialized")
        
        try:
            stats = self.provenance_tracker.get_statistics()
            return {
                "success": True,
                "statistics": stats,
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Error getting provenance statistics: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get provenance statistics: {str(e)}")
    
    async def _create_knowledge_snapshot(self) -> Dict[str, Any]:
        """Create a knowledge state snapshot."""
        if not self.provenance_tracker:
            raise HTTPException(status_code=503, detail="Provenance tracker not initialized")
        
        try:
            # Create a mock knowledge state for the snapshot
            knowledge_state = {
                "nodes": [],
                "edges": [],
                "timestamp": time.time(),
                "version": "1.0"
            }
            snapshot_id = self.provenance_tracker.create_snapshot(
                knowledge_state=knowledge_state,
                metadata={"api_created": True}
            )
            return {
                "success": True,
                "snapshot_id": snapshot_id,
                "timestamp": time.time(),
                "message": "Knowledge snapshot created successfully"
            }
            
        except Exception as e:
            logger.error(f"Error creating knowledge snapshot: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to create snapshot: {str(e)}")
    
    async def _get_rollback_info(self, snapshot_id: str) -> Dict[str, Any]:
        """Get rollback information for a snapshot."""
        if not self.provenance_tracker:
            raise HTTPException(status_code=503, detail="Provenance tracker not initialized")
        
        try:
            rollback_info = self.provenance_tracker.rollback_to_snapshot(snapshot_id)
            return {
                "success": True,
                "snapshot_id": snapshot_id,
                "rollback_info": rollback_info,
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Error getting rollback info: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get rollback info: {str(e)}")
    
    # Phase 2 Implementation Methods - Autonomous Learning
    async def _start_learning_session(self, request: LearningSessionRequest) -> LearningStatusResponse:
        """Start an autonomous learning session."""
        if not self.autonomous_learning:
            raise HTTPException(status_code=503, detail="Autonomous learning not initialized")
        
        try:
            strategy = None
            if request.strategy:
                strategy = LearningStrategy(request.strategy)
            
            session_id = await self.autonomous_learning.start_learning_session(
                focus_areas=request.focus_areas,
                strategy=strategy
            )
            
            status = await self.autonomous_learning.get_session_status(session_id)
            
            return LearningStatusResponse(
                session_id=session_id,
                status=status.get("status", "active"),
                current_strategy=status.get("strategy", "adaptive"),
                active_objectives_count=status.get("active_objectives", 0),
                performance_metrics=status.get("performance_metrics", {})
            )
            
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid learning strategy: {e}")
        except Exception as e:
            logger.error(f"Error starting learning session: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to start learning session: {str(e)}")
    
    async def _get_learning_status(self) -> Dict[str, Any]:
        """Get autonomous learning status."""
        if not self.autonomous_learning:
            raise HTTPException(status_code=503, detail="Autonomous learning not initialized")
        
        try:
            status = await self.autonomous_learning.get_global_status()
            return {
                "success": True,
                "learning_status": status,
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Error getting learning status: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get learning status: {str(e)}")
    
    async def _adapt_learning_strategy(self) -> Dict[str, Any]:
        """Trigger learning strategy adaptation."""
        if not self.autonomous_learning:
            raise HTTPException(status_code=503, detail="Autonomous learning not initialized")
        
        try:
            result = await self.autonomous_learning.adapt_strategy()
            return {
                "success": True,
                "adaptation_result": result,
                "timestamp": time.time(),
                "message": "Learning strategy adaptation triggered"
            }
            
        except Exception as e:
            logger.error(f"Error adapting learning strategy: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to adapt strategy: {str(e)}")
    
    async def _get_learning_recommendations(self) -> Dict[str, Any]:
        """Get learning performance recommendations."""
        if not self.autonomous_learning:
            raise HTTPException(status_code=503, detail="Autonomous learning not initialized")
        
        try:
            recommendations = await self.autonomous_learning.get_recommendations()
            return {
                "success": True,
                "recommendations": recommendations,
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Error getting learning recommendations: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")
    
    async def _execute_learning_objective(self, objective_id: str) -> Dict[str, Any]:
        """Execute a specific learning objective."""
        if not self.autonomous_learning:
            raise HTTPException(status_code=503, detail="Autonomous learning not initialized")
        
        try:
            result = await self.autonomous_learning.execute_objective(objective_id)
            return {
                "success": True,
                "objective_id": objective_id,
                "execution_result": result,
                "timestamp": time.time(),
                "message": f"Learning objective {objective_id} executed"
            }
            
        except Exception as e:
            logger.error(f"Error executing learning objective: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to execute objective: {str(e)}")
    
    # Phase 2 Implementation Methods - Uncertainty Quantification
    async def _analyze_uncertainty(self, request: UncertaintyAnalysisRequest) -> UncertaintyResponse:
        """Analyze uncertainty for a target."""
        if not self.uncertainty_engine:
            raise HTTPException(status_code=503, detail="Uncertainty engine not initialized")
        
        try:
            analysis = await self.uncertainty_engine.analyze_uncertainty(
                target_id=request.target_id,
                target_type=request.target_type,
                context=request.context or {}
            )
            
            return UncertaintyResponse(
                target_id=request.target_id,
                uncertainty_metrics=analysis.get("metrics", {}),
                contributing_factors=analysis.get("contributing_factors", []),
                mitigation_suggestions=analysis.get("mitigation_suggestions", [])
            )
            
        except Exception as e:
            logger.error(f"Error analyzing uncertainty: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to analyze uncertainty: {str(e)}")
    
    async def _get_uncertainty_visualization(self, target_ids: str) -> Dict[str, Any]:
        """Get uncertainty visualization data."""
        if not self.uncertainty_engine:
            raise HTTPException(status_code=503, detail="Uncertainty engine not initialized")
        
        try:
            target_id_list = target_ids.split(",")
            visualization_data = await self.uncertainty_engine.get_visualization_data(target_id_list)
            
            return {
                "success": True,
                "target_ids": target_id_list,
                "visualization_data": visualization_data,
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Error getting uncertainty visualization: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get visualization: {str(e)}")
    
    async def _get_uncertainty_statistics(self) -> Dict[str, Any]:
        """Get uncertainty quantification statistics."""
        if not self.uncertainty_engine:
            raise HTTPException(status_code=503, detail="Uncertainty engine not initialized")
        
        try:
            stats = await self.uncertainty_engine.get_statistics()
            return {
                "success": True,
                "statistics": stats,
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Error getting uncertainty statistics: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")
    
    async def _propagate_uncertainty(self, session_id: str, method: str) -> Dict[str, Any]:
        """Propagate uncertainty through a reasoning chain."""
        if not self.uncertainty_engine:
            raise HTTPException(status_code=503, detail="Uncertainty engine not initialized")
        
        try:
            propagation_method = PropagationMethod(method)
            result = await self.uncertainty_engine.propagate_uncertainty(
                session_id=session_id,
                method=propagation_method
            )
            
            return {
                "success": True,
                "session_id": session_id,
                "method": method,
                "propagation_result": result,
                "timestamp": time.time()
            }
            
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid propagation method: {e}")
        except Exception as e:
            logger.error(f"Error propagating uncertainty: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to propagate uncertainty: {str(e)}")
    
    # Phase 2 WebSocket Handlers
    async def _handle_knowledge_graph_websocket(self, websocket: WebSocket):
        """Handle WebSocket connection for knowledge graph updates."""
        await self.websocket_manager.connect(websocket, "knowledge_graph")
        
        try:
            await websocket.send_json({
                "type": "knowledge_graph_connection_established",
                "timestamp": time.time()
            })
            
            while True:
                try:
                    message = await websocket.receive_json()
                    
                    if message.get("type") == "ping":
                        await websocket.send_json({
                            "type": "pong",
                            "timestamp": time.time()
                        })
                    elif message.get("type") == "get_graph_stats":
                        if self.knowledge_graph:
                            stats = await self.knowledge_graph.get_statistics()
                            await websocket.send_json({
                                "type": "graph_stats",
                                "data": stats,
                                "timestamp": time.time()
                            })
                
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.warning(f"Error in knowledge graph WebSocket: {e}")
        
        except WebSocketDisconnect:
            pass
        finally:
            self.websocket_manager.disconnect(websocket, "knowledge_graph")

    async def _get_knowledge_categories(self) -> Dict[str, Any]:
        """Get available knowledge categories."""
        try:
            # Return predefined categories for now - can be enhanced to be dynamic
            categories = [
                {"id": "facts", "name": "Facts", "description": "Factual knowledge"},
                {"id": "concepts", "name": "Concepts", "description": "Conceptual knowledge"},
                {"id": "rules", "name": "Rules", "description": "Rule-based knowledge"},
                {"id": "procedures", "name": "Procedures", "description": "Procedural knowledge"},
                {"id": "relations", "name": "Relations", "description": "Relational knowledge"}
            ]
            
            return {
                "success": True,
                "categories": categories,
                "total_count": len(categories)
            }
            
        except Exception as e:
            logger.error(f"Error getting knowledge categories: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get categories: {str(e)}")

    async def _get_knowledge_statistics(self) -> Dict[str, Any]:
        """Get knowledge management statistics."""
        try:
            # Basic statistics - can be enhanced with actual data
            stats = {
                "total_knowledge_items": 0,
                "categories": {
                    "facts": 0,
                    "concepts": 0,
                    "rules": 0,
                    "procedures": 0,
                    "relations": 0
                },
                "recent_additions": 0,
                "confidence_distribution": {
                    "high": 0,
                    "medium": 0,
                    "low": 0
                }
            }
            
            # If knowledge graph is available, get real statistics
            if self.knowledge_graph:
                graph_stats = await self.knowledge_graph.get_statistics()
                stats.update({
                    "total_knowledge_items": graph_stats.get("node_count", 0),
                    "total_relationships": graph_stats.get("edge_count", 0),
                    "graph_density": graph_stats.get("density", 0.0),
                    "clustering_coefficient": graph_stats.get("clustering_coefficient", 0.0)
                })
            
            return {
                "success": True,
                "statistics": stats,
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Error getting knowledge statistics: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")
    
    async def _handle_learning_websocket(self, websocket: WebSocket):
        """Handle WebSocket connection for autonomous learning updates."""
        await self.websocket_manager.connect(websocket, "learning")
        
        try:
            await websocket.send_json({
                "type": "learning_connection_established",
                "timestamp": time.time()
            })
            
            while True:
                try:
                    message = await websocket.receive_json()
                    
                    if message.get("type") == "ping":
                        await websocket.send_json({
                            "type": "pong",
                            "timestamp": time.time()
                        })
                    elif message.get("type") == "get_learning_status":
                        if self.autonomous_learning:
                            status = await self.autonomous_learning.get_global_status()
                            await websocket.send_json({
                                "type": "learning_status",
                                "data": status,
                                "timestamp": time.time()
                            })
                
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.warning(f"Error in learning WebSocket: {e}")
        
        except WebSocketDisconnect:
            pass
        finally:
            self.websocket_manager.disconnect(websocket, "learning")


# Global instance
cognitive_transparency_api = CognitiveTransparencyAPI()