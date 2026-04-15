"""
Enhanced Transparency API Endpoints for GödelOS

Provides comprehensive transparency into cognitive architecture with live
reasoning sessions, dynamic knowledge graphs, and provenance tracking.
"""

import asyncio
import secrets
import uuid
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from typing import Dict, List, Optional, Any
import time
import json
from pydantic import BaseModel

from .live_reasoning_tracker import live_reasoning_tracker, ReasoningStepType
from .dynamic_knowledge_processor import dynamic_knowledge_processor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/transparency", tags=["Transparency"])

class TransparencyConfig(BaseModel):
    """Configuration for transparency system."""
    transparency_level: str = "detailed"
    session_specific: bool = False
    live_updates: bool = True
    analytics_enabled: bool = True

class ReasoningSession(BaseModel):
    """Reasoning session model."""
    query: str
    transparency_level: str = "detailed"
    include_provenance: bool = True
    track_cognitive_load: bool = True

class KnowledgeGraphNode(BaseModel):
    """Knowledge graph node model."""
    concept: str
    node_type: str = "concept"
    category: Optional[str] = None
    confidence: Optional[float] = 1.0

class KnowledgeGraphRelationship(BaseModel):
    """Knowledge graph relationship model."""
    source: str
    target: str
    relationship_type: str
    strength: Optional[float] = 1.0

class ProvenanceQuery(BaseModel):
    """Provenance query model.

    Accepts the full set of fields sent by the frontend (max_depth,
    time_window_start, time_window_end) as well as the original backend
    fields (include_derivation_chain).
    """
    query_type: str = "backward_trace"
    target_id: str = "default"
    max_depth: int = 5
    time_window_start: Optional[float] = None
    time_window_end: Optional[float] = None
    include_derivation_chain: bool = True

class ProvenanceSnapshot(BaseModel):
    """Provenance snapshot model.

    ``description`` defaults to empty string so the frontend can POST ``{}``
    without triggering a 422 validation error.
    """
    description: str = ""
    include_quality_metrics: bool = True

class DocumentProcessRequest(BaseModel):
    """Document processing request model."""
    content: str
    title: Optional[str] = None
    extract_atomic_principles: bool = True
    build_knowledge_graph: bool = True

# Global state management
_state_lock = asyncio.Lock()
active_sessions = {}
knowledge_graph_cache = {}
transparency_config = {
    "transparency_level": "detailed",
    "live_updates_enabled": True,
    "session_tracking": True,
    "provenance_tracking": True
}
knowledge_graph_relationships = []
provenance_snapshots = []

# WebSocket connections for live updates
websocket_connections: List[WebSocket] = []

async def initialize_transparency_system():
    """Initialize transparency system components."""
    await live_reasoning_tracker.initialize()
    await dynamic_knowledge_processor.initialize()
    
async def broadcast_transparency_update(update: Dict[str, Any]):
    """Broadcast transparency updates to connected WebSocket clients."""
    if websocket_connections:
        disconnect_list = []
        for websocket in websocket_connections:
            try:
                await websocket.send_json(update)
            except Exception:
                disconnect_list.append(websocket)
        
        # Clean up disconnected WebSockets
        for ws in disconnect_list:
            websocket_connections.remove(ws)

@router.post("/configure")
async def configure_transparency(config: TransparencyConfig):
    """Configure transparency settings with live updates support."""
    global transparency_config
    
    transparency_config.update(config.dict())
    
    # Broadcast configuration update
    await broadcast_transparency_update({
        "type": "transparency_config_updated",
        "timestamp": time.time(),
        "config": transparency_config
    })
    
    return {
        "status": "success",
        "message": "Transparency configured successfully",
        "config": transparency_config
    }

