"""
UnifiedSecurityManager Implementation for GodelOS

This module implements the UnifiedSecurityManager class, which provides security
features including authentication, authorization, and validation for the UnifiedAgentCore.
"""

import logging
import time
import uuid
from typing import Dict, List, Optional, Any, Set
import asyncio

from godelOS.unified_agent_core.security.interfaces import (
    AbstractUnifiedSecurityManager, AuthenticationManagerInterface,
    PermissionManagerInterface, SecurityMonitorInterface,
    UnifiedOperation, ValidationResult, SecurityException
)

logger = logging.getLogger(__name__)


class AuthenticationManager(AuthenticationManagerInterface):
    """
    Authentication manager implementation.
    
    Handles user authentication and session validation.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the authentication manager.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.session_timeout = self.config.get("session_timeout", 3600)  # 1 hour default
        self.lock = asyncio.Lock()
    
    async def authenticate(self, operation: UnifiedOperation) -> bool:
        """
        Authenticate an operation.
        
        Args:
            operation: The operation to authenticate
            
        Returns:
            True if authentication succeeds, False otherwise
        """
        async with self.lock:
            # Check if the session is valid (lock-free internal call)
            if not self._validate_session_unlocked(operation.security_context.session_id):
                logger.warning(f"Invalid session for operation {operation.id}")
                return False
            
            # Check if the user exists and has the required security level
            user_id = operation.security_context.user_id
            required_level = operation.security_context.security_level
            
            # In a real implementation, this would check against a user database
            # For now, we'll assume all users are valid
            
            # Refresh the session
            if operation.security_context.session_id in self.active_sessions:
                self.active_sessions[operation.security_context.session_id]["last_activity"] = time.time()
            
            return True
    
    def _validate_session_unlocked(self, session_id: str) -> bool:
        """Internal lock-free helper for session validation."""
        if session_id not in self.active_sessions:
            return False
        
        session = self.active_sessions[session_id]
        current_time = time.time()
        
        # Check if the session has expired
        if current_time - session["last_activity"] > self.session_timeout:
            # Remove expired session
            del self.active_sessions[session_id]
            return False
        
        return True

    async def validate_session(self, session_id: str) -> bool:
        """
        Validate a session.
        
        Args:
            session_id: The session ID to validate
            
        Returns:
            True if the session is valid, False otherwise
        """
        async with self.lock:
            return self._validate_session_unlocked(session_id)
    
    async def create_session(self, user_id: str, roles: List[str]) -> str:
        """
        Create a new session.
        
        Args:
            user_id: The user ID
            roles: The user's roles
            
        Returns:
            The session ID
        """
        async with self.lock:
            session_id = str(uuid.uuid4())
            
            self.active_sessions[session_id] = {
                "user_id": user_id,
                "roles": roles,
                "created_at": time.time(),
                "last_activity": time.time()
            }
            
            return session_id
    
    async def end_session(self, session_id: str) -> bool:
        """
        End a session.
        
        Args:
            session_id: The session ID
            
        Returns:
            True if the session was ended, False if it didn't exist
        """
        async with self.lock:
            if session_id not in self.active_sessions:
                return False
            
            del self.active_sessions[session_id]
            return True
    
    async def clean_expired_sessions(self) -> int:
        """
        Clean expired sessions.
        
        Returns:
            Number of sessions cleaned
        """
        async with self.lock:
            current_time = time.time()
            expired_sessions = [
                session_id for session_id, session in self.active_sessions.items()
                if current_time - session["last_activity"] > self.session_timeout
            ]
            
            for session_id in expired_sessions:
                del self.active_sessions[session_id]
            
            return len(expired_sessions)


class PermissionManager(PermissionManagerInterface):
    """
    Permission manager implementation.
    
    Handles permission checking and role-based access control.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the permission manager.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.lock = asyncio.Lock()
        
        # In a real implementation, these would be loaded from a database
        # For now, we'll use in-memory dictionaries
        self.role_permissions: Dict[str, Dict[str, Set[str]]] = {
            "admin": {
                "knowledge_store": {"read", "write", "delete"},
                "cognitive_engine": {"read", "write", "execute"},
                "interaction_engine": {"read", "write", "execute"},
                "resource_manager": {"read", "write", "execute"}
            },
            "user": {
                "knowledge_store": {"read"},
                "cognitive_engine": {"read", "execute"},
                "interaction_engine": {"read", "execute"},
                "resource_manager": {"read"}
            },
            "agent": {
                "knowledge_store": {"read"},
                "cognitive_engine": {"read", "execute"},
                "interaction_engine": {"read", "execute"},
                "resource_manager": {"read"}
            }
        }
        
        self.user_roles: Dict[str, List[str]] = {
            "system": ["admin"],
            "human": ["user"],
            "agent": ["agent"]
        }
    
    async def check_permission(self, operation: UnifiedOperation) -> bool:
        """
        Check if an operation has the required permissions.
        
        Args:
            operation: The operation to check
            
        Returns:
            True if the operation has the required permissions, False otherwise
        """
        async with self.lock:
            user_id = operation.security_context.user_id
            roles = operation.security_context.roles
            operation_type = operation.type
            target = operation.target
            
            # Get the user's permissions (lock-free internal call)
            user_permissions = self._get_user_permissions_unlocked(user_id)
            
            # Check if the user has the required permission for the target
            if target in user_permissions:
                if operation_type in user_permissions[target]:
                    return True
            
            # Check role-based permissions
            for role in roles:
                if role in self.role_permissions:
                    role_perms = self.role_permissions[role]
                    if target in role_perms and operation_type in role_perms[target]:
                        return True
            
            logger.warning(f"Permission denied for operation {operation.id}: {operation_type} on {target}")
            return False
    
    def _get_user_permissions_unlocked(self, user_id: str) -> Dict[str, List[str]]:
        """Internal lock-free helper for computing user permissions."""
        result: Dict[str, List[str]] = {}
        
        roles = self.user_roles.get(user_id, [])
        
        for role in roles:
            if role in self.role_permissions:
                role_perms = self.role_permissions[role]
                for target, perms in role_perms.items():
                    if target not in result:
                        result[target] = []
                    result[target].extend(list(perms))
        
        for target in result:
            result[target] = list(set(result[target]))
        
        return result

    async def get_user_permissions(self, user_id: str) -> Dict[str, List[str]]:
        """
        Get the permissions for a user.
        
        Args:
            user_id: The user ID
            
        Returns:
            Dictionary mapping targets to permission types
        """
        async with self.lock:
            return self._get_user_permissions_unlocked(user_id)
    
    async def add_role_permission(self, role: str, target: str, permission: str) -> bool:
        """
        Add a permission to a role.
        
        Args:
            role: The role
            target: The target
            permission: The permission
            
        Returns:
            True if the permission was added, False otherwise
        """
        async with self.lock:
            if role not in self.role_permissions:
                self.role_permissions[role] = {}
            
            if target not in self.role_permissions[role]:
                self.role_permissions[role][target] = set()
            
            self.role_permissions[role][target].add(permission)
            return True
    
    async def remove_role_permission(self, role: str, target: str, permission: str) -> bool:
        """
        Remove a permission from a role.
        
        Args:
            role: The role
            target: The target
            permission: The permission
            
        Returns:
            True if the permission was removed, False otherwise
        """
        async with self.lock:
            if (role not in self.role_permissions or
                target not in self.role_permissions[role] or
                permission not in self.role_permissions[role][target]):
                return False
            
            self.role_permissions[role][target].remove(permission)
            return True


