"""
Module Library & Activator (MLA) for GödelOS.

This module implements the ModuleLibraryActivator component (Module 7.5) of the Metacognition & 
Self-Improvement System, which is responsible for managing a library of alternative module 
implementations and supporting dynamic loading and unloading of modules.

The ModuleLibraryActivator:
1. Manages a library of alternative module implementations
2. Supports dynamic loading and unloading of modules
3. Provides mechanisms for module activation and deactivation
4. Maintains compatibility information between modules
5. Supports versioning and rollback
"""

import logging
import time
import os
import importlib
import importlib.util
import sys
import json
import shutil
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Callable, Type
from enum import Enum
from dataclasses import dataclass, field
import inspect
import hashlib
import semver

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class ModuleStatus(Enum):
    """Enum representing the status of a module."""
    AVAILABLE = "available"
    ACTIVE = "active"
    INACTIVE = "inactive"
    FAILED = "failed"
    INCOMPATIBLE = "incompatible"
    DEPRECATED = "deprecated"


@dataclass
class ModuleVersion:
    """Represents a version of a module."""
    major: int
    minor: int
    patch: int
    prerelease: str = ""
    build: str = ""
    
    def __str__(self) -> str:
        """Convert to string representation."""
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            version += f"-{self.prerelease}"
        if self.build:
            version += f"+{self.build}"
        return version
    
    @classmethod
    def from_string(cls, version_str: str) -> "ModuleVersion":
        """Create a ModuleVersion from a string."""
        version_info = semver.VersionInfo.parse(version_str)
        return cls(
            major=version_info.major,
            minor=version_info.minor,
            patch=version_info.patch,
            prerelease=version_info.prerelease,
            build=version_info.build
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "major": self.major,
            "minor": self.minor,
            "patch": self.patch,
            "prerelease": self.prerelease,
            "build": self.build
        }


@dataclass
class ModuleMetadata:
    """Represents metadata for a module."""
    module_id: str
    name: str
    description: str
    version: ModuleVersion
    author: str
    dependencies: Dict[str, str] = field(default_factory=dict)  # module_id -> version constraint
    interfaces: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    creation_date: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)
    checksum: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "module_id": self.module_id,
            "name": self.name,
            "description": self.description,
            "version": str(self.version),
            "author": self.author,
            "dependencies": self.dependencies,
            "interfaces": self.interfaces,
            "tags": self.tags,
            "creation_date": self.creation_date,
            "last_updated": self.last_updated,
            "checksum": self.checksum
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModuleMetadata":
        """Create a ModuleMetadata from a dictionary."""
        return cls(
            module_id=data["module_id"],
            name=data["name"],
            description=data["description"],
            version=ModuleVersion.from_string(data["version"]),
            author=data["author"],
            dependencies=data.get("dependencies", {}),
            interfaces=data.get("interfaces", []),
            tags=data.get("tags", []),
            creation_date=data.get("creation_date", time.time()),
            last_updated=data.get("last_updated", time.time()),
            checksum=data.get("checksum", "")
        )


@dataclass
class ModuleInstance:
    """Represents an instance of a module."""
    metadata: ModuleMetadata
    module_path: str
    status: ModuleStatus = ModuleStatus.AVAILABLE
    module_object: Any = None
    activation_time: Optional[float] = None
    error_message: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "metadata": self.metadata.to_dict(),
            "module_path": self.module_path,
            "status": self.status.value,
            "activation_time": self.activation_time,
            "error_message": self.error_message
        }


