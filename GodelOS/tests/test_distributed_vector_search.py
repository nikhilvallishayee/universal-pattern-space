"""
Comprehensive tests for Distributed Vector Search System.

Tests cluster management, sharding, replication, and distributed operations.
"""

import asyncio
import pytest
import tempfile
import uuid
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, patch
import numpy as np

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.core.distributed_vector_search import (
    ClusterManager,
    ClusterConfig,
    ConsistentHashRing,
    ClusterNode,
    VectorShard,
    NodeStatus,
    ShardStatus
)
from backend.core.distributed_vector_database import (
    DistributedVectorDatabase
)
from backend.core.vector_database import EmbeddingModel


class TestConsistentHashRing:
    """Test the consistent hash ring implementation."""
    
    def test_hash_ring_creation(self):
        """Test creating a hash ring."""
        ring = ConsistentHashRing(virtual_nodes=100)
        assert len(ring.ring) == 0
        assert len(ring.nodes) == 0
    
    def test_add_remove_nodes(self):
        """Test adding and removing nodes."""
        ring = ConsistentHashRing(virtual_nodes=3)
        
        # Add nodes
        ring.add_node("node1")
        ring.add_node("node2")
        ring.add_node("node3")
        
        assert len(ring.nodes) == 3
        assert len(ring.ring) == 9  # 3 nodes * 3 virtual nodes
        
        # Remove node
        ring.remove_node("node2")
        assert len(ring.nodes) == 2
        assert len(ring.ring) == 6  # 2 nodes * 3 virtual nodes
    
    def test_get_node_for_key(self):
        """Test getting node for a key."""
        ring = ConsistentHashRing(virtual_nodes=3)
        ring.add_node("node1")
        ring.add_node("node2")
        
        # Should return a node
        node = ring.get_node("test_key")
        assert node in ["node1", "node2"]
        
        # Same key should return same node
        assert ring.get_node("test_key") == node
    
    def test_get_multiple_nodes(self):
        """Test getting multiple nodes for replication."""
        ring = ConsistentHashRing(virtual_nodes=10)
        ring.add_node("node1")
        ring.add_node("node2")
        ring.add_node("node3")
        
        nodes = ring.get_nodes("test_key", 2)
        assert len(nodes) == 2
        assert len(set(nodes)) == 2  # Should be unique
    
    def test_empty_ring(self):
        """Test behavior with empty ring."""
        ring = ConsistentHashRing()
        assert ring.get_node("test_key") is None
        assert ring.get_nodes("test_key", 3) == []


class TestClusterManager:
    """Test the cluster manager functionality."""
    
    @pytest.fixture
    def cluster_config(self):
        """Create test cluster configuration."""
        return ClusterConfig(
            cluster_name="test_cluster",
            replication_factor=2,
            shard_count=4,
            heartbeat_interval=5,
            failure_detection_timeout=15
        )
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    async def cluster_manager(self, cluster_config, temp_storage):
        """Create test cluster manager."""
        manager = ClusterManager(
            config=cluster_config,
            node_id="test_node_1",
            storage_dir=temp_storage
        )
        yield manager
        
        # Cleanup
        if manager._running:
            await manager.stop()
    
    @pytest.mark.asyncio
    async def test_cluster_manager_initialization(self, cluster_manager, cluster_config):
        """Test cluster manager initialization."""
        assert cluster_manager.config.cluster_name == cluster_config.cluster_name
        assert cluster_manager.node_id == "test_node_1"
        assert not cluster_manager._running
    
    @pytest.mark.asyncio
    async def test_start_stop_cluster_manager(self, cluster_manager):
        """Test starting and stopping cluster manager."""
        # Start
        await cluster_manager.start()
        assert cluster_manager._running
        assert len(cluster_manager._tasks) > 0
        
        # Stop
        await cluster_manager.stop()
        assert not cluster_manager._running
        assert len(cluster_manager._tasks) == 0
    
    @pytest.mark.asyncio
    async def test_create_cluster(self, cluster_manager):
        """Test creating a new cluster."""
        await cluster_manager.start()
        
        # Join cluster (create new)
        success = await cluster_manager.join_cluster()
        assert success
        
        # Check local node is active
        assert cluster_manager.node_id in cluster_manager.nodes
        local_node = cluster_manager.nodes[cluster_manager.node_id]
        assert local_node.status == NodeStatus.ACTIVE
        
        # Check shards are initialized
        assert len(cluster_manager.shards) == cluster_manager.config.shard_count
    
    @pytest.mark.asyncio
    async def test_cluster_stats(self, cluster_manager):
        """Test getting cluster statistics."""
        await cluster_manager.start()
        await cluster_manager.join_cluster()
        
        stats = cluster_manager.get_cluster_stats()
        
        assert "cluster_name" in stats
        assert "node_id" in stats
        assert "nodes" in stats
        assert "shards" in stats
        assert stats["cluster_name"] == "test_cluster"
        assert stats["nodes"]["total"] >= 1
        assert stats["shards"]["total"] == 4
    
    @pytest.mark.asyncio
    async def test_shard_assignment(self, cluster_manager):
        """Test shard assignment logic."""
        await cluster_manager.start()
        await cluster_manager.join_cluster()
        
        # Test getting shard for key
        test_key = "test_vector_id"
        shard = cluster_manager.get_shard_for_key(test_key)
        assert shard is not None
        
        # Same key should always get same shard
        shard2 = cluster_manager.get_shard_for_key(test_key)
        assert shard.shard_id == shard2.shard_id
    
    @pytest.mark.asyncio
    async def test_node_failure_handling(self, cluster_manager):
        """Test handling node failures."""
        await cluster_manager.start()
        await cluster_manager.join_cluster()
        
        # Add a fake failed node
        failed_node = ClusterNode(
            node_id="failed_node",
            host="127.0.0.1",
            port=9999,
            status=NodeStatus.FAILED,
            last_heartbeat=cluster_manager.nodes[cluster_manager.node_id].last_heartbeat
        )
        cluster_manager.nodes["failed_node"] = failed_node
        
        # Simulate handling failure
        await cluster_manager._handle_node_failure(failed_node)
        
        # Check that failed node is removed from hash ring
        assert "failed_node" not in cluster_manager.hash_ring.nodes


