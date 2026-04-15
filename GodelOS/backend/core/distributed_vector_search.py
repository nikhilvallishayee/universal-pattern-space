"""
Distributed Vector Search System for GödelOS

This module implements a distributed vector search architecture with:
- Cluster management and node discovery
- Shard distribution and routing
- Data replication strategies
- Horizontal scaling capabilities
- Load balancing and failover
"""

import asyncio
import hashlib
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Any, Set, Callable, Tuple
from enum import Enum
from pathlib import Path
import threading
from concurrent.futures import ThreadPoolExecutor
import socket

import numpy as np

logger = logging.getLogger(__name__)


class NodeStatus(Enum):
    """Node status in the cluster."""
    JOINING = "joining"
    ACTIVE = "active"
    LEAVING = "leaving"
    FAILED = "failed"
    RECOVERING = "recovering"


class ShardStatus(Enum):
    """Shard status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    REBALANCING = "rebalancing"


@dataclass
class ClusterNode:
    """Represents a node in the distributed cluster."""
    node_id: str
    host: str
    port: int
    status: NodeStatus
    last_heartbeat: datetime
    shard_count: int = 0
    load_factor: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['status'] = self.status.value
        data['last_heartbeat'] = self.last_heartbeat.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ClusterNode':
        """Create from dictionary."""
        data['status'] = NodeStatus(data['status'])
        data['last_heartbeat'] = datetime.fromisoformat(data['last_heartbeat'])
        return cls(**data)
    
    @property
    def is_healthy(self) -> bool:
        """Check if node is healthy based on last heartbeat."""
        return (self.status == NodeStatus.ACTIVE and 
                datetime.now() - self.last_heartbeat < timedelta(seconds=30))


@dataclass
class VectorShard:
    """Represents a shard of vector data."""
    shard_id: str
    hash_range: Tuple[int, int]  # (start, end) hash range
    primary_node: str
    replica_nodes: List[str]
    status: ShardStatus
    document_count: int = 0
    size_bytes: int = 0
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['status'] = self.status.value
        data['last_updated'] = self.last_updated.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VectorShard':
        """Create from dictionary."""
        data['status'] = ShardStatus(data['status'])
        data['last_updated'] = datetime.fromisoformat(data['last_updated'])
        return cls(**data)


@dataclass
class ClusterConfig:
    """Configuration for the distributed cluster."""
    cluster_name: str
    replication_factor: int = 2
    shard_count: int = 32
    heartbeat_interval: int = 10  # seconds
    failure_detection_timeout: int = 30  # seconds
    max_load_factor: float = 0.8
    rebalance_threshold: float = 0.2
    enable_auto_scaling: bool = True
    min_nodes: int = 1
    max_nodes: int = 100


class ConsistentHashRing:
    """Consistent hash ring for shard distribution."""
    
    def __init__(self, virtual_nodes: int = 150):
        """Initialize hash ring."""
        self.virtual_nodes = virtual_nodes
        self.ring: Dict[int, str] = {}
        self.nodes: Set[str] = set()
    
    def add_node(self, node_id: str) -> None:
        """Add a node to the hash ring."""
        if node_id in self.nodes:
            return
        
        self.nodes.add(node_id)
        for i in range(self.virtual_nodes):
            key = self._hash(f"{node_id}:{i}")
            self.ring[key] = node_id
    
    def remove_node(self, node_id: str) -> None:
        """Remove a node from the hash ring."""
        if node_id not in self.nodes:
            return
        
        self.nodes.remove(node_id)
        keys_to_remove = [k for k, v in self.ring.items() if v == node_id]
        for key in keys_to_remove:
            del self.ring[key]
    
    def get_node(self, key: str) -> Optional[str]:
        """Get the node responsible for a key."""
        if not self.ring:
            return None
        
        hash_key = self._hash(key)
        
        # Find the first node clockwise from the hash
        for ring_key in sorted(self.ring.keys()):
            if ring_key >= hash_key:
                return self.ring[ring_key]
        
        # Wrap around to the first node
        return self.ring[min(self.ring.keys())]
    
    def get_nodes(self, key: str, count: int) -> List[str]:
        """Get multiple nodes for replication."""
        if not self.ring or count <= 0:
            return []
        
        hash_key = self._hash(key)
        nodes = []
        seen = set()
        
        sorted_keys = sorted(self.ring.keys())
        start_idx = 0
        
        # Find starting position
        for i, ring_key in enumerate(sorted_keys):
            if ring_key >= hash_key:
                start_idx = i
                break
        
        # Collect unique nodes
        for i in range(len(sorted_keys)):
            idx = (start_idx + i) % len(sorted_keys)
            node = self.ring[sorted_keys[idx]]
            if node not in seen:
                nodes.append(node)
                seen.add(node)
                if len(nodes) >= count:
                    break
        
        return nodes
    
    def _hash(self, key: str) -> int:
        """Compute hash for a key."""
        return int(hashlib.md5(key.encode()).hexdigest(), 16)


class ClusterManager:
    """Manages the distributed vector search cluster."""
    
    def __init__(self, 
                 config: ClusterConfig,
                 node_id: Optional[str] = None,
                 storage_dir: str = "data/cluster"):
        """Initialize cluster manager."""
        self.config = config
        self.node_id = node_id or str(uuid.uuid4())
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Cluster state
        self.nodes: Dict[str, ClusterNode] = {}
        self.shards: Dict[str, VectorShard] = {}
        self.hash_ring = ConsistentHashRing()
        
        # Synchronization
        self.lock = threading.RLock()
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Background tasks
        self._running = False
        self._tasks: List[asyncio.Task] = []
        
        # Event callbacks
        self.node_joined_callbacks: List[Callable[[ClusterNode], None]] = []
        self.node_failed_callbacks: List[Callable[[ClusterNode], None]] = []
        self.shard_rebalanced_callbacks: List[Callable[[List[VectorShard]], None]] = []
        
        logger.info(f"Cluster manager initialized for node {self.node_id}")
    
    async def start(self) -> None:
        """Start the cluster manager."""
        if self._running:
            return
        
        self._running = True
        
        # Initialize local node
        await self._initialize_local_node()
        
        # Start background tasks
        self._tasks = [
            asyncio.create_task(self._heartbeat_loop()),
            asyncio.create_task(self._failure_detection_loop()),
            asyncio.create_task(self._rebalancing_loop()),
            asyncio.create_task(self._cluster_monitoring_loop())
        ]
        
        logger.info(f"Cluster manager started for node {self.node_id}")
    
    async def stop(self) -> None:
        """Stop the cluster manager."""
        if not self._running:
            return
        
        self._running = False
        
        # Cancel background tasks
        for task in self._tasks:
            task.cancel()
        
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        
        # Leave cluster gracefully
        await self._leave_cluster()
        
        logger.info(f"Cluster manager stopped for node {self.node_id}")
    
    async def join_cluster(self, seed_nodes: List[Tuple[str, int]] = None) -> bool:
        """Join an existing cluster or create a new one."""
        try:
            if seed_nodes:
                # Try to join existing cluster
                for host, port in seed_nodes:
                    success = await self._attempt_join(host, port)
                    if success:
                        logger.info(f"Successfully joined cluster via {host}:{port}")
                        return True
                
                logger.warning("Failed to join cluster via seed nodes, creating new cluster")
            
            # Create new cluster
            await self._create_cluster()
            logger.info(f"Created new cluster '{self.config.cluster_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to join cluster: {e}")
            return False
    
    def get_shard_for_key(self, key: str) -> Optional[VectorShard]:
        """Get the shard responsible for a key."""
        shard_id = self._compute_shard_id(key)
        return self.shards.get(shard_id)
    
    def get_nodes_for_shard(self, shard_id: str) -> List[ClusterNode]:
        """Get all nodes (primary + replicas) for a shard."""
        shard = self.shards.get(shard_id)
        if not shard:
            return []
        
        nodes = []
        
        # Add primary node
        if shard.primary_node in self.nodes:
            nodes.append(self.nodes[shard.primary_node])
        
        # Add replica nodes
        for replica_id in shard.replica_nodes:
            if replica_id in self.nodes:
                nodes.append(self.nodes[replica_id])
        
        return [node for node in nodes if node.is_healthy]
    
    def get_cluster_stats(self) -> Dict[str, Any]:
        """Get cluster statistics."""
        with self.lock:
            healthy_nodes = sum(1 for node in self.nodes.values() if node.is_healthy)
            total_shards = len(self.shards)
            healthy_shards = sum(1 for shard in self.shards.values() 
                               if shard.status == ShardStatus.HEALTHY)
            
            return {
                "cluster_name": self.config.cluster_name,
                "node_id": self.node_id,
                "nodes": {
                    "total": len(self.nodes),
                    "healthy": healthy_nodes,
                    "failed": len(self.nodes) - healthy_nodes
                },
                "shards": {
                    "total": total_shards,
                    "healthy": healthy_shards,
                    "degraded": sum(1 for s in self.shards.values() 
                                  if s.status == ShardStatus.DEGRADED),
                    "unavailable": sum(1 for s in self.shards.values() 
                                     if s.status == ShardStatus.UNAVAILABLE)
                },
                "replication_factor": self.config.replication_factor,
                "auto_scaling_enabled": self.config.enable_auto_scaling
            }
    
    async def _initialize_local_node(self) -> None:
        """Initialize the local node."""
        host = self._get_local_ip()
        port = self._get_available_port()
        
        local_node = ClusterNode(
            node_id=self.node_id,
            host=host,
            port=port,
            status=NodeStatus.JOINING,
            last_heartbeat=datetime.now()
        )
        
        with self.lock:
            self.nodes[self.node_id] = local_node
    
    async def _attempt_join(self, host: str, port: int) -> bool:
        """Attempt to join cluster via a seed node."""
        try:
            # In a real implementation, this would make HTTP/gRPC calls
            # to the seed node to request cluster membership
            # For now, we'll simulate this
            
            # Mock cluster discovery response
            cluster_info = {
                "nodes": [],  # Would be populated by seed node
                "shards": []  # Would be populated by seed node
            }
            
            # Update local cluster state
            await self._update_cluster_state(cluster_info)
            
            # Mark local node as active
            with self.lock:
                if self.node_id in self.nodes:
                    self.nodes[self.node_id].status = NodeStatus.ACTIVE
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to join via {host}:{port}: {e}")
            return False
    
    async def _create_cluster(self) -> None:
        """Create a new cluster."""
        with self.lock:
            # Mark local node as active
            if self.node_id in self.nodes:
                self.nodes[self.node_id].status = NodeStatus.ACTIVE
            
            # Add node to hash ring
            self.hash_ring.add_node(self.node_id)
            
            # Initialize shards
            await self._initialize_shards()
    
    async def _initialize_shards(self) -> None:
        """Initialize shards for the cluster."""
        hash_range_size = (2**32) // self.config.shard_count
        
        for i in range(self.config.shard_count):
            start_hash = i * hash_range_size
            end_hash = (i + 1) * hash_range_size - 1
            
            shard_id = f"shard_{i:04d}"
            
            # Assign primary and replica nodes
            available_nodes = [n for n in self.nodes.values() if n.is_healthy]
            if not available_nodes:
                continue
            
            primary_node = available_nodes[0].node_id
            replica_nodes = []
            
            # Add replicas if we have enough nodes
            for j in range(1, min(self.config.replication_factor, len(available_nodes))):
                replica_nodes.append(available_nodes[j].node_id)
            
            shard = VectorShard(
                shard_id=shard_id,
                hash_range=(start_hash, end_hash),
                primary_node=primary_node,
                replica_nodes=replica_nodes,
                status=ShardStatus.HEALTHY
            )
            
            self.shards[shard_id] = shard
        
        logger.info(f"Initialized {len(self.shards)} shards")
    
    async def _heartbeat_loop(self) -> None:
        """Background task for sending heartbeats."""
        while self._running:
            try:
                await self._send_heartbeat()
                await asyncio.sleep(self.config.heartbeat_interval)
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
                await asyncio.sleep(5)
    
    async def _failure_detection_loop(self) -> None:
        """Background task for detecting failed nodes."""
        while self._running:
            try:
                await self._detect_failures()
                await asyncio.sleep(self.config.failure_detection_timeout // 3)
            except Exception as e:
                logger.error(f"Error in failure detection loop: {e}")
                await asyncio.sleep(5)
    
    async def _rebalancing_loop(self) -> None:
        """Background task for shard rebalancing."""
        while self._running:
            try:
                await self._check_rebalancing()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in rebalancing loop: {e}")
                await asyncio.sleep(10)
    
    async def _cluster_monitoring_loop(self) -> None:
        """Background task for cluster monitoring."""
        while self._running:
            try:
                await self._monitor_cluster_health()
                await asyncio.sleep(30)  # Monitor every 30 seconds
            except Exception as e:
                logger.error(f"Error in cluster monitoring loop: {e}")
                await asyncio.sleep(5)
    
    async def _send_heartbeat(self) -> None:
        """Send heartbeat to other nodes."""
        with self.lock:
            if self.node_id in self.nodes:
                self.nodes[self.node_id].last_heartbeat = datetime.now()
        
        # In a real implementation, broadcast heartbeat to other nodes
        logger.debug(f"Heartbeat sent from node {self.node_id}")
    
    async def _detect_failures(self) -> None:
        """Detect and handle failed nodes."""
        current_time = datetime.now()
        failed_nodes = []
        
        with self.lock:
            for node in self.nodes.values():
                if (node.status == NodeStatus.ACTIVE and 
                    current_time - node.last_heartbeat > timedelta(seconds=self.config.failure_detection_timeout)):
                    node.status = NodeStatus.FAILED
                    failed_nodes.append(node)
        
        # Handle failed nodes
        for node in failed_nodes:
            await self._handle_node_failure(node)
    
    async def _handle_node_failure(self, failed_node: ClusterNode) -> None:
        """Handle a failed node."""
        logger.warning(f"Node {failed_node.node_id} failed")
        
        # Remove from hash ring
        self.hash_ring.remove_node(failed_node.node_id)
        
        # Reassign shards
        affected_shards = []
        with self.lock:
            for shard in self.shards.values():
                if (shard.primary_node == failed_node.node_id or 
                    failed_node.node_id in shard.replica_nodes):
                    affected_shards.append(shard)
        
        for shard in affected_shards:
            await self._reassign_shard(shard, failed_node.node_id)
        
        # Trigger callbacks
        for callback in self.node_failed_callbacks:
            try:
                callback(failed_node)
            except Exception as e:
                logger.error(f"Error in node failed callback: {e}")
    
    async def _reassign_shard(self, shard: VectorShard, failed_node_id: str) -> None:
        """Reassign a shard after node failure."""
        available_nodes = [n.node_id for n in self.nodes.values() 
                          if n.is_healthy and n.node_id != failed_node_id]
        
        if not available_nodes:
            shard.status = ShardStatus.UNAVAILABLE
            logger.error(f"No available nodes to reassign shard {shard.shard_id}")
            return
        
        # Reassign primary if needed
        if shard.primary_node == failed_node_id:
            if shard.replica_nodes:
                # Promote a replica to primary
                new_primary = shard.replica_nodes[0]
                shard.replica_nodes.remove(new_primary)
                shard.primary_node = new_primary
            else:
                # Assign new primary
                shard.primary_node = available_nodes[0]
                available_nodes.remove(available_nodes[0])
        
        # Remove failed node from replicas
        if failed_node_id in shard.replica_nodes:
            shard.replica_nodes.remove(failed_node_id)
        
        # Add new replicas if needed
        needed_replicas = self.config.replication_factor - 1 - len(shard.replica_nodes)
        for i in range(min(needed_replicas, len(available_nodes))):
            if available_nodes[i] != shard.primary_node:
                shard.replica_nodes.append(available_nodes[i])
        
        # Update shard status
        if len(shard.replica_nodes) + 1 >= self.config.replication_factor:
            shard.status = ShardStatus.HEALTHY
        else:
            shard.status = ShardStatus.DEGRADED
        
        logger.info(f"Reassigned shard {shard.shard_id}, new primary: {shard.primary_node}")
    
    async def _check_rebalancing(self) -> None:
        """Check if cluster needs rebalancing."""
        if len(self.nodes) < 2:
            return
        
        # Calculate load distribution
        node_loads = {}
        with self.lock:
            for node_id in self.nodes:
                node_loads[node_id] = sum(1 for shard in self.shards.values() 
                                        if shard.primary_node == node_id or node_id in shard.replica_nodes)
        
        if not node_loads:
            return
        
        avg_load = sum(node_loads.values()) / len(node_loads)
        max_load = max(node_loads.values())
        min_load = min(node_loads.values())
        
        # Check if rebalancing is needed
        if (max_load - min_load) / avg_load > self.config.rebalance_threshold:
            logger.info(f"Rebalancing needed: max_load={max_load}, min_load={min_load}, avg={avg_load}")
            await self._rebalance_cluster()
    
    async def _rebalance_cluster(self) -> None:
        """Rebalance the cluster."""
        logger.info("Starting cluster rebalancing")
        
        # This is a simplified rebalancing algorithm
        # In production, you'd want more sophisticated algorithms
        
        rebalanced_shards = []
        
        # For now, just log that rebalancing would happen
        # Real implementation would migrate data between nodes
        
        # Trigger callbacks
        for callback in self.shard_rebalanced_callbacks:
            try:
                callback(rebalanced_shards)
            except Exception as e:
                logger.error(f"Error in shard rebalanced callback: {e}")
        
        logger.info("Cluster rebalancing completed")
    
    async def _monitor_cluster_health(self) -> None:
        """Monitor overall cluster health."""
        stats = self.get_cluster_stats()
        
        # Log cluster health periodically
        if stats["nodes"]["total"] > 0:
            health_ratio = stats["nodes"]["healthy"] / stats["nodes"]["total"]
            shard_health_ratio = stats["shards"]["healthy"] / max(stats["shards"]["total"], 1)
            
            logger.debug(f"Cluster health: {health_ratio:.2%} nodes, {shard_health_ratio:.2%} shards")
            
            # Alert on poor health
            if health_ratio < 0.5 or shard_health_ratio < 0.5:
                logger.warning(f"Poor cluster health detected: {stats}")
    
    async def _update_cluster_state(self, cluster_info: Dict[str, Any]) -> None:
        """Update cluster state from external source."""
        # Update nodes
        for node_data in cluster_info.get("nodes", []):
            node = ClusterNode.from_dict(node_data)
            with self.lock:
                self.nodes[node.node_id] = node
                if node.is_healthy:
                    self.hash_ring.add_node(node.node_id)
        
        # Update shards
        for shard_data in cluster_info.get("shards", []):
            shard = VectorShard.from_dict(shard_data)
            with self.lock:
                self.shards[shard.shard_id] = shard
    
    async def _leave_cluster(self) -> None:
        """Leave the cluster gracefully."""
        with self.lock:
            if self.node_id in self.nodes:
                self.nodes[self.node_id].status = NodeStatus.LEAVING
        
        # In a real implementation, notify other nodes and migrate data
        logger.info(f"Node {self.node_id} leaving cluster")
    
    def _compute_shard_id(self, key: str) -> str:
        """Compute shard ID for a key."""
        hash_value = int(hashlib.md5(key.encode()).hexdigest(), 16)
        shard_index = hash_value % self.config.shard_count
        return f"shard_{shard_index:04d}"
    
    def _get_local_ip(self) -> str:
        """Get local IP address."""
        try:
            # Connect to a remote address to determine local IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception:
            return "127.0.0.1"
    
    def _get_available_port(self) -> int:
        """Get an available port."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            return s.getsockname()[1]


# Global cluster manager instance
cluster_manager: Optional[ClusterManager] = None


def initialize_cluster_manager(config: ClusterConfig, 
                              node_id: Optional[str] = None,
                              storage_dir: str = "data/cluster") -> ClusterManager:
    """Initialize the global cluster manager."""
    global cluster_manager
    cluster_manager = ClusterManager(config, node_id, storage_dir)
    return cluster_manager


def get_cluster_manager() -> Optional[ClusterManager]:
    """Get the global cluster manager instance."""
    return cluster_manager
