"""
Tests for the security module.

These tests verify the functionality of the UnifiedSecurityManager and its components.
"""

import unittest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock

from godelOS.unified_agent_core.security.interfaces import (
    SecurityContext, SecurityLevel, UnifiedOperation, ValidationResult
)
from godelOS.unified_agent_core.security.manager import (
    AuthenticationManager, PermissionManager, SecurityMonitor, UnifiedSecurityManager
)


class TestAuthenticationManager(unittest.TestCase):
    """Test cases for the AuthenticationManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.auth_manager = AuthenticationManager({"session_timeout": 1})
        
        # Set up event loop for async tests
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test fixtures."""
        self.loop.close()

    def test_create_session(self):
        """Test creating a session."""
        session_id = self.loop.run_until_complete(
            self.auth_manager.create_session("test_user", ["user"])
        )
        
        self.assertIsNotNone(session_id)
        self.assertIn(session_id, self.auth_manager.active_sessions)
        
        session = self.auth_manager.active_sessions[session_id]
        self.assertEqual(session["user_id"], "test_user")
        self.assertEqual(session["roles"], ["user"])

    def test_validate_session(self):
        """Test validating a session."""
        # Create a session
        session_id = self.loop.run_until_complete(
            self.auth_manager.create_session("test_user", ["user"])
        )
        
        # Validate the session
        is_valid = self.loop.run_until_complete(
            self.auth_manager.validate_session(session_id)
        )
        
        self.assertTrue(is_valid)
        
        # Validate a non-existent session
        is_valid = self.loop.run_until_complete(
            self.auth_manager.validate_session("non-existent")
        )
        
        self.assertFalse(is_valid)

    def test_session_expiration(self):
        """Test session expiration."""
        # Create a session
        session_id = self.loop.run_until_complete(
            self.auth_manager.create_session("test_user", ["user"])
        )
        
        # Wait for the session to expire
        time.sleep(1.1)
        
        # Validate the session
        is_valid = self.loop.run_until_complete(
            self.auth_manager.validate_session(session_id)
        )
        
        self.assertFalse(is_valid)
        self.assertNotIn(session_id, self.auth_manager.active_sessions)

    def test_end_session(self):
        """Test ending a session."""
        # Create a session
        session_id = self.loop.run_until_complete(
            self.auth_manager.create_session("test_user", ["user"])
        )
        
        # End the session
        result = self.loop.run_until_complete(
            self.auth_manager.end_session(session_id)
        )
        
        self.assertTrue(result)
        self.assertNotIn(session_id, self.auth_manager.active_sessions)
        
        # Try to end a non-existent session
        result = self.loop.run_until_complete(
            self.auth_manager.end_session("non-existent")
        )
        
        self.assertFalse(result)


class TestPermissionManager(unittest.TestCase):
    """Test cases for the PermissionManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.perm_manager = PermissionManager()
        
        # Set up event loop for async tests
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test fixtures."""
        self.loop.close()

    def test_get_user_permissions(self):
        """Test getting user permissions."""
        # Get permissions for a user with roles
        perms = self.loop.run_until_complete(
            self.perm_manager.get_user_permissions("human")
        )
        
        self.assertIn("knowledge_store", perms)
        self.assertIn("read", perms["knowledge_store"])
        
        # Get permissions for a user without roles
        perms = self.loop.run_until_complete(
            self.perm_manager.get_user_permissions("unknown")
        )
        
        self.assertEqual(perms, {})

    def test_check_permission(self):
        """Test checking permissions."""
        # Create a security context
        context = SecurityContext(
            user_id="human",
            roles=["user"],
            security_level=SecurityLevel.MEDIUM,
            session_id="test-session",
            metadata={}
        )
        
        # Create an operation with allowed permission
        operation = UnifiedOperation(
            operation_id="test-op",
            operation_type="read",
            source="human",
            target="knowledge_store",
            security_context=context
        )
        
        # Check permission
        has_perm = self.loop.run_until_complete(
            self.perm_manager.check_permission(operation)
        )
        
        self.assertTrue(has_perm)
        
        # Create an operation with disallowed permission
        operation = UnifiedOperation(
            operation_id="test-op",
            operation_type="delete",
            source="human",
            target="knowledge_store",
            security_context=context
        )
        
        # Check permission
        has_perm = self.loop.run_until_complete(
            self.perm_manager.check_permission(operation)
        )
        
        self.assertFalse(has_perm)

    def test_add_remove_role_permission(self):
        """Test adding and removing role permissions."""
        # Add a new permission
        result = self.loop.run_until_complete(
            self.perm_manager.add_role_permission("user", "knowledge_store", "delete")
        )
        
        self.assertTrue(result)
        self.assertIn("delete", self.perm_manager.role_permissions["user"]["knowledge_store"])
        
        # Remove the permission
        result = self.loop.run_until_complete(
            self.perm_manager.remove_role_permission("user", "knowledge_store", "delete")
        )
        
        self.assertTrue(result)
        self.assertNotIn("delete", self.perm_manager.role_permissions["user"]["knowledge_store"])
        
        # Try to remove a non-existent permission
        result = self.loop.run_until_complete(
            self.perm_manager.remove_role_permission("user", "knowledge_store", "non-existent")
        )
        
        self.assertFalse(result)