class SecurityMonitor(SecurityMonitorInterface):
    """
    Security monitor implementation.
    
    Monitors security events and detects anomalies.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the security monitor.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.lock = asyncio.Lock()
        self.security_events: List[Dict[str, Any]] = []
        self.max_events = self.config.get("max_events", 1000)
        self.anomaly_detection_enabled = self.config.get("anomaly_detection_enabled", True)
        
        # Anomaly detection parameters
        self.operation_frequency: Dict[str, Dict[str, int]] = {}  # user_id -> operation_type -> count
        self.frequency_threshold = self.config.get("frequency_threshold", 10)
        self.time_window = self.config.get("time_window", 60)  # 1 minute
    
    async def log_security_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """
        Log a security event.
        
        Args:
            event_type: The type of event
            details: Details about the event
        """
        async with self.lock:
            event = {
                "id": str(uuid.uuid4()),
                "type": event_type,
                "timestamp": time.time(),
                "details": details
            }
            
            self.security_events.append(event)
            
            # Trim events if necessary
            if len(self.security_events) > self.max_events:
                self.security_events = self.security_events[-self.max_events:]
            
            # Update operation frequency for anomaly detection
            if "operation" in details and "user_id" in details:
                user_id = details["user_id"]
                operation_type = details["operation"].type
                
                if user_id not in self.operation_frequency:
                    self.operation_frequency[user_id] = {}
                
                if operation_type not in self.operation_frequency[user_id]:
                    self.operation_frequency[user_id][operation_type] = 0
                
                self.operation_frequency[user_id][operation_type] += 1
    
    async def detect_anomalies(self, operation: UnifiedOperation) -> List[Dict[str, Any]]:
        """
        Detect anomalies in an operation.
        
        Args:
            operation: The operation to check
            
        Returns:
            List of detected anomalies
        """
        if not self.anomaly_detection_enabled:
            return []
        
        async with self.lock:
            anomalies = []
            user_id = operation.security_context.user_id
            operation_type = operation.type
            
            # Check operation frequency
            if user_id in self.operation_frequency and operation_type in self.operation_frequency[user_id]:
                frequency = self.operation_frequency[user_id][operation_type]
                
                if frequency > self.frequency_threshold:
                    anomalies.append({
                        "type": "high_frequency",
                        "user_id": user_id,
                        "operation_type": operation_type,
                        "frequency": frequency,
                        "threshold": self.frequency_threshold
                    })
            
            # Additional anomaly detection logic would go here
            # For example, checking for unusual patterns, suspicious operations, etc.
            
            return anomalies
    
    async def get_recent_events(self, max_count: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent security events.
        
        Args:
            max_count: Maximum number of events to return
            
        Returns:
            List of recent security events
        """
        async with self.lock:
            # Return the most recent events
            return self.security_events[-max_count:]
    
    async def clear_old_events(self, max_age: float = 86400) -> int:
        """
        Clear old security events.
        
        Args:
            max_age: Maximum age of events to keep (in seconds)
            
        Returns:
            Number of events cleared
        """
        async with self.lock:
            current_time = time.time()
            old_count = len(self.security_events)
            
            self.security_events = [
                event for event in self.security_events
                if current_time - event["timestamp"] <= max_age
            ]
            
            return old_count - len(self.security_events)


