"""
API endpoints for Adaptive Knowledge Ingestion Pipeline
"""

import asyncio
import logging
import os
import tempfile
import time
from typing import Dict, List, Optional, Any
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from pydantic import BaseModel

from backend.core.adaptive_ingestion_pipeline import (
    AdaptiveIngestionPipeline, 
    AnalysisLevel, 
    PreflightEstimate
)

logger = logging.getLogger(__name__)

# Global pipeline instance
pipeline: Optional[AdaptiveIngestionPipeline] = None

# Request/Response models
class PreflightRequest(BaseModel):
    """Request for preflight estimation."""
    file_size_bytes: int
    file_type: str
    sample_text: Optional[str] = None


class PreflightResponse(BaseModel):
    """Response with preflight estimates for all analysis levels."""
    estimates: Dict[str, Dict[str, Any]]  # level -> estimate data
    

class ImportJobRequest(BaseModel):
    """Request to start an import job."""
    analysis_level: str
    file_path: Optional[str] = None  # For server-side files
    

class ImportJobResponse(BaseModel):
    """Response when starting an import job."""
    job_id: str
    status: str
    message: str
    

class JobStatusResponse(BaseModel):
    """Job status response."""
    job_id: str
    status: str
    progress_percent: float
    processed_chunks: int
    total_chunks: int
    elapsed_time_seconds: float
    eta_seconds: Optional[float]
    error_message: Optional[str]
    analysis_level: str


class JobListResponse(BaseModel):
    """Response for listing jobs."""
    jobs: List[JobStatusResponse]
    

class GraphResponse(BaseModel):
    """Knowledge graph response."""
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    metadata: Dict[str, Any]


# Create router
router = APIRouter(prefix="/api/import", tags=["import"])


async def get_pipeline() -> AdaptiveIngestionPipeline:
    """Get or create the global pipeline instance."""
    global pipeline
    if pipeline is None:
        # Import here to avoid circular imports
        try:
            from backend.core.vector_service import get_vector_database
            vector_db = get_vector_database()
        except ImportError:
            logger.warning("Vector database not available, using None")
            vector_db = None
            
        pipeline = AdaptiveIngestionPipeline(vector_database=vector_db)
        logger.info("Initialized adaptive ingestion pipeline")
    return pipeline


@router.post("/preflight", response_model=PreflightResponse)
async def preflight_estimation(
    file: UploadFile = File(...),
) -> PreflightResponse:
    """
    Get preflight estimation for ingestion job.
    Provides ETA and resource estimates for all analysis levels.
    """
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
            
        try:
            ingestion_pipeline = await get_pipeline()
            estimates = await ingestion_pipeline.estimate_workload(tmp_file_path)
            
            # Convert to response format
            estimates_dict = {}
            for level, estimate in estimates.items():
                estimates_dict[level.value] = {
                    "estimated_chunks": estimate.estimated_chunks,
                    "estimated_tokens": estimate.estimated_tokens,
                    "eta_p50_seconds": estimate.eta_p50_seconds,
                    "eta_p90_seconds": estimate.eta_p90_seconds,
                    "memory_usage_mb": estimate.memory_usage_mb,
                    "eta_p50_human": _format_duration(estimate.eta_p50_seconds),
                    "eta_p90_human": _format_duration(estimate.eta_p90_seconds),
                }
                
            return PreflightResponse(estimates=estimates_dict)
            
        finally:
            # Clean up temporary file
            os.unlink(tmp_file_path)
            
    except Exception as e:
        logger.error(f"Preflight estimation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Preflight estimation failed: {str(e)}")


