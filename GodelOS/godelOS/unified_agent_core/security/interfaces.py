"""
Interfaces for the security module.

This module defines the interfaces for the security components of the UnifiedAgentCore.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any, Union


class SecurityLevel(Enum):
    """Security levels for operations."""
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    CRITICAL = 3


class PermissionType(Enum):
    """Types of permissions."""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"


@dataclass
class SecurityContext:
    """Security context for operations."""
    user_id: str
    roles: List[str]
    security_level: SecurityLevel
    session_id: str
    metadata: Dict[str, Any]


@dataclass
class ValidationResult:
    """Result of a security validation."""
    success: bool
    message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class UnifiedOperation:
    """
    Represents an operation in the UnifiedAgentCore that requires security validation.
    """
    
    def __init__(
        self,
        operation_id: str,
        operation_type: str,
        source: str,
        target: str,
        security_context: SecurityContext,
        data: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a UnifiedOperation.
        
        Args:
            operation_id: Unique identifier for the operation
            operation_type: Type of operation (e.g., "read", "write", "execute")
            source: Source of the operation (e.g., "human", "agent", "system")
            target: Target of the operation (e.g., "knowledge_store", "cognitive_engine")
            security_context: Security context for the operation
            data: Optional data associated with the operation
        """
        self.id = operation_id
        self.type = operation_type
        self.source = source
        self.target = target
        self.security_context = security_context
        self.data = data or {}
        self.timestamp = None  # Will be set when the operation is processed


class SecurityException(Exception):
    """Exception raised for security violations."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize a SecurityException.
        
        Args:
            message: The error message
            details: Optional details about the error
        """
        self.message = message
        self.details = details
        super().__init__(message)


class AuthenticationManagerInterface(ABC):
    """Interface for the authentication manager."""
    
    @abstractmethod
    async def authenticate(self, operation: UnifiedOperation) -> bool:
        """
        Authenticate an operation.
        
        Args:
            operation: The operation to authenticate
            
        Returns:
            True if authentication succeeds, False otherwise
        """
        pass
    
    @abstractmethod
    async def validate_session(self, session_id: str) -> bool:
        """
        Validate a session.
        
        Args:
            session_id: The session ID to validate
            
        Returns:
            True if the session is valid, False otherwise
        """
        pass


class PermissionManagerInterface(ABC):
    """Interface for the permission manager."""
    
    @abstractmethod
    async def check_permission(self, operation: UnifiedOperation) -> bool:
        """
        Check if an operation has the required permissions.
        
        Args:
            operation: The operation to check
            
        Returns:
            True if the operation has the required permissions, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_user_permissions(self, user_id: str) -> Dict[str, List[PermissionType]]:
        """
        Get the permissions for a user.
        
        Args:
            user_id: The user ID
            
        Returns:
            Dictionary mapping targets to permission types
        """
        pass


class SecurityMonitorInterface(ABC):
    """Interface for the security monitor."""
    
    @abstractmethod
    async def log_security_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """
        Log a security event.
        
        Args:
            event_type: The type of event
            details: Details about the event
        """
        pass
    
    @abstractmethod
    async def detect_anomalies(self, operation: UnifiedOperation) -> List[Dict[str, Any]]:
        """
        Detect anomalies in an operation.
        
        Args:
            operation: The operation to check
            
        Returns:
            List of detected anomalies
        """
        pass


class AbstractUnifiedSecurityManager(ABC):
    """Abstract base class for the UnifiedSecurityManager."""
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the security manager.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def start(self) -> bool:
        """
        Start the security manager.
        
        Returns:
            True if the manager was started successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def stop(self) -> bool:
        """
        Stop the security manager.
        
        Returns:
            True if the manager was stopped successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def validate_operation(self, operation: UnifiedOperation) -> ValidationResult:
        """
        Validate an operation.
        
        Args:
            operation: The operation to validate
            
        Returns:
            ValidationResult indicating success or failure
        """
        pass