"""
Persistent data storage layer for GödelOS.

Provides reliable data persistence with transactional integrity, concurrent access control,
and automatic backup/recovery mechanisms to prevent data loss on restart.
"""

import asyncio
import json
import logging
import pickle
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import aiofiles
import fcntl
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class TransactionalJSONStore:
    """Thread-safe, transactional JSON file store with locking."""
    
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.mkdir(exist_ok=True)
        self.locks: Dict[str, asyncio.Lock] = {}
    
    def _get_lock(self, key: str) -> asyncio.Lock:
        """Get or create a lock for a specific key."""
        if key not in self.locks:
            self.locks[key] = asyncio.Lock()
        return self.locks[key]
    
    async def store(self, key: str, data: Any) -> bool:
        """Store data with transactional integrity."""
        try:
            file_path = self.storage_path / f"{key}.json"
            temp_path = self.storage_path / f"{key}.json.tmp"
            backup_path = self.storage_path / f"{key}.json.bak"
            
            lock = self._get_lock(key)
            async with lock:
                # Create backup if file exists
                if file_path.exists():
                    await self._copy_file(file_path, backup_path)
                
                # Write to temporary file first
                async with aiofiles.open(temp_path, 'w') as f:
                    if isinstance(data, dict) or isinstance(data, list):
                        await f.write(json.dumps(data, indent=2, default=str))
                    else:
                        await f.write(json.dumps(data.model_dump() if hasattr(data, 'model_dump') else data, indent=2, default=str))
                
                # Atomic rename
                temp_path.rename(file_path)
                
                # Clean up backup after successful write
                if backup_path.exists():
                    backup_path.unlink()
                
            return True
            
        except Exception as e:
            logger.error(f"Error storing {key}: {e}")
            # Try to restore from backup
            if backup_path.exists():
                try:
                    await self._copy_file(backup_path, file_path)
                    logger.info(f"Restored {key} from backup")
                except Exception as restore_error:
                    logger.error(f"Failed to restore {key} from backup: {restore_error}")
            return False
    
    async def load(self, key: str, default: Any = None) -> Any:
        """Load data with fallback to backup."""
        file_path = self.storage_path / f"{key}.json"
        backup_path = self.storage_path / f"{key}.json.bak"
        
        lock = self._get_lock(key)
        async with lock:
            # Try main file first
            try:
                if file_path.exists():
                    async with aiofiles.open(file_path, 'r') as f:
                        content = await f.read()
                        return json.loads(content)
            except Exception as e:
                logger.warning(f"Error loading {key} from main file: {e}")
                
                # Try backup file
                try:
                    if backup_path.exists():
                        async with aiofiles.open(backup_path, 'r') as f:
                            content = await f.read()
                            data = json.loads(content)
                            logger.info(f"Loaded {key} from backup file")
                            return data
                except Exception as backup_error:
                    logger.error(f"Error loading {key} from backup: {backup_error}")
            
            return default
    
    async def delete(self, key: str) -> bool:
        """Delete data file safely."""
        try:
            file_path = self.storage_path / f"{key}.json"
            backup_path = self.storage_path / f"{key}.json.bak"
            
            lock = self._get_lock(key)
            async with lock:
                if file_path.exists():
                    file_path.unlink()
                if backup_path.exists():
                    backup_path.unlink()
            return True
        except Exception as e:
            logger.error(f"Error deleting {key}: {e}")
            return False
    
    async def list_keys(self) -> List[str]:
        """List all stored keys."""
        try:
            keys = []
            for file_path in self.storage_path.glob("*.json"):
                if not file_path.name.endswith(('.tmp', '.bak')):
                    keys.append(file_path.stem)
            return keys
        except Exception as e:
            logger.error(f"Error listing keys: {e}")
            return []
    
    async def _copy_file(self, src: Path, dst: Path):
        """Copy file asynchronously."""
        async with aiofiles.open(src, 'rb') as src_file:
            async with aiofiles.open(dst, 'wb') as dst_file:
                content = await src_file.read()
                await dst_file.write(content)


class PersistentSessionManager:
    """Manages session persistence with automatic cleanup."""
    
    def __init__(self, storage_path: Path):
        self.store = TransactionalJSONStore(storage_path / "sessions")
        self.session_timeout = timedelta(hours=24)  # Sessions expire after 24 hours
        
    async def store_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """Store session data persistently."""
        session_data["last_updated"] = time.time()
        session_data["created_at"] = session_data.get("created_at", time.time())
        return await self.store.store(session_id, session_data)
    
    async def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load session data if it exists and hasn't expired."""
        session_data = await self.store.load(session_id)
        if session_data:
            # Check if session has expired
            last_updated = session_data.get("last_updated", 0)
            if time.time() - last_updated > self.session_timeout.total_seconds():
                # Session expired, clean it up
                await self.delete_session(session_id)
                return None
        return session_data
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session data."""
        return await self.store.delete(session_id)
    
    async def list_active_sessions(self) -> List[str]:
        """List all active (non-expired) sessions."""
        all_sessions = await self.store.list_keys()
        active_sessions = []
        
        for session_id in all_sessions:
            session_data = await self.load_session(session_id)
            if session_data:  # load_session already checks expiry
                active_sessions.append(session_id)
        
        return active_sessions
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions. Returns number of sessions cleaned."""
        all_sessions = await self.store.list_keys()
        cleaned = 0
        
        for session_id in all_sessions:
            session_data = await self.store.load(session_id)
            if session_data:
                last_updated = session_data.get("last_updated", 0)
                if time.time() - last_updated > self.session_timeout.total_seconds():
                    await self.delete_session(session_id)
                    cleaned += 1
        
        logger.info(f"Cleaned up {cleaned} expired sessions")
        return cleaned


