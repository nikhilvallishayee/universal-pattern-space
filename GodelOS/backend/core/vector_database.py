"""
Production Vector Database for GödelOS

This module implements a production-grade vector database with persistent storage,
backup/recovery capabilities, and multiple embedding model support.

Based on stable FAISS + sentence-transformers patterns for Intel macOS.

.. deprecated::
    The in-memory FAISS-based ``PersistentVectorDatabase`` in this module
    overlaps with the new ChromaDB-backed knowledge store
    (``godelOS.core_kr.knowledge_store.chroma_store.ChromaKnowledgeStore``).
    ChromaDB handles both vector embeddings and structured metadata in a
    single persistence layer.  New code should prefer
    ``ChromaKnowledgeStore`` for unified knowledge + vector retrieval.
    This module is retained for backward compatibility; it will be
    removed in a future release once all consumers have migrated.
"""

import os
import json
import pickle
import logging
import hashlib
import asyncio
import time
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor
import threading

# 1) Cap threads early to avoid OpenMP conflicts (CRITICAL for macOS stability)
for var in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ.setdefault(var, "1")

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.neighbors import NearestNeighbors
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import atexit
import signal
import sys
import threading

# Import FAISS *after* other heavy libs on macOS (prevents conflicts)
import faiss
faiss.omp_set_num_threads(1)  # Force single-threaded FAISS

logger = logging.getLogger(__name__)


@dataclass
class VectorMetadata:
    """Metadata for vector embeddings."""
    id: str
    text: str
    embedding_model: str
    timestamp: datetime
    content_hash: str
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VectorMetadata':
        """Create from dictionary."""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class EmbeddingModel:
    """Configuration for embedding models."""
    name: str
    model_path: str
    dimension: int
    is_primary: bool = False
    is_available: bool = True
    fallback_order: int = 1


def check_model_cache_status(cache_dir: Path) -> Dict[str, bool]:
    """Check which models are available in cache."""
    models_to_check = [
        "sentence-transformers_all-MiniLM-L6-v2",
        "sentence-transformers_all-mpnet-base-v2", 
        "sentence-transformers_distilbert-base-nli-mean-tokens"
    ]
    
    status = {}
    for model in models_to_check:
        model_path = cache_dir / model
        status[model] = model_path.exists()
    
    return status


def pre_cache_models(cache_dir: Path, models: List[str] = None) -> None:
    """Pre-download and cache SentenceTransformer models."""
    if models is None:
        models = [
            "sentence-transformers/all-MiniLM-L6-v2",
            "sentence-transformers/all-mpnet-base-v2",
            "sentence-transformers/distilbert-base-nli-mean-tokens"
        ]
    
    # Set cache directory
    os.environ['SENTENCE_TRANSFORMERS_HOME'] = str(cache_dir)
    
    for model in models:
        try:
            logger.info(f"Pre-caching model: {model}")
            _ = SentenceTransformer(model, cache_folder=str(cache_dir))
            logger.info(f"Successfully cached model: {model}")
        except Exception as e:
            logger.warning(f"Failed to cache model {model}: {e}")