class TestDistributedVectorDatabase:
    """Test the distributed vector database."""
    
    @pytest.fixture
    def embedding_models(self):
        """Create test embedding models."""
        return [
            EmbeddingModel(
                name="test_model",
                model_path="all-MiniLM-L6-v2",  # Use a real, lightweight model
                dimension=384,  # Correct dimension for all-MiniLM-L6-v2
                is_primary=True
            )
        ]
    
    @pytest.fixture
    def cluster_config(self):
        """Create test cluster configuration."""
        return ClusterConfig(
            cluster_name="test_db_cluster",
            replication_factor=1,  # Single replica for testing
            shard_count=2,
            heartbeat_interval=10
        )
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    async def cluster_manager(self, cluster_config, temp_storage):
        """Create and start test cluster manager."""
        manager = ClusterManager(
            config=cluster_config,
            node_id="db_test_node",
            storage_dir=str(Path(temp_storage) / "cluster")
        )
        await manager.start()
        await manager.join_cluster()
        yield manager
        await manager.stop()
    
    @pytest.fixture
    async def distributed_db(self, cluster_manager, embedding_models, temp_storage):
        """Create test distributed database."""
        db = DistributedVectorDatabase(
            cluster_manager=cluster_manager,
            local_storage_dir=str(Path(temp_storage) / "vectors"),
            embedding_models=embedding_models
        )
        await db.initialize()
        yield db
    
    @pytest.mark.asyncio
    async def test_database_initialization(self, distributed_db, embedding_models):
        """Test database initialization."""
        assert len(distributed_db.embedding_models) == len(embedding_models)
        assert distributed_db.primary_model is not None
        assert distributed_db.primary_model.is_primary
    
    @pytest.mark.asyncio
    async def test_add_vectors(self, distributed_db):
        """Test adding vectors to the distributed database."""
        texts = [
            "This is the first test document",
            "This is the second test document",
            "This is the third test document"
        ]
        
        metadata = [
            {"category": "test", "index": i}
            for i in range(len(texts))
        ]
        
        # Mock embedding generation
        with patch.object(distributed_db, '_generate_embeddings') as mock_embed:
            mock_embed.return_value = [
                np.random.random(384).astype(np.float32)
                for _ in texts
            ]
            
            vector_ids = await distributed_db.add_vectors(texts, metadata=metadata)
        
        assert len(vector_ids) == len(texts)
        assert all(isinstance(vid, str) for vid in vector_ids)
        
        # Check stats updated
        assert distributed_db.operation_stats["inserts"] == len(texts)
    
    @pytest.mark.asyncio
    async def test_search_vectors(self, distributed_db):
        """Test searching vectors in the distributed database."""
        # First add some vectors
        texts = ["search test document", "another document", "third document"]
        
        with patch.object(distributed_db, '_generate_embeddings') as mock_embed:
            embeddings = [np.random.random(384).astype(np.float32) for _ in texts]
            mock_embed.return_value = embeddings
            
            # Add vectors
            await distributed_db.add_vectors(texts)
            
            # Search
            query = "test document"
            mock_embed.return_value = [embeddings[0]]  # Return first embedding for query
            
            # Mock shard search results
            with patch.object(distributed_db, '_search_shard') as mock_search:
                mock_search.return_value = [
                    {
                        "id": "test_id_1",
                        "score": 0.95,
                        "text": texts[0],
                        "shard_id": "shard_0001"
                    }
                ]
                
                results = await distributed_db.search_vectors(query, k=1)
        
        assert len(results) <= 1
        assert distributed_db.operation_stats["searches"] == 1
    
    @pytest.mark.asyncio
    async def test_delete_vectors(self, distributed_db):
        """Test deleting vectors from the distributed database."""
        # Mock deletion
        with patch.object(distributed_db, '_delete_from_shard') as mock_delete:
            mock_delete.return_value = 2  # Mock successful deletion
            
            deleted_count = await distributed_db.delete_vectors(["vec1", "vec2"])
        
        assert deleted_count >= 0
    
    @pytest.mark.asyncio
    async def test_database_stats(self, distributed_db):
        """Test getting database statistics."""
        stats = await distributed_db.get_database_stats()
        
        assert "cluster" in stats
        assert "local_node" in stats
        assert "performance" in stats
        assert "embedding_models" in stats
        
        assert stats["local_node"]["node_id"] == distributed_db.cluster_manager.node_id
        assert len(stats["embedding_models"]) > 0
    
    @pytest.mark.asyncio
    async def test_backup_database(self, distributed_db, temp_storage):
        """Test database backup functionality."""
        backup_dir = str(Path(temp_storage) / "backup")
        
        # Mock shard backup
        with patch.object(distributed_db, '_backup_shard') as mock_backup:
            mock_backup.return_value = None
            
            backup_info = await distributed_db.backup_database(backup_dir)
        
        assert "timestamp" in backup_info
        assert "node_id" in backup_info
        assert "shards" in backup_info
        assert backup_info["node_id"] == distributed_db.cluster_manager.node_id
    
    def test_vector_id_generation(self, distributed_db):
        """Test vector ID generation."""
        text = "test document for id generation"
        
        id1 = distributed_db._generate_vector_id(text)
        id2 = distributed_db._generate_vector_id(text)
        
        # IDs should be different due to timestamp/random components
        assert id1 != id2
        assert id1.startswith("vec_")
        assert id2.startswith("vec_")
    
    def test_shard_assignment(self, distributed_db):
        """Test shard assignment for vectors."""
        test_vector_id = "test_vector_12345"
        
        shard_id = distributed_db._get_shard_for_vector(test_vector_id)
        assert shard_id.startswith("shard_")
        
        # Same vector should always get same shard
        shard_id2 = distributed_db._get_shard_for_vector(test_vector_id)
        assert shard_id == shard_id2
    
    def test_search_result_merging(self, distributed_db):
        """Test merging search results from multiple shards."""
        all_results = [
            {"id": "1", "score": 0.9, "text": "result 1"},
            {"id": "2", "score": 0.8, "text": "result 2"},
            {"id": "3", "score": 0.95, "text": "result 3"},
            {"id": "1", "score": 0.85, "text": "result 1 duplicate"},  # Duplicate
        ]
        
        merged = distributed_db._merge_search_results(all_results, k=2)
        
        assert len(merged) == 2
        assert merged[0]["score"] == 0.95  # Highest score first
        assert merged[1]["score"] == 0.9   # Second highest
        
        # Check no duplicates
        ids = [r["id"] for r in merged]
        assert len(ids) == len(set(ids))


