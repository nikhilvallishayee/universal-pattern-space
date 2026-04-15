"""
Test Discovery Module for the GödelOS Test Runner.

This module provides functionality to discover test files in the project
based on configurable patterns and directories.
"""

import os
import fnmatch
import importlib.util
import inspect
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any, Callable

import pytest


class TestDiscovery:
    """
    Discovers test files and test functions in the project.
    
    This class is responsible for finding test files based on patterns and
    directories, and for extracting test functions and metadata from those files.
    """
    
    def __init__(self, config: Any):
        """
        Initialize the TestDiscovery.
        
        Args:
            config: Configuration object containing test discovery settings.
        """
        self.test_patterns = getattr(config, 'test_patterns', ['test_*.py'])
        self.test_dirs = getattr(config, 'test_dirs', ['tests'])
        self.discovered_files = []
        self.discovered_tests = {}
    
    def discover_test_files(self) -> List[str]:
        """
        Discover test files in the project.
        
        Returns:
            A list of paths to discovered test files.
        """
        discovered_files = []
        
        # DEBUG: Print current working directory and test directories
        print(f"DEBUG: Test discovery - Current working directory: {os.getcwd()}")
        print(f"DEBUG: Test discovery - Test directories: {self.test_dirs}")
        print(f"DEBUG: Test discovery - Test patterns: {self.test_patterns}")
        
        for test_dir in self.test_dirs:
            if not os.path.exists(test_dir):
                print(f"Warning: Test directory {test_dir} does not exist")
                continue
                
            print(f"DEBUG: Searching for tests in directory: {test_dir}")
            for root, _, files in os.walk(test_dir):
                for pattern in self.test_patterns:
                    matched_files = fnmatch.filter(files, pattern)
                    if matched_files:
                        print(f"DEBUG: Found {len(matched_files)} files matching pattern '{pattern}' in {root}")
                    for filename in matched_files:
                        file_path = os.path.join(root, filename)
                        discovered_files.append(file_path)
                        print(f"DEBUG: Discovered test file: {file_path}")
        
        # Remove duplicates and sort
        self.discovered_files = sorted(set(discovered_files))
        return self.discovered_files
    
    def parse_test_file(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a test file to extract test functions and metadata.
        
        Args:
            file_path: Path to the test file to parse.
            
        Returns:
            A dictionary containing information about the test file and its tests.
        """
        if not os.path.exists(file_path):
            return {'file_path': file_path, 'error': 'File not found'}
        
        try:
            # Import the module
            module_name = os.path.splitext(os.path.basename(file_path))[0]
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec is None or spec.loader is None:
                return {'file_path': file_path, 'error': 'Could not load module spec'}
                
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            # Extract test functions and classes
            test_items = self._extract_test_items(module, file_path)
            
            # Extract module-level docstring
            module_doc = inspect.getdoc(module) or ""
            
            return {
                'file_path': file_path,
                'module_name': module_name,
                'module_doc': module_doc,
                'test_items': test_items
            }
            
        except Exception as e:
            return {
                'file_path': file_path,
                'error': f"Error parsing file: {str(e)}"
            }
    
    def _extract_test_items(self, module: Any, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract test functions and methods from a module.
        
        Args:
            module: The imported module object.
            file_path: Path to the test file.
            
        Returns:
            A list of dictionaries containing information about test items.
        """
        test_items = []
        
        # Get all members of the module
        for name, obj in inspect.getmembers(module):
            # Check if it's a test function
            if name.startswith('test_') and callable(obj):
                test_items.append(self._process_test_function(name, obj, file_path))
            
            # Check if it's a test class
            elif name.startswith('Test') and inspect.isclass(obj):
                # Extract test methods from the class
                for method_name, method in inspect.getmembers(obj, predicate=inspect.isfunction):
                    if method_name.startswith('test_'):
                        test_items.append(self._process_test_method(name, method_name, method, file_path))
        
        return test_items
    
    def _process_test_function(self, name: str, func: Callable, file_path: str) -> Dict[str, Any]:
        """
        Process a test function to extract metadata.
        
        Args:
            name: Name of the test function.
            func: The function object.
            file_path: Path to the test file.
            
        Returns:
            A dictionary containing information about the test function.
        """
        # Get function docstring
        doc = inspect.getdoc(func) or ""
        
        # Get function source code
        try:
            source = inspect.getsource(func)
        except (IOError, TypeError):
            source = "Could not retrieve source code"
        
        # Get function line number
        try:
            line_number = inspect.getsourcelines(func)[1]
        except (IOError, TypeError):
            line_number = 0
        
        # Extract pytest markers
        markers = self._extract_pytest_markers(func)
        
        return {
            'type': 'function',
            'name': name,
            'full_name': f"{os.path.basename(file_path)}::{name}",
            'doc': doc,
            'source': source,
            'line_number': line_number,
            'file_path': file_path,
            'markers': markers
        }
    
    def _process_test_method(self, class_name: str, method_name: str, method: Callable, file_path: str) -> Dict[str, Any]:
        """
        Process a test method to extract metadata.
        
        Args:
            class_name: Name of the test class.
            method_name: Name of the test method.
            method: The method object.
            file_path: Path to the test file.
            
        Returns:
            A dictionary containing information about the test method.
        """
        # Get method docstring
        doc = inspect.getdoc(method) or ""
        
        # Get method source code
        try:
            source = inspect.getsource(method)
        except (IOError, TypeError):
            source = "Could not retrieve source code"
        
        # Get method line number
        try:
            line_number = inspect.getsourcelines(method)[1]
        except (IOError, TypeError):
            line_number = 0
        
        # Extract pytest markers
        markers = self._extract_pytest_markers(method)
        
        return {
            'type': 'method',
            'name': method_name,
            'class_name': class_name,
            'full_name': f"{os.path.basename(file_path)}::{class_name}::{method_name}",
            'doc': doc,
            'source': source,
            'line_number': line_number,
            'file_path': file_path,
            'markers': markers
        }
    
    def _extract_pytest_markers(self, obj: Callable) -> List[str]:
        """
        Extract pytest markers from a test function or method.
        
        Args:
            obj: The function or method object.
            
        Returns:
            A list of marker names.
        """
        markers = []
        
        # Check for pytest markers
        if hasattr(obj, 'pytestmark'):
            for marker in obj.pytestmark:
                if hasattr(marker, 'name'):
                    markers.append(marker.name)
        
        return markers
    
    def discover_and_parse_tests(self) -> Dict[str, Dict[str, Any]]:
        """
        Discover and parse all test files in the project.
        
        Returns:
            A dictionary mapping file paths to test file information.
        """
        # Discover test files
        self.discover_test_files()
        
        # Parse each test file
        test_files_info = {}
        for file_path in self.discovered_files:
            test_files_info[file_path] = self.parse_test_file(file_path)
        
        self.discovered_tests = test_files_info
        return test_files_info
    
    def get_test_node_ids(self) -> List[str]:
        """
        Get pytest node IDs for all discovered tests.
        
        Returns:
            A list of pytest node IDs.
        """
        node_ids = []
        
        for file_info in self.discovered_tests.values():
            if 'error' in file_info:
                continue
                
            for test_item in file_info.get('test_items', []):
                node_ids.append(test_item['full_name'])
        
        return node_ids
    
    def filter_tests_by_pattern(self, pattern: str) -> List[str]:
        """
        Filter tests by a glob pattern.
        
        Args:
            pattern: Glob pattern to match against test node IDs.
            
        Returns:
            A list of matching test node IDs.
        """
        all_node_ids = self.get_test_node_ids()
        return fnmatch.filter(all_node_ids, pattern)