class PersistentImportTracker:
    """Tracks import progress persistently."""
    
    def __init__(self, storage_path: Path):
        self.store = TransactionalJSONStore(storage_path / "imports")
        self.progress_timeout = timedelta(hours=2)  # Import progress expires after 2 hours
    
    async def store_progress(self, import_id: str, progress_data: Dict[str, Any]) -> bool:
        """Store import progress."""
        progress_data["last_updated"] = time.time()
        return await self.store.store(import_id, progress_data)
    
    async def load_progress(self, import_id: str) -> Optional[Dict[str, Any]]:
        """Load import progress if it exists and hasn't expired."""
        progress_data = await self.store.load(import_id)
        if progress_data:
            # Check if progress has expired
            last_updated = progress_data.get("last_updated", 0)
            if time.time() - last_updated > self.progress_timeout.total_seconds():
                await self.delete_progress(import_id)
                return None
        return progress_data
    
    async def delete_progress(self, import_id: str) -> bool:
        """Delete import progress."""
        return await self.store.delete(import_id)
    
    async def list_active_imports(self) -> List[str]:
        """List all active imports."""
        all_imports = await self.store.list_keys()
        active_imports = []
        
        for import_id in all_imports:
            progress_data = await self.load_progress(import_id)
            if progress_data:
                active_imports.append(import_id)
        
        return active_imports


class GödelOSPersistenceLayer:
    """Main persistence layer for GödelOS system."""
    
    def __init__(self, base_path: str = "./godelos_data"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        
        # Initialize components
        self.session_manager = PersistentSessionManager(self.base_path)
        self.import_tracker = PersistentImportTracker(self.base_path)
        self.knowledge_store = TransactionalJSONStore(self.base_path / "knowledge")
        
        # Metadata store for system state
        self.metadata_store = TransactionalJSONStore(self.base_path / "metadata")
        
        # Background cleanup task
        self.cleanup_task = None
        
        logger.info(f"GödelOS persistence layer initialized at {self.base_path}")
    
    async def initialize(self):
        """Initialize the persistence layer."""
        try:
            # Load system metadata
            system_info = await self.metadata_store.load("system_info", {})
            system_info.update({
                "last_startup": time.time(),
                "startup_count": system_info.get("startup_count", 0) + 1,
                "version": "1.0.0"
            })
            await self.metadata_store.store("system_info", system_info)
            
            # Start background cleanup
            self.cleanup_task = asyncio.create_task(self._background_cleanup())
            
            logger.info("Persistence layer initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing persistence layer: {e}")
            raise
    
    async def shutdown(self):
        """Shutdown the persistence layer."""
        try:
            if self.cleanup_task:
                self.cleanup_task.cancel()
                try:
                    await self.cleanup_task
                except asyncio.CancelledError:
                    pass
            
            # Store shutdown info
            system_info = await self.metadata_store.load("system_info", {})
            system_info["last_shutdown"] = time.time()
            await self.metadata_store.store("system_info", system_info)
            
            logger.info("Persistence layer shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during persistence layer shutdown: {e}")
    
    async def _background_cleanup(self):
        """Background task for periodic cleanup."""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                # Clean up expired sessions and imports
                await self.session_manager.cleanup_expired_sessions()
                
                # Clean up orphaned files
                await self._cleanup_orphaned_files()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in background cleanup: {e}")
    
    async def _cleanup_orphaned_files(self):
        """Clean up orphaned temporary and backup files."""
        try:
            for storage_dir in [self.base_path / "sessions", self.base_path / "imports", self.base_path / "knowledge"]:
                if storage_dir.exists():
                    for file_path in storage_dir.glob("*.tmp"):
                        if file_path.stat().st_mtime < time.time() - 3600:  # 1 hour old
                            file_path.unlink()
                    
                    for file_path in storage_dir.glob("*.bak"):
                        if file_path.stat().st_mtime < time.time() - 86400:  # 24 hours old
                            file_path.unlink()
        except Exception as e:
            logger.error(f"Error cleaning up orphaned files: {e}")


# Global persistence layer instance
persistence_layer = None

async def get_persistence_layer() -> GödelOSPersistenceLayer:
    """Get the global persistence layer instance."""
    global persistence_layer
    if persistence_layer is None:
        persistence_layer = GödelOSPersistenceLayer()
        await persistence_layer.initialize()
    return persistence_layer

async def initialize_persistence(base_path: str = "./godelos_data") -> GödelOSPersistenceLayer:
    """Initialize the global persistence layer."""
    global persistence_layer
    if persistence_layer is None:
        persistence_layer = GödelOSPersistenceLayer(base_path)
        await persistence_layer.initialize()
    return persistence_layer

async def shutdown_persistence():
    """Shutdown the global persistence layer."""
    global persistence_layer
    if persistence_layer:
        await persistence_layer.shutdown()
        persistence_layer = None