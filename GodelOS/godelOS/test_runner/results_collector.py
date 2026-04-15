"""
Results Collector Module for the GödelOS Test Runner.

This module provides functionality to collect, structure, and store test results
from pytest executions.
"""

import json
import os
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Callable, Tuple, Union

from godelOS.test_runner.pytest_wrapper import TestResult


@dataclass
class EnhancedTestResult(TestResult):
    """
    Enhanced data class representing a test result with additional metadata.
    
    Extends the basic TestResult class with additional fields for more detailed
    analysis and reporting, including docstring information and test phase timing.
    """
    
    # Test metadata
    module_name: Optional[str] = None
    class_name: Optional[str] = None
    function_name: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    # Timing information
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    # Historical data
    previous_outcomes: List[str] = field(default_factory=list)
    previous_durations: List[float] = field(default_factory=list)
    
    # Additional test data
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Docstring information (new)
    docstring: Optional[str] = None
    parsed_docstring: Dict[str, str] = field(default_factory=dict)  # Purpose, expected behavior, edge cases
    
    # Test phases (new)
    setup_time: Optional[float] = None
    execution_time: Optional[float] = None
    teardown_time: Optional[float] = None
    
    @classmethod
    def from_test_result(cls, result: TestResult, **kwargs) -> 'EnhancedTestResult':
        """
        Create an EnhancedTestResult from a basic TestResult.
        
        Args:
            result: The basic TestResult to enhance.
            **kwargs: Additional fields to set on the enhanced result.
            
        Returns:
            An EnhancedTestResult object.
        """
        # Extract node_id components
        module_name = None
        class_name = None
        function_name = None
        
        if result.node_id:
            parts = result.node_id.split('::')
            if len(parts) >= 1:
                module_name = parts[0].replace('/', '.').replace('.py', '')
            if len(parts) >= 2:
                if '[' in parts[1]:
                    # Handle parameterized tests
                    class_or_func = parts[1].split('[')[0]
                else:
                    class_or_func = parts[1]
                
                # Check if this is a class or function
                if len(parts) >= 3:
                    class_name = class_or_func
                    function_name = parts[2].split('[')[0] if '[' in parts[2] else parts[2]
                else:
                    function_name = class_or_func
        
        # Create the enhanced result
        enhanced = cls(
            node_id=result.node_id,
            outcome=result.outcome,
            duration=result.duration,
            message=result.message,
            traceback=result.traceback,
            stdout=result.stdout,
            stderr=result.stderr,
            exception=result.exception,
            module_name=module_name,
            class_name=class_name,
            function_name=function_name,
            **kwargs
        )
        
        return enhanced
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the test result to a dictionary suitable for serialization.
        
        Returns:
            A dictionary representation of the test result.
        """
        # Convert to dict using dataclasses.asdict
        result_dict = asdict(self)
        
        # Handle non-serializable objects
        if 'exception' in result_dict and result_dict['exception'] is not None:
            result_dict['exception'] = str(result_dict['exception'])
        
        # Convert datetime objects to ISO format strings
        if result_dict['start_time']:
            result_dict['start_time'] = result_dict['start_time'].isoformat()
        if result_dict['end_time']:
            result_dict['end_time'] = result_dict['end_time'].isoformat()
            
        # Handle parsed_docstring if it contains complex objects
        if 'parsed_docstring' in result_dict:
            for key, value in result_dict['parsed_docstring'].items():
                if not isinstance(value, (str, int, float, bool, type(None))):
                    result_dict['parsed_docstring'][key] = str(value)
        
        return result_dict


class ResultsCollector:
    """
    Collects and structures test results from pytest executions.
    
    This class is responsible for collecting test results, enhancing them with
    additional metadata, and providing methods to query and analyze the results.
    """
    
    def __init__(self, config: Any):
        """
        Initialize the ResultsCollector.
        
        Args:
            config: Configuration object containing result collection settings.
        """
        self.config = config
        self.results: Dict[str, EnhancedTestResult] = {}
        self.categorized_results: Dict[str, Dict[str, EnhancedTestResult]] = {}
        self.run_start_time: Optional[datetime] = None
        self.run_end_time: Optional[datetime] = None
        
        # Initialize storage directory if specified
        self.storage_dir = None
        if hasattr(config, 'results_dir') and config.results_dir:
            self.storage_dir = Path(config.results_dir)
            os.makedirs(self.storage_dir, exist_ok=True)
    
    def start_test_run(self) -> None:
        """
        Mark the start of a test run.
        
        This should be called before any tests are executed.
        """
        self.run_start_time = datetime.now()
        self.results = {}
        self.categorized_results = {}
    
    def end_test_run(self) -> None:
        """
        Mark the end of a test run.
        
        This should be called after all tests have been executed.
        """
        self.run_end_time = datetime.now()
        
        # Save results if storage is configured
        if self.storage_dir:
            self.save_results()
    
    def collect_result(self, result: TestResult, category: Optional[str] = None) -> EnhancedTestResult:
        """
        Collect and enhance a test result.
        
        Args:
            result: The TestResult to collect.
            category: Optional category the test belongs to.
            
        Returns:
            The enhanced test result.
        """
        # Create enhanced result
        enhanced_result = EnhancedTestResult.from_test_result(
            result,
            category=category,
            end_time=datetime.now()
        )
        
        # Store the result
        self.results[result.node_id] = enhanced_result
        
        # Store by category if provided
        if category:
            if category not in self.categorized_results:
                self.categorized_results[category] = {}
            self.categorized_results[category][result.node_id] = enhanced_result
        
        return enhanced_result
    
    def get_result(self, node_id: str) -> Optional[EnhancedTestResult]:
        """
        Get a test result by node ID.
        
        Args:
            node_id: The pytest node ID of the test.
            
        Returns:
            The test result, or None if not found.
        """
        return self.results.get(node_id)
    
    def get_results_by_category(self, category: str) -> Dict[str, EnhancedTestResult]:
        """
        Get all test results for a category.
        
        Args:
            category: The category to get results for.
            
        Returns:
            A dictionary mapping node IDs to test results.
        """
        return self.categorized_results.get(category, {})
    
    def get_all_results(self) -> Dict[str, EnhancedTestResult]:
        """
        Get all collected test results.
        
        Returns:
            A dictionary mapping node IDs to test results.
        """
        return self.results
    
    def get_run_duration(self) -> Optional[float]:
        """
        Get the total duration of the test run in seconds.
        
        Returns:
            The duration in seconds, or None if the run is not complete.
        """
        if self.run_start_time and self.run_end_time:
            return (self.run_end_time - self.run_start_time).total_seconds()
        return None
    
    def save_results(self, path: Optional[str] = None) -> str:
        """
        Save the test results to a JSON file.
        
        Args:
            path: Optional path to save the results to. If not provided,
                 a default path in the storage directory will be used.
                 
        Returns:
            The path where the results were saved.
        """
        if not path and not self.storage_dir:
            raise ValueError("No path provided and no storage directory configured")
        
        # Generate default path if not provided
        if not path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = self.storage_dir / f"test_results_{timestamp}.json"
        
        # Convert results to serializable format
        serializable_results = {
            'run_info': {
                'start_time': self.run_start_time.isoformat() if self.run_start_time else None,
                'end_time': self.run_end_time.isoformat() if self.run_end_time else None,
                'duration': self.get_run_duration(),
            },
            'results': {node_id: result.to_dict() for node_id, result in self.results.items()},
            'categories': {
                category: list(results.keys())
                for category, results in self.categorized_results.items()
            }
        }
        
        # Write to file
        with open(path, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        return str(path)
    
    def load_results(self, path: str) -> Dict[str, Any]:
        """
        Load test results from a JSON file.
        
        Args:
            path: Path to the JSON file to load.
            
        Returns:
            A dictionary containing the loaded results.
        """
        with open(path, 'r') as f:
            data = json.load(f)
        
        # TODO: Convert the loaded data back to EnhancedTestResult objects
        # This would require parsing the JSON and recreating the objects
        
        return data
    
    def filter_results(self, predicate: Callable[[EnhancedTestResult], bool]) -> Dict[str, EnhancedTestResult]:
        """
        Filter test results using a predicate function.
        
        Args:
            predicate: A function that takes a test result and returns a boolean.
            
        Returns:
            A dictionary of test results that match the predicate.
        """
        return {
            node_id: result
            for node_id, result in self.results.items()
            if predicate(result)
        }
    
    def get_failed_results(self) -> Dict[str, EnhancedTestResult]:
        """
        Get all failed test results.
        
        Returns:
            A dictionary of failed test results.
        """
        return self.filter_results(lambda r: r.outcome in ('failed', 'error'))
    
    def get_passed_results(self) -> Dict[str, EnhancedTestResult]:
        """
        Get all passed test results.
        
        Returns:
            A dictionary of passed test results.
        """
        return self.filter_results(lambda r: r.outcome == 'passed')
    
    def get_skipped_results(self) -> Dict[str, EnhancedTestResult]:
        """
        Get all skipped test results.
        
        Returns:
            A dictionary of skipped test results.
        """
        return self.filter_results(lambda r: r.outcome == 'skipped')