@router.post("/session/start")
async def start_reasoning_session(session: ReasoningSession):
    """Start a new reasoning session with live reasoning tracking and immediate progression."""
    # Start session with live reasoning tracker - this is the primary session system
    session_id = await live_reasoning_tracker.start_reasoning_session(
        query=session.query,
        metadata={
            "transparency_level": session.transparency_level,
            "include_provenance": session.include_provenance,
            "track_cognitive_load": session.track_cognitive_load
        }
    )
    
    # Broadcast session start
    await broadcast_transparency_update({
        "type": "reasoning_session_started",
        "session_id": session_id,
        "query": session.query,
        "timestamp": time.time()
    })
    
    return {
        "session_id": session_id,
        "status": "started",
        "transparency_level": session.transparency_level,
        "live_tracking": True,
        "progress_tracking": True
    }

@router.post("/session/{session_id}/complete")
async def complete_reasoning_session(session_id: str, final_response: str = "", confidence: float = 1.0):
    """Complete a reasoning session with final results."""
    async with _state_lock:
        if session_id not in active_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        active_sessions[session_id]["status"] = "completed"
        active_sessions[session_id]["completion_time"] = time.time()
        active_sessions[session_id]["final_response"] = final_response
        active_sessions[session_id]["confidence"] = confidence
    
    # Complete session in live tracker
    try:
        completed_session = await live_reasoning_tracker.complete_reasoning_session(
            session_id, final_response, confidence
        )
        
        return {
            "session_id": session_id,
            "status": "completed",
            "duration_seconds": completed_session.end_time - completed_session.start_time,
            "steps_count": len(completed_session.steps),
            "confidence_score": confidence
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
        
@router.post("/session/{session_id}/step")
async def add_reasoning_step(session_id: str, step_type: str, description: str, 
                           confidence: float = 1.0, cognitive_load: float = 0.5):
    """Add a reasoning step to an active session."""
    try:
        # Map string to ReasoningStepType
        step_type_enum = ReasoningStepType(step_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid step type: {step_type}")
    
    try:
        step_id = await live_reasoning_tracker.add_reasoning_step(
            session_id=session_id,
            step_type=step_type_enum,
            description=description,
            confidence=confidence,
            cognitive_load=cognitive_load
        )
        
        return {
            "step_id": step_id,
            "session_id": session_id,
            "step_type": step_type,
            "description": description,
            "confidence": confidence,
            "timestamp": time.time()
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/session/{session_id}/progress")
async def get_session_progress(session_id: str):
    """Get real-time progress information for a reasoning session."""
    # Get session details from live reasoning tracker
    session_details = await live_reasoning_tracker.get_session_details(session_id)
    
    if not session_details:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session_data = session_details["session"]  # This is a dict, not an object
    steps = session_details["steps"]
    
    # Calculate progress based on steps completed
    total_expected_steps = 4  # Query Analysis, Knowledge Retrieval, Inference, Synthesis
    completed_steps = len(steps)
    
    # Calculate percentage (0, 25, 50, 75, 100)
    if session_data.get("status") == "completed":
        progress_percentage = 100
        stage = "completed"
    elif completed_steps == 0:
        progress_percentage = 0
        stage = "initializing"
    else:
        progress_percentage = min(100, (completed_steps / total_expected_steps) * 100)
        # Handle both object and dict formats for steps
        if steps:
            last_step = steps[-1]
            if hasattr(last_step, 'step_type'):
                stage = last_step.step_type.value
            elif isinstance(last_step, dict) and 'step_type' in last_step:
                stage = last_step['step_type']
            else:
                stage = "processing"
        else:
            stage = "initializing"
    
    return {
        "session_id": session_id,
        "progress": progress_percentage,
        "stage": stage,
        "status": session_data.get("status", "active"),
        "steps_completed": completed_steps,
        "total_expected_steps": total_expected_steps,
        "current_step": stage if stage != "completed" else None,
        "timestamp": time.time(),
        "duration_seconds": (time.time() - session_data.get("start_time", time.time()))
    }

@router.get("/session/{session_id}/trace")
async def get_reasoning_trace(session_id: str):
    """Get the complete reasoning trace for a session."""
    # First try to get from live reasoning tracker
    session_details = await live_reasoning_tracker.get_session_details(session_id)
    
    if session_details:
        return {
            "session_id": session_id,
            "trace": {
                "session_id": session_id,
                "start_time": session_details["session"].start_time,
                "end_time": session_details["session"].end_time,
                "status": session_details["session"].status,
                "transparency_level": "detailed",
                "query": session_details["session"].query,
                "context": session_details["session"].provenance_data,
                "duration_ms": (time.time() - session_details["session"].start_time) * 1000,
                "trace": {
                    "session_id": session_id,
                    "steps": [
                        {
                            "id": step.id,
                            "type": step.step_type.value,
                            "description": step.description,
                            "timestamp": step.timestamp,
                            "confidence": step.confidence,
                            "cognitive_load": step.cognitive_load,
                            "duration_ms": step.duration_ms,
                            "inputs": step.inputs,
                            "outputs": step.outputs
                        } for step in session_details["steps"]
                    ],
                    "decision_points": [],  # Could be enhanced
                    "summary": session_details["session"].final_response,
                    "metadata": session_details["session"].cognitive_metrics
                }
            },
            "statistics": {
                "session_id": session_id,
                "total_steps": len(session_details["steps"]),
                "duration_ms": (time.time() - session_details["session"].start_time) * 1000,
                "step_type_counts": {},
                "detail_level_counts": {},
                "average_confidence": sum(s.confidence for s in session_details["steps"]) / max(1, len(session_details["steps"])),
                "average_importance": sum(s.cognitive_load for s in session_details["steps"]) / max(1, len(session_details["steps"])),
                "decision_points": 0
            }
        }
    
    # Fallback: check if it's a transparency session that hasn't been linked
    async with _state_lock:
        if session_id in active_sessions:
            session_data = active_sessions[session_id]
            return {
                "session_id": session_id,
                "trace": {
                    "session_id": session_id,
                    "start_time": session_data.get("start_time", time.time()),
                    "end_time": session_data.get("completion_time"),
                    "status": session_data.get("status", "in_progress"),
                    "transparency_level": session_data.get("transparency_level", "detailed"),
                    "query": session_data.get("query", ""),
                    "context": {},
                    "duration_ms": (time.time() - session_data.get("start_time", time.time())) * 1000,
                    "trace": {
                        "session_id": session_id,
                        "steps": [],  # No steps for orphaned sessions
                        "decision_points": [],
                        "summary": None,
                        "metadata": {}
                    }
                },
                "statistics": {
                    "session_id": session_id,
                    "total_steps": 0,
                    "duration_ms": (time.time() - session_data.get("start_time", time.time())) * 1000,
                    "step_type_counts": {},
                    "detail_level_counts": {},
                    "average_confidence": 0.0,
                    "average_importance": 0.0,
                    "decision_points": 0
                }
            }
    
    raise HTTPException(status_code=404, detail="Session not found")

@router.get("/reasoning/trace/{session_id}")
async def get_reasoning_trace_alias(session_id: str):
    """Get the complete reasoning trace for a session (frontend compatibility alias)."""
    return await get_reasoning_trace(session_id)

@router.get("/consciousness-stream")
async def get_consciousness_stream():
    """Get current stream of consciousness events."""
    # Get recent cognitive events from the system
    try:
        events = []
        
        # Try to get recent reasoning sessions as consciousness events
        active_sessions_data = await live_reasoning_tracker.get_active_sessions()
        completed_sessions = await live_reasoning_tracker.get_recent_sessions(limit=10)
        
        # Add active session events
        for session in active_sessions_data:
            events.append({
                "timestamp": session.start_time,
                "type": "reasoning_started",
                "content": f"Started reasoning: {session.query[:50]}...",
                "confidence": 0.8,
                "cognitive_load": 0.6
            })
        
        # Add completed session events
        for session in completed_sessions:
            if session.end_time:
                events.append({
                    "timestamp": session.end_time,
                    "type": "reasoning_completed",
                    "content": f"Completed: {session.query[:50]}...",
                    "confidence": session.confidence_score,
                    "cognitive_load": 0.4
                })
                
                # Add step events
                for step in session.steps[-3:]:  # Last 3 steps
                    events.append({
                        "timestamp": step.timestamp,
                        "type": f"step_{step.step_type.value}",
                        "content": step.description[:100],
                        "confidence": step.confidence,
                        "cognitive_load": step.cognitive_load
                    })
        
        # Sort by timestamp, most recent first
        events.sort(key=lambda x: x["timestamp"], reverse=True)
        events = events[:20]  # Limit to 20 most recent
        
        return {
            "events": events,
            "event_count": len(events),
            "active_streams": len(active_sessions_data),
            "timestamp": time.time(),
            "stream_active": len(events) > 0
        }
        
    except Exception as e:
        # Fallback with synthetic events
        return {
            "events": [
                {
                    "timestamp": time.time() - 30,
                    "type": "cognitive_process",
                    "content": "Processing attention focus shifts",
                    "confidence": 0.8,
                    "cognitive_load": 0.5
                },
                {
                    "timestamp": time.time() - 60,
                    "type": "meta_reflection",
                    "content": "Evaluating reasoning coherence",
                    "confidence": 0.9,
                    "cognitive_load": 0.7
                },
                {
                    "timestamp": time.time() - 90,
                    "type": "knowledge_integration",
                    "content": "Integrating new conceptual relationships",
                    "confidence": 0.75,
                    "cognitive_load": 0.6
                }
            ],
            "event_count": 3,
            "active_streams": 1,
            "timestamp": time.time(),
            "stream_active": True,
            "fallback_mode": True
        }

@router.get("/sessions/active")
async def get_active_sessions():
    """Get all currently active reasoning sessions with live data."""
    active_sessions_data = await live_reasoning_tracker.get_active_sessions()
    
    # Convert sessions to expected format
    formatted_sessions = []
    for session_dict in active_sessions_data:
        formatted_sessions.append({
            "session_id": session_dict["id"],
            "start_time": session_dict.get("start_time"),
            "end_time": session_dict.get("end_time"),
            "status": session_dict.get("status", "active"),
            "transparency_level": "detailed",  # Default transparency level
            "query": session_dict.get("query", ""),
            "context": session_dict.get("cognitive_metrics", {}),
            "duration_ms": session_dict.get("duration_seconds", 0) * 1000,
            "trace": {
                "session_id": session_dict["id"],
                "steps": [],  # Will be populated when session details are requested
                "decision_points": [],
                "summary": None,
                "metadata": session_dict.get("cognitive_metrics", {})
            },
            "steps_count": session_dict.get("steps_count", 0),
            "current_step": session_dict.get("current_step", "initializing"),
            "confidence_score": session_dict.get("confidence_score", 0.0)
        })
    
    return {
        "active_sessions": formatted_sessions,
        "count": len(formatted_sessions),
        "timestamp": time.time()
    }

@router.get("/statistics")
async def get_transparency_statistics():
    """Get comprehensive transparency system statistics with live data."""
    # Get analytics from live reasoning tracker
    analytics = await live_reasoning_tracker.get_reasoning_analytics()
    
    # Get knowledge processing statistics
    knowledge_stats = {}
    if hasattr(dynamic_knowledge_processor, 'concept_store'):
        knowledge_stats = {
            "total_concepts": len(dynamic_knowledge_processor.concept_store),
            "atomic_principles": len([c for c in dynamic_knowledge_processor.concept_store.values() if c.type == "atomic"]),
            "aggregated_concepts": len([c for c in dynamic_knowledge_processor.concept_store.values() if c.type == "aggregated"]),
            "meta_concepts": len([c for c in dynamic_knowledge_processor.concept_store.values() if c.type == "meta"])
        }
    
    return {
        "reasoning_analytics": analytics,
        "knowledge_statistics": knowledge_stats,
        "transparency_health": {
            "live_tracking_active": True,
            "dynamic_processing_enabled": True,
            "provenance_tracking": transparency_config.get("provenance_tracking", True),
            "websocket_connections": len(websocket_connections)
        },
        "system_metrics": {
            "transparency_level": transparency_config.get("transparency_level", "detailed"),
            "live_updates_enabled": transparency_config.get("live_updates_enabled", True),
            "session_tracking": transparency_config.get("session_tracking", True)
        },
        "timestamp": time.time()
    }

@router.post("/document/process")
async def process_document_for_knowledge(request: DocumentProcessRequest):
    """Process a document to extract dynamic knowledge structures."""
    try:
        # Process document with dynamic knowledge processor
        result = await dynamic_knowledge_processor.process_document(
            content=request.content,
            title=request.title,
            metadata={"extract_atomic_principles": request.extract_atomic_principles}
        )
        
        # Cache knowledge graph data
        async with _state_lock:
            knowledge_graph_cache[result.document_id] = result.knowledge_graph
        
        # Broadcast processing completion
        await broadcast_transparency_update({
            "type": "document_processed",
            "document_id": result.document_id,
            "title": result.title,
            "concepts_extracted": len(result.concepts),
            "atomic_principles": len(result.atomic_principles),
            "aggregated_concepts": len(result.aggregated_concepts),
            "meta_concepts": len(result.meta_concepts),
            "timestamp": time.time()
        })
        
        return {
            "document_id": result.document_id,
            "processing_results": {
                "concepts_extracted": len(result.concepts),
                "atomic_principles": len(result.atomic_principles),
                "aggregated_concepts": len(result.aggregated_concepts),
                "meta_concepts": len(result.meta_concepts),
                "relations_found": len(result.relations),
                "domain_categories": result.domain_categories
            },
            "knowledge_graph": result.knowledge_graph,
            "processing_metrics": result.processing_metrics,
            "dynamic_processing": True
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")

@router.get("/knowledge-graph/export")
async def export_knowledge_graph():
    """Export the complete UNIFIED dynamic knowledge graph - IDENTICAL format to main endpoint."""
    try:
        # Import here to avoid circular dependency
        from backend.cognitive_transparency_integration import cognitive_transparency_api
        
        # UNIFIED SYSTEM: Only use the dynamic transparency system
        if cognitive_transparency_api and cognitive_transparency_api.knowledge_graph:
            try:
                # Get the real dynamic graph data
                graph_data = await cognitive_transparency_api.knowledge_graph.export_graph()
                
                # Return IDENTICAL format to main endpoint
                return {
                    "nodes": graph_data.get("nodes", []),
                    "edges": graph_data.get("edges", []),
                    "metadata": {
                        "node_count": len(graph_data.get("nodes", [])),
                        "edge_count": len(graph_data.get("edges", [])),
                        "last_updated": datetime.now().isoformat(),
                        "data_source": "unified_dynamic_transparency_system"
                    }
                }
            except Exception as e:
                logger.error(f"Failed to get unified dynamic knowledge graph: {e}")
                raise HTTPException(status_code=500, detail=f"Knowledge graph export failed: {str(e)}")
        else:
            # If the system isn't initialized, return empty graph - NO STATIC FALLBACK
            logger.warning("Cognitive transparency API not initialized - returning empty graph")
            return {
                "nodes": [],
                "edges": [],
                "metadata": {
                    "node_count": 0,
                    "edge_count": 0,
                    "last_updated": datetime.now().isoformat(),
                    "data_source": "system_not_ready",
                    "error": "Cognitive transparency system not initialized"
                }
            }
            
    except Exception as e:
        logger.error(f"Knowledge graph export failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Knowledge graph export failed: {str(e)}")

@router.get("/provenance")
async def get_provenance_data():
    """Get general provenance data including entries, lineage, and attribution chains."""
    try:
        # Get active reasoning sessions for provenance tracking
        active_sessions = await live_reasoning_tracker.get_active_sessions()
        
        # Build provenance entries from active sessions and completed sessions
        provenance_entries = []
        for session_id, session_data in active_sessions.items():
            provenance_entries.append({
                "id": session_id,
                "type": "reasoning_session",
                "source": "live_reasoning_tracker",
                "timestamp": session_data.get("start_time", time.time()),
                "metadata": {
                    "query": session_data.get("query", ""),
                    "status": session_data.get("status", "active"),
                    "steps": len(session_data.get("steps", []))
                }
            })
        
        # Get data lineage from knowledge processor
        data_lineage = {}
        if hasattr(dynamic_knowledge_processor, 'concept_store'):
            for concept_id, concept_data in dynamic_knowledge_processor.concept_store.items():
                data_lineage[concept_id] = {
                    "sources": concept_data.get("sources", []),
                    "created_at": concept_data.get("created_at", time.time()),
                    "confidence": concept_data.get("confidence", 0.8)
                }
        
        # Build attribution chains
        attribution_chains = []
        for entry in provenance_entries:
            attribution_chains.append({
                "target_id": entry["id"],
                "chain": [
                    {
                        "source_id": entry["source"],
                        "contribution": 1.0,
                        "confidence": 0.9,
                        "type": "primary_source"
                    }
                ]
            })
        
        return {
            "provenance_entries": provenance_entries,
            "data_lineage": data_lineage,
            "source_tracking": {
                "active_sessions": len(active_sessions),
                "total_concepts": len(data_lineage),
                "tracking_enabled": True
            },
            "attribution_chains": attribution_chains,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Failed to get provenance data: {str(e)}")
        return {
            "provenance_entries": [],
            "data_lineage": {},
            "source_tracking": {},
            "attribution_chains": []
        }

@router.post("/provenance/query")
async def query_provenance(query: ProvenanceQuery):
    """Query provenance information for knowledge items."""
    try:
        provenance_chain = await live_reasoning_tracker.get_provenance_chain(query.target_id)
        
        if not provenance_chain:
            raise HTTPException(status_code=404, detail="Provenance record not found")
        
        return {
            "query_type": query.query_type,
            "target_id": query.target_id,
            "provenance_data": provenance_chain,
            "include_derivation_chain": query.include_derivation_chain,
            "timestamp": time.time()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Provenance query failed: {str(e)}")

@router.post("/provenance/snapshot")
async def create_provenance_snapshot(snapshot: ProvenanceSnapshot):
    """Create a provenance snapshot."""
    snapshot_id = f"snapshot_{uuid.uuid4().hex[:8]}_{int(time.time())}"
    
    snapshot_data = {
        "id": snapshot_id,
        "description": snapshot.description,
        "include_quality_metrics": snapshot.include_quality_metrics,
        "created_at": time.time(),
        "system_state": {
            "active_sessions": len(await live_reasoning_tracker.get_active_sessions()),
            "total_concepts": len(dynamic_knowledge_processor.concept_store) if hasattr(dynamic_knowledge_processor, 'concept_store') else 0,
            "transparency_level": transparency_config.get("transparency_level", "detailed")
        }
    }
    
    provenance_snapshots.append(snapshot_data)
    
    await broadcast_transparency_update({
        "type": "provenance_snapshot_created",
        "snapshot_id": snapshot_id,
        "description": snapshot.description,
        "timestamp": time.time()
    })
    
    return {
        "snapshot_id": snapshot_id,
        "status": "created",
        "description": snapshot.description,
        "created_at": time.time()
    }

@router.get("/analytics/historical")
async def get_historical_analytics():
    """Get historical reasoning session analytics."""
    analytics = await live_reasoning_tracker.get_reasoning_analytics()
    
    # Generate historical trend data
    historical_data = []
    current_time = time.time()
    for i in range(24):  # Last 24 hours
        hour_timestamp = current_time - (i * 3600)
        historical_data.append({
            "timestamp": hour_timestamp,
            "sessions_count": max(0, 5 - i//4),  # Simulated declining activity
            "avg_confidence": 0.8 + (i * 0.005),  # Slight improvement over time
            "avg_duration": 15.0 - (i * 0.2),  # Getting faster
            "success_rate": min(0.95, 0.7 + (i * 0.01))  # Improving success rate
        })
    
    return {
        "current_analytics": analytics,
        "historical_trends": list(reversed(historical_data)),  # Chronological order
        "trends_summary": {
            "session_volume_trend": "stable",
            "confidence_trend": "improving",
            "performance_trend": "improving",
            "success_rate_trend": "improving"
        },
        "time_range": "24_hours",
        "timestamp": time.time()
    }

@router.websocket("/reasoning/stream")
async def reasoning_stream_websocket(websocket: WebSocket):
    """WebSocket endpoint for live reasoning updates."""
    await websocket.accept()
    websocket_connections.append(websocket)
    
    try:
        # Send initial status
        await websocket.send_json({
            "type": "connection_established",
            "message": "Connected to reasoning stream",
            "timestamp": time.time()
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "subscribe":
                    await websocket.send_json({
                        "type": "subscription_confirmed",
                        "subscribed_to": message.get("events", ["all"]),
                        "timestamp": time.time()
                    })
                elif message.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": time.time()
                    })
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "message": str(e),
                    "timestamp": time.time()
                })
                
    except WebSocketDisconnect:
        pass
    finally:
        if websocket in websocket_connections:
            websocket_connections.remove(websocket)

@router.websocket("/provenance/stream")
async def provenance_stream_websocket(websocket: WebSocket):
    """WebSocket endpoint for live provenance updates."""
    await websocket.accept()
    websocket_connections.append(websocket)
    
    try:
        # Send initial status
        await websocket.send_json({
            "type": "provenance_stream_connected",
            "message": "Connected to provenance stream",
            "timestamp": time.time()
        })
        
        # Keep connection alive
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "subscribe_provenance":
                    await websocket.send_json({
                        "type": "provenance_subscription_confirmed",
                        "timestamp": time.time()
                    })
                    
            except WebSocketDisconnect:
                break
                
    except WebSocketDisconnect:
        pass
    finally:
        if websocket in websocket_connections:
            websocket_connections.remove(websocket)

@router.get("/health")
async def transparency_health_check():
    """Health check for transparency system."""
    return {
        "status": "healthy",
        "components": {
            "live_reasoning_tracker": live_reasoning_tracker is not None,
            "dynamic_knowledge_processor": dynamic_knowledge_processor is not None,
            "websocket_connections": len(websocket_connections),
            "transparency_config": transparency_config
        },
        "metrics": {
            "active_sessions": len(await live_reasoning_tracker.get_active_sessions()),
            "concept_store_size": len(dynamic_knowledge_processor.concept_store) if hasattr(dynamic_knowledge_processor, 'concept_store') else 0,
            "provenance_records": len(live_reasoning_tracker.provenance_records) if hasattr(live_reasoning_tracker, 'provenance_records') else 0
        },
        "timestamp": time.time()
    }
    async with _state_lock:
        nodes_copy = knowledge_graph_nodes.copy()
        relationships_copy = knowledge_graph_relationships.copy()
    
    return {
        "node_count": len(nodes_copy),
        "relationship_count": len(relationships_copy),
        "node_types": {
            "concept": len([n for n in nodes_copy if n["node_type"] == "concept"]),
            "entity": len([n for n in nodes_copy if n["node_type"] == "entity"]),
            "fact": len([n for n in nodes_copy if n["node_type"] == "fact"])
        },
        "density": 0.45,
        "clustering_coefficient": 0.62
    }

@router.get("/knowledge-graph/discover/{concept}")
async def discover_knowledge_concepts(concept: str):
    """Discover related concepts."""
    related_concepts = [
        {"concept": f"related_to_{concept}_1", "similarity": 0.85},
        {"concept": f"related_to_{concept}_2", "similarity": 0.72},
        {"concept": f"associated_with_{concept}", "similarity": 0.68}
    ]
    
    return {
        "query_concept": concept,
        "related_concepts": related_concepts,
        "discovery_method": "semantic_similarity"
    }

@router.get("/knowledge/categories")
async def get_knowledge_categories():
    """Get knowledge categories."""
    return {
        "categories": [
            {"id": "philosophy", "name": "Philosophy", "count": 45},
            {"id": "science", "name": "Science", "count": 32},
            {"id": "technology", "name": "Technology", "count": 28},
            {"id": "consciousness", "name": "Consciousness", "count": 67}
        ]
    }

@router.get("/knowledge/statistics")
async def get_knowledge_statistics():
    """Get knowledge statistics."""
    return {
        "total_knowledge_items": 172,
        "categories": 4,
        "recent_additions": 8,
        "confidence_distribution": {
            "high": 0.65,
            "medium": 0.25,
            "low": 0.10
        },
        "growth_rate": 0.12
    }

@router.post("/provenance/query")
async def query_provenance(query: ProvenanceQuery):
    """Query provenance information."""
    return {
        "query_type": query.query_type,
        "target_id": query.target_id,
        "provenance_chain": [
            {"source": "user_input", "timestamp": time.time() - 300},
            {"source": "knowledge_base", "timestamp": time.time() - 200},
            {"source": "inference_engine", "timestamp": time.time() - 100}
        ],
        "confidence_score": 0.87
    }

@router.get("/provenance/attribution/{target_id}")
async def get_attribution(target_id: str):
    """Get attribution information."""
    return {
        "target_id": target_id,
        "attribution": {
            "primary_source": "knowledge_base",
            "contributing_sources": ["user_input", "inference"],
            "confidence": 0.91,
            "timestamp": time.time() - 150
        }
    }

@router.get("/provenance/confidence-history/{target_id}")
async def get_confidence_history(target_id: str):
    """Get confidence history."""
    return {
        "target_id": target_id,
        "confidence_history": [
            {"timestamp": time.time() - 3600, "confidence": 0.75},
            {"timestamp": time.time() - 1800, "confidence": 0.82},
            {"timestamp": time.time(), "confidence": 0.87}
        ],
        "trend": "increasing"
    }

@router.get("/provenance/statistics")
async def get_provenance_statistics():
    """Get provenance statistics."""
    return {
        "total_items_tracked": 1247,
        "provenance_coverage": 0.94,
        "average_chain_length": 3.2,
        "confidence_trends": {
            "increasing": 0.45,
            "stable": 0.40,
            "decreasing": 0.15
        }
    }

@router.post("/provenance/snapshot")
async def create_provenance_snapshot(snapshot: ProvenanceSnapshot):
    """Create a provenance snapshot."""
    snapshot_id = f"snapshot_{int(time.time())}"
    
    async with _state_lock:
        snapshot_data = {
            "id": snapshot_id,
            "description": snapshot.description,
            "created_at": time.time(),
            "item_count": 1247,
            "status": "created"
        }
        
        provenance_snapshots.append(snapshot_data)
    
    return {
        "snapshot_id": snapshot_id,
        "status": "created",
        "description": snapshot.description
    }

@router.get("/provenance/rollback/{snapshot_id}")
async def rollback_to_snapshot(snapshot_id: str):
    """Rollback to a provenance snapshot."""
    async with _state_lock:
        snapshot = next((s for s in provenance_snapshots if s["id"] == snapshot_id), None)
        
        if not snapshot:
            raise HTTPException(status_code=404, detail="Snapshot not found")
    
    return {
        "snapshot_id": snapshot_id,
        "status": "rollback_simulated",
        "items_restored": snapshot["item_count"],
        "rollback_time": time.time()
    }
