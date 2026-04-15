"""
Unit tests for the ModuleLibraryActivator.
"""

import unittest
from unittest.mock import MagicMock, patch
import tempfile
import os
import shutil
import json
import time
import sys
import logging

from godelOS.metacognition.module_library import (
    ModuleLibraryActivator,
    ModuleStatus,
    ModuleVersion,
    ModuleMetadata,
    ModuleInstance
)


class TestModuleLibraryActivator(unittest.TestCase):
    """Test cases for the ModuleLibraryActivator."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Configure logging
        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger(__name__)
        
        # Create temporary directories
        self.temp_dir = tempfile.mkdtemp()
        self.modules_dir = os.path.join(self.temp_dir, "modules")
        self.backup_dir = os.path.join(self.temp_dir, "backups")
        self.config_file = os.path.join(self.temp_dir, "module_config.json")
        
        logger.debug(f"Test setup: temp_dir={self.temp_dir}")
        logger.debug(f"Test setup: modules_dir={self.modules_dir}")
        
        # Create directories
        os.makedirs(self.modules_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Create test module directories and metadata
        self.create_test_modules()
        
        # Log the contents of the modules directory after creating test modules
        logger.debug(f"Modules directory contents after creating test modules: {os.listdir(self.modules_dir)}")
        
        # Create ModuleLibraryActivator instance
        logger.debug("Creating ModuleLibraryActivator instance")
        self.module_library = ModuleLibraryActivator(
            modules_directory=self.modules_dir,
            config_file=self.config_file,
            backup_directory=self.backup_dir
        )
        
        # Log the modules detected by the ModuleLibraryActivator
        logger.debug(f"Modules detected by ModuleLibraryActivator: {list(self.module_library.modules.keys())}")
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Clean up the temporary directory
        shutil.rmtree(self.temp_dir)
    
    def create_test_modules(self):
        """Create test module directories and metadata."""
        # Create test module 1
        module1_dir = os.path.join(self.modules_dir, "test_module1")
        os.makedirs(module1_dir, exist_ok=True)
        
        # Create metadata file
        metadata1 = {
            "module_id": "test_module1",
            "name": "Test Module 1",
            "description": "A test module",
            "version": "1.0.0",
            "author": "Test Author",
            "dependencies": {},
            "interfaces": ["TestInterface"],
            "tags": ["test", "module"]
        }
        
        with open(os.path.join(module1_dir, "metadata.json"), "w") as f:
            json.dump(metadata1, f)
        
        # Create main.py file
        with open(os.path.join(module1_dir, "main.py"), "w") as f:
            f.write("""
# Test module 1
def hello():
    return "Hello from Test Module 1"

def cleanup():
    print("Cleaning up Test Module 1")
""")
        
        # Create test module 2
        module2_dir = os.path.join(self.modules_dir, "test_module2")
        os.makedirs(module2_dir, exist_ok=True)
        
        # Create metadata file
        metadata2 = {
            "module_id": "test_module2",
            "name": "Test Module 2",
            "description": "Another test module",
            "version": "2.1.0",
            "author": "Test Author",
            "dependencies": {"test_module1": ">=1.0.0"},
            "interfaces": ["AnotherInterface"],
            "tags": ["test", "module", "advanced"]
        }
        
        with open(os.path.join(module2_dir, "metadata.json"), "w") as f:
            json.dump(metadata2, f)
        
        # Create main.py file
        with open(os.path.join(module2_dir, "main.py"), "w") as f:
            f.write("""
# Test module 2
def hello():
    return "Hello from Test Module 2"

def cleanup():
    print("Cleaning up Test Module 2")