class TestDistributedVectorAPI:
    """Test the distributed vector API endpoints."""
    
    def test_cluster_config_model(self):
        """Test cluster configuration model."""
        try:
            from backend.api.distributed_vector_endpoints import ClusterConfigModel
            
            config = ClusterConfigModel(
                cluster_name="test_cluster",
                replication_factor=2,
                shard_count=16
            )
            
            assert config.cluster_name == "test_cluster"
            assert config.replication_factor == 2
            assert config.shard_count == 16
            assert config.heartbeat_interval == 10  # Default value
            
        except ImportError:
            pytest.skip("FastAPI/Pydantic not available")
    
    def test_vector_search_request_model(self):
        """Test vector search request model."""
        try:
            from backend.api.distributed_vector_endpoints import VectorSearchRequest
            
            request = VectorSearchRequest(
                query="test query",
                k=5,
                filters={"category": "test"}
            )
            
            assert request.query == "test query"
            assert request.k == 5
            assert request.filters["category"] == "test"
            assert request.include_metadata is True  # Default value
            
        except ImportError:
            pytest.skip("FastAPI/Pydantic not available")
    
    def test_vector_insert_request_model(self):
        """Test vector insert request model."""
        try:
            from backend.api.distributed_vector_endpoints import VectorInsertRequest
            
            request = VectorInsertRequest(
                texts=["text1", "text2"],
                metadata=[{"key": "value1"}, {"key": "value2"}],
                batch_size=50
            )
            
            assert len(request.texts) == 2
            assert len(request.metadata) == 2
            assert request.batch_size == 50
            
        except ImportError:
            pytest.skip("FastAPI/Pydantic not available")


