"""
Vector Database Management Endpoints

FastAPI endpoints for managing the production vector database.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field

from .vector_service import get_vector_database, VectorDatabaseService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/vector-db", tags=["Vector Database"])


class VectorItem(BaseModel):
    """Model for vector database items."""
    id: str = Field(..., description="Unique identifier for the item")
    text: str = Field(..., description="Text content to be vectorized")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class BatchAddRequest(BaseModel):
    """Request model for batch adding items."""
    items: List[VectorItem] = Field(..., description="Items to add to the database")
    model_name: Optional[str] = Field(default=None, description="Embedding model to use")
    batch_size: Optional[int] = Field(default=100, description="Batch processing size")


class SearchRequest(BaseModel):
    """Request model for vector search."""
    query: str = Field(..., description="Search query text")
    k: Optional[int] = Field(default=5, description="Number of results to return")
    model_name: Optional[str] = Field(default=None, description="Model to use for search")
    similarity_threshold: Optional[float] = Field(default=0.0, description="Minimum similarity score")


class BackupRequest(BaseModel):
    """Request model for database backup."""
    backup_name: Optional[str] = Field(default=None, description="Name for the backup")


class RestoreRequest(BaseModel):
    """Request model for database restore."""
    backup_path: str = Field(..., description="Path to the backup to restore")


def get_vector_db() -> VectorDatabaseService:
    """Dependency to get vector database service."""
    return get_vector_database()


@router.get("/health")
async def vector_db_health(db: VectorDatabaseService = Depends(get_vector_db)):
    """Get vector database health status."""
    try:
        health = db.health_check()
        return {
            "status": "success",
            "data": health,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/stats")
async def vector_db_stats(db: VectorDatabaseService = Depends(get_vector_db)):
    """Get vector database statistics."""
    try:
        stats = db.get_stats()
        return {
            "status": "success",
            "data": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.post("/add-items")
async def add_items(
    request: BatchAddRequest,
    background_tasks: BackgroundTasks,
    db: VectorDatabaseService = Depends(get_vector_db)
):
    """Add items to the vector database."""
    try:
        # Convert request to the format expected by the database
        items = [(item.id, item.text) for item in request.items]
        metadata = [item.metadata for item in request.items]
        
        # For large batches, process in background
        if len(items) > 1000:
            background_tasks.add_task(
                _process_large_batch,
                db, items, metadata, request.model_name, request.batch_size
            )
            return {
                "status": "accepted",
                "message": f"Large batch of {len(items)} items queued for background processing",
                "items_queued": len(items)
            }
        
        # Process small batches immediately
        result = db.add_items(
            items,
            model_name=request.model_name,
            metadata=metadata,
            batch_size=request.batch_size
        )
        
        if isinstance(result, dict):
            return {
                "status": "success",
                "data": result,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "success" if result else "error",
                "items_processed": len(items),
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Failed to add items: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add items: {str(e)}")


async def _process_large_batch(
    db: VectorDatabaseService,
    items: List[tuple],
    metadata: List[Dict],
    model_name: Optional[str],
    batch_size: int
):
    """Process large batches in the background."""
    try:
        result = db.add_items(
            items,
            model_name=model_name,
            metadata=metadata,
            batch_size=batch_size
        )
        logger.info(f"Background batch processing completed: {result}")
    except Exception as e:
        logger.error(f"Background batch processing failed: {e}")


@router.post("/search")
async def search_vectors(
    request: SearchRequest,
    db: VectorDatabaseService = Depends(get_vector_db)
):
    """Search for similar vectors."""
    try:
        results = db.search(
            request.query,
            k=request.k,
            model_name=request.model_name,
            similarity_threshold=request.similarity_threshold
        )
        
        return {
            "status": "success",
            "data": {
                "query": request.query,
                "results": results,
                "total_results": len(results)
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/backup")
async def create_backup(
    request: BackupRequest,
    background_tasks: BackgroundTasks,
    db: VectorDatabaseService = Depends(get_vector_db)
):
    """Create a backup of the vector database."""
    try:
        # Create backup in background for large databases
        background_tasks.add_task(_create_backup, db, request.backup_name)
        
        return {
            "status": "accepted",
            "message": "Backup creation started in background",
            "backup_name": request.backup_name or f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Backup creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Backup creation failed: {str(e)}")


async def _create_backup(db: VectorDatabaseService, backup_name: Optional[str]):
    """Create backup in background."""
    try:
        success = db.backup(backup_name)
        if success:
            logger.info(f"Backup created successfully: {backup_name}")
        else:
            logger.error(f"Backup creation failed: {backup_name}")
    except Exception as e:
        logger.error(f"Background backup creation failed: {e}")


@router.post("/restore")
async def restore_backup(
    request: RestoreRequest,
    db: VectorDatabaseService = Depends(get_vector_db)
):
    """Restore the vector database from a backup."""
    try:
        # Validate backup path
        backup_path = Path(request.backup_path)
        if not backup_path.exists():
            raise HTTPException(status_code=404, detail="Backup path not found")
        
        success = db.restore(request.backup_path)
        
        if success:
            return {
                "status": "success",
                "message": "Database restored successfully",
                "backup_path": request.backup_path,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Restore operation failed")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Restore failed: {e}")
        raise HTTPException(status_code=500, detail=f"Restore failed: {str(e)}")


@router.post("/optimize")
async def optimize_indices(
    background_tasks: BackgroundTasks,
    db: VectorDatabaseService = Depends(get_vector_db)
):
    """Optimize vector database indices."""
    try:
        # Run optimization in background
        background_tasks.add_task(_optimize_indices, db)
        
        return {
            "status": "accepted",
            "message": "Index optimization started in background",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Index optimization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Index optimization failed: {str(e)}")


async def _optimize_indices(db: VectorDatabaseService):
    """Optimize indices in background."""
    try:
        success = db.optimize_indices()
        if success:
            logger.info("Index optimization completed successfully")
        else:
            logger.error("Index optimization failed")
    except Exception as e:
        logger.error(f"Background index optimization failed: {e}")


@router.get("/backups")
async def list_backups():
    """List available backups."""
    try:
        backup_dir = Path("data/vector_db/backups")
        if not backup_dir.exists():
            return {
                "status": "success",
                "data": {"backups": []},
                "timestamp": datetime.now().isoformat()
            }
        
        backups = []
        for backup_path in backup_dir.iterdir():
            if backup_path.is_dir() and backup_path.name.startswith("backup_"):
                backup_info = {
                    "name": backup_path.name,
                    "path": str(backup_path),
                    "created": datetime.fromtimestamp(backup_path.stat().st_mtime).isoformat(),
                    "size_mb": sum(f.stat().st_size for f in backup_path.rglob('*') if f.is_file()) / (1024 * 1024)
                }
                
                # Try to load backup metadata
                info_file = backup_path / "backup_info.json"
                if info_file.exists():
                    try:
                        import json
                        with open(info_file, 'r') as f:
                            backup_metadata = json.load(f)
                        backup_info.update(backup_metadata)
                    except Exception:
                        pass
                
                backups.append(backup_info)
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x.get("created", ""), reverse=True)
        
        return {
            "status": "success",
            "data": {"backups": backups},
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to list backups: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list backups: {str(e)}")


@router.delete("/backups/{backup_name}")
async def delete_backup(backup_name: str):
    """Delete a specific backup."""
    try:
        backup_path = Path("data/vector_db/backups") / backup_name
        
        if not backup_path.exists():
            raise HTTPException(status_code=404, detail="Backup not found")
        
        if not backup_path.is_dir() or not backup_name.startswith("backup_"):
            raise HTTPException(status_code=400, detail="Invalid backup name")
        
        import shutil
        shutil.rmtree(backup_path)
        
        return {
            "status": "success", 
            "message": f"Backup {backup_name} deleted successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete backup: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete backup: {str(e)}")


@router.delete("/clear")
async def clear_database(
    confirm: bool = False,
    db: VectorDatabaseService = Depends(get_vector_db)
):
    """
    Clear all vectors and metadata from the database.
    
    This is a destructive operation that cannot be undone.
    Requires confirmation parameter to be True.
    """
    if not confirm:
        raise HTTPException(
            status_code=400, 
            detail="This is a destructive operation. Set 'confirm=true' parameter to proceed."
        )
    
    try:
        success = db.clear_all()
        
        if success:
            return {
                "status": "success",
                "message": "All vectors and metadata have been cleared from the database",
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to clear database")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to clear database: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear database: {str(e)}")