class ModuleLibraryActivator:
    """
    Module Library & Activator (MLA) for GödelOS.
    
    The ModuleLibraryActivator manages a library of alternative module implementations
    and supports dynamic loading and unloading of modules.
    """
    
    def __init__(
        self,
        modules_directory: str,
        config_file: Optional[str] = None,
        backup_directory: Optional[str] = None
    ):
        """Initialize the module library activator."""
        logger.debug(f"Initializing ModuleLibraryActivator with modules_directory={modules_directory}")
        self.modules_directory = modules_directory
        self.config_file = config_file or os.path.join(modules_directory, "module_config.json")
        self.backup_directory = backup_directory or os.path.join(modules_directory, "backups")
        
        logger.debug(f"Using config_file={self.config_file}, backup_directory={self.backup_directory}")
        
        # Create directories if they don't exist
        os.makedirs(self.modules_directory, exist_ok=True)
        os.makedirs(self.backup_directory, exist_ok=True)
        
        # Initialize module registry
        self.modules: Dict[str, Dict[str, ModuleInstance]] = {}  # module_id -> version_str -> ModuleInstance
        self.active_modules: Dict[str, ModuleInstance] = {}  # module_id -> ModuleInstance
        
        # Load module registry from config file
        self._load_config()
        
        # Scan modules directory for new modules
        self._scan_modules_directory()
        
        logger.debug(f"Initialization complete. Modules: {list(self.modules.keys())}")
    
    def _load_config(self) -> None:
        """Load module configuration from config file."""
        if not os.path.exists(self.config_file):
            logger.info(f"Config file {self.config_file} not found, creating new config")
            self._save_config()
            return
        
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            # Load modules
            for module_id, versions in config.get("modules", {}).items():
                self.modules[module_id] = {}
                
                for version_str, module_data in versions.items():
                    metadata = ModuleMetadata.from_dict(module_data["metadata"])
                    
                    instance = ModuleInstance(
                        metadata=metadata,
                        module_path=module_data["module_path"],
                        status=ModuleStatus(module_data["status"]),
                        activation_time=module_data.get("activation_time"),
                        error_message=module_data.get("error_message", "")
                    )
                    
                    self.modules[module_id][version_str] = instance
            
            # Load active modules
            for module_id, module_data in config.get("active_modules", {}).items():
                if module_id in self.modules and module_data["version"] in self.modules[module_id]:
                    self.active_modules[module_id] = self.modules[module_id][module_data["version"]]
            
            logger.info(f"Loaded {len(self.modules)} modules from config")
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            # Create a backup of the corrupted config
            if os.path.exists(self.config_file):
                backup_path = os.path.join(
                    self.backup_directory,
                    f"module_config_backup_{int(time.time())}.json"
                )
                shutil.copy2(self.config_file, backup_path)
                logger.info(f"Created backup of corrupted config at {backup_path}")
            
            # Initialize with empty config
            self.modules = {}
            self.active_modules = {}
            self._save_config()
    
    def _save_config(self) -> None:
        """Save module configuration to config file."""
        config = {
            "modules": {},
            "active_modules": {}
        }
        
        # Save modules
        for module_id, versions in self.modules.items():
            config["modules"][module_id] = {}
            
            for version_str, instance in versions.items():
                config["modules"][module_id][version_str] = instance.to_dict()
        
        # Save active modules
        for module_id, instance in self.active_modules.items():
            config["active_modules"][module_id] = {
                "version": str(instance.metadata.version)
            }
        
        try:
            # Create a backup of the current config
            if os.path.exists(self.config_file):
                backup_path = os.path.join(
                    self.backup_directory,
                    f"module_config_backup_{int(time.time())}.json"
                )
                shutil.copy2(self.config_file, backup_path)
            
            # Save the new config
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            logger.info(f"Saved config with {len(self.modules)} modules")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def _scan_modules_directory(self) -> None:
        """Scan modules directory for new modules."""
        logger.debug(f"Scanning modules directory: {self.modules_directory}")
        if not os.path.exists(self.modules_directory):
            logger.warning(f"Modules directory {self.modules_directory} not found")
            return
        
        # Log the contents of the modules directory
        dir_contents = os.listdir(self.modules_directory)
        logger.debug(f"Contents of modules directory: {dir_contents}")
        
        for item in dir_contents:
            item_path = os.path.join(self.modules_directory, item)
            logger.debug(f"Checking item: {item} (is directory: {os.path.isdir(item_path)})")
            
            # Check if it's a directory
            if os.path.isdir(item_path):
                # Check for metadata file
                metadata_path = os.path.join(item_path, "metadata.json")
                logger.debug(f"Checking for metadata file: {metadata_path} (exists: {os.path.exists(metadata_path)})")
                
                if os.path.exists(metadata_path):
                    try:
                        with open(metadata_path, 'r') as f:
                            metadata_dict = json.load(f)
                        
                        logger.debug(f"Loaded metadata: {metadata_dict}")
                        metadata = ModuleMetadata.from_dict(metadata_dict)
                        module_id = metadata.module_id
                        version_str = str(metadata.version)
                        
                        # Check if module already exists in registry
                        if module_id in self.modules and version_str in self.modules[module_id]:
                            logger.debug(f"Module {module_id} v{version_str} already exists in registry")
                            continue
                        
                        # Calculate checksum
                        checksum = self._calculate_module_checksum(item_path)
                        metadata.checksum = checksum
                        
                        # Add to registry
                        if module_id not in self.modules:
                            self.modules[module_id] = {}
                        
                        self.modules[module_id][version_str] = ModuleInstance(
                            metadata=metadata,
                            module_path=item_path
                        )
                        
                        logger.info(f"Found new module: {module_id} v{version_str}")
                    except Exception as e:
                        logger.error(f"Error processing module in {item_path}: {e}")
                        logger.exception(e)  # Log the full exception traceback
        
        logger.debug(f"Modules after scanning: {list(self.modules.keys())}")
        # Save updated registry
        self._save_config()
    
    def _calculate_module_checksum(self, module_path: str) -> str:
        """Calculate a checksum for a module directory."""
        if not os.path.exists(module_path):
            return ""
        
        hasher = hashlib.sha256()
        
        for root, _, files in os.walk(module_path):
            for file in sorted(files):
                file_path = os.path.join(root, file)
                
                # Skip metadata.json since it contains the checksum
                if file == "metadata.json":
                    continue
                
                try:
                    with open(file_path, 'rb') as f:
                        # Update hash with file path and content
                        rel_path = os.path.relpath(file_path, module_path)
                        hasher.update(rel_path.encode())
                        hasher.update(f.read())
                except Exception as e:
                    logger.error(f"Error calculating checksum for {file_path}: {e}")
        
        return hasher.hexdigest()
    
    def get_available_modules(self) -> Dict[str, List[ModuleMetadata]]:
        """
        Get all available modules.
        
        Returns:
            Dictionary mapping module IDs to lists of available versions
        """
        result = {}
        
        for module_id, versions in self.modules.items():
            result[module_id] = []
            
            for instance in versions.values():
                result[module_id].append(instance.metadata)
        
        return result
    
    def get_module_info(self, module_id: str, version: Optional[str] = None) -> Optional[ModuleMetadata]:
        """
        Get information about a specific module.
        
        Args:
            module_id: ID of the module
            version: Optional version string (if None, returns the active version)
            
        Returns:
            Module metadata if found, None otherwise
        """
        if module_id not in self.modules:
            return None
        
        if version is None:
            # Return active version if available
            if module_id in self.active_modules:
                return self.active_modules[module_id].metadata
            
            # Otherwise, return latest version
            latest_version = self._get_latest_version(module_id)
            if latest_version:
                return self.modules[module_id][latest_version].metadata
            
            return None
        
        if version not in self.modules[module_id]:
            return None
        
        return self.modules[module_id][version].metadata
    
    def _get_latest_version(self, module_id: str) -> Optional[str]:
        """Get the latest version of a module."""
        if module_id not in self.modules or not self.modules[module_id]:
            return None
        
        versions = list(self.modules[module_id].keys())
        
        # Sort versions using semver
        sorted_versions = sorted(versions, key=lambda v: semver.VersionInfo.parse(v), reverse=True)
        
        return sorted_versions[0] if sorted_versions else None
    
    def activate_module(
        self,
        module_id: str,
        version: Optional[str] = None,
        force: bool = False
    ) -> Tuple[bool, str]:
        """
        Activate a module.
        
        Args:
            module_id: ID of the module to activate
            version: Optional version string (if None, activates the latest version)
            force: If True, activates even if dependencies are not satisfied
            
        Returns:
            Tuple of (success, message)
        """
        if module_id not in self.modules:
            return False, f"Module {module_id} not found"
        
        # Determine version to activate
        if version is None:
            version = self._get_latest_version(module_id)
            if not version:
                return False, f"No versions available for module {module_id}"
        elif version not in self.modules[module_id]:
            return False, f"Version {version} not found for module {module_id}"
        
        instance = self.modules[module_id][version]
        
        # Check if already active
        if module_id in self.active_modules and self.active_modules[module_id].metadata.version == instance.metadata.version:
            return True, f"Module {module_id} v{version} is already active"
        
        # Check dependencies
        if not force:
            satisfied, message = self._check_dependencies(instance.metadata)
            if not satisfied:
                return False, message
        
        # Deactivate current version if active
        if module_id in self.active_modules:
            success, message = self.deactivate_module(module_id)
            if not success:
                return False, f"Failed to deactivate current version: {message}"
        
        # Load the module
        try:
            module_object = self._load_module(instance.module_path, module_id)
            
            # Update instance
            instance.module_object = module_object
            instance.status = ModuleStatus.ACTIVE
            instance.activation_time = time.time()
            instance.error_message = ""
            
            # Update active modules
            self.active_modules[module_id] = instance
            
            # Save config
            self._save_config()
            
            return True, f"Module {module_id} v{version} activated successfully"
        except Exception as e:
            instance.status = ModuleStatus.FAILED
            instance.error_message = str(e)
            self._save_config()
            return False, f"Failed to activate module {module_id} v{version}: {e}"
    
    def deactivate_module(self, module_id: str) -> Tuple[bool, str]:
        """
        Deactivate a module.
        
        Args:
            module_id: ID of the module to deactivate
            
        Returns:
            Tuple of (success, message)
        """
        logger.debug(f"Deactivating module {module_id}")
        
        if module_id not in self.active_modules:
            logger.error(f"Module {module_id} is not active. Active modules: {list(self.active_modules.keys())}")
            return False, f"Module {module_id} is not active"
        
        instance = self.active_modules[module_id]
        logger.debug(f"Found active instance: {instance.metadata.module_id} v{instance.metadata.version}")
        
        # Check if other active modules depend on this one
        for other_id, other_instance in self.active_modules.items():
            if other_id == module_id:
                continue
            
            if module_id in other_instance.metadata.dependencies:
                logger.error(f"Cannot deactivate module {module_id}: it is required by {other_id}")
                return False, f"Cannot deactivate module {module_id}: it is required by {other_id}"
        
        try:
            # Unload the module if it has a module object
            if instance.module_object is not None:
                logger.debug(f"Unloading module object for {module_id}")
                self._unload_module(instance.module_object)
            else:
                logger.warning(f"Module {module_id} has no module object to unload")
            
            # Update instance
            instance.status = ModuleStatus.INACTIVE
            instance.module_object = None
            
            # Remove from active modules
            del self.active_modules[module_id]
            
            # Save config
            self._save_config()
            
            logger.info(f"Module {module_id} deactivated successfully")
            return True, f"Module {module_id} deactivated successfully"
        except Exception as e:
            logger.error(f"Failed to deactivate module {module_id}: {e}")
            logger.exception(e)
            return False, f"Failed to deactivate module {module_id}: {e}"
    
    def _check_dependencies(self, metadata: ModuleMetadata) -> Tuple[bool, str]:
        """
        Check if dependencies are satisfied.
        
        Args:
            metadata: Metadata of the module to check
            
        Returns:
            Tuple of (satisfied, message)
        """
        for dep_id, version_constraint in metadata.dependencies.items():
            # Check if dependency is active
            if dep_id not in self.active_modules:
                return False, f"Dependency {dep_id} is not active"
            
            # Check version constraint
            active_version = str(self.active_modules[dep_id].metadata.version)
            if not self._version_satisfies_constraint(active_version, version_constraint):
                return False, f"Dependency {dep_id} version {active_version} does not satisfy constraint {version_constraint}"
        
        return True, "All dependencies satisfied"
    
    def _version_satisfies_constraint(self, version: str, constraint: str) -> bool:
        """
        Check if a version satisfies a constraint.
        
        Args:
            version: Version string to check
            constraint: Version constraint string
            
        Returns:
            True if the version satisfies the constraint, False otherwise
        """
        logger.debug(f"Checking if version {version} satisfies constraint {constraint}")
        try:
            # Handle complex constraints with spaces (e.g., ">=1.0.0 <2.0.0")
            if " " in constraint:
                constraints = constraint.split()
                logger.debug(f"Split complex constraint into: {constraints}")
                return all(self._version_satisfies_constraint(version, c) for c in constraints)
            
            result = semver.match(version, constraint)
            logger.debug(f"semver.match result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error checking version constraint: {e}")
            logger.exception(e)
            return False
    
    def _load_module(self, module_path: str, module_id: str) -> Any:
        """
        Load a module from a path.
        
        Args:
            module_path: Path to the module directory
            module_id: ID of the module
            
        Returns:
            The loaded module object
        """
        # Check if module directory exists
        if not os.path.exists(module_path):
            raise FileNotFoundError(f"Module directory {module_path} not found")
        
        # Check for main module file
        main_file = os.path.join(module_path, "main.py")
        if not os.path.exists(main_file):
            raise FileNotFoundError(f"Main module file {main_file} not found")
        
        # Add module directory to Python path
        if module_path not in sys.path:
            sys.path.insert(0, module_path)
        
        # Load the module
        module_name = f"godelOS_module_{module_id}"
        spec = importlib.util.spec_from_file_location(module_name, main_file)
        if spec is None:
            raise ImportError(f"Failed to create module spec for {main_file}")
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        return module
    
    def _unload_module(self, module_object: Any) -> None:
        """
        Unload a module.
        
        Args:
            module_object: The module object to unload
        """
        logger.debug(f"Unloading module object: {module_object}")
        
        try:
            # Call cleanup method if available
            if hasattr(module_object, "cleanup") and callable(module_object.cleanup):
                logger.debug("Calling cleanup method")
                module_object.cleanup()
            
            # Remove from sys.modules
            if hasattr(module_object, "__name__"):
                module_name = module_object.__name__
                logger.debug(f"Module name: {module_name}")
                if module_name in sys.modules:
                    logger.debug(f"Removing {module_name} from sys.modules")
                    del sys.modules[module_name]
            else:
                logger.warning("Module object has no __name__ attribute")
        except Exception as e:
            logger.error(f"Error unloading module: {e}")
            logger.exception(e)
    
    def get_active_modules(self) -> Dict[str, ModuleMetadata]:
        """
        Get all active modules.
        
        Returns:
            Dictionary mapping module IDs to their metadata
        """
        return {module_id: instance.metadata for module_id, instance in self.active_modules.items()}
    
    def add_module(self, module_dir: str) -> Tuple[bool, str]:
        """
        Add a module to the library from a directory.
        
        Args:
            module_dir: Path to the module directory
            
        Returns:
            Tuple of (success, message)
        """
        logger.debug(f"Adding module from directory: {module_dir}")
        
        # Check if directory exists
        if not os.path.exists(module_dir):
            return False, f"Module directory {module_dir} not found"
        
        # Check for metadata file
        metadata_path = os.path.join(module_dir, "metadata.json")
        if not os.path.exists(metadata_path):
            return False, f"Metadata file not found in {module_dir}"
        
        # Check for main.py file
        main_py_path = os.path.join(module_dir, "main.py")
        if not os.path.exists(main_py_path):
            return False, f"main.py file not found in {module_dir}"
        
        try:
            # Load metadata
            with open(metadata_path, 'r') as f:
                metadata_dict = json.load(f)
            
            logger.debug(f"Loaded metadata: {metadata_dict}")
            metadata = ModuleMetadata.from_dict(metadata_dict)
            module_id = metadata.module_id
            version_str = str(metadata.version)
            
            # Calculate checksum
            checksum = self._calculate_module_checksum(module_dir)
            metadata.checksum = checksum
            
            # Create module destination directory
            dest_dir = os.path.join(self.modules_directory, f"{module_id}_{version_str.replace('.', '_')}")
            os.makedirs(dest_dir, exist_ok=True)
            
            # Copy module files to destination
            for item in os.listdir(module_dir):
                src_path = os.path.join(module_dir, item)
                dst_path = os.path.join(dest_dir, item)
                
                if os.path.isdir(src_path):
                    shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
                else:
                    shutil.copy2(src_path, dst_path)
            
            # Add to registry
            if module_id not in self.modules:
                self.modules[module_id] = {}
            
            self.modules[module_id][version_str] = ModuleInstance(
                metadata=metadata,
                module_path=dest_dir
            )
            
            # Save updated registry
            self._save_config()
            
            logger.info(f"Added module {module_id} v{version_str} to library")
            return True, f"Module {module_id} v{version_str} added successfully"
            
        except Exception as e:
            logger.error(f"Error adding module from {module_dir}: {e}")
            logger.exception(e)
            return False, f"Failed to add module: {e}"
    
    def remove_module(self, module_id: str, version: str) -> Tuple[bool, str]:
        """
        Remove a module from the library.
        
        Args:
            module_id: ID of the module to remove
            version: Version of the module to remove
            
        Returns:
            Tuple of (success, message)
        """
        logger.debug(f"Removing module {module_id} v{version}")
        
        # Check if module exists
        if module_id not in self.modules:
            return False, f"Module {module_id} not found"
        
        if version not in self.modules[module_id]:
            return False, f"Version {version} not found for module {module_id}"
        
        # Check if module is active
        if module_id in self.active_modules and str(self.active_modules[module_id].metadata.version) == version:
            return False, f"Cannot remove active module {module_id} v{version}. Deactivate it first."
        
        try:
            # Get module instance
            instance = self.modules[module_id][version]
            
            # Remove module directory
            if os.path.exists(instance.module_path):
                shutil.rmtree(instance.module_path)
            
            # Remove from registry
            del self.modules[module_id][version]
            
            # If no more versions, remove module entry
            if not self.modules[module_id]:
                del self.modules[module_id]
            
            # Save updated registry
            self._save_config()
            
            logger.info(f"Removed module {module_id} v{version} from library")
            return True, f"Module {module_id} v{version} removed successfully"
            
        except Exception as e:
            logger.error(f"Error removing module {module_id} v{version}: {e}")
            logger.exception(e)
            return False, f"Failed to remove module: {e}"
    
    def get_module_status(self, module_id: str, version: Optional[str] = None) -> Optional[ModuleStatus]:
        """
        Get the status of a module.
        
        Args:
            module_id: ID of the module
            version: Optional version string (if None, returns status of the latest version)
            
        Returns:
            Module status if found, None otherwise
        """
        if module_id not in self.modules:
            return None
        
        if version is None:
            # Return active version status if available
            if module_id in self.active_modules:
                return self.active_modules[module_id].status
            
            # Otherwise, return latest version status
            latest_version = self._get_latest_version(module_id)
            if latest_version:
                return self.modules[module_id][latest_version].status
            
            return None
        
        if version not in self.modules[module_id]:
            return None
        
        return self.modules[module_id][version].status
    
    def rollback_module(self, module_id: str, target_version: Optional[str] = None) -> Tuple[bool, str]:
        """
        Rollback a module to a previous version.
        
        Args:
            module_id: ID of the module to rollback
            target_version: Optional target version (if None, rolls back to the previous version)
            
        Returns:
            Tuple of (success, message)
        """
        logger.debug(f"Rolling back module {module_id} to target_version={target_version}")
        
        if module_id not in self.modules:
            logger.error(f"Module {module_id} not found in modules: {list(self.modules.keys())}")
            return False, f"Module {module_id} not found"
        
        if module_id not in self.active_modules:
            logger.error(f"Module {module_id} is not active. Active modules: {list(self.active_modules.keys())}")
            return False, f"Module {module_id} is not active"
        
        current_version = str(self.active_modules[module_id].metadata.version)
        logger.debug(f"Current version of module {module_id}: {current_version}")
        
        # Determine target version
        if target_version is None:
            # Get all versions
            versions = list(self.modules[module_id].keys())
            logger.debug(f"Available versions for module {module_id}: {versions}")
            
            # Sort versions using semver
            sorted_versions = sorted(versions, key=lambda v: semver.VersionInfo.parse(v), reverse=True)
            logger.debug(f"Sorted versions: {sorted_versions}")
            
            # Find the version before the current one
            try:
                current_index = sorted_versions.index(current_version)
                logger.debug(f"Current version index: {current_index}")
                
                if current_index == len(sorted_versions) - 1:
                    logger.error(f"No previous version available for module {module_id}")
                    return False, f"No previous version available for module {module_id}"
                
                target_version = sorted_versions[current_index + 1]
                logger.debug(f"Selected target version: {target_version}")
            except ValueError:
                logger.error(f"Current version {current_version} not found in available versions")
                return False, f"Current version {current_version} not found in available versions"
        elif target_version not in self.modules[module_id]:
            logger.error(f"Target version {target_version} not found for module {module_id}")
            return False, f"Target version {target_version} not found for module {module_id}"
        
        # Activate the target version
        logger.debug(f"Activating target version {target_version} for module {module_id}")
        success, message = self.activate_module(module_id, target_version)
        logger.debug(f"Activation result: success={success}, message={message}")
        return success, message