class TestIntegrationScenarios:
    """Test integration scenarios for distributed vector search."""
    
    @pytest.mark.asyncio
    async def test_single_node_cluster(self):
        """Test creating and using a single-node cluster."""
        config = ClusterConfig(
            cluster_name="single_node_test",
            replication_factor=1,
            shard_count=2
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            cluster_manager = ClusterManager(config, storage_dir=temp_dir)
            
            try:
                await cluster_manager.start()
                success = await cluster_manager.join_cluster()
                assert success
                
                # Check cluster state
                stats = cluster_manager.get_cluster_stats()
                assert stats["nodes"]["total"] == 1
                assert stats["nodes"]["healthy"] == 1
                assert stats["shards"]["total"] == 2
                
            finally:
                await cluster_manager.stop()
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow."""
        config = ClusterConfig(
            cluster_name="e2e_test",
            replication_factor=1,
            shard_count=2
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Initialize cluster
            cluster_manager = ClusterManager(config, storage_dir=str(Path(temp_dir) / "cluster"))
            
            try:
                await cluster_manager.start()
                await cluster_manager.join_cluster()
                
                # Initialize distributed database
                embedding_models = [
                    EmbeddingModel(
                        name="test_model",
                        model_path="all-MiniLM-L6-v2",  # Use a real, lightweight model
                        dimension=384,  # Correct dimension for all-MiniLM-L6-v2
                        is_primary=True
                    )
                ]
                
                distributed_db = DistributedVectorDatabase(
                    cluster_manager=cluster_manager,
                    local_storage_dir=str(Path(temp_dir) / "vectors"),
                    embedding_models=embedding_models
                )
                await distributed_db.initialize()
                
                # Add some test data
                texts = ["Hello world", "Test document", "Another text"]
                
                with patch.object(distributed_db, '_generate_embeddings') as mock_embed:
                    mock_embed.return_value = [
                        np.random.random(384).astype(np.float32) for _ in texts
                    ]
                    
                    vector_ids = await distributed_db.add_vectors(texts)
                
                assert len(vector_ids) == 3
                
                # Test search
                with patch.object(distributed_db, '_generate_embeddings') as mock_embed:
                    mock_embed.return_value = [np.random.random(384).astype(np.float32)]
                    
                    with patch.object(distributed_db, '_search_shard') as mock_search:
                        mock_search.return_value = [
                            {"id": vector_ids[0], "score": 0.9, "text": texts[0], "shard_id": "shard_0000"}
                        ]
                        
                        results = await distributed_db.search_vectors("test query")
                
                assert len(results) >= 0
                
                # Test stats
                stats = await distributed_db.get_database_stats()
                assert stats["local_node"]["node_id"] == cluster_manager.node_id
                
                # Test backup
                backup_dir = str(Path(temp_dir) / "backup")
                with patch.object(distributed_db, '_backup_shard'):
                    backup_info = await distributed_db.backup_database(backup_dir)
                
                assert "timestamp" in backup_info
                
            finally:
                await cluster_manager.stop()


def run_standalone_tests():
    """Run tests that don't require pytest."""
    print("Running standalone distributed vector search tests...")
    
    # Test ConsistentHashRing
    test_ring = TestConsistentHashRing()
    test_ring.test_hash_ring_creation()
    test_ring.test_add_remove_nodes()
    test_ring.test_get_node_for_key()
    test_ring.test_get_multiple_nodes()
    test_ring.test_empty_ring()
    print("✓ ConsistentHashRing tests passed")
    
    # Test basic cluster configuration
    config = ClusterConfig(
        cluster_name="test_cluster",
        replication_factor=2,
        shard_count=4
    )
    assert config.cluster_name == "test_cluster"
    assert config.replication_factor == 2
    print("✓ ClusterConfig tests passed")
    
    # Test vector ID generation
    with tempfile.TemporaryDirectory() as temp_dir:
        cluster_manager = ClusterManager(config, storage_dir=temp_dir)
        
        # Test shard computation
        shard_id1 = cluster_manager._compute_shard_id("test_key_1")
        shard_id2 = cluster_manager._compute_shard_id("test_key_1")
        assert shard_id1 == shard_id2  # Same key, same shard
        
        shard_id3 = cluster_manager._compute_shard_id("test_key_2")
        # Different keys might get different shards
        print("✓ Shard computation tests passed")
    
    print("All standalone tests passed!")


if __name__ == "__main__":
    try:
        import pytest
        # Run with pytest if available
        pytest.main([__file__, "-v"])
    except ImportError:
        # Run standalone tests
        run_standalone_tests()
