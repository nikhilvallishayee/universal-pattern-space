"""
API endpoints for Query Replay Harness

Provides REST API endpoints for managing query recordings and replays.
"""

from fastapi import HTTPException, Query as FastAPIQuery
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


def setup_replay_endpoints(app, cognitive_manager):
    """Setup replay harness API endpoints."""
    
    import backend.core.query_replay_harness as _harness_mod
    ReplayStatus = _harness_mod.ReplayStatus
    
    @app.get("/api/v1/replay/recordings")
    async def list_recordings(
        tags: Optional[str] = FastAPIQuery(None, description="Comma-separated tags to filter by"),
        limit: int = FastAPIQuery(100, description="Maximum number of recordings to return")
    ):
        """List available query recordings."""
        try:
            filter_tags = tags.split(',') if tags else None
            recordings = _harness_mod.replay_harness.list_recordings(tags=filter_tags, limit=limit)
            
            return {
                "status": "success",
                "recordings": recordings,
                "total": len(recordings),
                "limit": limit,
                "filters": {"tags": filter_tags} if filter_tags else None
            }
            
        except Exception as e:
            logger.error(f"Error listing recordings: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to list recordings: {str(e)}")
    
    @app.get("/api/v1/replay/recordings/{recording_id}")
    async def get_recording(recording_id: str):
        """Get details of a specific recording."""
        try:
            recording = _harness_mod.replay_harness.load_recording(recording_id)
            
            if not recording:
                raise HTTPException(status_code=404, detail=f"Recording not found: {recording_id}")
            
            # Convert to dict for JSON serialization
            from dataclasses import asdict
            recording_dict = asdict(recording)
            
            return {
                "status": "success",
                "recording": recording_dict
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting recording {recording_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get recording: {str(e)}")
    
    @app.post("/api/v1/replay/recordings/{recording_id}/replay")
    async def replay_recording(
        recording_id: str,
        compare_results: bool = FastAPIQuery(True, description="Whether to compare with original results"),
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Replay a recorded query."""
        try:
            if not cognitive_manager:
                raise HTTPException(status_code=503, detail="Cognitive manager not available")
            
            # Check if recording exists
            recording = _harness_mod.replay_harness.load_recording(recording_id)
            if not recording:
                raise HTTPException(status_code=404, detail=f"Recording not found: {recording_id}")
            
            # Start replay
            replay_result = await _harness_mod.replay_harness.replay_query(
                recording_id=recording_id,
                cognitive_manager=cognitive_manager,
                compare_results=compare_results,
                metadata=metadata or {}
            )
            
            if not replay_result:
                raise HTTPException(status_code=500, detail="Failed to start replay")
            
            # Convert to dict for JSON serialization
            from dataclasses import asdict
            result_dict = asdict(replay_result)
            
            return {
                "status": "success",
                "replay": result_dict
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error replaying recording {recording_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to replay recording: {str(e)}")
    
    @app.get("/api/v1/replay/replays/{replay_id}/status")
    async def get_replay_status(replay_id: str):
        """Get the status of a replay operation."""
        try:
            status = _harness_mod.replay_harness.get_replay_status(replay_id)
            
            if not status:
                raise HTTPException(status_code=404, detail=f"Replay not found: {replay_id}")
            
            return {
                "status": "success",
                "replay_status": status
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting replay status {replay_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get replay status: {str(e)}")
    
    @app.post("/api/v1/replay/recordings/{recording_id}/analyze")
    async def analyze_recording(recording_id: str):
        """Analyze a recording to extract insights and patterns."""
        try:
            recording = _harness_mod.replay_harness.load_recording(recording_id)
            if not recording:
                raise HTTPException(status_code=404, detail=f"Recording not found: {recording_id}")
            
            # Perform analysis
            analysis = _analyze_recording(recording)
            
            return {
                "status": "success",
                "analysis": analysis,
                "recording_id": recording_id
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error analyzing recording {recording_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to analyze recording: {str(e)}")
    
    @app.get("/api/v1/replay/stats")
    async def get_replay_stats():
        """Get statistics about recordings and replays."""
        try:
            # Get all recordings
            all_recordings = _harness_mod.replay_harness.list_recordings(limit=1000)
            
            # Calculate statistics
            total_recordings = len(all_recordings)
            
            if total_recordings == 0:
                return {
                    "status": "success",
                    "stats": {
                        "total_recordings": 0,
                        "total_duration_ms": 0,
                        "average_duration_ms": 0,
                        "total_steps": 0,
                        "average_steps": 0,
                        "tag_distribution": {},
                        "recent_activity": []
                    }
                }
            
            total_duration = sum(r.get("duration_ms", 0) or 0 for r in all_recordings)
            total_steps = sum(r.get("steps_count", 0) or 0 for r in all_recordings)
            
            # Tag distribution
            tag_counts = {}
            for recording in all_recordings:
                for tag in recording.get("tags", []):
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
            # Recent activity (last 10 recordings)
            recent_activity = all_recordings[:10]
            
            stats = {
                "total_recordings": total_recordings,
                "total_duration_ms": total_duration,
                "average_duration_ms": total_duration / total_recordings if total_recordings > 0 else 0,
                "total_steps": total_steps,
                "average_steps": total_steps / total_recordings if total_recordings > 0 else 0,
                "tag_distribution": tag_counts,
                "recent_activity": recent_activity
            }
            
            return {
                "status": "success",
                "stats": stats
            }
            
        except Exception as e:
            logger.error(f"Error getting replay stats: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get replay stats: {str(e)}")
    
    @app.delete("/api/v1/replay/recordings/{recording_id}")
    async def delete_recording(recording_id: str):
        """Delete a specific recording."""
        try:
            # Find and delete the recording file
            from pathlib import Path
            
            recording_files = list(_harness_mod.replay_harness.storage_path.glob(f"{recording_id}_*.json"))
            
            if not recording_files:
                raise HTTPException(status_code=404, detail=f"Recording not found: {recording_id}")
            
            filepath = recording_files[0]
            filepath.unlink()
            
            logger.info(f"Deleted recording {recording_id}")
            
            return {
                "status": "success",
                "message": f"Recording {recording_id} deleted successfully"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting recording {recording_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to delete recording: {str(e)}")
    
    @app.post("/api/v1/replay/settings")
    async def update_replay_settings(
        enable_recording: Optional[bool] = None,
        max_recordings: Optional[int] = None,
        auto_cleanup_days: Optional[int] = None
    ):
        """Update replay harness settings."""
        try:
            settings_updated = {}
            
            if enable_recording is not None:
                _harness_mod.replay_harness.enable_recording = enable_recording
                settings_updated["enable_recording"] = enable_recording
            
            if max_recordings is not None:
                _harness_mod.replay_harness.max_recordings = max_recordings
                settings_updated["max_recordings"] = max_recordings
            
            if auto_cleanup_days is not None:
                _harness_mod.replay_harness.auto_cleanup_days = auto_cleanup_days
                settings_updated["auto_cleanup_days"] = auto_cleanup_days
            
            # Get current settings
            current_settings = {
                "enable_recording": _harness_mod.replay_harness.enable_recording,
                "max_recordings": _harness_mod.replay_harness.max_recordings,
                "auto_cleanup_days": _harness_mod.replay_harness.auto_cleanup_days
            }
            
            return {
                "status": "success",
                "message": "Settings updated successfully",
                "updated": settings_updated,
                "current_settings": current_settings
            }
            
        except Exception as e:
            logger.error(f"Error updating replay settings: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to update settings: {str(e)}")


def _analyze_recording(recording) -> Dict[str, Any]:
    """Analyze a recording to extract insights and patterns."""
    from dataclasses import asdict
    
    if hasattr(recording, '__dict__'):
        recording_dict = asdict(recording)
    else:
        recording_dict = recording
    
    analysis = {
        "performance": {
            "total_duration_ms": recording_dict.get("total_duration_ms", 0),
            "steps_count": len(recording_dict.get("steps", [])),
            "average_step_duration_ms": 0
        },
        "cognitive_patterns": {
            "reasoning_depth": 0,
            "knowledge_sources_used": 0,
            "error_count": 0
        },
        "efficiency_metrics": {
            "processing_speed": "normal",
            "resource_usage": "normal",
            "bottlenecks": []
        },
        "insights": []
    }
    
    steps = recording_dict.get("steps", [])
    
    if steps:
        total_step_time = sum(step.get("duration_ms", 0) for step in steps)
        analysis["performance"]["average_step_duration_ms"] = total_step_time / len(steps)
        
        # Count errors
        analysis["cognitive_patterns"]["error_count"] = sum(
            1 for step in steps if step.get("error")
        )
        
        # Analyze step types
        step_types = [step.get("step_type", "") for step in steps]
        analysis["cognitive_patterns"]["reasoning_depth"] = len(set(step_types))
        
        # Performance insights
        if analysis["performance"]["total_duration_ms"] > 10000:  # > 10 seconds
            analysis["insights"].append("Query took longer than expected - consider optimization")
        
        if analysis["cognitive_patterns"]["error_count"] > 0:
            analysis["insights"].append(f"Processing included {analysis['cognitive_patterns']['error_count']} errors")
        
        if len(steps) > 10:
            analysis["insights"].append("Complex reasoning process with many steps")
    
    return analysis
