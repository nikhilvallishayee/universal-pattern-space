"""
Vector Database Integration Service

This service provides a compatibility layer between the old VectorStore interface
and the new PersistentVectorDatabase for seamless migration.

Enhancements:
- Retry/backoff for production DB operations (add_items, search)
- Telemetry hook for recoverable errors (emits structured info to WS)
"""

import logging
import time
from typing import List, Tuple, Optional, Dict, Any, Callable
from pathlib import Path

from .vector_database import PersistentVectorDatabase, EmbeddingModel

logger = logging.getLogger(__name__)

# Optional telemetry notifier (set by unified server)
_telemetry_notify: Optional[Callable[[Dict[str, Any]], None]] = None

def set_telemetry_notifier(notify: Optional[Callable[[Dict[str, Any]], None]]):
    global _telemetry_notify
    _telemetry_notify = notify


class VectorDatabaseService:
    """
    Service layer for vector database operations with migration support.
    
    This class provides backward compatibility with the existing VectorStore
    interface while using the new PersistentVectorDatabase underneath.
    """
    
    def __init__(self, 
                 storage_dir: str = "data/vector_db",
                 enable_migration: bool = True,
                 legacy_fallback: bool = True):
        """
        Initialize the vector database service.
        
        Args:
            storage_dir: Directory for vector database storage
            enable_migration: Whether to attempt migration from old VectorStore
            legacy_fallback: Whether to fall back to old VectorStore on errors
        """
        self.storage_dir = storage_dir
        self.enable_migration = enable_migration
        self.legacy_fallback = legacy_fallback
        
        # Initialize production database
        try:
            self.production_db = PersistentVectorDatabase(storage_dir=storage_dir)
            self.use_production = True
            logger.info("Production vector database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize production database: {e}")
            self.production_db = None
            self.use_production = False
        
        # Initialize legacy fallback if needed
        self.legacy_store = None
        if legacy_fallback and not self.use_production:
            try:
                from godelOS.semantic_search.vector_store import VectorStore
                self.legacy_store = VectorStore()
                logger.info("Legacy vector store initialized as fallback")
            except Exception as e:
                logger.error(f"Failed to initialize legacy fallback: {e}")
        
        # Perform migration if enabled
        if enable_migration and self.use_production:
            self._attempt_migration()

    # -----------------
    # Internal helpers
    # -----------------

    def _notify_recoverable_error(self, *, operation: str, attempt: int, max_attempts: int, message: str):
        try:
            if _telemetry_notify is not None:
                _telemetry_notify({
                    "type": "recoverable_error",
                    "service": "vector_db",
                    "operation": operation,
                    "attempt": attempt,
                    "max_attempts": max_attempts,
                    "message": message,
                    "timestamp": time.time(),
                })
        except Exception:
            # Never raise from telemetry
            pass

    def _with_retries(self, fn, *, retries: int = 2, delay: float = 0.4, backoff: float = 1.8, op_name: str = "vector_op"):
        attempt = 0
        current_delay = delay
        last_exc = None
        while attempt <= retries:
            try:
                return fn()
            except Exception as e:
                last_exc = e
                attempt += 1
                logger.warning(f"{op_name} failed (attempt {attempt}/{retries + 1}): {e}")
                if attempt <= retries:
                    self._notify_recoverable_error(operation=op_name, attempt=attempt, max_attempts=retries + 1, message=str(e))
                    try:
                        time.sleep(current_delay)
                    except Exception:
                        pass
                    current_delay *= backoff
        # Exhausted retries
        if last_exc is not None:
            raise last_exc
        return None
    
    def _attempt_migration(self):
        """Attempt to migrate data from legacy vector store."""
        try:
            # Look for existing legacy data
            legacy_data_path = Path("data/knowledge_base")  # Common location
            if legacy_data_path.exists():
                logger.info("Found potential legacy data, migration may be needed")
                # Migration logic would go here
                # For now, we'll just log that it's available
        except Exception as e:
            logger.error(f"Migration attempt failed: {e}")
    
    def add_items(self, items: List[Tuple[str, str]], **kwargs) -> bool:
        """
        Add items to the vector database.
        
        Args:
            items: List of (id, text) tuples
            **kwargs: Additional arguments (metadata, batch_size, etc.)
            
        Returns:
            True if successful
        """
        if self.use_production and self.production_db:
            try:
                def _op():
                    return self.production_db.add_items(items, **kwargs)
                result = self._with_retries(_op, op_name="vector_add_items")
                return bool(result.get("success", False)) if isinstance(result, dict) else bool(result)
            except Exception as e:
                logger.error(f"Production database add_items failed after retries: {e}")
                if not self.legacy_fallback:
                    raise
        
        # Fall back to legacy store
        if self.legacy_store:
            try:
                self.legacy_store.add_items(items)
                return True
            except Exception as e:
                logger.error(f"Legacy store add_items failed: {e}")
                
        return False
    
    def search(self, 
               query_text: str, 
               k: int = 5, 
               **kwargs) -> List[Tuple[str, float]]:
        """
        Search for similar items.
        
        Args:
            query_text: Text to search for
            k: Number of results to return
            **kwargs: Additional search parameters
            
        Returns:
            List of (id, similarity_score) tuples
        """
        if self.use_production and self.production_db:
            try:
                def _op():
                    return self.production_db.search(query_text, k=k, **kwargs)
                results = self._with_retries(_op, op_name="vector_search")
                # Convert to legacy format
                return [(r["id"], r.get("similarity_score", r.get("score", 0.0))) for r in (results or [])]
            except Exception as e:
                logger.error(f"Production database search failed after retries: {e}")
                if not self.legacy_fallback:
                    raise
        
        # Fall back to legacy store
        if self.legacy_store:
            try:
                return self.legacy_store.search(query_text, k=k)
            except Exception as e:
                logger.error(f"Legacy store search failed: {e}")
        
        return []
    
    def backup(self, backup_name: Optional[str] = None) -> bool:
        """
        Create a backup of the vector database.
        
        Args:
            backup_name: Optional name for the backup
            
        Returns:
            True if backup was successful
        """
        if self.use_production and self.production_db:
            try:
                backup_path = self.production_db.backup(backup_name)
                logger.info(f"Backup created at: {backup_path}")
                return True
            except Exception as e:
                logger.error(f"Backup failed: {e}")
        
        return False
    
    def restore(self, backup_path: str) -> bool:
        """
        Restore from a backup.
        
        Args:
            backup_path: Path to the backup
            
        Returns:
            True if restore was successful
        """
        if self.use_production and self.production_db:
            try:
                return self.production_db.restore(backup_path)
            except Exception as e:
                logger.error(f"Restore failed: {e}")
        
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        if self.use_production and self.production_db:
            try:
                return self.production_db.get_stats()
            except Exception as e:
                logger.error(f"Failed to get stats: {e}")
        
        # Basic stats for legacy store
        if self.legacy_store:
            return {
                "type": "legacy",
                "total_vectors": len(getattr(self.legacy_store, 'id_map', [])),
                "models": {"legacy": {"available": True}}
            }
        
        return {"type": "none", "total_vectors": 0, "models": {}}
    
    def optimize_indices(self) -> bool:
        """Optimize vector indices for better performance."""
        if self.use_production and self.production_db:
            try:
                # Future: implement index optimization
                logger.info("Index optimization not yet implemented")
                return True
            except Exception as e:
                logger.error(f"Index optimization failed: {e}")
        
        return False
    
    def clear_all(self) -> bool:
        """
        Clear all vectors and metadata from the database.
        
        Returns:
            True if clearing was successful
        """
        if self.use_production and self.production_db:
            try:
                return self.production_db.clear_all()
            except Exception as e:
                logger.error(f"Failed to clear database: {e}")
                return False
        
        # Clear legacy store if being used
        if self.legacy_store:
            try:
                # Reset legacy store
                self.legacy_store.id_map = []
                self.legacy_store.embeddings = []
                logger.info("Cleared legacy vector store")
                return True
            except Exception as e:
                logger.error(f"Failed to clear legacy store: {e}")
                return False
        
        logger.warning("No vector database available to clear")
        return False
    
    def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the vector database."""
        health = {
            "status": "unknown",
            "production_db": False,
            "legacy_fallback": False,
            "total_vectors": 0,
            "errors": [],
            "timestamp": time.time(),
        }
        
        # Check production database
        if self.production_db:
            try:
                stats = self.production_db.get_stats()
                health["production_db"] = True
                health["total_vectors"] = stats.get("total_vectors", 0)
                health["status"] = "healthy"
            except Exception as e:
                health["errors"].append(f"Production DB error: {e}")
        
        # Check legacy fallback
        if self.legacy_store:
            try:
                vector_count = len(getattr(self.legacy_store, 'id_map', []))
                health["legacy_fallback"] = True
                if not health["production_db"]:
                    health["total_vectors"] = vector_count
                    health["status"] = "legacy"
            except Exception as e:
                health["errors"].append(f"Legacy store error: {e}")
        
        if health["status"] == "unknown":
            health["status"] = "error"
        
        return health
    
    def get_all_metadata(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all metadata from the vector database for knowledge graph construction.
        
        Returns:
            Dictionary with model names as keys and lists of metadata as values
        """
        if self.use_production and self.production_db:
            try:
                all_metadata = {}
                
                # Access metadata from production database
                if hasattr(self.production_db, 'metadata'):
                    for model_name, model_metadata in self.production_db.metadata.items():
                        metadata_list = []
                        for vector_id, metadata in model_metadata.items():
                            # Convert metadata to dictionary format
                            if hasattr(metadata, 'to_dict'):
                                metadata_dict = metadata.to_dict()
                            elif isinstance(metadata, dict):
                                metadata_dict = metadata.copy()
                            else:
                                metadata_dict = {"text": str(metadata), "id": vector_id}
                            
                            metadata_dict["vector_id"] = vector_id
                            metadata_list.append(metadata_dict)
                        
                        all_metadata[model_name] = metadata_list
                
                return all_metadata
                
            except Exception as e:
                logger.error(f"Failed to get all metadata: {e}")
                return {}
        
        # No fallback for metadata - legacy store doesn't have structured metadata
        return {}
    
    def close(self):
        """Clean shutdown of the vector database service."""
        if self.production_db:
            try:
                self.production_db.close()
            except Exception as e:
                logger.error(f"Error closing production database: {e}")
        
        logger.info("Vector database service closed")


# Global instance for backward compatibility
_vector_db_service = None

def get_vector_database() -> VectorDatabaseService:
    """Get the global vector database service instance."""
    global _vector_db_service
    if _vector_db_service is None:
        _vector_db_service = VectorDatabaseService()
    return _vector_db_service

def init_vector_database(storage_dir: str = "data/vector_db", **kwargs) -> VectorDatabaseService:
    """Initialize the vector database service with custom settings."""
    global _vector_db_service
    _vector_db_service = VectorDatabaseService(storage_dir=storage_dir, **kwargs)
    return _vector_db_service
