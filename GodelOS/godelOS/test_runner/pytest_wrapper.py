"""
PyTest Wrapper Module for the GödelOS Test Runner.

This module provides an interface to pytest for executing tests and
handling test results.
"""

import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Callable, Tuple, Union

import pytest


@dataclass
class TestResult:
    """Data class representing the result of a test execution."""
    
    node_id: str
    outcome: str  # 'passed', 'failed', 'skipped', 'xfailed', 'xpassed', 'error'
    duration: float
    message: Optional[str] = None
    traceback: Optional[str] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    exception: Optional[Exception] = None


class PyTestWrapper:
    """
    Interface to pytest for executing tests.
    
    This class provides methods to run tests using pytest and collect
    detailed results.
    """
    
    def __init__(self, config: Any):
        """
        Initialize the PyTestWrapper.
        
        Args:
            config: Configuration object containing pytest settings.
        """
        self.config = config
        self.parallel = getattr(config, 'parallel', False)
        self.max_workers = getattr(config, 'max_workers', 1)
        self.timeout = getattr(config, 'timeout', 300)
        self.pytest_args = getattr(config, 'pytest_args', [])
    
    def run_tests(self, node_ids: List[str]) -> Dict[str, TestResult]:
        """
        Run tests using pytest.
        
        Args:
            node_ids: List of pytest node IDs to run.
            
        Returns:
            A dictionary mapping node IDs to TestResult objects.
        """
        if not node_ids:
            return {}
            
        if self.parallel and len(node_ids) > 1:
            return self._run_tests_parallel(node_ids)
        else:
            return self._run_tests_sequential(node_ids)
    
    def _run_tests_sequential(self, node_ids: List[str]) -> Dict[str, TestResult]:
        """
        Run tests sequentially using pytest.
        
        Args:
            node_ids: List of pytest node IDs to run.
            
        Returns:
            A dictionary mapping node IDs to TestResult objects.
        """
        results = {}
        
        for node_id in node_ids:
            result = self._run_single_test(node_id)
            results[node_id] = result
        
        return results
    
    def _run_tests_parallel(self, node_ids: List[str]) -> Dict[str, TestResult]:
        """
        Run tests in parallel using pytest and ThreadPoolExecutor.
        
        Args:
            node_ids: List of pytest node IDs to run.
            
        Returns:
            A dictionary mapping node IDs to TestResult objects.
        """
        results = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_node_id = {
                executor.submit(self._run_single_test, node_id): node_id
                for node_id in node_ids
            }
            
            for future in future_to_node_id:
                node_id = future_to_node_id[future]
                try:
                    result = future.result(timeout=self.timeout)
                    results[node_id] = result
                except Exception as e:
                    # Handle timeout or other exceptions
                    results[node_id] = TestResult(
                        node_id=node_id,
                        outcome='error',
                        duration=0.0,
                        message=f"Error running test: {str(e)}",
                        exception=e
                    )
        
        return results
    
    def _run_single_test(self, node_id: str) -> TestResult:
        """
        Run a single test using pytest.
        
        Args:
            node_id: The pytest node ID to run.
            
        Returns:
            A TestResult object with the test result.
        """
        # DEBUG: Print current working directory and node ID
        print(f"DEBUG: Current working directory: {os.getcwd()}")
        print(f"DEBUG: Running test with node ID: {node_id}")
        
        # Check if this is a node ID with :: separators (file::class::method)
        if "::" in node_id:
            # Extract the file part (before the first ::)
            file_part = node_id.split("::")[0]
            
            # First check if the file exists at the specified path
            if os.path.exists(file_part):
                print(f"DEBUG: Test file exists at specified path: {file_part}")
            else:
                print(f"DEBUG: Test file not found at specified path: {file_part}")
                
                # Check if this is a relative path without directory
                if "/" not in file_part and "\\" not in file_part:
                    # Search for the file in the tests directory and its subdirectories
                    for root, _, files in os.walk("tests"):
                        if file_part in files:
                            full_path = os.path.join(root, file_part)
                            print(f"DEBUG: Found test file at: {full_path}")
                            # Replace the file part in the node ID with the full path
                            node_id = node_id.replace(file_part, full_path)
                            print(f"DEBUG: Updated node ID: {node_id}")
                            break
                    else:
                        print(f"DEBUG: Could not find test file: {file_part}")
        
        # Create a custom pytest plugin to collect results
        class ResultCollector:
            def __init__(self):
                self.result = None
            
            def pytest_runtest_logreport(self, report):
                if report.when == 'call' or (report.when == 'setup' and report.outcome != 'passed'):
                    if self.result is None or report.when == 'call':
                        outcome = report.outcome
                        # Handle xfail and xpass
                        if hasattr(report, 'wasxfail'):
                            if report.outcome == 'passed':
                                outcome = 'xpassed'
                            else:
                                outcome = 'xfailed'
                        
                        # Extract traceback and message if test failed
                        traceback = None
                        message = None
                        if report.outcome != 'passed' and hasattr(report, 'longrepr'):
                            if hasattr(report.longrepr, 'reprtraceback'):
                                traceback = str(report.longrepr)
                            elif isinstance(report.longrepr, tuple) and len(report.longrepr) == 3:
                                _, lineno, message = report.longrepr
                                message = str(message)
                            else:
                                message = str(report.longrepr)
                        
                        # Get stdout and stderr
                        stdout = None
                        stderr = None
                        if hasattr(report, 'capstdout'):
                            stdout = report.capstdout
                        if hasattr(report, 'capstderr'):
                            stderr = report.capstderr
                        
                        self.result = TestResult(
                            node_id=node_id,
                            outcome=outcome,
                            duration=report.duration,
                            message=message,
                            traceback=traceback,
                            stdout=stdout,
                            stderr=stderr
                        )
        
        # Create the result collector
        collector = ResultCollector()
        
        # Prepare pytest arguments
        # When using node IDs, pass the entire node ID to pytest
        if "::" in node_id:
            # For node IDs with ::, use the exact node ID
            pytest_args = [node_id, '-v']
            print(f"DEBUG: Running pytest with exact node ID: {node_id}")
        else:
            # For file paths, just pass the file path
            pytest_args = [node_id, '-v']
            print(f"DEBUG: Running pytest with file path: {node_id}")
        
        # Add custom pytest arguments from config
        pytest_args.extend(self.pytest_args)
        
        # Run pytest with the collector plugin
        start_time = time.time()
        try:
            pytest.main(pytest_args, plugins=[collector])
        except Exception as e:
            # Handle pytest exceptions
            return TestResult(
                node_id=node_id,
                outcome='error',
                duration=time.time() - start_time,
                message=f"Error running pytest: {str(e)}",
                exception=e
            )
        
        # If no result was collected, the test might not exist
        if collector.result is None:
            return TestResult(
                node_id=node_id,
                outcome='error',
                duration=time.time() - start_time,
                message=f"No result collected for {node_id}. The test might not exist."
            )
        
        return collector.result
    
    def run_tests_by_category(self, categorized_tests: Dict[str, List[str]], 
                             categories: Optional[List[str]] = None) -> Dict[str, Dict[str, TestResult]]:
        """
        Run tests by category.
        
        Args:
            categorized_tests: Dictionary mapping category names to lists of test node IDs.
            categories: Optional list of categories to run. If None, all categories are run.
            
        Returns:
            A dictionary mapping category names to dictionaries of test results.
        """
        results = {}
        
        # Determine which categories to run
        if categories is None:
            categories_to_run = list(categorized_tests.keys())
        else:
            categories_to_run = categories
        
        # Run tests for each category
        for category in categories_to_run:
            if category in categorized_tests:
                node_ids = categorized_tests[category]
                if node_ids:
                    category_results = self.run_tests(node_ids)
                    results[category] = category_results
        
        return results
    
    def get_pytest_version(self) -> str:
        """
        Get the version of pytest being used.
        
        Returns:
            The pytest version string.
        """
        return pytest.__version__