#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified Consciousness API Endpoints

REST API and WebSocket endpoints for the unified consciousness system.
Provides access to consciousness state, emergence detection, and real-time streaming.

Based on GODELOS_UNIFIED_CONSCIOUSNESS_BLUEPRINT.md
"""

import asyncio
import json
import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import asdict

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Query, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Global consciousness engine reference (will be set by unified_server)
unified_consciousness_engine = None
enhanced_websocket_manager = None
emergence_detector = None  # ConsciousnessEmergenceDetector instance

def set_consciousness_engine(engine, websocket_manager):
    """Set the global consciousness engine and websocket manager references"""
    global unified_consciousness_engine, enhanced_websocket_manager
    unified_consciousness_engine = engine
    enhanced_websocket_manager = websocket_manager

def set_emergence_detector(detector):
    """Set the global emergence detector reference"""
    global emergence_detector
    emergence_detector = detector

# Create router
router = APIRouter(prefix="/api/consciousness", tags=["Unified Consciousness"])

# Request/Response models
class ConsciousnessQuery(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None
    include_analysis: bool = True

class ConsciousnessResponse(BaseModel):
    response: str
    consciousness_state: Dict[str, Any]
    emergence_score: float
    processing_time: float
    timestamp: float

class ConsciousnessControlRequest(BaseModel):
    action: str  # "start", "stop", "pause", "resume"
    parameters: Optional[Dict[str, Any]] = None

@router.get("/status")
async def get_consciousness_status():
    """Get current consciousness system status"""
    try:
        if not unified_consciousness_engine:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unavailable",
                    "message": "Unified consciousness engine not initialized",
                    "consciousness_active": False
                }
            )
        
        # Get consciousness report
        consciousness_report = await unified_consciousness_engine.get_consciousness_report()
        
        return {
            "status": "active",
            "consciousness_active": unified_consciousness_engine.consciousness_loop_active,
            "current_consciousness_level": consciousness_report["current_consciousness_level"],
            "recursive_awareness_depth": consciousness_report["recursive_awareness_depth"],
            "phi_measure": consciousness_report["phi_measure"],
            "emergence_indicators": consciousness_report["emergence_indicators"],
            "breakthrough_threshold": consciousness_report["breakthrough_threshold"],
            "consciousness_history_length": consciousness_report["consciousness_history_length"],
            "timestamp": time.time()
        }
    
    except Exception as e:
        logger.error(f"Failed to get consciousness status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve consciousness status: {str(e)}")

@router.post("/process")
async def process_with_consciousness(request: ConsciousnessQuery) -> ConsciousnessResponse:
    """Process a query with full unified consciousness"""
    try:
        if not unified_consciousness_engine:
            raise HTTPException(status_code=503, detail="Unified consciousness engine not available")
        
        start_time = time.time()
        
        # Process with unified consciousness
        response = await unified_consciousness_engine.process_with_unified_awareness(
            request.query, 
            request.context
        )
        
        processing_time = time.time() - start_time
        
        # Get current consciousness state
        consciousness_state = asdict(unified_consciousness_engine.consciousness_state)
        emergence_score = unified_consciousness_engine._detect_consciousness_emergence(
            unified_consciousness_engine.consciousness_state
        )
        
        return ConsciousnessResponse(
            response=response,
            consciousness_state=consciousness_state,
            emergence_score=emergence_score,
            processing_time=processing_time,
            timestamp=time.time()
        )
    
    except Exception as e:
        logger.error(f"Failed to process consciousness query: {e}")
        raise HTTPException(status_code=500, detail=f"Consciousness processing failed: {str(e)}")

@router.get("/state")
async def get_consciousness_state():
    """Get detailed consciousness state"""
    try:
        if not unified_consciousness_engine:
            raise HTTPException(status_code=503, detail="Unified consciousness engine not available")
        
        consciousness_state = unified_consciousness_engine.consciousness_state
        
        return {
            "consciousness_state": asdict(consciousness_state),
            "consciousness_score": consciousness_state.consciousness_score,
            "emergence_level": consciousness_state.emergence_level,
            "timestamp": consciousness_state.timestamp,
            "loops_active": unified_consciousness_engine.consciousness_loop_active
        }
    
    except Exception as e:
        logger.error(f"Failed to get consciousness state: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve consciousness state: {str(e)}")

@router.get("/report")
async def get_consciousness_report():
    """Get comprehensive consciousness assessment report"""
    try:
        if not unified_consciousness_engine:
            raise HTTPException(status_code=503, detail="Unified consciousness engine not available")
        
        report = await unified_consciousness_engine.get_consciousness_report()
        
        return {
            "consciousness_report": report,
            "generation_timestamp": time.time(),
            "engine_status": "active" if unified_consciousness_engine.consciousness_loop_active else "inactive"
        }
    
    except Exception as e:
        logger.error(f"Failed to generate consciousness report: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate consciousness report: {str(e)}")

@router.post("/control")
async def control_consciousness_system(request: ConsciousnessControlRequest):
    """Control consciousness system (start/stop/pause/resume)"""
    try:
        if not unified_consciousness_engine:
            raise HTTPException(status_code=503, detail="Unified consciousness engine not available")
        
        if request.action == "start":
            await unified_consciousness_engine.start_consciousness_loop()
            message = "Consciousness loop started"
        
        elif request.action == "stop":
            await unified_consciousness_engine.stop_consciousness_loop()
            message = "Consciousness loop stopped"
        
        elif request.action == "pause":
            # Note: This would require implementing pause functionality
            message = "Consciousness loop pause not yet implemented"
        
        elif request.action == "resume":
            # Note: This would require implementing resume functionality
            message = "Consciousness loop resume not yet implemented"
        
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {request.action}")
        
        return {
            "action": request.action,
            "status": "success",
            "message": message,
            "consciousness_active": unified_consciousness_engine.consciousness_loop_active,
            "timestamp": time.time()
        }
    
    except Exception as e:
        logger.error(f"Failed to control consciousness system: {e}")
        raise HTTPException(status_code=500, detail=f"Consciousness control failed: {str(e)}")

@router.get("/history")
async def get_consciousness_history(limit: int = Query(100, ge=1, le=1000)):
    """Get consciousness state history"""
    try:
        if not unified_consciousness_engine:
            raise HTTPException(status_code=503, detail="Unified consciousness engine not available")
        
        history = unified_consciousness_engine.consciousness_history[-limit:]
        
        return {
            "history": [asdict(state) for state in history],
            "total_entries": len(unified_consciousness_engine.consciousness_history),
            "returned_entries": len(history),
            "timestamp": time.time()
        }
    
    except Exception as e:
        logger.error(f"Failed to get consciousness history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve consciousness history: {str(e)}")

# Emergence score endpoint

@router.get("/emergence")
async def get_emergence_score():
    """Get current consciousness emergence score and dimensional breakdown."""
    try:
        if emergence_detector is not None:
            return emergence_detector.get_emergence_status()

        # Fallback: derive a basic score from the consciousness engine
        if unified_consciousness_engine:
            state = unified_consciousness_engine.consciousness_state
            score = unified_consciousness_engine._detect_consciousness_emergence(state)
            return {
                "emergence_score": score,
                "dimensions": {},
                "threshold": 0.8,
                "window_size": 60.0,
                "window_samples": 0,
                "breakthrough": score >= 0.8,
                "timestamp": time.time(),
            }

        raise HTTPException(
            status_code=503,
            detail="Neither emergence detector nor consciousness engine is available",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get emergence score: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve emergence score: {str(e)}")


@router.get("/breakthroughs")
async def get_breakthroughs(limit: int = Query(50, ge=1, le=500)):
    """Return historical breakthrough log entries (newest first).

    Reads the persistent ``logs/breakthroughs.jsonl`` file and returns up to
    *limit* entries.  Returns an empty list when no breakthroughs have been
    recorded yet.
    """
    try:
        if emergence_detector is not None:
            entries = emergence_detector.get_breakthroughs(limit=limit)
            return {
                "breakthroughs": entries,
                "total": len(entries),
                "limit": limit,
                "threshold": emergence_detector.threshold,
            }
        raise HTTPException(
            status_code=503,
            detail="Emergence detector is not initialised",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get breakthroughs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve breakthroughs: {str(e)}")


# Observatory reference — set by unified_server at startup
_observatory = None


def set_observatory(observatory) -> None:
    """Register the UnifiedConsciousnessObservatory instance."""
    global _observatory
    _observatory = observatory


def get_observatory():
    """Return the active UnifiedConsciousnessObservatory instance (may be None)."""
    return _observatory


@router.get("/observatory")
async def get_observatory_report():
    """Return the full UnifiedConsciousnessObservatory report.

    Includes uptime, total observed states, total breakthrough events, peak
    score, current emergence snapshot, and the 10 most recent breakthroughs.
    """
    try:
        if _observatory is not None:
            return _observatory.get_report()
        # Fallback: lightweight report using the detector only
        if emergence_detector is not None:
            status = emergence_detector.get_emergence_status()
            recent = emergence_detector.get_breakthroughs(limit=10)
            return {
                "running": False,
                "uptime_seconds": 0,
                "total_states_observed": 0,
                "total_breakthroughs": len(recent),
                "peak_score": status.get("emergence_score", 0.0),
                "current_emergence": status,
                "recent_breakthroughs": recent,
            }
        raise HTTPException(
            status_code=503,
            detail="Neither observatory nor emergence detector is available",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get observatory report: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve observatory report: {str(e)}")


# WebSocket endpoints for real-time consciousness streaming

@router.websocket("/stream")
async def consciousness_stream(websocket: WebSocket):
    """Main consciousness stream - real-time consciousness state updates"""
    if not enhanced_websocket_manager:
        await websocket.close(code=1003, reason="Enhanced WebSocket manager not available")
        return
    
    await enhanced_websocket_manager.handle_consciousness_connection(websocket, "updates")

@router.websocket("/emergence")
async def emergence_stream(websocket: WebSocket):
    """Consciousness emergence detection stream"""
    if not enhanced_websocket_manager:
        await websocket.close(code=1003, reason="Enhanced WebSocket manager not available")
        return
    
    await enhanced_websocket_manager.handle_consciousness_connection(websocket, "emergence")

@router.websocket("/recursive")
async def recursive_awareness_stream(websocket: WebSocket):
    """Recursive self-awareness stream"""
    if not enhanced_websocket_manager:
        await websocket.close(code=1003, reason="Enhanced WebSocket manager not available")
        return
    
    await enhanced_websocket_manager.handle_consciousness_connection(websocket, "recursive")

@router.websocket("/phenomenal")
async def phenomenal_experience_stream(websocket: WebSocket):
    """Phenomenal experience stream"""
    if not enhanced_websocket_manager:
        await websocket.close(code=1003, reason="Enhanced WebSocket manager not available")
        return
    
    await enhanced_websocket_manager.handle_consciousness_connection(websocket, "phenomenal")

@router.websocket("/integration")
async def information_integration_stream(websocket: WebSocket):
    """Information integration (φ/phi) stream"""
    if not enhanced_websocket_manager:
        await websocket.close(code=1003, reason="Enhanced WebSocket manager not available")
        return
    
    await enhanced_websocket_manager.handle_consciousness_connection(websocket, "integration")

@router.websocket("/workspace")
async def global_workspace_stream(websocket: WebSocket):
    """Global workspace broadcasting stream"""
    if not enhanced_websocket_manager:
        await websocket.close(code=1003, reason="Enhanced WebSocket manager not available")
        return
    
    await enhanced_websocket_manager.handle_consciousness_connection(websocket, "workspace")


# ---------------------------------------------------------------------------
# Autonomous Goal Engine endpoints (Issue #81)
# ---------------------------------------------------------------------------

# Module-level references populated at startup by unified_server
_goal_generator = None
_creative_engine = None


def set_goal_engine(generator, creative_engine) -> None:
    """Register the AutonomousGoalGenerator and CreativeSynthesisEngine."""
    global _goal_generator, _creative_engine
    _goal_generator = generator
    _creative_engine = creative_engine


@router.get("/goals")
async def get_autonomous_goals():
    """Return the currently active autonomous goals generated by the system.

    Goals are produced without external prompting by monitoring cognitive
    state gaps (low phi, coherence drift, knowledge gaps, etc.).
    """
    try:
        if _goal_generator is not None:
            goals = _goal_generator.active_goals
            metrics = _goal_generator.get_metrics()
            return {
                "goals": goals,
                "total": len(goals),
                "metrics": metrics,
            }
        raise HTTPException(
            status_code=503,
            detail="Autonomous goal generator is not initialised",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get autonomous goals: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve goals: {str(e)}")


@router.post("/goals/generate")
async def trigger_goal_generation():
    """Manually trigger a round of autonomous goal generation.

    Useful for testing or seeding the goal list before any cognitive state
    has been observed.  Returns the newly proposed goals.
    """
    try:
        if _goal_generator is not None:
            # Use an empty cognitive state to trigger baseline exploration
            new_goals = await _goal_generator.generate({})
            return {
                "new_goals": new_goals,
                "total_new": len(new_goals),
                "active_total": len(_goal_generator.active_goals),
            }
        raise HTTPException(
            status_code=503,
            detail="Autonomous goal generator is not initialised",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate autonomous goals: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate goals: {str(e)}")


@router.get("/creative-synthesis")
async def get_creative_synthesis(n: int = Query(5, ge=1, le=20)):
    """Return the most recent creative concept-synthesis outputs.

    The CreativeSynthesisEngine combines concepts from the active knowledge
    store and scores them on novelty and coherence.
    """
    try:
        if _creative_engine is not None:
            outputs = _creative_engine.get_recent_outputs(limit=n)
            metrics = _creative_engine.get_metrics()
            return {
                "syntheses": outputs,
                "total": len(outputs),
                "metrics": metrics,
            }
        raise HTTPException(
            status_code=503,
            detail="Creative synthesis engine is not initialised",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get creative syntheses: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve syntheses: {str(e)}")


# Health and statistics endpoints

@router.get("/health")
async def consciousness_health():
    """Consciousness system health check"""
    try:
        health_status = {
            "consciousness_engine": "unavailable",
            "websocket_manager": "unavailable",
            "consciousness_loop": False,
            "streaming_connections": 0,
            "last_update": None
        }
        
        if unified_consciousness_engine:
            health_status["consciousness_engine"] = "active"
            health_status["consciousness_loop"] = unified_consciousness_engine.consciousness_loop_active
            if unified_consciousness_engine.consciousness_state:
                health_status["last_update"] = unified_consciousness_engine.consciousness_state.timestamp
        
        if enhanced_websocket_manager:
            health_status["websocket_manager"] = "active"
            stats = await enhanced_websocket_manager.get_consciousness_stats()
            health_status["streaming_connections"] = stats.get("consciousness", {}).get("total_clients", 0)
        
        return health_status
    
    except Exception as e:
        logger.error(f"Consciousness health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@router.get("/stats")
async def consciousness_statistics():
    """Get detailed consciousness system statistics"""
    try:
        stats = {
            "engine_available": unified_consciousness_engine is not None,
            "websocket_manager_available": enhanced_websocket_manager is not None,
            "consciousness_loop_active": False,
            "consciousness_history_size": 0,
            "streaming_stats": {},
            "last_activity": None
        }
        
        if unified_consciousness_engine:
            stats["consciousness_loop_active"] = unified_consciousness_engine.consciousness_loop_active
            stats["consciousness_history_size"] = len(unified_consciousness_engine.consciousness_history)
            if unified_consciousness_engine.consciousness_state:
                stats["last_activity"] = unified_consciousness_engine.consciousness_state.timestamp
        
        if enhanced_websocket_manager:
            streaming_stats = await enhanced_websocket_manager.get_consciousness_stats()
            stats["streaming_stats"] = streaming_stats.get("consciousness", {})
        
        return stats
    
    except Exception as e:
        logger.error(f"Failed to get consciousness statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve statistics: {str(e)}")

# Compatibility endpoint for existing consciousness engine
@router.post("/assess")
async def assess_consciousness_level(query: str = "", context: Optional[Dict] = None):
    """Legacy compatibility endpoint for consciousness assessment"""
    try:
        if not unified_consciousness_engine:
            # Return a fallback response for compatibility
            return {
                "awareness_level": 0.0,
                "self_reflection_depth": 0,
                "autonomous_goals": [],
                "cognitive_integration": 0.0,
                "manifest_behaviors": [],
                "timestamp": time.time(),
                "engine_status": "unavailable"
            }
        
        # Use the unified consciousness engine's compatibility method
        consciousness_state = await unified_consciousness_engine.assess_consciousness_level(query, context)
        
        return {
            "awareness_level": consciousness_state.awareness_level,
            "self_reflection_depth": consciousness_state.self_reflection_depth,
            "autonomous_goals": consciousness_state.autonomous_goals,
            "cognitive_integration": consciousness_state.cognitive_integration,
            "manifest_behaviors": consciousness_state.manifest_behaviors,
            "phenomenal_experience": consciousness_state.phenomenal_experience,
            "meta_cognitive_activity": consciousness_state.meta_cognitive_activity,
            "timestamp": consciousness_state.timestamp,
            "engine_status": "unified_consciousness"
        }
    
    except Exception as e:
        logger.error(f"Consciousness assessment failed: {e}")
        raise HTTPException(status_code=500, detail=f"Assessment failed: {str(e)}")

# Export router
__all__ = [
    'router',
    'set_consciousness_engine',
    'set_emergence_detector',
    'set_observatory',
    'get_observatory',
    'set_goal_engine',
]