""")
    
    def test_initialization(self):
        """Test initialization of ModuleLibraryActivator."""
        # Verify directories were created
        self.assertTrue(os.path.exists(self.modules_dir))
        self.assertTrue(os.path.exists(self.backup_dir))
        
        # Verify config file was created
        self.assertTrue(os.path.exists(self.config_file))
        
        # Verify modules were scanned
        self.assertIn("test_module1", self.module_library.modules)
        self.assertIn("test_module2", self.module_library.modules)
        
        # Verify module metadata
        self.assertEqual(
            self.module_library.modules["test_module1"]["1.0.0"].metadata.name,
            "Test Module 1"
        )
        self.assertEqual(
            self.module_library.modules["test_module2"]["2.1.0"].metadata.name,
            "Test Module 2"
        )
    
    def test_get_available_modules(self):
        """Test getting available modules."""
        # Get available modules
        available_modules = self.module_library.get_available_modules()
        
        # Verify modules
        self.assertIn("test_module1", available_modules)
        self.assertIn("test_module2", available_modules)
        
        # Verify module metadata
        self.assertEqual(len(available_modules["test_module1"]), 1)
        self.assertEqual(len(available_modules["test_module2"]), 1)
        
        self.assertEqual(available_modules["test_module1"][0].name, "Test Module 1")
        self.assertEqual(available_modules["test_module2"][0].name, "Test Module 2")
    
    def test_get_module_info(self):
        """Test getting module information."""
        # Get module info
        module1_info = self.module_library.get_module_info("test_module1", "1.0.0")
        module2_info = self.module_library.get_module_info("test_module2", "2.1.0")
        
        # Verify module info
        self.assertIsNotNone(module1_info)
        self.assertIsNotNone(module2_info)
        
        self.assertEqual(module1_info.name, "Test Module 1")
        self.assertEqual(module2_info.name, "Test Module 2")
        
        # Test getting latest version
        latest_info = self.module_library.get_module_info("test_module1")
        self.assertIsNotNone(latest_info)
        self.assertEqual(latest_info.name, "Test Module 1")
        
        # Test getting unknown module
        unknown_info = self.module_library.get_module_info("unknown_module")
        self.assertIsNone(unknown_info)
    
    @patch('importlib.util.spec_from_file_location')
    @patch('importlib.util.module_from_spec')
    def test_activate_deactivate_module(self, mock_module_from_spec, mock_spec_from_file_location):
        """Test activating and deactivating a module."""
        # Configure mocks
        mock_spec = MagicMock()
        mock_spec_from_file_location.return_value = mock_spec
        
        mock_module = MagicMock()
        mock_module.__name__ = "godelOS_module_test_module1"
        mock_module_from_spec.return_value = mock_module
        
        # Activate module
        success, message = self.module_library.activate_module("test_module1", "1.0.0")
        
        # Verify activation
        self.assertTrue(success)
        self.assertIn("test_module1", self.module_library.active_modules)
        self.assertEqual(
            self.module_library.active_modules["test_module1"].status,
            ModuleStatus.ACTIVE
        )
        
        # Verify module was loaded
        mock_spec_from_file_location.assert_called_once()
        mock_module_from_spec.assert_called_once()
        mock_spec.loader.exec_module.assert_called_once_with(mock_module)
        
        # Deactivate module
        success, message = self.module_library.deactivate_module("test_module1")
        
        # Verify deactivation
        self.assertTrue(success)
        self.assertNotIn("test_module1", self.module_library.active_modules)
        self.assertEqual(
            self.module_library.modules["test_module1"]["1.0.0"].status,
            ModuleStatus.INACTIVE
        )
        
        # Verify cleanup was called
        mock_module.cleanup.assert_called_once()
    
    def test_dependency_checking(self):
        """Test dependency checking."""
        # Configure mocks for activating test_module1
        with patch('importlib.util.spec_from_file_location') as mock_spec_from_file_location, \
             patch('importlib.util.module_from_spec') as mock_module_from_spec:
            
            mock_spec1 = MagicMock()
            mock_spec_from_file_location.return_value = mock_spec1
            
            mock_module1 = MagicMock()
            mock_module1.__name__ = "godelOS_module_test_module1"
            mock_module_from_spec.return_value = mock_module1
            
            # Activate test_module1
            success, message = self.module_library.activate_module("test_module1", "1.0.0")
            self.assertTrue(success)
        
        # Now try to activate test_module2 which depends on test_module1
        with patch('importlib.util.spec_from_file_location') as mock_spec_from_file_location, \
             patch('importlib.util.module_from_spec') as mock_module_from_spec:
            
            mock_spec2 = MagicMock()
            mock_spec_from_file_location.return_value = mock_spec2
            
            mock_module2 = MagicMock()
            mock_module2.__name__ = "godelOS_module_test_module2"
            mock_module_from_spec.return_value = mock_module2
            
            # Activate test_module2
            success, message = self.module_library.activate_module("test_module2", "2.1.0")
            self.assertTrue(success)
        
        # Now try to deactivate test_module1 while test_module2 is active
        success, message = self.module_library.deactivate_module("test_module1")
        self.assertFalse(success)
        self.assertIn("required by test_module2", message)
        
        # Deactivate test_module2 first
        success, message = self.module_library.deactivate_module("test_module2")
        self.assertTrue(success)
        
        # Now test_module1 can be deactivated
        success, message = self.module_library.deactivate_module("test_module1")
        self.assertTrue(success)
    
    def test_version_constraints(self):
        """Test version constraint checking."""
        # Test version satisfies constraint
        self.assertTrue(
            self.module_library._version_satisfies_constraint("1.0.0", ">=1.0.0")
        )
        self.assertTrue(
            self.module_library._version_satisfies_constraint("1.1.0", ">=1.0.0")
        )
        self.assertTrue(
            self.module_library._version_satisfies_constraint("2.0.0", ">=1.0.0")
        )
        
        # Test version does not satisfy constraint
        self.assertFalse(
            self.module_library._version_satisfies_constraint("0.9.0", ">=1.0.0")
        )
        self.assertFalse(
            self.module_library._version_satisfies_constraint("1.0.0", ">1.0.0")
        )
        
        # Test complex constraints
        self.assertTrue(
            self.module_library._version_satisfies_constraint("1.5.0", ">=1.0.0 <2.0.0")
        )
        self.assertFalse(
            self.module_library._version_satisfies_constraint("2.0.0", ">=1.0.0 <2.0.0")
        )
    
    def test_add_remove_module(self):
        """Test adding and removing modules."""
        test_logger = logging.getLogger(__name__)
        test_logger.debug("=== Starting test_add_remove_module ===")
        
        # Create a new module directory
        new_module_dir = os.path.join(self.temp_dir, "new_module")
        os.makedirs(new_module_dir, exist_ok=True)
        test_logger.debug(f"Created new module directory: {new_module_dir}")
        
        # Create metadata file
        metadata = {
            "module_id": "new_module",
            "name": "New Module",
            "description": "A new test module",
            "version": "1.0.0",
            "author": "Test Author",
            "dependencies": {},
            "interfaces": ["NewInterface"],
            "tags": ["test", "new"]
        }
        
        metadata_path = os.path.join(new_module_dir, "metadata.json")
        with open(metadata_path, "w") as f:
            json.dump(metadata, f)
        test_logger.debug(f"Created metadata file at {metadata_path}: {metadata}")
        
        # Create main.py file
        main_py_path = os.path.join(new_module_dir, "main.py")
        with open(main_py_path, "w") as f:
            f.write("""
