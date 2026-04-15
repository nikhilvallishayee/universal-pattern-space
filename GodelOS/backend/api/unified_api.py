#!/usr/bin/env python3
"""
Unified API Router for GodelOS

Implements the comprehensive API contracts defined in the architectural specification.
Provides consistent, versioned endpoints for all cognitive functionality.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query as QueryParam
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import json

logger = logging.getLogger(__name__)

# Import core components
from backend.core.cognitive_manager import CognitiveManager, get_cognitive_manager, CognitiveProcessType
from backend.core.agentic_daemon_system import AgenticDaemonSystem, get_agentic_daemon_system


# ===== API MODELS =====

class CognitiveProcessRequest(BaseModel):
    """Request for cognitive processing."""
    query: str = Field(..., description="The input query or prompt")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Optional context information")
    reasoning_depth: int = Field(default=3, ge=1, le=10, description="Depth of reasoning to perform")
    include_transparency: bool = Field(default=True, description="Include cognitive transparency data")
    process_type: str = Field(default="query_processing", description="Type of cognitive processing")


class CognitiveResponse(BaseModel):
    """Response from cognitive processing."""
    session_id: str
    answer: str
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: List[Dict[str, Any]]
    knowledge_used: List[str]
    processing_time: float
    metadata: Dict[str, Any]


class KnowledgeNode(BaseModel):
    """Knowledge graph node."""
    id: str
    content: str
    node_type: str
    confidence: float = Field(ge=0.0, le=1.0)
    created_at: datetime
    embeddings: Optional[List[float]] = None
    relationships: List[str] = Field(default_factory=list)


class Relationship(BaseModel):
    """Knowledge graph relationship."""
    source: str
    target: str
    relationship_type: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: List[str] = Field(default_factory=list)


class KnowledgeIngestRequest(BaseModel):
    """Request for knowledge ingestion."""
    content: str = Field(..., description="Content to ingest")
    title: Optional[str] = Field(default=None, description="Title or identifier")
    content_type: str = Field(default="text", description="Type of content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    extract_entities: bool = Field(default=True, description="Extract entities and relationships")


class KnowledgeGraphResponse(BaseModel):
    """Knowledge graph data response."""
    nodes: List[KnowledgeNode]
    edges: List[Relationship]
    statistics: Dict[str, Any]
    metadata: Dict[str, Any]


class KnowledgeGapResponse(BaseModel):
    """Knowledge gap analysis response."""
    gaps: List[Dict[str, Any]]
    priority_gaps: List[Dict[str, Any]]
    recommendations: List[str]
    metadata: Dict[str, Any]


class DaemonTriggerRequest(BaseModel):
    """Request to trigger daemon process."""
    process_type: str = Field(..., description="Type of process to trigger")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Process parameters")
    priority: int = Field(default=5, ge=1, le=10, description="Task priority")


class DaemonStatusResponse(BaseModel):
    """Daemon system status response."""
    system_enabled: bool
    active_daemons: int
    total_daemons: int
    uptime_hours: float
    aggregate_metrics: Dict[str, Any]
    daemons: Dict[str, Any]


# ===== DEPENDENCY INJECTION =====

async def get_cognitive_manager_dependency() -> CognitiveManager:
    """Dependency injection for cognitive manager."""
    return await get_cognitive_manager()


async def get_daemon_system_dependency() -> AgenticDaemonSystem:
    """Dependency injection for daemon system."""
    return await get_agentic_daemon_system()


# ===== API ROUTER =====

# Create versioned router
router_v1 = APIRouter(prefix="/api/v1", tags=["GodelOS API v1"])


# ===== COGNITIVE PROCESSING ENDPOINTS =====

@router_v1.post("/cognitive/process", response_model=CognitiveResponse)
async def process_cognitive_query(
    request: CognitiveProcessRequest,
    cognitive_manager: CognitiveManager = Depends(get_cognitive_manager_dependency)
):
    """
    Process a query through the complete cognitive pipeline.
    
    This is the main endpoint for cognitive processing, providing:
    - Context-aware reasoning
    - Knowledge integration
    - Self-reflection
    - Transparency logging
    """
    try:
        # Map process type string to enum
        process_type_map = {
            "query_processing": CognitiveProcessType.QUERY_PROCESSING,
            "knowledge_integration": CognitiveProcessType.KNOWLEDGE_INTEGRATION,
            "autonomous_reasoning": CognitiveProcessType.AUTONOMOUS_REASONING,
            "self_reflection": CognitiveProcessType.SELF_REFLECTION,
            "knowledge_gap_analysis": CognitiveProcessType.KNOWLEDGE_GAP_ANALYSIS
        }
        
        process_type = process_type_map.get(request.process_type, CognitiveProcessType.QUERY_PROCESSING)
        
        # Process the query
        result = await cognitive_manager.process_query(
            query=request.query,
            context=request.context,
            process_type=process_type
        )
        
        # Convert to API response format
        return CognitiveResponse(
            session_id=result.session_id,
            answer=result.response.get("answer", "No answer generated"),
            confidence=result.confidence,
            reasoning=result.reasoning_trace,
            knowledge_used=result.knowledge_used,
            processing_time=result.processing_time,
            metadata=result.metadata
        )
        
    except Exception as e:
        logger.error(f"Error in cognitive processing: {e}")
        raise HTTPException(status_code=500, detail=f"Cognitive processing failed: {str(e)}")


@router_v1.get("/cognitive/state")
async def get_cognitive_state(
    cognitive_manager: CognitiveManager = Depends(get_cognitive_manager_dependency)
):
    """Get current cognitive state and metrics."""
    try:
        state = await cognitive_manager.get_cognitive_state()
        return state
    except Exception as e:
        logger.error(f"Error getting cognitive state: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cognitive state: {str(e)}")


@router_v1.post("/cognitive/reflect")
async def reflect_on_reasoning(
    reasoning_trace: List[Dict[str, Any]],
    cognitive_manager: CognitiveManager = Depends(get_cognitive_manager_dependency)
):
    """Perform self-reflection on a reasoning trace."""
    try:
        reflection = await cognitive_manager.reflect_on_reasoning(reasoning_trace)
        return {
            "insights": reflection.insights,
            "improvements": reflection.improvements,
            "confidence_adjustment": reflection.confidence_adjustment,
            "knowledge_gaps_identified": reflection.knowledge_gaps_identified,
            "learning_opportunities": reflection.learning_opportunities
        }
    except Exception as e:
        logger.error(f"Error in reflection: {e}")
        raise HTTPException(status_code=500, detail=f"Reflection failed: {str(e)}")


# ===== KNOWLEDGE MANAGEMENT ENDPOINTS =====

@router_v1.get("/knowledge/graph", response_model=KnowledgeGraphResponse)
async def get_knowledge_graph(
    node_id: Optional[str] = QueryParam(None, description="Specific node ID to focus on"),
    max_depth: int = QueryParam(3, ge=1, le=10, description="Maximum relationship depth"),
    include_embeddings: bool = QueryParam(False, description="Include vector embeddings")
):
    """Get knowledge graph data for visualization."""
    try:
        # This would interface with the knowledge pipeline
        # For now, return mock data matching the expected structure
        
        mock_nodes = [
            KnowledgeNode(
                id="node_1",
                content="Artificial Intelligence",
                node_type="concept",
                confidence=0.95,
                created_at=datetime.now(),
                relationships=["rel_1", "rel_2"]
            ),
            KnowledgeNode(
                id="node_2", 
                content="Machine Learning",
                node_type="concept",
                confidence=0.92,
                created_at=datetime.now(),
                relationships=["rel_1"]
            )
        ]
        
        mock_edges = [
            Relationship(
                source="node_1",
                target="node_2",
                relationship_type="encompasses",
                confidence=0.9,
                evidence=["ML is a subset of AI"]
            )
        ]
        
        return KnowledgeGraphResponse(
            nodes=mock_nodes,
            edges=mock_edges,
            statistics={
                "total_nodes": len(mock_nodes),
                "total_edges": len(mock_edges),
                "avg_confidence": 0.93
            },
            metadata={
                "query_time": time.time(),
                "max_depth": max_depth,
                "focused_node": node_id
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting knowledge graph: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get knowledge graph: {str(e)}")


@router_v1.post("/knowledge/ingest")
async def ingest_knowledge(
    request: KnowledgeIngestRequest,
    background_tasks: BackgroundTasks
):
    """Ingest new knowledge into the system."""
    try:
        # This would interface with the knowledge pipeline
        ingestion_id = f"ingest_{int(time.time())}"
        
        # Add background task for processing
        background_tasks.add_task(
            _process_knowledge_ingestion,
            ingestion_id,
            request.content,
            request.title,
            request.metadata
        )
        
        return {
            "ingestion_id": ingestion_id,
            "status": "accepted",
            "message": "Knowledge ingestion started",
            "content_length": len(request.content),
            "extract_entities": request.extract_entities
        }
        
    except Exception as e:
        logger.error(f"Error in knowledge ingestion: {e}")
        raise HTTPException(status_code=500, detail=f"Knowledge ingestion failed: {str(e)}")


@router_v1.put("/knowledge/update/{node_id}")
async def update_knowledge_node(
    node_id: str,
    updates: Dict[str, Any]
):
    """Update a specific knowledge node."""
    try:
        # This would interface with the knowledge store
        return {
            "node_id": node_id,
            "status": "updated",
            "updates_applied": list(updates.keys()),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error updating knowledge node: {e}")
        raise HTTPException(status_code=500, detail=f"Knowledge update failed: {str(e)}")


# ===== GAP ANALYSIS ENDPOINTS =====

@router_v1.get("/gaps/identify", response_model=KnowledgeGapResponse)
async def identify_knowledge_gaps(
    cognitive_manager: CognitiveManager = Depends(get_cognitive_manager_dependency)
):
    """Identify knowledge gaps in the system."""
    try:
        gaps = await cognitive_manager.identify_knowledge_gaps()
        
        # Convert gaps to dict format
        gap_dicts = []
        priority_gaps = []
        
        for gap in gaps:
            gap_dict = {
                "id": gap.id,
                "description": gap.description,
                "priority": gap.priority,
                "domain": gap.domain,
                "confidence": gap.confidence,
                "identified_at": gap.identified_at.isoformat(),
                "status": gap.status
            }
            gap_dicts.append(gap_dict)
            
            if gap.priority in ["high", "critical"]:
                priority_gaps.append(gap_dict)
        
        recommendations = [
            "Focus on high-priority gaps first",
            "Consider automated research for well-defined gaps",
            "Expand knowledge in frequently queried domains"
        ]
        
        return KnowledgeGapResponse(
            gaps=gap_dicts,
            priority_gaps=priority_gaps,
            recommendations=recommendations,
            metadata={
                "total_gaps": len(gaps),
                "high_priority": len(priority_gaps),
                "analysis_time": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Error identifying knowledge gaps: {e}")
        raise HTTPException(status_code=500, detail=f"Gap analysis failed: {str(e)}")


@router_v1.post("/gaps/research/{gap_id}")
async def research_knowledge_gap(
    gap_id: str,
    background_tasks: BackgroundTasks,
    daemon_system: AgenticDaemonSystem = Depends(get_daemon_system_dependency)
):
    """Trigger research for a specific knowledge gap."""
    try:
        # Trigger autonomous researcher daemon
        success = await daemon_system.trigger_daemon(
            daemon_name="autonomous_researcher",
            task_type="research_gap",
            parameters={"gap_id": gap_id, "priority": "high"}
        )
        
        if success:
            return {
                "gap_id": gap_id,
                "status": "research_triggered",
                "message": "Autonomous research task created",
                "estimated_completion": "5-15 minutes"
            }
        else:
            raise HTTPException(status_code=503, detail="Failed to trigger research daemon")
            
    except Exception as e:
        logger.error(f"Error triggering gap research: {e}")
        raise HTTPException(status_code=500, detail=f"Gap research failed: {str(e)}")


# ===== AUTONOMOUS PROCESSES ENDPOINTS =====

@router_v1.get("/daemon/status", response_model=DaemonStatusResponse)
async def get_daemon_status(
    daemon_system: AgenticDaemonSystem = Depends(get_daemon_system_dependency)
):
    """Get status of all autonomous daemon processes."""
    try:
        status = await daemon_system.get_system_status()
        
        return DaemonStatusResponse(
            system_enabled=status["system_enabled"],
            active_daemons=status["active_daemons"],
            total_daemons=status["total_daemons"],
            uptime_hours=status["uptime_hours"],
            aggregate_metrics=status["aggregate_metrics"],
            daemons=status["daemons"]
        )
        
    except Exception as e:
        logger.error(f"Error getting daemon status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get daemon status: {str(e)}")


@router_v1.post("/daemon/trigger/{process_type}")
async def trigger_daemon_process(
    process_type: str,
    request: DaemonTriggerRequest,
    daemon_system: AgenticDaemonSystem = Depends(get_daemon_system_dependency)
):
    """Manually trigger a specific daemon process."""
    try:
        # Map process types to daemon names
        daemon_map = {
            "knowledge_gap_analysis": "knowledge_gap_detector",
            "autonomous_research": "autonomous_researcher", 
            "system_optimization": "system_optimizer"
        }
        
        daemon_name = daemon_map.get(process_type)
        if not daemon_name:
            raise HTTPException(status_code=400, detail=f"Unknown process type: {process_type}")
        
        success = await daemon_system.trigger_daemon(
            daemon_name=daemon_name,
            task_type=request.process_type,
            parameters=request.parameters
        )
        
        if success:
            return {
                "process_type": process_type,
                "daemon": daemon_name,
                "status": "triggered",
                "task_type": request.process_type,
                "priority": request.priority,
                "parameters": request.parameters
            }
        else:
            raise HTTPException(status_code=503, detail=f"Failed to trigger daemon: {daemon_name}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering daemon process: {e}")
        raise HTTPException(status_code=500, detail=f"Daemon trigger failed: {str(e)}")


@router_v1.post("/daemon/enable/{daemon_name}")
async def enable_daemon(
    daemon_name: str,
    daemon_system: AgenticDaemonSystem = Depends(get_daemon_system_dependency)
):
    """Enable a specific daemon."""
    try:
        success = daemon_system.enable_daemon(daemon_name)
        
        if success:
            return {
                "daemon": daemon_name,
                "status": "enabled",
                "message": f"Daemon {daemon_name} has been enabled"
            }
        else:
            raise HTTPException(status_code=404, detail=f"Daemon not found: {daemon_name}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enabling daemon: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to enable daemon: {str(e)}")


@router_v1.post("/daemon/disable/{daemon_name}")
async def disable_daemon(
    daemon_name: str,
    daemon_system: AgenticDaemonSystem = Depends(get_daemon_system_dependency)
):
    """Disable a specific daemon."""
    try:
        success = daemon_system.disable_daemon(daemon_name)
        
        if success:
            return {
                "daemon": daemon_name,
                "status": "disabled",
                "message": f"Daemon {daemon_name} has been disabled"
            }
        else:
            raise HTTPException(status_code=404, detail=f"Daemon not found: {daemon_name}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling daemon: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to disable daemon: {str(e)}")


# ===== STREAMING ENDPOINTS =====

@router_v1.get("/cognitive/stream")
async def stream_cognitive_updates():
    """Stream real-time cognitive updates via Server-Sent Events."""
    
    async def generate_updates():
        """Generate cognitive update stream."""
        try:
            while True:
                # This would interface with the WebSocket manager or event system
                update = {
                    "timestamp": datetime.now().isoformat(),
                    "type": "cognitive_update",
                    "data": {
                        "active_processes": 3,
                        "processing_load": 0.45,
                        "recent_activity": "Processing user query"
                    }
                }
                
                yield f"data: {json.dumps(update)}\n\n"
                await asyncio.sleep(2)  # Update every 2 seconds
                
        except asyncio.CancelledError:
            logger.info("Cognitive stream cancelled")
        except Exception as e:
            logger.error(f"Error in cognitive stream: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_updates(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


# ===== HELPER FUNCTIONS =====

async def _process_knowledge_ingestion(
    ingestion_id: str,
    content: str,
    title: Optional[str],
    metadata: Dict[str, Any]
):
    """Background task for processing knowledge ingestion."""
    try:
        logger.info(f"Processing knowledge ingestion: {ingestion_id}")
        
        # This would interface with the knowledge pipeline
        # Simulate processing time
        await asyncio.sleep(2)
        
        logger.info(f"Completed knowledge ingestion: {ingestion_id}")
        
    except Exception as e:
        logger.error(f"Error in knowledge ingestion {ingestion_id}: {e}")


# ===== LEGACY COMPATIBILITY ENDPOINTS =====

# Add legacy endpoints for backward compatibility
legacy_router = APIRouter(prefix="/api", tags=["Legacy API"])

@legacy_router.post("/query")
async def legacy_process_query(
    request: Dict[str, Any],
    cognitive_manager: CognitiveManager = Depends(get_cognitive_manager_dependency)
):
    """Legacy query processing endpoint for backward compatibility."""
    try:
        # Convert legacy request to new format
        cognitive_request = CognitiveProcessRequest(
            query=request.get("query", ""),
            context=request.get("context", {}),
            reasoning_depth=request.get("reasoning_depth", 3)
        )
        
        # Process using new cognitive endpoint
        result = await process_cognitive_query(cognitive_request, cognitive_manager)
        
        # Convert to legacy response format
        return {
            "answer": result.answer,
            "confidence": result.confidence,
            "reasoning": result.reasoning,
            "session_id": result.session_id,
            "processing_time": result.processing_time
        }
        
    except Exception as e:
        logger.error(f"Error in legacy query processing: {e}")
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")


# Export routers
unified_api_router = router_v1
legacy_api_router = legacy_router