@router.post("/jobs", response_model=ImportJobResponse)
async def start_import_job(
    analysis_level: str = Form(...),
    file: UploadFile = File(...),
) -> ImportJobResponse:
    """
    Start a new import job with the specified analysis level.
    """
    try:
        # Validate analysis level
        try:
            level = AnalysisLevel(analysis_level)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid analysis level: {analysis_level}. Must be one of: fast, balanced, deep"
            )
            
        # Save uploaded file
        upload_dir = Path("/tmp/godelos_uploads")
        upload_dir.mkdir(exist_ok=True)
        
        timestamp = int(time.time())
        safe_filename = f"{timestamp}_{file.filename}"
        file_path = upload_dir / safe_filename
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
            
        # Start ingestion job
        ingestion_pipeline = await get_pipeline()
        job_id = await ingestion_pipeline.start_ingestion_job(str(file_path), level)
        
        return ImportJobResponse(
            job_id=job_id,
            status="queued",
            message=f"Import job started with analysis level '{analysis_level}'"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start import job: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start import job: {str(e)}")


@router.get("/jobs", response_model=JobListResponse)
async def list_jobs() -> JobListResponse:
    """
    List all import jobs with their current status.
    """
    try:
        ingestion_pipeline = await get_pipeline()
        jobs = []
        
        for job_id in ingestion_pipeline.active_jobs.keys():
            status_data = ingestion_pipeline.get_job_status(job_id)
            if status_data:
                jobs.append(JobStatusResponse(**status_data))
                
        return JobListResponse(jobs=jobs)
        
    except Exception as e:
        logger.error(f"Failed to list jobs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list jobs: {str(e)}")


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str) -> JobStatusResponse:
    """
    Get detailed status for a specific job.
    """
    try:
        ingestion_pipeline = await get_pipeline()
        status_data = ingestion_pipeline.get_job_status(job_id)
        
        if not status_data:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
            
        return JobStatusResponse(**status_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get job status: {str(e)}")


@router.post("/jobs/{job_id}/pause")
async def pause_job(job_id: str):
    """
    Pause a running job.
    """
    # For now, this is the same as cancel since we don't have pause/resume implemented
    return await cancel_job(job_id)


@router.post("/jobs/{job_id}/resume")
async def resume_job(job_id: str):
    """
    Resume a paused job.
    """
    raise HTTPException(status_code=501, detail="Job resume not yet implemented")


@router.post("/jobs/{job_id}/cancel")
async def cancel_job(job_id: str):
    """
    Cancel a running job.
    """
    try:
        ingestion_pipeline = await get_pipeline()
        success = await ingestion_pipeline.cancel_job(job_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found or cannot be cancelled")
            
        return {"message": f"Job {job_id} cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel job: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel job: {str(e)}")


@router.get("/graph/{doc_id}", response_model=GraphResponse)
async def get_knowledge_graph(doc_id: str) -> GraphResponse:
    """
    Get knowledge graph for a specific document.
    """
    try:
        # This would integrate with the existing knowledge graph system
        # For now, return a mock response
        nodes = [
            {
                "id": f"{doc_id}_chunk_0",
                "type": "Chunk",
                "label": "Document Chunk 0",
                "properties": {
                    "chunk_index": 0,
                    "token_count": 150,
                    "quality_score": 0.85
                }
            },
            {
                "id": f"{doc_id}_concept_0",
                "type": "Concept",
                "label": "Main Topic",
                "properties": {
                    "confidence": 0.92
                }
            }
        ]
        
        edges = [
            {
                "source": f"{doc_id}_chunk_0",
                "target": f"{doc_id}_concept_0",
                "type": "TAGGED_AS",
                "properties": {
                    "score": 0.88
                }
            }
        ]
        
        metadata = {
            "doc_id": doc_id,
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "generated_at": time.time()
        }
        
        return GraphResponse(
            nodes=nodes,
            edges=edges,
            metadata=metadata
        )
        
    except Exception as e:
        logger.error(f"Failed to get knowledge graph: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get knowledge graph: {str(e)}")


@router.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    try:
        ingestion_pipeline = await get_pipeline()
        
        # Get system resources
        resources = ingestion_pipeline.autotuner.get_system_resources()
        
        return {
            "status": "healthy",
            "pipeline_active": True,
            "active_jobs": len(ingestion_pipeline.active_jobs),
            "workers": len(ingestion_pipeline.worker_tasks),
            "system_resources": {
                "cpu_cores": resources.cpu_cores,
                "memory_usage_percent": resources.current_memory_usage_percent,
                "cpu_usage_percent": resources.cpu_usage_percent,
                "available_memory_gb": resources.available_memory_gb
            },
            "autotuner_config": {
                "num_workers": ingestion_pipeline.autotuner.current_config.num_workers,
                "batch_size": ingestion_pipeline.autotuner.current_config.batch_size,
                "memory_limit_gb": ingestion_pipeline.autotuner.current_config.memory_limit_gb
            }
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


# Background task for cleanup
async def cleanup_old_jobs():
    """Background task to clean up old jobs."""
    try:
        ingestion_pipeline = await get_pipeline()
        await ingestion_pipeline.cleanup_completed_jobs()
    except Exception as e:
        logger.error(f"Job cleanup failed: {e}")


# Utility functions
def _format_duration(seconds: float) -> str:
    """Format duration in human-readable format."""
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} minutes"
    else:
        hours = seconds / 3600
        return f"{hours:.1f} hours"


# Startup/shutdown handlers
async def startup_handler():
    """Initialize the pipeline on startup."""
    try:
        await get_pipeline()
        logger.info("Adaptive ingestion API initialized")
    except Exception as e:
        logger.error(f"Failed to initialize adaptive ingestion API: {e}")


async def shutdown_handler():
    """Cleanup on shutdown."""
    global pipeline
    if pipeline:
        try:
            await pipeline.shutdown()
            logger.info("Adaptive ingestion pipeline shutdown complete")
        except Exception as e:
            logger.error(f"Error during pipeline shutdown: {e}")