class PersistentVectorDatabase:
    """
    Production-grade vector database with persistent storage.
    
    Features:
    - Persistent FAISS index storage
    - Multiple embedding model support
    - Automatic backup and recovery
    - Batch processing capabilities
    - Metadata management
    - Thread-safe operations
    """
    
    def __init__(self, 
                 storage_dir: str = "data/vector_db",
                 backup_dir: str = "data/vector_db/backups",
                 auto_backup_interval: int = 3600,  # 1 hour
                 max_backups: int = 10):
        """
        Initialize the vector database.
        
        Args:
            storage_dir: Directory for persistent storage
            backup_dir: Directory for backups
            auto_backup_interval: Automatic backup interval in seconds
            max_backups: Maximum number of backups to keep
        """
        self.storage_dir = Path(storage_dir)
        self.backup_dir = Path(backup_dir)
        self.auto_backup_interval = auto_backup_interval
        self.max_backups = max_backups
        
        # Ensure directories exist
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up model cache directory for SentenceTransformers
        self.model_cache_dir = self.storage_dir / "model_cache"
        self.model_cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure SentenceTransformers to use our cache directory
        os.environ['SENTENCE_TRANSFORMERS_HOME'] = str(self.model_cache_dir)
        logger.info(f"SentenceTransformers cache directory: {self.model_cache_dir}")
        
        # Thread safety - disable ThreadPoolExecutor to prevent segfaults
        self.lock = threading.RLock()
        # self.executor = ThreadPoolExecutor(max_workers=4)  # Disabled due to FAISS threading issues
        
        # Initialize embedding models
        self.embedding_models: Dict[str, EmbeddingModel] = {}
        self.model_instances: Dict[str, SentenceTransformer] = {}
        self.primary_model: Optional[str] = None
        
        # Vector storage
        self.indices: Dict[str, faiss.Index] = {}
        self.metadata: Dict[str, Dict[str, VectorMetadata]] = {}  # model_name -> id -> metadata
        self.id_maps: Dict[str, List[str]] = {}  # model_name -> list of ids
        
        # Initialize models and load data
        self._initialize_embedding_models()
        self._load_from_disk()
        
        # Start auto-backup if enabled
        if auto_backup_interval > 0:
            self._start_auto_backup()
        
        # Register cleanup handlers for FAISS segfault prevention
        atexit.register(self._cleanup_faiss)
        
        # Only set signal handlers in main thread
        try:
            if threading.current_thread() is threading.main_thread():
                signal.signal(signal.SIGTERM, self._signal_cleanup)
                signal.signal(signal.SIGINT, self._signal_cleanup)
                logger.debug("Signal handlers registered in main thread")
            else:
                logger.debug("Skipping signal handler registration in worker thread")
        except Exception as e:
            logger.warning(f"Could not set signal handlers: {e}")
        
        logger.info(f"PersistentVectorDatabase initialized with storage at {self.storage_dir}")
    
    def _initialize_embedding_models(self):
        """Initialize default embedding models with optimized single-model approach."""
        # OPTIMIZED: Use single primary model to reduce memory overhead
        # The distilbert-base-nli-mean-tokens model provides best balance of performance/efficiency
        models_config = [
            EmbeddingModel(
                name="sentence-transformers/distilbert-base-nli-mean-tokens",
                model_path="distilbert-base-nli-mean-tokens",
                dimension=768,
                is_primary=True,
                fallback_order=1
            ),
            # FALLBACK: Keep one lightweight model for emergency fallback only
            EmbeddingModel(
                name="sentence-transformers/all-MiniLM-L6-v2",
                model_path="all-MiniLM-L6-v2",
                dimension=384,
                fallback_order=2,
                is_available=False  # Only load if primary fails
            )
        ]
        
        # Test model availability and load with optimized loading strategy
        network_available = False
        primary_loaded = False
        
        for model_config in models_config:
            # Skip fallback models unless primary fails
            if not model_config.is_primary and primary_loaded:
                logger.info(f"Skipping fallback model {model_config.name} - primary model loaded")
                continue
                
            try:
                # Check if model exists in cache first
                model_cache_path = self.model_cache_dir / model_config.model_path.replace("/", "_")
                cached_model_exists = model_cache_path.exists()
                
                if cached_model_exists:
                    logger.info(f"Found cached model for {model_config.name} at {model_cache_path}")
                else:
                    logger.info(f"Model {model_config.name} not in cache, will attempt download")
                
                # Test network connectivity only if model not cached
                if not cached_model_exists and not network_available:
                    try:
                        import requests
                        response = requests.get("https://huggingface.co", timeout=5)
                        network_available = True
                        logger.info("Network connectivity confirmed for model downloads")
                    except Exception as net_e:
                        logger.warning(f"No network connectivity for model downloads: {net_e}")
                        if model_config.is_primary:
                            logger.warning("Primary model unavailable, will try fallback")
                            continue
                
                # Try to load the model (might work from cache even without network)
                logger.info(f"Loading SentenceTransformer model: {model_config.model_path}")
                model_instance = SentenceTransformer(
                    model_config.model_path,
                    cache_folder=str(self.model_cache_dir)
                )
                self.model_instances[model_config.name] = model_instance
                self.embedding_models[model_config.name] = model_config
                
                if model_config.is_primary:
                    self.primary_model = model_config.name
                    primary_loaded = True
                
                logger.info(f"✅ Successfully loaded embedding model: {model_config.name}")
                
                # If primary loaded successfully, break to avoid loading fallbacks
                if model_config.is_primary:
                    break
                
            except Exception as e:
                logger.warning(f"Could not load embedding model {model_config.name}: {e}")
                model_config.is_available = False
                self.embedding_models[model_config.name] = model_config
        
        # Fallback to first available model if primary failed
        if not self.primary_model:
            for name, config in self.embedding_models.items():
                if config.is_available:
                    self.primary_model = name
                    config.is_primary = True
                    break
        
        if not self.primary_model:
            logger.error("No embedding models available! Vector operations will be limited.")
    
    def _load_from_disk(self):
        """Load existing vector indices and metadata from disk."""
        with self.lock:
            for model_name in self.embedding_models.keys():
                self._load_model_data(model_name)
    
    def _load_model_data(self, model_name: str):
        """Load data for a specific model."""
        model_dir = self.storage_dir / model_name.replace("/", "_")
        
        # Load FAISS index
        index_path = model_dir / "index.faiss"
        if index_path.exists():
            try:
                self.indices[model_name] = faiss.read_index(str(index_path))
                logger.info(f"Loaded FAISS index for {model_name}: {self.indices[model_name].ntotal} vectors")
            except Exception as e:
                logger.error(f"Failed to load FAISS index for {model_name}: {e}")
                # Initialize empty index with stable IndexHNSWFlat (robust on CPU)
                dimension = self.embedding_models[model_name].dimension
                index = faiss.IndexHNSWFlat(dimension, 32)  # M=32 connections
                index.hnsw.efSearch = 64  # Search parameter
                self.indices[model_name] = index
        else:
            # Initialize empty index with stable IndexHNSWFlat (robust on CPU)
            dimension = self.embedding_models[model_name].dimension
            index = faiss.IndexHNSWFlat(dimension, 32)  # M=32 connections
            index.hnsw.efSearch = 64  # Search parameter
            self.indices[model_name] = index
        
        # Load metadata
        metadata_path = model_dir / "metadata.json"
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r') as f:
                    metadata_data = json.load(f)
                self.metadata[model_name] = {
                    id_: VectorMetadata.from_dict(data) 
                    for id_, data in metadata_data.items()
                }
                logger.info(f"Loaded metadata for {model_name}: {len(self.metadata[model_name])} items")
            except Exception as e:
                logger.error(f"Failed to load metadata for {model_name}: {e}")
                self.metadata[model_name] = {}
        else:
            self.metadata[model_name] = {}
        
        # Load ID mapping
        id_map_path = model_dir / "id_map.json"
        if id_map_path.exists():
            try:
                with open(id_map_path, 'r') as f:
                    self.id_maps[model_name] = json.load(f)
                logger.info(f"Loaded ID map for {model_name}: {len(self.id_maps[model_name])} IDs")
            except Exception as e:
                logger.error(f"Failed to load ID map for {model_name}: {e}")
                self.id_maps[model_name] = []
        else:
            self.id_maps[model_name] = []
    
    def _save_to_disk(self, model_name: str):
        """Save vector data for a specific model to disk."""
        model_dir = self.storage_dir / model_name.replace("/", "_")
        model_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Save FAISS index
            index_path = model_dir / "index.faiss"
            faiss.write_index(self.indices[model_name], str(index_path))
            
            # Save metadata
            metadata_path = model_dir / "metadata.json"
            metadata_data = {}
            for id_, meta in self.metadata[model_name].items():
                if isinstance(meta, VectorMetadata):
                    metadata_data[id_] = meta.to_dict()
                else:
                    # Already a dictionary
                    metadata_data[id_] = meta
            with open(metadata_path, 'w') as f:
                json.dump(metadata_data, f, indent=2)
            
            # Save ID mapping
            id_map_path = model_dir / "id_map.json"
            with open(id_map_path, 'w') as f:
                json.dump(self.id_maps[model_name], f, indent=2)
            
            logger.info(f"Saved vector data for {model_name}")
            
        except Exception as e:
            logger.error(f"Failed to save vector data for {model_name}: {e}")
            raise
    
    def safe_cleanup(self):
        """Safe cleanup of FAISS resources with proper threading"""
        try:
            if hasattr(self, 'indices'):
                for model_name, index in self.indices.items():
                    if index is not None:
                        try:
                            # Serialize/deserialize for safe cleanup
                            serialized = faiss.serialize_index(index)
                            del serialized
                        except Exception as e:
                            logger.warning(f"Error during index cleanup for {model_name}: {e}")
                        finally:
                            index = None
                self.indices.clear()
            
            if hasattr(self, 'embedding_models'):
                self.embedding_models.clear()
                
            # Force garbage collection
            import gc
            gc.collect()
            
        except Exception as e:
            logger.warning(f"Error during safe cleanup: {e}")
    
    def __del__(self):
        """Destructor with safe cleanup"""
        try:
            self.safe_cleanup()
        except:
            pass  # Suppress errors during destruction

    async def close(self):
        """Async close method for proper resource cleanup"""
        self.safe_cleanup()
        await asyncio.sleep(0.1)  # Allow cleanup to complete
    
    def add_items(self, 
                  items: List[Tuple[str, str]], 
                  model_name: Optional[str] = None,
                  metadata: Optional[List[Dict[str, Any]]] = None,
                  batch_size: int = 100) -> Dict[str, Any]:
        """
        Add items to the vector database with batch processing.
        
        Args:
            items: List of (id, text) tuples
            model_name: Embedding model to use (defaults to primary)
            metadata: Optional metadata for each item
            batch_size: Number of items to process in each batch
            
        Returns:
            Dictionary with results and statistics
        """
        if not items:
            return {"success": False, "message": "No items provided"}
        
        model_name = model_name or self.primary_model
        if not model_name or model_name not in self.model_instances:
            return {"success": False, "message": f"Model {model_name} not available"}
        
        with self.lock:
            model_instance = self.model_instances[model_name]
            results = {
                "success": True,
                "model_used": model_name,
                "items_processed": 0,
                "items_added": 0,
                "items_updated": 0,
                "items_skipped": 0,
                "processing_time": 0
            }
            
            start_time = datetime.now()
            
            # Process in batches
            for i in range(0, len(items), batch_size):
                batch_items = items[i:i+batch_size]
                batch_metadata = metadata[i:i+batch_size] if metadata else [{}] * len(batch_items)
                
                try:
                    self._process_batch(model_name, model_instance, batch_items, batch_metadata, results)
                except Exception as e:
                    logger.error(f"Error processing batch {i//batch_size + 1}: {e}")
                    continue
            
            # Save to disk
            try:
                self._save_to_disk(model_name)
                results["persisted"] = True
            except Exception as e:
                logger.error(f"Failed to persist data: {e}")
                results["persisted"] = False
            
            results["processing_time"] = (datetime.now() - start_time).total_seconds()
            logger.info(f"Batch processing complete: {results}")
            
            return results
    
    async def add_vectors(self, 
                         embeddings: List[np.ndarray], 
                         metadata: Optional[List[Dict[str, Any]]] = None,
                         model_name: Optional[str] = None) -> List[str]:
        """
        Add pre-computed embeddings to the vector database.
        
        Args:
            embeddings: Pre-computed embedding vectors
            metadata: Metadata for each vector
            model_name: Model name to use (defaults to primary)
            
        Returns:
            List of vector IDs that were added
        """
        
        if not embeddings:
            return []
            
        # Use primary model if not specified
        if model_name is None:
            model_name = self.get_primary_model_name()
            if not model_name:
                raise ValueError("No embedding models available")
        
        if model_name not in self.indices:
            raise ValueError(f"Model {model_name} not found in database")
        
        # Prepare metadata
        if metadata is None:
            metadata = [{}] * len(embeddings)
        elif len(metadata) != len(embeddings):
            raise ValueError("Metadata length must match embeddings length")
        
        try:
            # Convert embeddings to numpy array
            embeddings_array = np.array(embeddings, dtype=np.float32)
            
            # Generate IDs for the vectors
            vector_ids = []
            for i in range(len(embeddings)):
                # Handle both VectorMetadata objects and dictionary metadata
                meta_item = metadata[i]
                if isinstance(meta_item, VectorMetadata):
                    # Use the ID from VectorMetadata object
                    vector_id = meta_item.id
                elif isinstance(meta_item, dict) and 'content_hash' in meta_item:
                    vector_id = meta_item['content_hash']
                else:
                    vector_id = f"vec_{int(time.time() * 1000000)}_{i}"
                vector_ids.append(vector_id)
            
            # Add to FAISS index
            self.indices[model_name].add(embeddings_array)
            
            # Update metadata and ID mapping
            start_idx = len(self.id_maps[model_name])
            for i, (vector_id, meta_item) in enumerate(zip(vector_ids, metadata)):
                idx = start_idx + i
                self.id_maps[model_name].append(vector_id)
                
                # Store metadata - convert VectorMetadata to dict if needed
                if model_name not in self.metadata:
                    self.metadata[model_name] = {}
                
                if isinstance(meta_item, VectorMetadata):
                    # Convert VectorMetadata to dictionary
                    self.metadata[model_name][vector_id] = meta_item.to_dict()
                else:
                    # Already a dictionary
                    self.metadata[model_name][vector_id] = meta_item
            
            # Save to disk
            self._save_to_disk(model_name)
            
            logger.info(f"Added {len(embeddings)} vectors to {model_name}")
            return vector_ids
            
        except Exception as e:
            logger.error(f"Failed to add embeddings to FAISS index for {model_name}: {type(e).__name__}: {e}")
            logger.debug(f"Full exception details for model {model_name}", exc_info=True)
            raise
    
    def _process_batch(self, 
                       model_name: str,
                       model_instance: SentenceTransformer,
                       batch_items: List[Tuple[str, str]],
                       batch_metadata: List[Dict[str, Any]],
                       results: Dict[str, Any]):
        """Process a single batch of items."""
        ids, texts = zip(*batch_items)
        
        # Generate embeddings for the batch
        embeddings = model_instance.encode(texts, convert_to_tensor=False, show_progress_bar=False)
        
        new_embeddings = []
        new_ids = []
        
        for i, (item_id, text) in enumerate(batch_items):
            results["items_processed"] += 1
            
            # Check if item already exists
            if item_id in self.metadata[model_name]:
                # Check if content changed
                content_hash = hashlib.md5(text.encode()).hexdigest()
                existing_meta = self.metadata[model_name][item_id]
                
                if existing_meta.content_hash == content_hash:
                    results["items_skipped"] += 1
                    continue
                else:
                    # Update existing item
                    # Remove old embedding (complex operation, for now we'll add new)
                    results["items_updated"] += 1
            else:
                results["items_added"] += 1
            
            # Prepare metadata
            content_hash = hashlib.md5(text.encode()).hexdigest()
            vector_metadata = VectorMetadata(
                id=item_id,
                text=text,
                embedding_model=model_name,
                timestamp=datetime.now(),
                content_hash=content_hash,
                metadata=batch_metadata[i]
            )
            
            # Store metadata
            self.metadata[model_name][item_id] = vector_metadata
            
            # Prepare for FAISS addition
            new_embeddings.append(embeddings[i])
            new_ids.append(item_id)
        
        # Add new embeddings to FAISS index
        if new_embeddings:
            try:
                embeddings_array = np.array(new_embeddings).astype('float32')
                
                # Validate embedding dimensions
                expected_dim = self.embedding_models[model_name].dimension
                if embeddings_array.shape[1] != expected_dim:
                    raise ValueError(f"Embedding dimension mismatch: expected {expected_dim}, got {embeddings_array.shape[1]}")
                
                # Ensure embeddings are contiguous and properly formatted
                if not embeddings_array.flags['C_CONTIGUOUS']:
                    embeddings_array = np.ascontiguousarray(embeddings_array)
                
                # Thread-safe FAISS operations with explicit locking
                with self.lock:
                    # Add to FAISS index with error handling
                    self.indices[model_name].add(embeddings_array)
                    self.id_maps[model_name].extend(new_ids)
                
                logger.debug(f"Successfully added {len(new_embeddings)} embeddings to {model_name} index")
                
            except Exception as e:
                logger.error(f"Failed to add embeddings to FAISS index for {model_name}: {e}")
                # Rollback metadata for failed embeddings
                for new_id in new_ids:
                    if new_id in self.metadata[model_name]:
                        del self.metadata[model_name][new_id]
                raise
    
    def search(self, 
               query_text: str, 
               k: int = 5,
               model_name: Optional[str] = None,
               similarity_threshold: float = 0.0) -> List[Dict[str, Any]]:
        """
        Search for similar items in the vector database.
        
        Args:
            query_text: Text to search for
            k: Number of results to return
            model_name: Model to use for search (defaults to primary)
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of search results with metadata
        """
        model_name = model_name or self.primary_model
        if not model_name or model_name not in self.model_instances:
            logger.error(f"Model {model_name} not available for search")
            return []
        
        with self.lock:
            if model_name not in self.indices or self.indices[model_name].ntotal == 0:
                return []
            
            model_instance = self.model_instances[model_name]
            
            # Generate query embedding
            query_embedding = model_instance.encode([query_text], convert_to_tensor=False)
            
            # Search in FAISS index
            distances, indices = self.indices[model_name].search(
                query_embedding.astype('float32'), 
                min(k, self.indices[model_name].ntotal)
            )
            
            results = []
            for i in range(len(indices[0])):
                idx = indices[0][i]
                distance = distances[0][i]
                
                # Convert distance to similarity score (lower distance = higher similarity)
                similarity = 1 / (1 + distance)
                
                if similarity < similarity_threshold:
                    continue
                
                if idx < len(self.id_maps[model_name]):
                    item_id = self.id_maps[model_name][idx]
                    metadata = self.metadata[model_name].get(item_id)
                    
                    result = {
                        "id": item_id,
                        "text": metadata.text if metadata else "",
                        "similarity_score": float(similarity),
                        "distance": float(distance),
                        "model_used": model_name,
                        "metadata": metadata.metadata if metadata else {}
                    }
                    results.append(result)
            
            logger.info(f"Search for '{query_text[:50]}...' returned {len(results)} results")
            return results
    
    def backup(self, backup_name: Optional[str] = None) -> str:
        """
        Create a backup of the vector database.
        
        Args:
            backup_name: Name for the backup (defaults to timestamp)
            
        Returns:
            Path to the backup
        """
        if not backup_name:
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(parents=True, exist_ok=True)
        
        with self.lock:
            try:
                # Copy entire storage directory
                import shutil
                shutil.copytree(self.storage_dir, backup_path / "storage", dirs_exist_ok=True)
                
                # Create backup metadata
                backup_info = {
                    "timestamp": datetime.now().isoformat(),
                    "models": list(self.embedding_models.keys()),
                    "total_vectors": sum(idx.ntotal for idx in self.indices.values()),
                    "backup_name": backup_name
                }
                
                with open(backup_path / "backup_info.json", 'w') as f:
                    json.dump(backup_info, f, indent=2)
                
                logger.info(f"Backup created: {backup_path}")
                
                # Clean up old backups
                self._cleanup_old_backups()
                
                return str(backup_path)
                
            except Exception as e:
                logger.error(f"Backup failed: {e}")
                # Clean up partial backup
                if backup_path.exists():
                    import shutil
                    shutil.rmtree(backup_path)
                raise
    
    def restore(self, backup_path: str) -> bool:
        """
        Restore the vector database from a backup.
        
        Args:
            backup_path: Path to the backup to restore
            
        Returns:
            True if restore was successful
        """
        backup_path = Path(backup_path)
        if not backup_path.exists():
            logger.error(f"Backup path does not exist: {backup_path}")
            return False
        
        storage_backup = backup_path / "storage"
        if not storage_backup.exists():
            logger.error(f"Invalid backup structure: {backup_path}")
            return False
        
        with self.lock:
            try:
                # Clear current data
                self.indices.clear()
                self.metadata.clear()
                self.id_maps.clear()
                
                # Restore storage directory
                import shutil
                if self.storage_dir.exists():
                    shutil.rmtree(self.storage_dir)
                shutil.copytree(storage_backup, self.storage_dir)
                
                # Reload data
                self._load_from_disk()
                
                logger.info(f"Successfully restored from backup: {backup_path}")
                return True
                
            except Exception as e:
                logger.error(f"Restore failed: {e}")
                return False
    
    def _cleanup_old_backups(self):
        """Remove old backups to maintain max_backups limit."""
        try:
            backups = [d for d in self.backup_dir.iterdir() if d.is_dir() and d.name.startswith("backup_")]
            backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            for backup in backups[self.max_backups:]:
                import shutil
                shutil.rmtree(backup)
                logger.info(f"Removed old backup: {backup.name}")
                
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {e}")
    
    def _start_auto_backup(self):
        """Start automatic backup process."""
        def auto_backup_worker():
            while True:
                try:
                    import time
                    time.sleep(self.auto_backup_interval)
                    self.backup()
                except Exception as e:
                    logger.error(f"Auto-backup failed: {e}")
        
        import threading
        backup_thread = threading.Thread(target=auto_backup_worker, daemon=True)
        backup_thread.start()
        logger.info(f"Auto-backup started with {self.auto_backup_interval}s interval")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        with self.lock:
            stats = {
                "models": {},
                "total_vectors": 0,
                "storage_size_mb": self._get_storage_size(),
                "primary_model": self.primary_model
            }
            
            for model_name in self.embedding_models.keys():
                model_stats = {
                    "available": model_name in self.model_instances,
                    "vectors": self.indices.get(model_name, faiss.IndexFlatL2(384)).ntotal,
                    "metadata_items": len(self.metadata.get(model_name, {})),
                    "dimension": self.embedding_models[model_name].dimension
                }
                stats["models"][model_name] = model_stats
                stats["total_vectors"] += model_stats["vectors"]
            
            return stats
    
    def clear_all(self) -> bool:
        """
        Clear all vectors and metadata from the database.
        
        Returns:
            True if clearing was successful
        """
        with self.lock:
            try:
                logger.info("Clearing all vectors from database...")
                
                # Clear all FAISS indices
                for model_name in list(self.indices.keys()):
                    try:
                        index = self.indices[model_name]
                        if hasattr(index, 'reset'):
                            index.reset()
                        # Recreate empty index with same dimension
                        dimension = self.embedding_models[model_name].dimension
                        self.indices[model_name] = faiss.IndexFlatL2(dimension)
                        logger.debug(f"Cleared index for model {model_name}")
                    except Exception as e:
                        logger.error(f"Error clearing index for {model_name}: {e}")
                
                # Clear all metadata
                self.metadata.clear()
                
                # Clear all ID maps
                self.id_maps.clear()
                
                # Save cleared state to disk
                for model_name in self.embedding_models.keys():
                    try:
                        self._save_to_disk(model_name)
                    except Exception as e:
                        logger.error(f"Error saving cleared state for {model_name}: {e}")
                
                logger.info("Successfully cleared all vectors from database")
                return True
                
            except Exception as e:
                logger.error(f"Error clearing database: {e}")
                return False
    
    def _get_storage_size(self) -> float:
        """Get storage directory size in MB."""
        try:
            total_size = 0
            for path in self.storage_dir.rglob('*'):
                if path.is_file():
                    total_size += path.stat().st_size
            return round(total_size / (1024 * 1024), 2)
        except Exception:
            return 0.0
    
    async def initialize(self):
        """Initialize the vector database asynchronously."""
        # The actual initialization happens in __init__, this is for compatibility
        logger.info("Vector database initialization complete")
        return True
    
    async def add_embedding_model(self, model_or_name, **kwargs):
        """Add a new embedding model to the database."""
        try:
            # Handle both EmbeddingModel objects and string names
            if isinstance(model_or_name, EmbeddingModel):
                # Extract attributes from EmbeddingModel object
                model_config = EmbeddingModel(
                    name=model_or_name.name,
                    model_path=model_or_name.model_path,
                    dimension=model_or_name.dimension,
                    is_primary=model_or_name.is_primary,
                    fallback_order=model_or_name.fallback_order
                )
                model_name = model_config.name
            else:
                model_name = model_or_name
                # Create model configuration from string name
                model_config = EmbeddingModel(
                    name=model_name,
                    model_path=kwargs.get('model_path', model_name),
                    dimension=kwargs.get('dimension', 384),
                    is_primary=kwargs.get('is_primary', False),
                    fallback_order=kwargs.get('fallback_order', 999)
                )
            
            # Skip if model already exists
            if model_name in self.embedding_models:
                logger.warning(f"Embedding model {model_name} already exists")
                return
            
            # Test model availability
            try:
                # Ensure we're using the string path, not the object
                model_path = str(model_config.model_path)
                model_instance = SentenceTransformer(model_path)
                
                # Get actual dimension from the model
                actual_dimension = model_instance.get_sentence_embedding_dimension()
                
                # Update the model config with correct dimension
                model_config = EmbeddingModel(
                    name=model_config.name,
                    model_path=model_config.model_path,
                    dimension=actual_dimension,  # Use actual dimension from model
                    is_primary=model_config.is_primary,
                    fallback_order=model_config.fallback_order
                )
                
                self.model_instances[model_name] = model_instance
                model_config.is_available = True
                logger.info(f"Successfully loaded embedding model: {model_name}")
            except Exception as e:
                logger.warning(f"Failed to load embedding model {model_name}: {e}")
                model_config.is_available = False
            
            # Add to models
            self.embedding_models[model_name] = model_config
            
            # Initialize storage structures if model is available
            if model_config.is_available:
                self.indices[model_name] = faiss.IndexFlatIP(model_config.dimension)
                self.metadata[model_name] = {}
                self.id_maps[model_name] = []
                
                # Set as primary if none exists
                if not self.primary_model:
                    self.primary_model = model_name
                    model_config.is_primary = True
            
        except Exception as e:
            logger.error(f"Error adding embedding model {getattr(model_or_name, 'name', model_or_name)}: {e}")
    
    def close(self):
        """Clean shutdown of the vector database."""
        with self.lock:
            logger.info("Shutting down vector database...")
            
            # Save all data
            for model_name in self.embedding_models.keys():
                if model_name in self.indices:
                    try:
                        self._save_to_disk(model_name)
                    except Exception as e:
                        logger.error(f"Error saving {model_name} on shutdown: {e}")
            
            # Clean up FAISS resources
            self._cleanup_faiss()
            
            # Shutdown executor (disabled due to threading issues)
            # self.executor.shutdown(wait=True)
            
            logger.info("Vector database shutdown complete")
    
    def _cleanup_faiss(self):
        """Clean up FAISS resources to prevent segfault on shutdown."""
        try:
            logger.debug("Cleaning up FAISS resources...")
            
            # Disable FAISS threading before cleanup
            faiss.omp_set_num_threads(1)
            
            # Clear all indices explicitly with aggressive cleanup
            for model_name in list(self.indices.keys()):
                try:
                    index = self.indices[model_name]
                    if hasattr(index, 'reset'):
                        index.reset()
                    if hasattr(index, 'ntotal'):
                        logger.debug(f"Cleaning index {model_name} with {index.ntotal} vectors")
                    
                    # Force immediate deletion
                    del self.indices[model_name]
                    
                except Exception as e:
                    logger.warning(f"Error cleaning up FAISS index for {model_name}: {e}")
            
            # Clear the indices dictionary
            self.indices.clear()
            
            # Force Python garbage collection multiple times
            import gc
            for _ in range(3):
                gc.collect()
            
            # Try to force FAISS internal cleanup
            try:
                # Create and immediately destroy a dummy index to flush FAISS state
                dummy = faiss.IndexFlatIP(128)
                dummy.reset()
                del dummy
                gc.collect()
            except:
                pass
            
            logger.debug("FAISS cleanup completed successfully")
            
        except Exception as e:
            logger.warning(f"Error during FAISS cleanup: {e}")
    
    def get_primary_model_name(self) -> Optional[str]:
        """Get the name of the primary embedding model."""
        for model_name, model in self.embedding_models.items():
            if model.is_primary:
                return model_name
        
        # If no primary model found, return the first available model
        if self.embedding_models:
            return next(iter(self.embedding_models.keys()))
        
        return None
    
    def __enter__(self):
        """Context manager entry."""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with guaranteed cleanup."""
        self.close()
        return False
    
    def _signal_cleanup(self, signum, frame):
        """Handle cleanup for signal termination."""
        logger.info(f"Received signal {signum}, cleaning up...")
        self._cleanup_faiss()
        self.close()
        sys.exit(0)