# New module
def hello():
    return "Hello from New Module"
""")
        test_logger.debug(f"Created main.py file at {main_py_path}")
        
        # Check if add_module method exists
        test_logger.debug(f"ModuleLibraryActivator methods: {[method for method in dir(self.module_library) if not method.startswith('_')]}")
        
        # Add the module
        test_logger.debug("Attempting to call add_module method")
        try:
            success, message = self.module_library.add_module(new_module_dir)
            test_logger.debug(f"add_module result: success={success}, message={message}")
        except AttributeError as e:
            test_logger.error(f"AttributeError when calling add_module: {e}")
            raise
        
        # Verify module was added
        self.assertTrue(success)
        self.assertIn("new_module", self.module_library.modules)
        self.assertIn("1.0.0", self.module_library.modules["new_module"])
        
        # Remove the module
        success, message = self.module_library.remove_module("new_module", "1.0.0")
        
        # Verify module was removed
        self.assertTrue(success)
        self.assertTrue(
            "new_module" not in self.module_library.modules or
            "1.0.0" not in self.module_library.modules["new_module"]
        )
    
    def test_rollback_module(self):
        """Test rolling back a module to a previous version."""
        test_logger = logging.getLogger(__name__)
        test_logger.debug("=== Starting test_rollback_module ===")
        
        # Create a new version of test_module1
        module1_v2_dir = os.path.join(self.modules_dir, "test_module1_v2")
        os.makedirs(module1_v2_dir, exist_ok=True)
        test_logger.debug(f"Created new module version directory: {module1_v2_dir}")
        
        # Create metadata file
        metadata = {
            "module_id": "test_module1",
            "name": "Test Module 1",
            "description": "A test module (version 2)",
            "version": "2.0.0",
            "author": "Test Author",
            "dependencies": {},
            "interfaces": ["TestInterface"],
            "tags": ["test", "module"]
        }
        
        metadata_path = os.path.join(module1_v2_dir, "metadata.json")
        with open(metadata_path, "w") as f:
            json.dump(metadata, f)
        test_logger.debug(f"Created metadata file at {metadata_path}: {metadata}")
        
        # Create main.py file
        main_py_path = os.path.join(module1_v2_dir, "main.py")
        with open(main_py_path, "w") as f:
            f.write("""
