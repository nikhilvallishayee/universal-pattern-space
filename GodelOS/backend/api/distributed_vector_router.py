"""
Distributed Vector Search API Router

FastAPI router for distributed vector search cluster management.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any

try:
    from fastapi import APIRouter, HTTPException, Query as FastAPIQuery
    from pydantic import BaseModel
    FASTAPI_AVAILABLE = True
except ImportError:
    # Create fallback classes
    class BaseModel:
        pass
    def APIRouter():
        return None
    FASTAPI_AVAILABLE = False

from backend.core.distributed_vector_search import (
    ClusterManager, ClusterConfig, NodeStatus, ShardStatus,
    get_cluster_manager, initialize_cluster_manager
)
from backend.core.distributed_vector_database import (
    DistributedVectorDatabase, get_distributed_database,
    initialize_distributed_database
)
from backend.core.vector_database import EmbeddingModel

logger = logging.getLogger(__name__)

# Create the router
router = APIRouter() if FASTAPI_AVAILABLE else None


class ClusterConfigModel(BaseModel):
    """Pydantic model for cluster configuration."""
    cluster_name: str
    replication_factor: int = 2
    shard_count: int = 16
    heartbeat_interval: int = 10
    failure_detection_timeout: int = 30
    max_load_factor: float = 0.8
    rebalance_threshold: float = 0.1
    enable_auto_scaling: bool = False
    min_nodes: int = 1
    max_nodes: int = 10


class VectorSearchRequest(BaseModel):
    """Request model for vector search."""
    query: str
    k: int = 10
    filters: Optional[Dict[str, Any]] = None
    include_metadata: bool = True
    similarity_threshold: float = 0.0


class VectorInsertRequest(BaseModel):
    """Request model for vector insertion."""
    texts: List[str]
    metadata: Optional[List[Dict[str, Any]]] = None
    batch_size: int = 100


class NodeJoinRequest(BaseModel):
    """Request model for joining a cluster."""
    cluster_name: str
    seed_nodes: List[str]  # List of "host:port" addresses


# Only define endpoints if FastAPI is available
if FASTAPI_AVAILABLE and router:
    
    @router.post("/cluster/create", tags=["Cluster Management"])
    async def create_cluster(config: ClusterConfigModel):
        """Create a new distributed vector search cluster."""
        try:
            cluster_config = ClusterConfig(
                cluster_name=config.cluster_name,
                replication_factor=config.replication_factor,
                shard_count=config.shard_count,
                heartbeat_interval=config.heartbeat_interval,
                failure_detection_timeout=config.failure_detection_timeout,
                max_load_factor=config.max_load_factor,
                rebalance_threshold=config.rebalance_threshold,
                enable_auto_scaling=config.enable_auto_scaling,
                min_nodes=config.min_nodes,
                max_nodes=config.max_nodes
            )
            
            # Initialize cluster manager
            cluster_manager = initialize_cluster_manager(cluster_config)
            await cluster_manager.start()
            
            # Join cluster (create new if no seed nodes)
            success = await cluster_manager.join_cluster()
            
            if not success:
                raise HTTPException(status_code=500, detail="Failed to create cluster")
            
            # Initialize distributed database
            embedding_models = [
                EmbeddingModel(
                    name="sentence-transformers/all-MiniLM-L6-v2",
                    model_path="sentence-transformers/all-MiniLM-L6-v2",
                    dimension=384,
                    is_primary=True
                )
            ]
            
            distributed_db = initialize_distributed_database(
                cluster_manager=cluster_manager,
                embedding_models=embedding_models
            )
            await distributed_db.initialize()
            
            return {
                "status": "success",
                "cluster_name": config.cluster_name,
                "node_id": cluster_manager.node_id,
                "message": "Cluster created successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to create cluster: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/cluster/join", tags=["Cluster Management"])
    async def join_cluster(request: NodeJoinRequest):
        """Join an existing distributed vector search cluster."""
        try:
            # Get cluster manager (should be initialized)
            cluster_manager = get_cluster_manager()
            if not cluster_manager:
                raise HTTPException(status_code=400, detail="No cluster manager available")
            
            # Set seed nodes and join
            cluster_manager.seed_nodes = request.seed_nodes
            success = await cluster_manager.join_cluster()
            
            if not success:
                raise HTTPException(status_code=500, detail="Failed to join cluster")
            
            return {
                "status": "success",
                "cluster_name": request.cluster_name,
                "node_id": cluster_manager.node_id,
                "seed_nodes": request.seed_nodes,
                "message": "Successfully joined cluster"
            }
            
        except Exception as e:
            logger.error(f"Failed to join cluster: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/cluster/status", tags=["Cluster Management"])
    async def get_cluster_status():
        """Get current cluster status and statistics."""
        try:
            cluster_manager = get_cluster_manager()
            if not cluster_manager:
                return {"status": "no_cluster", "message": "No cluster manager active"}
            
            stats = cluster_manager.get_cluster_stats()
            return {
                "status": "active",
                "cluster_stats": stats
            }
            
        except Exception as e:
            logger.error(f"Failed to get cluster status: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/vectors/search", tags=["Vector Operations"])
    async def search_vectors(request: VectorSearchRequest):
        """Search for similar vectors in the distributed database."""
        try:
            distributed_db = get_distributed_database()
            if not distributed_db:
                raise HTTPException(status_code=400, detail="No distributed database available")
            
            results = await distributed_db.search_vectors(
                query=request.query,
                k=request.k,
                filters=request.filters,
                include_metadata=request.include_metadata,
                similarity_threshold=request.similarity_threshold
            )
            
            return {
                "status": "success",
                "query": request.query,
                "results": results,
                "count": len(results)
            }
            
        except Exception as e:
            logger.error(f"Failed to search vectors: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/vectors/insert", tags=["Vector Operations"])
    async def insert_vectors(request: VectorInsertRequest):
        """Insert vectors into the distributed database."""
        try:
            distributed_db = get_distributed_database()
            if not distributed_db:
                raise HTTPException(status_code=400, detail="No distributed database available")
            
            vector_ids = await distributed_db.add_vectors(
                texts=request.texts,
                metadata=request.metadata,
                batch_size=request.batch_size
            )
            
            return {
                "status": "success",
                "vector_ids": vector_ids,
                "count": len(vector_ids),
                "message": f"Successfully inserted {len(vector_ids)} vectors"
            }
            
        except Exception as e:
            logger.error(f"Failed to insert vectors: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.delete("/vectors/{vector_id}", tags=["Vector Operations"])
    async def delete_vector(vector_id: str):
        """Delete a specific vector from the distributed database."""
        try:
            distributed_db = get_distributed_database()
            if not distributed_db:
                raise HTTPException(status_code=400, detail="No distributed database available")
            
            deleted_count = await distributed_db.delete_vectors([vector_id])
            
            if deleted_count == 0:
                raise HTTPException(status_code=404, detail="Vector not found")
            
            return {
                "status": "success",
                "vector_id": vector_id,
                "message": "Vector deleted successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to delete vector: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/nodes", tags=["Cluster Management"])
    async def list_nodes():
        """List all nodes in the cluster."""
        try:
            cluster_manager = get_cluster_manager()
            if not cluster_manager:
                return {"nodes": [], "message": "No cluster active"}
            
            nodes = []
            for node_id, node in cluster_manager.nodes.items():
                nodes.append({
                    "node_id": node_id,
                    "host": node.host,
                    "port": node.port,
                    "status": node.status.value,
                    "last_heartbeat": node.last_heartbeat.isoformat() if node.last_heartbeat else None
                })
            
            return {
                "status": "success",
                "nodes": nodes,
                "count": len(nodes)
            }
            
        except Exception as e:
            logger.error(f"Failed to list nodes: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/shards", tags=["Cluster Management"])
    async def list_shards():
        """List all shards in the cluster."""
        try:
            cluster_manager = get_cluster_manager()
            if not cluster_manager:
                return {"shards": [], "message": "No cluster active"}
            
            shards = []
            for shard_id, shard in cluster_manager.shards.items():
                shards.append({
                    "shard_id": shard_id,
                    "primary_node": shard.primary_node,
                    "replica_nodes": shard.replica_nodes,
                    "status": shard.status.value,
                    "range_start": shard.range_start,
                    "range_end": shard.range_end
                })
            
            return {
                "status": "success",
                "shards": shards,
                "count": len(shards)
            }
            
        except Exception as e:
            logger.error(f"Failed to list shards: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/health", tags=["Monitoring"])
    async def health_check():
        """Check the health of the distributed vector search system."""
        try:
            cluster_manager = get_cluster_manager()
            distributed_db = get_distributed_database()
            
            cluster_healthy = cluster_manager is not None and cluster_manager._running
            db_healthy = distributed_db is not None
            
            overall_status = "healthy" if cluster_healthy and db_healthy else "unhealthy"
            
            return {
                "status": overall_status,
                "cluster_manager": {
                    "available": cluster_manager is not None,
                    "running": cluster_healthy,
                    "node_id": cluster_manager.node_id if cluster_manager else None
                },
                "distributed_database": {
                    "available": db_healthy,
                    "models_loaded": len(distributed_db.embedding_models) if distributed_db else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    @router.get("/stats", tags=["Monitoring"])
    async def get_statistics():
        """Get comprehensive statistics for the distributed system."""
        try:
            cluster_manager = get_cluster_manager()
            distributed_db = get_distributed_database()
            
            stats = {}
            
            if cluster_manager:
                stats["cluster"] = cluster_manager.get_cluster_stats()
            
            if distributed_db:
                stats["database"] = await distributed_db.get_database_stats()
            
            return {
                "status": "success",
                "statistics": stats
            }
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/backup", tags=["Management"])
    async def create_backup(backup_dir: str = FastAPIQuery(..., description="Directory to store backup")):
        """Create a backup of the distributed database."""
        try:
            distributed_db = get_distributed_database()
            if not distributed_db:
                raise HTTPException(status_code=400, detail="No distributed database available")
            
            backup_info = await distributed_db.backup_database(backup_dir)
            
            return {
                "status": "success",
                "backup_info": backup_info,
                "message": "Backup created successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise HTTPException(status_code=500, detail=str(e))

else:
    logger.warning("FastAPI not available, distributed vector endpoints will not be created")


# Legacy compatibility function
def setup_distributed_vector_endpoints(app, unified_server_globals=None):
    """Legacy setup function for compatibility."""
    if not FASTAPI_AVAILABLE:
        logger.warning("FastAPI not available, cannot setup distributed vector endpoints")
        return
    
    logger.info("Using router-based distributed vector endpoints instead of app-based setup")
    # The router should be included via app.include_router in unified_server.py