class UnifiedSecurityManager(AbstractUnifiedSecurityManager):
    """
    UnifiedSecurityManager implementation for GodelOS.
    
    The UnifiedSecurityManager provides security features including authentication,
    authorization, and validation for the UnifiedAgentCore.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the unified security manager.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        
        # Initialize components
        self.authentication_manager = AuthenticationManager(self.config.get("authentication_manager"))
        self.permission_manager = PermissionManager(self.config.get("permission_manager"))
        self.security_monitor = SecurityMonitor(self.config.get("security_monitor"))
        
        # Initialize state
        self.is_initialized = False
        self.is_running = False
        
        # Initialize lock
        self.lock = asyncio.Lock()
        
        # Maintenance task
        self.maintenance_task = None
        self.maintenance_interval = self.config.get("maintenance_interval", 300)  # 5 minutes
    
    async def initialize(self) -> bool:
        """
        Initialize the security manager.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        if self.is_initialized:
            logger.warning("UnifiedSecurityManager is already initialized")
            return True
        
        try:
            logger.info("Initializing UnifiedSecurityManager")
            
            # Add initialization logic here
            
            self.is_initialized = True
            logger.info("UnifiedSecurityManager initialized successfully")
            
            return True
        except Exception as e:
            logger.error(f"Error initializing UnifiedSecurityManager: {e}")
            return False
    
    async def start(self) -> bool:
        """
        Start the security manager.
        
        Returns:
            True if the manager was started successfully, False otherwise
        """
        if not self.is_initialized:
            success = await self.initialize()
            if not success:
                return False
        
        if self.is_running:
            logger.warning("UnifiedSecurityManager is already running")
            return True
        
        try:
            logger.info("Starting UnifiedSecurityManager")
            
            # Start maintenance task
            self.maintenance_task = asyncio.create_task(self._maintenance_loop())
            
            self.is_running = True
            logger.info("UnifiedSecurityManager started successfully")
            
            return True
        except Exception as e:
            logger.error(f"Error starting UnifiedSecurityManager: {e}")
            return False
    
    async def stop(self) -> bool:
        """
        Stop the security manager.
        
        Returns:
            True if the manager was stopped successfully, False otherwise
        """
        if not self.is_running:
            logger.warning("UnifiedSecurityManager is not running")
            return True
        
        try:
            logger.info("Stopping UnifiedSecurityManager")
            
            # Cancel maintenance task
            if self.maintenance_task:
                self.maintenance_task.cancel()
                try:
                    await self.maintenance_task
                except asyncio.CancelledError:
                    pass
                self.maintenance_task = None
            
            self.is_running = False
            logger.info("UnifiedSecurityManager stopped successfully")
            
            return True
        except Exception as e:
            logger.error(f"Error stopping UnifiedSecurityManager: {e}")
            return False
    
    async def validate_operation(self, operation: UnifiedOperation) -> ValidationResult:
        """
        Validate an operation.
        
        Args:
            operation: The operation to validate
            
        Returns:
            ValidationResult indicating success or failure
        """
        if not self.is_running:
            raise RuntimeError("UnifiedSecurityManager is not running")
        
        try:
            # Authenticate the operation
            auth_result = await self.authentication_manager.authenticate(operation)
            if not auth_result:
                return ValidationResult(
                    success=False,
                    message="Authentication failed",
                    details={"operation_id": operation.id}
                )
            
            # Check permissions
            perm_result = await self.permission_manager.check_permission(operation)
            if not perm_result:
                return ValidationResult(
                    success=False,
                    message="Permission denied",
                    details={"operation_id": operation.id}
                )
            
            # Detect anomalies
            anomalies = await self.security_monitor.detect_anomalies(operation)
            if anomalies:
                # Log anomalies but don't block the operation
                await self.security_monitor.log_security_event(
                    "anomaly_detected",
                    {
                        "operation": operation,
                        "user_id": operation.security_context.user_id,
                        "anomalies": anomalies
                    }
                )
            
            # Log successful validation
            await self.security_monitor.log_security_event(
                "operation_validated",
                {
                    "operation": operation,
                    "user_id": operation.security_context.user_id
                }
            )
            
            return ValidationResult(
                success=True,
                message="Operation validated successfully"
            )
        
        except Exception as e:
            logger.error(f"Error validating operation: {e}")
            await self.security_monitor.log_security_event(
                "validation_error",
                {
                    "operation": operation,
                    "error": str(e)
                }
            )
            return ValidationResult(
                success=False,
                message=f"Validation error: {str(e)}"
            )
    
    async def _maintenance_loop(self) -> None:
        """Maintenance loop for periodic tasks."""
        try:
            while True:
                await asyncio.sleep(self.maintenance_interval)
                
                try:
                    # Clean expired sessions
                    cleaned_sessions = await self.authentication_manager.clean_expired_sessions()
                    if cleaned_sessions > 0:
                        logger.info(f"Cleaned {cleaned_sessions} expired sessions")
                    
                    # Clear old security events
                    cleared_events = await self.security_monitor.clear_old_events()
                    if cleared_events > 0:
                        logger.info(f"Cleared {cleared_events} old security events")
                
                except Exception as e:
                    logger.error(f"Error in security maintenance loop: {e}")
        
        except asyncio.CancelledError:
            logger.info("Security maintenance loop cancelled")