# Test module 1 (version 2)
def hello():
    return "Hello from Test Module 1 (version 2)"

def cleanup():
    print("Cleaning up Test Module 1 (version 2)")
""")
        test_logger.debug(f"Created main.py file at {main_py_path}")
        
        # Check what methods are available in ModuleLibraryActivator
        test_logger.debug(f"Available methods in ModuleLibraryActivator: {[method for method in dir(self.module_library) if not method.startswith('_')]}")
        
        # Add the new version
        test_logger.debug("Attempting to call add_module method")
        try:
            success, message = self.module_library.add_module(module1_v2_dir)
            test_logger.debug(f"add_module result: success={success}, message={message}")
        except AttributeError as e:
            test_logger.error(f"AttributeError when calling add_module: {e}")
            raise
        self.assertTrue(success)
        
        # Activate the new version
        with patch('importlib.util.spec_from_file_location'), \
             patch('importlib.util.module_from_spec'):
            success, message = self.module_library.activate_module("test_module1", "2.0.0")
            self.assertTrue(success)
        
        # Rollback to the previous version
        with patch('importlib.util.spec_from_file_location'), \
             patch('importlib.util.module_from_spec'):
            success, message = self.module_library.rollback_module("test_module1")
            print(f"Rollback result: success={success}, message={message}")
            self.assertTrue(success)
        
        # Verify the previous version is active
        self.assertEqual(
            str(self.module_library.active_modules["test_module1"].metadata.version),
            "1.0.0"
        )
    
    def test_module_version(self):
        """Test ModuleVersion class."""
        # Create a version
        version = ModuleVersion(1, 2, 3, "beta", "001")
        
        # Test string representation
        self.assertEqual(str(version), "1.2.3-beta+001")
        
        # Test from_string method
        version2 = ModuleVersion.from_string("2.3.4-alpha+002")
        self.assertEqual(version2.major, 2)
        self.assertEqual(version2.minor, 3)
        self.assertEqual(version2.patch, 4)
        self.assertEqual(version2.prerelease, "alpha")
        self.assertEqual(version2.build, "002")
        
        # Test to_dict method
        version_dict = version.to_dict()
        self.assertEqual(version_dict["major"], 1)
        self.assertEqual(version_dict["minor"], 2)
        self.assertEqual(version_dict["patch"], 3)
        self.assertEqual(version_dict["prerelease"], "beta")
        self.assertEqual(version_dict["build"], "001")
    
    def test_module_metadata(self):
        """Test ModuleMetadata class."""
        # Create metadata
        metadata = ModuleMetadata(
            module_id="test_module",
            name="Test Module",
            description="A test module",
            version=ModuleVersion(1, 0, 0),
            author="Test Author",
            dependencies={"other_module": ">=1.0.0"},
            interfaces=["TestInterface"],
            tags=["test", "module"]
        )
        
        # Test to_dict method
        metadata_dict = metadata.to_dict()
        self.assertEqual(metadata_dict["module_id"], "test_module")
        self.assertEqual(metadata_dict["name"], "Test Module")
        self.assertEqual(metadata_dict["description"], "A test module")
        self.assertEqual(metadata_dict["version"], "1.0.0")
        self.assertEqual(metadata_dict["author"], "Test Author")
        self.assertEqual(metadata_dict["dependencies"], {"other_module": ">=1.0.0"})
        self.assertEqual(metadata_dict["interfaces"], ["TestInterface"])
        self.assertEqual(metadata_dict["tags"], ["test", "module"])
        
        # Test from_dict method
        metadata2 = ModuleMetadata.from_dict(metadata_dict)
        self.assertEqual(metadata2.module_id, "test_module")
        self.assertEqual(metadata2.name, "Test Module")
        self.assertEqual(metadata2.description, "A test module")
        self.assertEqual(str(metadata2.version), "1.0.0")
        self.assertEqual(metadata2.author, "Test Author")
        self.assertEqual(metadata2.dependencies, {"other_module": ">=1.0.0"})
        self.assertEqual(metadata2.interfaces, ["TestInterface"])
        self.assertEqual(metadata2.tags, ["test", "module"])


if __name__ == '__main__':
    unittest.main()