class TestSecurityMonitor(unittest.TestCase):
    """Test cases for the SecurityMonitor class."""

    def setUp(self):
        """Set up test fixtures."""
        self.monitor = SecurityMonitor({
            "max_events": 5,
            "frequency_threshold": 3
        })
        
        # Set up event loop for async tests
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test fixtures."""
        self.loop.close()

    def test_log_security_event(self):
        """Test logging security events."""
        # Log an event
        self.loop.run_until_complete(
            self.monitor.log_security_event("test_event", {"test": "data"})
        )
        
        self.assertEqual(len(self.monitor.security_events), 1)
        self.assertEqual(self.monitor.security_events[0]["type"], "test_event")
        self.assertEqual(self.monitor.security_events[0]["details"], {"test": "data"})

    def test_max_events(self):
        """Test maximum events limit."""
        # Log more events than the maximum
        for i in range(10):
            self.loop.run_until_complete(
                self.monitor.log_security_event(f"test_event_{i}", {"index": i})
            )
        
        self.assertEqual(len(self.monitor.security_events), 5)
        self.assertEqual(self.monitor.security_events[0]["type"], "test_event_5")
        self.assertEqual(self.monitor.security_events[4]["type"], "test_event_9")

    def test_detect_anomalies(self):
        """Test anomaly detection."""
        # Create a security context
        context = SecurityContext(
            user_id="test_user",
            roles=["user"],
            security_level=SecurityLevel.MEDIUM,
            session_id="test-session",
            metadata={}
        )
        
        # Create an operation
        operation = UnifiedOperation(
            operation_id="test-op",
            operation_type="read",
            source="human",
            target="knowledge_store",
            security_context=context
        )
        
        # Log operation events to trigger anomaly detection
        for i in range(5):
            self.loop.run_until_complete(
                self.monitor.log_security_event(
                    "operation_event",
                    {
                        "operation": operation,
                        "user_id": "test_user"
                    }
                )
            )
        
        # Detect anomalies
        anomalies = self.loop.run_until_complete(
            self.monitor.detect_anomalies(operation)
        )
        
        self.assertEqual(len(anomalies), 1)
        self.assertEqual(anomalies[0]["type"], "high_frequency")
        self.assertEqual(anomalies[0]["user_id"], "test_user")


class TestUnifiedSecurityManager(unittest.TestCase):
    """Test cases for the UnifiedSecurityManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.security_manager = UnifiedSecurityManager({
            "authentication_manager": {"session_timeout": 3600},
            "permission_manager": {},
            "security_monitor": {"max_events": 100}
        })
        
        # Set up event loop for async tests
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test fixtures."""
        if self.security_manager.is_running:
            self.loop.run_until_complete(self.security_manager.stop())
        
        self.loop.close()

    def test_initialize_start_stop(self):
        """Test initializing, starting, and stopping the security manager."""
        # Initialize
        result = self.loop.run_until_complete(self.security_manager.initialize())
        self.assertTrue(result)
        self.assertTrue(self.security_manager.is_initialized)
        
        # Start
        result = self.loop.run_until_complete(self.security_manager.start())
        self.assertTrue(result)
        self.assertTrue(self.security_manager.is_running)
        
        # Stop
        result = self.loop.run_until_complete(self.security_manager.stop())
        self.assertTrue(result)
        self.assertFalse(self.security_manager.is_running)

    def test_validate_operation(self):
        """Test validating operations."""
        # Initialize and start the security manager
        self.loop.run_until_complete(self.security_manager.initialize())
        self.loop.run_until_complete(self.security_manager.start())
        
        # Create a session
        session_id = self.loop.run_until_complete(
            self.security_manager.authentication_manager.create_session("human", ["user"])
        )
        
        # Create a security context
        context = SecurityContext(
            user_id="human",
            roles=["user"],
            security_level=SecurityLevel.MEDIUM,
            session_id=session_id,
            metadata={}
        )
        
        # Create an operation with allowed permission
        operation = UnifiedOperation(
            operation_id="test-op",
            operation_type="read",
            source="human",
            target="knowledge_store",
            security_context=context
        )
        
        # Validate the operation
        result = self.loop.run_until_complete(
            self.security_manager.validate_operation(operation)
        )
        
        self.assertTrue(result.success)
        
        # Create an operation with disallowed permission
        operation = UnifiedOperation(
            operation_id="test-op",
            operation_type="delete",
            source="human",
            target="knowledge_store",
            security_context=context
        )
        
        # Validate the operation
        result = self.loop.run_until_complete(
            self.security_manager.validate_operation(operation)
        )
        
        self.assertFalse(result.success)
        self.assertEqual(result.message, "Permission denied")


if __name__ == "__main__":
    unittest.main()