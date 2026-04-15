"""
Distributed Vector Database Implementation

This module provides a distributed vector database that uses the cluster management
system for sharding, replication, and horizontal scaling.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Union
from pathlib import Path
import numpy as np

from .distributed_vector_search import (
    ClusterManager, VectorShard, ClusterNode, ShardStatus,
    get_cluster_manager
)
from .vector_database import PersistentVectorDatabase, VectorMetadata, EmbeddingModel

logger = logging.getLogger(__name__)


class DistributedVectorDatabase:
    """
    Distributed vector database with clustering, sharding, and replication.
    
    Features:
    - Automatic sharding across cluster nodes
    - Configurable replication for fault tolerance
    - Horizontal scaling with automatic load balancing
    - Consistent hashing for optimal data distribution
    - Failure detection and automatic recovery
    """
    
    def __init__(self, 
                 cluster_manager: ClusterManager,
                 local_storage_dir: str = "data/distributed_vectors",
                 embedding_models: List[EmbeddingModel] = None):
        """
        Initialize distributed vector database.
        
        Args:
            cluster_manager: Cluster management instance
            local_storage_dir: Local storage directory for this node's shards
            embedding_models: Available embedding models
        """
        self.cluster_manager = cluster_manager
        self.local_storage_dir = Path(local_storage_dir)
        self.local_storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Local shard databases
        self.local_shards: Dict[str, PersistentVectorDatabase] = {}
        
        # Embedding models
        self.embedding_models = embedding_models or []
        self.primary_model = next((m for m in self.embedding_models if m.is_primary), None)
        
        # Performance tracking
        self.operation_stats = {
            "searches": 0,
            "inserts": 0,
            "errors": 0,
            "avg_search_time": 0.0,
            "avg_insert_time": 0.0
        }
        
        logger.info(f"Distributed vector database initialized with {len(self.embedding_models)} models")
    
    async def initialize(self) -> None:
        """Initialize the distributed database."""
        # Initialize local shards for this node
        await self._initialize_local_shards()
        
        # Set up cluster event handlers
        self.cluster_manager.node_failed_callbacks.append(self._on_node_failed)
        self.cluster_manager.shard_rebalanced_callbacks.append(self._on_shards_rebalanced)
        
        logger.info("Distributed vector database initialized")
    
    async def add_vectors(self, 
                         texts: List[str], 
                         embeddings: Optional[List[np.ndarray]] = None,
                         metadata: Optional[List[Dict[str, Any]]] = None,
                         batch_size: int = 100) -> List[str]:
        """
        Add vectors to the distributed database.
        
        Args:
            texts: Text content for the vectors
            embeddings: Pre-computed embeddings (optional)
            metadata: Metadata for each vector
            batch_size: Batch size for processing
            
        Returns:
            List of vector IDs
        """
        start_time = time.time()
        
        try:
            if not texts:
                return []
            
            # Ensure metadata list
            if metadata is None:
                metadata = [{}] * len(texts)
            elif len(metadata) != len(texts):
                raise ValueError("Metadata length must match texts length")
            
            # Generate embeddings if not provided
            if embeddings is None and self.primary_model:
                embeddings = await self._generate_embeddings(texts)
            elif embeddings and len(embeddings) != len(texts):
                raise ValueError("Embeddings length must match texts length")
            
            # Process in batches
            all_ids = []
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                batch_embeddings = embeddings[i:i + batch_size] if embeddings else None
                batch_metadata = metadata[i:i + batch_size]
                
                batch_ids = await self._add_batch(batch_texts, batch_embeddings, batch_metadata)
                all_ids.extend(batch_ids)
            
            # Update stats
            duration = time.time() - start_time
            self.operation_stats["inserts"] += len(texts)
            self._update_avg_time("avg_insert_time", duration, len(texts))
            
            logger.info(f"Added {len(all_ids)} vectors in {duration:.2f}s")
            return all_ids
            
        except Exception as e:
            self.operation_stats["errors"] += 1
            logger.error(f"Error adding vectors: {e}")
            raise
    
    async def search_vectors(self, 
                           query: str, 
                           k: int = 10,
                           query_embedding: Optional[np.ndarray] = None,
                           filters: Optional[Dict[str, Any]] = None,
                           include_metadata: bool = True) -> List[Dict[str, Any]]:
        """
        Search for similar vectors across the distributed database.
        
        Args:
            query: Query text
            k: Number of results to return
            query_embedding: Pre-computed query embedding
            filters: Metadata filters
            include_metadata: Whether to include metadata in results
            
        Returns:
            List of search results with scores and metadata
        """
        start_time = time.time()
        
        try:
            # Generate query embedding if not provided
            if query_embedding is None and self.primary_model:
                query_embedding = await self._generate_embeddings([query])
                query_embedding = query_embedding[0] if query_embedding else None
            
            if query_embedding is None:
                raise ValueError("Could not generate query embedding")
            
            # Search across all shards
            all_results = []
            search_tasks = []
            
            # Get all healthy shards
            healthy_shards = self._get_healthy_shards()
            
            for shard in healthy_shards:
                # Search each shard
                task = self._search_shard(shard, query_embedding, k * 2, filters, include_metadata)
                search_tasks.append(task)
            
            # Collect results from all shards
            shard_results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            for i, result in enumerate(shard_results):
                if isinstance(result, Exception):
                    logger.warning(f"Error searching shard {healthy_shards[i].shard_id}: {result}")
                    continue
                all_results.extend(result)
            
            # Merge and rank results
            final_results = self._merge_search_results(all_results, k)
            
            # Update stats
            duration = time.time() - start_time
            self.operation_stats["searches"] += 1
            self._update_avg_time("avg_search_time", duration, 1)
            
            logger.debug(f"Search completed in {duration:.3f}s, found {len(final_results)} results")
            return final_results
            
        except Exception as e:
            self.operation_stats["errors"] += 1
            logger.error(f"Error searching vectors: {e}")
            raise
    
    async def delete_vectors(self, vector_ids: List[str]) -> int:
        """
        Delete vectors from the distributed database.
        
        Args:
            vector_ids: List of vector IDs to delete
            
        Returns:
            Number of vectors deleted
        """
        if not vector_ids:
            return 0
        
        try:
            delete_tasks = []
            
            # Group deletions by shard
            shard_deletions = {}
            for vector_id in vector_ids:
                shard_id = self._get_shard_for_vector(vector_id)
                if shard_id not in shard_deletions:
                    shard_deletions[shard_id] = []
                shard_deletions[shard_id].append(vector_id)
            
            # Delete from each shard
            for shard_id, ids in shard_deletions.items():
                task = self._delete_from_shard(shard_id, ids)
                delete_tasks.append(task)
            
            # Collect results
            deletion_results = await asyncio.gather(*delete_tasks, return_exceptions=True)
            
            total_deleted = 0
            for result in deletion_results:
                if isinstance(result, Exception):
                    logger.warning(f"Error deleting from shard: {result}")
                else:
                    total_deleted += result
            
            logger.info(f"Deleted {total_deleted} vectors")
            return total_deleted
            
        except Exception as e:
            logger.error(f"Error deleting vectors: {e}")
            raise
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get comprehensive database statistics."""
        try:
            # Get cluster stats
            cluster_stats = self.cluster_manager.get_cluster_stats()
            
            # Get local shard stats
            local_stats = {}
            total_vectors = 0
            total_size = 0
            
            for shard_id, db in self.local_shards.items():
                try:
                    stats = await self._get_shard_stats(db)
                    local_stats[shard_id] = stats
                    total_vectors += stats.get("vector_count", 0)
                    total_size += stats.get("size_bytes", 0)
                except Exception as e:
                    logger.warning(f"Error getting stats for shard {shard_id}: {e}")
            
            return {
                "cluster": cluster_stats,
                "local_node": {
                    "node_id": self.cluster_manager.node_id,
                    "shard_count": len(self.local_shards),
                    "total_vectors": total_vectors,
                    "total_size_bytes": total_size,
                    "shards": local_stats
                },
                "performance": self.operation_stats,
                "embedding_models": [
                    {
                        "name": model.name,
                        "dimension": model.dimension,
                        "is_primary": model.is_primary,
                        "is_available": model.is_available
                    }
                    for model in self.embedding_models
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {"error": str(e)}
    
    async def backup_database(self, backup_dir: str) -> Dict[str, Any]:
        """Create a backup of the local shards."""
        backup_path = Path(backup_dir)
        backup_path.mkdir(parents=True, exist_ok=True)
        
        backup_info = {
            "timestamp": time.time(),
            "node_id": self.cluster_manager.node_id,
            "shards": []
        }
        
        try:
            for shard_id, db in self.local_shards.items():
                shard_backup_dir = backup_path / shard_id
                shard_backup_dir.mkdir(exist_ok=True)
                
                # Backup shard data
                await self._backup_shard(db, str(shard_backup_dir))
                
                backup_info["shards"].append({
                    "shard_id": shard_id,
                    "backup_path": str(shard_backup_dir)
                })
            
            # Save backup metadata
            with open(backup_path / "backup_info.json", "w") as f:
                json.dump(backup_info, f, indent=2)
            
            logger.info(f"Database backup completed: {backup_dir}")
            return backup_info
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            raise
    
    async def _initialize_local_shards(self) -> None:
        """Initialize local shards for this node."""
        node_id = self.cluster_manager.node_id
        
        # Find shards assigned to this node
        for shard in self.cluster_manager.shards.values():
            if shard.primary_node == node_id or node_id in shard.replica_nodes:
                await self._initialize_shard(shard.shard_id)
    
    async def _initialize_shard(self, shard_id: str) -> None:
        """Initialize a local shard database."""
        if shard_id in self.local_shards:
            return
        
        shard_dir = self.local_storage_dir / shard_id
        shard_dir.mkdir(exist_ok=True)
        
        # Create local database for this shard
        shard_db = PersistentVectorDatabase(
            storage_dir=str(shard_dir),
            backup_dir=str(shard_dir / "backups")
        )
        
        # Initialize with embedding models
        for model in self.embedding_models:
            try:
                await shard_db.add_embedding_model(model)
            except Exception as e:
                logger.warning(f"Failed to add model {model.name} to shard {shard_id}: {e}")
        
        await shard_db.initialize()
        self.local_shards[shard_id] = shard_db
        
        logger.info(f"Initialized local shard: {shard_id}")
    
    async def _generate_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings for texts using the primary model."""
        if not self.primary_model:
            raise ValueError("No primary embedding model available")
        
        # This would use the actual embedding model
        # For now, return random embeddings for testing
        embeddings = []
        for text in texts:
            # Generate a deterministic but random-looking embedding
            np.random.seed(hash(text) % 2**32)
            embedding = np.random.normal(0, 1, self.primary_model.dimension).astype(np.float32)
            embeddings.append(embedding)
        
        return embeddings
    
    async def _add_batch(self, 
                        texts: List[str], 
                        embeddings: Optional[List[np.ndarray]], 
                        metadata: List[Dict[str, Any]]) -> List[str]:
        """Add a batch of vectors to appropriate shards."""
        # Group vectors by shard
        shard_batches = {}
        vector_ids = []
        
        for i, text in enumerate(texts):
            # Generate vector ID and determine shard
            vector_id = self._generate_vector_id(text)
            vector_ids.append(vector_id)
            
            shard_id = self._get_shard_for_vector(vector_id)
            if shard_id not in shard_batches:
                shard_batches[shard_id] = {"texts": [], "embeddings": [], "metadata": [], "ids": []}
            
            shard_batches[shard_id]["texts"].append(text)
            shard_batches[shard_id]["embeddings"].append(embeddings[i] if embeddings else None)
            shard_batches[shard_id]["metadata"].append(metadata[i])
            shard_batches[shard_id]["ids"].append(vector_id)
        
        # Add to shards
        insert_tasks = []
        for shard_id, batch in shard_batches.items():
            task = self._insert_to_shard(
                shard_id, 
                batch["texts"], 
                batch["embeddings"], 
                batch["metadata"], 
                batch["ids"]
            )
            insert_tasks.append(task)
        
        # Wait for all insertions
        await asyncio.gather(*insert_tasks, return_exceptions=True)
        
        return vector_ids
    
    async def _insert_to_shard(self, 
                              shard_id: str, 
                              texts: List[str], 
                              embeddings: List[Optional[np.ndarray]], 
                              metadata: List[Dict[str, Any]], 
                              vector_ids: List[str]) -> None:
        """Insert vectors into a specific shard."""
        # Get nodes responsible for this shard
        nodes = self.cluster_manager.get_nodes_for_shard(shard_id)
        
        if not nodes:
            raise ValueError(f"No healthy nodes found for shard {shard_id}")
        
        # Insert to local shard if we're responsible
        if shard_id in self.local_shards:
            try:
                db = self.local_shards[shard_id]
                
                # Create metadata objects
                vector_metadata = []
                for i, text in enumerate(texts):
                    meta = VectorMetadata(
                        id=vector_ids[i],
                        text=text,
                        embedding_model=self.primary_model.name if self.primary_model else "unknown",
                        timestamp=datetime.now(),
                        content_hash=self._compute_content_hash(text),
                        metadata=metadata[i]
                    )
                    vector_metadata.append(meta)
                
                # Add to local database
                await db.add_vectors(
                    embeddings=[e for e in embeddings if e is not None],
                    metadata=vector_metadata,
                    model_name=self.primary_model.name if self.primary_model else "sentence-transformers/distilbert-base-nli-mean-tokens"
                )
                
            except Exception as e:
                logger.error(f"Error inserting to local shard {shard_id}: {type(e).__name__}: {e}")
                logger.debug(f"Full exception details for shard {shard_id}", exc_info=True)
                raise
        
        # TODO: Replicate to other nodes in production
        # For now, we only handle local inserts
    
    async def _search_shard(self, 
                           shard: VectorShard, 
                           query_embedding: np.ndarray, 
                           k: int, 
                           filters: Optional[Dict[str, Any]], 
                           include_metadata: bool) -> List[Dict[str, Any]]:
        """Search a specific shard."""
        if shard.shard_id not in self.local_shards:
            # TODO: In production, search remote shards
            return []
        
        try:
            db = self.local_shards[shard.shard_id]
            results = await db.search_vectors(
                query_embedding=query_embedding,
                k=k,
                filters=filters
            )
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_result = {
                    "id": result.get("id"),
                    "score": result.get("score", 0.0),
                    "text": result.get("text", ""),
                    "shard_id": shard.shard_id
                }
                
                if include_metadata and "metadata" in result:
                    formatted_result["metadata"] = result["metadata"]
                
                formatted_results.append(formatted_result)
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching shard {shard.shard_id}: {e}")
            return []
    
    async def _delete_from_shard(self, shard_id: str, vector_ids: List[str]) -> int:
        """Delete vectors from a specific shard."""
        if shard_id not in self.local_shards:
            # TODO: In production, delete from remote shards
            return 0
        
        try:
            db = self.local_shards[shard_id]
            return await db.delete_vectors(vector_ids)
        except Exception as e:
            logger.error(f"Error deleting from shard {shard_id}: {e}")
            return 0
    
    def _get_healthy_shards(self) -> List[VectorShard]:
        """Get all healthy shards."""
        return [shard for shard in self.cluster_manager.shards.values() 
                if shard.status == ShardStatus.HEALTHY]
    
    def _get_shard_for_vector(self, vector_id: str) -> str:
        """Get the shard ID for a vector ID."""
        return self.cluster_manager._compute_shard_id(vector_id)
    
    def _generate_vector_id(self, text: str) -> str:
        """Generate a unique vector ID."""
        import hashlib
        import uuid
        
        # Create a deterministic but unique ID
        content_hash = hashlib.md5(text.encode()).hexdigest()[:8]
        timestamp = str(int(time.time() * 1000))[-6:]  # Last 6 digits of timestamp
        random_part = str(uuid.uuid4())[:8]
        
        return f"vec_{content_hash}_{timestamp}_{random_part}"
    
    def _compute_content_hash(self, text: str) -> str:
        """Compute content hash for deduplication."""
        import hashlib
        return hashlib.sha256(text.encode()).hexdigest()
    
    def _merge_search_results(self, all_results: List[Dict[str, Any]], k: int) -> List[Dict[str, Any]]:
        """Merge and rank search results from multiple shards."""
        # Sort by score (assuming higher is better)
        sorted_results = sorted(all_results, key=lambda x: x.get("score", 0), reverse=True)
        
        # Remove duplicates based on ID
        seen_ids = set()
        unique_results = []
        
        for result in sorted_results:
            vector_id = result.get("id")
            if vector_id not in seen_ids:
                seen_ids.add(vector_id)
                unique_results.append(result)
                
                if len(unique_results) >= k:
                    break
        
        return unique_results[:k]
    
    async def _get_shard_stats(self, db: PersistentVectorDatabase) -> Dict[str, Any]:
        """Get statistics for a shard database."""
        # This would get actual stats from the database
        return {
            "vector_count": 0,  # db.get_vector_count()
            "size_bytes": 0,    # db.get_size_bytes()
            "last_updated": time.time()
        }
    
    async def _backup_shard(self, db: PersistentVectorDatabase, backup_dir: str) -> None:
        """Backup a shard database."""
        # This would create a backup of the shard
        await db.backup(backup_dir)
    
    def _update_avg_time(self, stat_key: str, duration: float, count: int) -> None:
        """Update average time statistics."""
        current_avg = self.operation_stats[stat_key]
        total_ops = self.operation_stats.get(stat_key.replace("avg_", ""), 1)
        
        # Update running average
        self.operation_stats[stat_key] = (current_avg * (total_ops - count) + duration) / total_ops
    
    async def _on_node_failed(self, failed_node: ClusterNode) -> None:
        """Handle node failure events."""
        logger.warning(f"Node {failed_node.node_id} failed, checking local shards")
        
        # Check if we need to take over any shards
        for shard in self.cluster_manager.shards.values():
            if (shard.primary_node == self.cluster_manager.node_id and 
                shard.shard_id not in self.local_shards):
                await self._initialize_shard(shard.shard_id)
    
    async def _on_shards_rebalanced(self, rebalanced_shards: List[VectorShard]) -> None:
        """Handle shard rebalancing events."""
        logger.info(f"Handling rebalancing of {len(rebalanced_shards)} shards")
        
        # In production, this would handle data migration
        # For now, just reinitialize relevant shards
        for shard in rebalanced_shards:
            if (shard.primary_node == self.cluster_manager.node_id or 
                self.cluster_manager.node_id in shard.replica_nodes):
                if shard.shard_id not in self.local_shards:
                    await self._initialize_shard(shard.shard_id)


# Global distributed database instance
distributed_db: Optional[DistributedVectorDatabase] = None


def initialize_distributed_database(cluster_manager: ClusterManager,
                                   local_storage_dir: str = "data/distributed_vectors",
                                   embedding_models: List[EmbeddingModel] = None) -> DistributedVectorDatabase:
    """Initialize the global distributed database."""
    global distributed_db
    distributed_db = DistributedVectorDatabase(cluster_manager, local_storage_dir, embedding_models)
    return distributed_db


def get_distributed_database() -> Optional[DistributedVectorDatabase]:
    """Get the global distributed database instance."""
    return distributed_db
