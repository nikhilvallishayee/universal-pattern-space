"""
API endpoints for Distributed Vector Search Management

Provides REST API endpoints for managing the distributed vector search cluster,
monitoring health, and performing distributed operations.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any

try:
    from fastapi import APIRouter, HTTPException, Query as FastAPIQuery, Body
    from pydantic import BaseModel
    FASTAPI_AVAILABLE = True
except ImportError:
    # Fallback when FastAPI is not available
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

# Create router
router = APIRouter() if FASTAPI_AVAILABLE else None


class ClusterConfigModel(BaseModel):
    """Pydantic model for cluster configuration."""
    cluster_name: str
    replication_factor: int = 2
    shard_count: int = 32
    heartbeat_interval: int = 10
    failure_detection_timeout: int = 30
    max_load_factor: float = 0.8
    rebalance_threshold: float = 0.2
    enable_auto_scaling: bool = True
    min_nodes: int = 1
    max_nodes: int = 100


class VectorSearchRequest(BaseModel):
    """Pydantic model for vector search requests."""
    query: str
    k: int = 10
    filters: Optional[Dict[str, Any]] = None
    include_metadata: bool = True


class VectorInsertRequest(BaseModel):
    """Pydantic model for vector insertion requests."""
    texts: List[str]
    metadata: Optional[List[Dict[str, Any]]] = None
    batch_size: int = 100


def setup_distributed_vector_endpoints(app, unified_server_globals=None):
    """Setup distributed vector search API endpoints."""
    
    @app.post("/api/v1/distributed-vectors/cluster/create")
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
                "message": f"Cluster '{config.cluster_name}' created successfully",
                "cluster_stats": cluster_manager.get_cluster_stats()
            }
            
        except Exception as e:
            logger.error(f"Error creating cluster: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to create cluster: {str(e)}")
    
    @app.post("/api/v1/distributed-vectors/cluster/join")
    async def join_cluster(
        config: ClusterConfigModel,
        seed_nodes: List[Dict[str, Any]] = Body(..., description="List of seed nodes with 'host' and 'port'")
    ):
        """Join an existing distributed vector search cluster."""
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
            
            # Parse seed nodes
            seed_node_tuples = [(node["host"], node["port"]) for node in seed_nodes]
            
            # Join cluster
            success = await cluster_manager.join_cluster(seed_node_tuples)
            
            if not success:
                raise HTTPException(status_code=500, detail="Failed to join cluster")
            
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
                "message": f"Successfully joined cluster '{config.cluster_name}'",
                "cluster_stats": cluster_manager.get_cluster_stats()
            }
            
        except Exception as e:
            logger.error(f"Error joining cluster: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to join cluster: {str(e)}")
    
    @app.get("/api/v1/distributed-vectors/cluster/status")
    async def get_cluster_status():
        """Get the current cluster status and statistics."""
        try:
            cluster_manager = get_cluster_manager()
            if not cluster_manager:
                raise HTTPException(status_code=503, detail="Cluster not initialized")
            
            stats = cluster_manager.get_cluster_stats()
            
            # Add detailed node information
            node_details = []
            for node in cluster_manager.nodes.values():
                node_details.append({
                    "node_id": node.node_id,
                    "host": node.host,
                    "port": node.port,
                    "status": node.status.value,
                    "last_heartbeat": node.last_heartbeat.isoformat(),
                    "shard_count": node.shard_count,
                    "load_factor": node.load_factor,
                    "is_healthy": node.is_healthy
                })
            
            # Add detailed shard information
            shard_details = []
            for shard in cluster_manager.shards.values():
                shard_details.append({
                    "shard_id": shard.shard_id,
                    "hash_range": shard.hash_range,
                    "primary_node": shard.primary_node,
                    "replica_nodes": shard.replica_nodes,
                    "status": shard.status.value,
                    "document_count": shard.document_count,
                    "size_bytes": shard.size_bytes,
                    "last_updated": shard.last_updated.isoformat()
                })
            
            return {
                "status": "success",
                "cluster_stats": stats,
                "nodes": node_details,
                "shards": shard_details
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting cluster status: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get cluster status: {str(e)}")
    
    @app.post("/api/v1/distributed-vectors/cluster/rebalance")
    async def trigger_rebalance():
        """Manually trigger cluster rebalancing."""
        try:
            cluster_manager = get_cluster_manager()
            if not cluster_manager:
                raise HTTPException(status_code=503, detail="Cluster not initialized")
            
            # Trigger rebalancing
            await cluster_manager._rebalance_cluster()
            
            return {
                "status": "success",
                "message": "Cluster rebalancing triggered",
                "cluster_stats": cluster_manager.get_cluster_stats()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error triggering rebalance: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to trigger rebalance: {str(e)}")
    
    @app.post("/api/v1/distributed-vectors/search")
    async def search_distributed_vectors(request: VectorSearchRequest):
        """Search for vectors across the distributed database."""
        try:
            distributed_db = get_distributed_database()
            if not distributed_db:
                raise HTTPException(status_code=503, detail="Distributed database not initialized")
            
            results = await distributed_db.search_vectors(
                query=request.query,
                k=request.k,
                filters=request.filters,
                include_metadata=request.include_metadata
            )
            
            return {
                "status": "success",
                "query": request.query,
                "results": results,
                "total_found": len(results)
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error searching vectors: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to search vectors: {str(e)}")
    
    @app.post("/api/v1/distributed-vectors/insert")
    async def insert_distributed_vectors(request: VectorInsertRequest):
        """Insert vectors into the distributed database."""
        try:
            distributed_db = get_distributed_database()
            if not distributed_db:
                raise HTTPException(status_code=503, detail="Distributed database not initialized")
            
            if not request.texts:
                raise HTTPException(status_code=400, detail="No texts provided")
            
            vector_ids = await distributed_db.add_vectors(
                texts=request.texts,
                metadata=request.metadata,
                batch_size=request.batch_size
            )
            
            return {
                "status": "success",
                "message": f"Successfully inserted {len(vector_ids)} vectors",
                "vector_ids": vector_ids,
                "total_inserted": len(vector_ids)
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error inserting vectors: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to insert vectors: {str(e)}")
    
    @app.delete("/api/v1/distributed-vectors/{vector_id}")
    async def delete_distributed_vector(vector_id: str):
        """Delete a specific vector from the distributed database."""
        try:
            distributed_db = get_distributed_database()
            if not distributed_db:
                raise HTTPException(status_code=503, detail="Distributed database not initialized")
            
            deleted_count = await distributed_db.delete_vectors([vector_id])
            
            if deleted_count == 0:
                raise HTTPException(status_code=404, detail=f"Vector {vector_id} not found")
            
            return {
                "status": "success",
                "message": f"Vector {vector_id} deleted successfully",
                "deleted_count": deleted_count
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting vector: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to delete vector: {str(e)}")
    
    @app.post("/api/v1/distributed-vectors/delete-batch")
    async def delete_distributed_vectors_batch(vector_ids: List[str] = Body(...)):
        """Delete multiple vectors from the distributed database."""
        try:
            distributed_db = get_distributed_database()
            if not distributed_db:
                raise HTTPException(status_code=503, detail="Distributed database not initialized")
            
            if not vector_ids:
                raise HTTPException(status_code=400, detail="No vector IDs provided")
            
            deleted_count = await distributed_db.delete_vectors(vector_ids)
            
            return {
                "status": "success",
                "message": f"Deleted {deleted_count} vectors",
                "requested_count": len(vector_ids),
                "deleted_count": deleted_count
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting vectors: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to delete vectors: {str(e)}")
    
    @app.get("/api/v1/distributed-vectors/stats")
    async def get_distributed_database_stats():
        """Get comprehensive statistics for the distributed database."""
        try:
            distributed_db = get_distributed_database()
            if not distributed_db:
                raise HTTPException(status_code=503, detail="Distributed database not initialized")
            
            stats = await distributed_db.get_database_stats()
            
            return {
                "status": "success",
                "stats": stats
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get database stats: {str(e)}")
    
    @app.post("/api/v1/distributed-vectors/backup")
    async def backup_distributed_database(backup_dir: str = Body(..., embed=True)):
        """Create a backup of the local distributed database shards."""
        try:
            distributed_db = get_distributed_database()
            if not distributed_db:
                raise HTTPException(status_code=503, detail="Distributed database not initialized")
            
            backup_info = await distributed_db.backup_database(backup_dir)
            
            return {
                "status": "success",
                "message": "Database backup completed",
                "backup_info": backup_info
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to create backup: {str(e)}")
    
    @app.get("/api/v1/distributed-vectors/cluster/nodes")
    async def list_cluster_nodes(
        status_filter: Optional[str] = FastAPIQuery(None, description="Filter by node status")
    ):
        """List all nodes in the cluster with optional status filtering."""
        try:
            cluster_manager = get_cluster_manager()
            if not cluster_manager:
                raise HTTPException(status_code=503, detail="Cluster not initialized")
            
            nodes = []
            for node in cluster_manager.nodes.values():
                if status_filter and node.status.value != status_filter:
                    continue
                
                nodes.append({
                    "node_id": node.node_id,
                    "host": node.host,
                    "port": node.port,
                    "status": node.status.value,
                    "last_heartbeat": node.last_heartbeat.isoformat(),
                    "shard_count": node.shard_count,
                    "load_factor": node.load_factor,
                    "is_healthy": node.is_healthy,
                    "metadata": node.metadata
                })
            
            return {
                "status": "success",
                "nodes": nodes,
                "total_count": len(nodes),
                "filter_applied": status_filter
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error listing nodes: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to list nodes: {str(e)}")
    
    @app.get("/api/v1/distributed-vectors/cluster/shards")
    async def list_cluster_shards(
        status_filter: Optional[str] = FastAPIQuery(None, description="Filter by shard status"),
        node_filter: Optional[str] = FastAPIQuery(None, description="Filter by node ID")
    ):
        """List all shards in the cluster with optional filtering."""
        try:
            cluster_manager = get_cluster_manager()
            if not cluster_manager:
                raise HTTPException(status_code=503, detail="Cluster not initialized")
            
            shards = []
            for shard in cluster_manager.shards.values():
                if status_filter and shard.status.value != status_filter:
                    continue
                
                if node_filter and (shard.primary_node != node_filter and 
                                  node_filter not in shard.replica_nodes):
                    continue
                
                shards.append({
                    "shard_id": shard.shard_id,
                    "hash_range": shard.hash_range,
                    "primary_node": shard.primary_node,
                    "replica_nodes": shard.replica_nodes,
                    "status": shard.status.value,
                    "document_count": shard.document_count,
                    "size_bytes": shard.size_bytes,
                    "last_updated": shard.last_updated.isoformat()
                })
            
            return {
                "status": "success",
                "shards": shards,
                "total_count": len(shards),
                "filters_applied": {
                    "status": status_filter,
                    "node": node_filter
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error listing shards: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to list shards: {str(e)}")
    
    @app.post("/api/v1/distributed-vectors/cluster/stop")
    async def stop_cluster():
        """Gracefully stop the cluster manager and distributed database."""
        try:
            cluster_manager = get_cluster_manager()
            distributed_db = get_distributed_database()
            
            if cluster_manager:
                await cluster_manager.stop()
            
            # Note: In production, you'd also gracefully shutdown the distributed database
            
            return {
                "status": "success",
                "message": "Cluster stopped successfully"
            }
            
        except Exception as e:
            logger.error(f"Error stopping cluster: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to stop cluster: {str(e)}")


def setup_distributed_vector_health_endpoints(app):
    """Setup health check endpoints for distributed vector search."""
    
    @app.get("/api/v1/distributed-vectors/health")
    async def distributed_vector_health():
        """Health check for distributed vector search system."""
        try:
            cluster_manager = get_cluster_manager()
            distributed_db = get_distributed_database()
            
            health_status = {
                "status": "healthy",
                "timestamp": asyncio.get_event_loop().time(),
                "components": {
                    "cluster_manager": {
                        "available": cluster_manager is not None,
                        "status": "healthy" if cluster_manager else "unavailable"
                    },
                    "distributed_database": {
                        "available": distributed_db is not None,
                        "status": "healthy" if distributed_db else "unavailable"
                    }
                }
            }
            
            if cluster_manager:
                stats = cluster_manager.get_cluster_stats()
                health_status["cluster_stats"] = {
                    "cluster_name": stats.get("cluster_name"),
                    "node_count": stats.get("nodes", {}).get("total", 0),
                    "healthy_nodes": stats.get("nodes", {}).get("healthy", 0),
                    "shard_count": stats.get("shards", {}).get("total", 0),
                    "healthy_shards": stats.get("shards", {}).get("healthy", 0)
                }
            
            # Determine overall health
            if not cluster_manager or not distributed_db:
                health_status["status"] = "degraded"
            
            status_code = 200 if health_status["status"] == "healthy" else 503
            
            return health_status
            
        except Exception as e:
            logger.error(f"Error checking distributed vector health: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": asyncio.get_event_loop().time()
            }
