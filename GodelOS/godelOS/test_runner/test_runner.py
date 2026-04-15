"""
Test Runner Module for the GödelOS Test Runner.

This module provides the main TestRunner class that orchestrates the testing
process by coordinating the various components of the test runner.
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Callable, Tuple, Union

from godelOS.test_runner.config_manager import ConfigurationManager, TestRunnerConfig
from godelOS.test_runner.test_discovery import TestDiscovery
from godelOS.test_runner.test_categorizer import TestCategorizer
from godelOS.test_runner.pytest_wrapper import PyTestWrapper, TestResult
from godelOS.test_runner.output_manager import OutputManager, OutputLevel
from godelOS.test_runner.console_formatter import ConsoleFormatter
from godelOS.test_runner.results_collector import ResultsCollector, EnhancedTestResult
from godelOS.test_runner.timing_tracker import TimingTracker
from godelOS.test_runner.statistics_collector import StatisticsCollector, TestStatistics
from godelOS.test_runner.docstring_extractor import DocstringExtractor
from godelOS.test_runner.html_report_generator import HTMLReportGenerator
from godelOS.test_runner.json_report_generator import JSONReportGenerator


class TestRunner:
    """
    Main orchestrator class for the GödelOS Test Runner.
    
    This class coordinates the testing process by managing the configuration,
    test discovery, categorization, and execution components.
    """
    
    def __init__(self, config_path: Optional[str] = None, cli_args: Optional[List[str]] = None):
        """
        Initialize the TestRunner.
        
        Args:
            config_path: Optional path to a configuration file.
            cli_args: Optional list of command line arguments.
        """
        # Initialize configuration
        self.config_manager = ConfigurationManager(config_path)
        self.config = self.config_manager.load_config(cli_args)
        
        # Initialize components
        self.test_discovery = TestDiscovery(self.config)
        self.test_categorizer = TestCategorizer(self.config)
        self.pytest_wrapper = PyTestWrapper(self.config)
        
        # Initialize output formatting components
        self.output_manager = OutputManager(self.config)
        self.console_formatter = ConsoleFormatter(self.config)
        self.output_manager.register_formatter("console", self.console_formatter)
        
        # Initialize report generators if enabled
        if hasattr(self.config, 'generate_html_report') and self.config.generate_html_report:
            self.html_report_generator = HTMLReportGenerator(self.config)
            
        if hasattr(self.config, 'generate_json_report') and self.config.generate_json_report:
            self.json_report_generator = JSONReportGenerator(self.config)
            
        # Initialize docstring extractor
        self.docstring_extractor = DocstringExtractor(self.config)
        
        # Initialize results collection and statistics components
        self.results_collector = ResultsCollector(self.config)
        self.timing_tracker = TimingTracker(self.config)
        self.statistics_collector = StatisticsCollector(
            self.config, self.results_collector, self.timing_tracker
        )
        
        # Initialize state
        self.discovered_tests = {}
        self.categorized_tests = {}
        self.test_results = {}
        self.start_time = None
        self.end_time = None
    
    def discover_tests(self) -> Dict[str, Dict[str, Any]]:
        """
        Discover tests in the project.
        
        Returns:
            A dictionary mapping file paths to test file information.
        """
        self.discovered_tests = self.test_discovery.discover_and_parse_tests()
        return self.discovered_tests
    
    def categorize_tests(self) -> Dict[str, List[str]]:
        """
        Categorize discovered tests.
        
        Returns:
            A dictionary mapping category names to lists of test node IDs.
        """
        if not self.discovered_tests:
            self.discover_tests()
            
        self.categorized_tests = self.test_categorizer.categorize_tests(self.discovered_tests)
        return self.categorized_tests
    
    def run_tests(self, categories: Optional[List[str]] = None) -> Dict[str, Dict[str, TestResult]]:
        """
        Run tests in specified categories.
        
        Args:
            categories: Optional list of categories to run. If None, all categories are run.
            
        Returns:
            A dictionary mapping category names to dictionaries of test results.
        """
        # Ensure tests are discovered and categorized
        if not self.categorized_tests:
            self.categorize_tests()
            
        # Determine which categories to run
        if categories is None:
            categories_to_run = list(self.categorized_tests.keys())
        else:
            categories_to_run = [cat for cat in categories if cat in self.categorized_tests]
        
        # Count total tests to run
        total_tests = sum(len(self.categorized_tests[cat]) for cat in categories_to_run)
        
        # Print test run header
        self.output_manager.print(f"Running {total_tests} tests in {len(categories_to_run)} categories",
                                level=OutputLevel.MINIMAL,
                                formatter="console",
                                status="header")
        
        # Start progress indicator
        self.output_manager.start_progress(total_tests)
        
        # Record start time
        self.start_time = datetime.now()
        
        # Start timing and results collection
        self.timing_tracker.start_run()
        self.results_collector.start_test_run()
        
        # Initialize results dictionary
        self.test_results = {}
        tests_completed = 0
        
        # Run tests for each category
        for category in categories_to_run:
            node_ids = self.categorized_tests[category]
            if not node_ids:
                continue
                
            self.output_manager.print(f"\nCategory: {category} ({len(node_ids)} tests)",
                                    level=OutputLevel.NORMAL,
                                    formatter="console",
                                    status="header")
            
            # Start timing for this category
            self.timing_tracker.start_category(category)
            
            # Run tests for this category
            category_results = {}
            for node_id in node_ids:
                # Print test start
                self.output_manager.print_test_start(node_id)
                
                # Start timing for this test
                self.timing_tracker.start_test(node_id)
                
                # Print execution phase header if phase separation is enabled
                if hasattr(self.config, 'show_phase_separation') and self.config.show_phase_separation:
                    self.output_manager.print(self.console_formatter.format_phase_header("Execution"),
                                            level=OutputLevel.NORMAL,  # Changed from VERBOSE to NORMAL for better visibility
                                            formatter=None)
                
                # Run the test
                result = self.pytest_wrapper._run_single_test(node_id)
                
                # Print teardown phase header if phase separation is enabled
                if hasattr(self.config, 'show_phase_separation') and self.config.show_phase_separation:
                    self.output_manager.print(self.console_formatter.format_phase_header("Teardown"),
                                            level=OutputLevel.NORMAL,  # Changed from VERBOSE to NORMAL for better visibility
                                            formatter=None)
                
                # End timing for this test
                test_duration = self.timing_tracker.end_test(node_id)
                
                # Add timing information to result with more realistic distribution
                # In a real implementation, we would measure these phases separately
                if hasattr(result, 'setup_time'):
                    # Improved approximation based on typical test phase distribution
                    if test_duration < 0.1:  # Very fast tests
                        result.setup_time = test_duration * 0.3
                        result.execution_time = test_duration * 0.6
                        result.teardown_time = test_duration * 0.1
                    elif test_duration > 1.0:  # Slower tests
                        result.setup_time = test_duration * 0.15
                        result.execution_time = test_duration * 0.8
                        result.teardown_time = test_duration * 0.05
                    else:  # Medium duration tests
                        result.setup_time = test_duration * 0.2
                        result.execution_time = test_duration * 0.7
                        result.teardown_time = test_duration * 0.1
                
                # Collect and enhance the result
                enhanced_result = self.results_collector.collect_result(result, category)
                
                # Store the result
                category_results[node_id] = result
                
                # Print test result
                self.output_manager.print_test_result(result)
                
                # Update progress
                tests_completed += 1
                self.output_manager.update_progress(tests_completed, result.outcome)
            
            # End timing for this category
            self.timing_tracker.end_category(category)
            
            self.test_results[category] = category_results
        
        # Finish progress indicator
        self.output_manager.finish_progress()
        
        # Record end time
        self.end_time = datetime.now()
        
        # End timing and results collection
        self.timing_tracker.end_run()
        self.results_collector.end_test_run()
        
        # Calculate statistics
        statistics = self.statistics_collector.calculate_statistics()
        
        # Get test summary
        summary = self.get_test_summary()
        
        # Add results to summary for HTML report
        summary['results'] = self.test_results
        
        # Print summary
        self.output_manager.print_summary(summary)

        # Print failing tests grouped by module
        self.print_failing_tests_by_module()
        
        return self.test_results
    
    def print_failing_tests_by_module(self):
        """
        Print a summary of failing tests grouped by module (file).
        """
        from collections import defaultdict

        all_results = self.results_collector.get_all_results()
        failures_by_module = defaultdict(list)

        for node_id, result in all_results.items():
            # Outcome might be 'failed', 'error', etc. Adjust as needed.
            if hasattr(result, 'outcome') and result.outcome == 'failed':
                # Extract module (file path before '::')
                module = node_id.split("::")[0]
                failures_by_module[module].append(node_id)

        if failures_by_module:
            self.output_manager.print(
                "\nFailing tests grouped by module:",
                level=OutputLevel.MINIMAL,
                formatter="console",
                status="header"
            )
            for module, failures in sorted(failures_by_module.items(), key=lambda x: len(x[1]), reverse=True):
                self.output_manager.print(
                    f"  {module}: {len(failures)} failing test(s)",
                    level=OutputLevel.MINIMAL,
                    formatter="console"
                )
                for node_id in failures:
                    self.output_manager.print(
                        f"    - {node_id}",
                        level=OutputLevel.MINIMAL,
                        formatter="console"
                    )
        else:
            self.output_manager.print(
                "\nNo failing tests detected.",
                level=OutputLevel.MINIMAL,
                formatter="console"
            )

    def run_specific_tests(self, node_ids: List[str]) -> Dict[str, TestResult]:
        """
        Run specific tests by node ID.
        
        Args:
            node_ids: List of pytest node IDs to run.
            
        Returns:
            A dictionary mapping node IDs to TestResult objects.
        """
        if not node_ids:
            self.output_manager.print("No tests to run",
                                    level=OutputLevel.MINIMAL,
                                    formatter="console",
                                    status="warning")
            return {}
        
        # Print test run header
        self.output_manager.print(f"Running {len(node_ids)} specific tests",
                                level=OutputLevel.MINIMAL,
                                formatter="console",
                                status="header")
        
        # Start progress indicator
        self.output_manager.start_progress(len(node_ids))
        
        # Record start time
        self.start_time = datetime.now()
        
        # Start timing and results collection
        self.timing_tracker.start_run()
        self.results_collector.start_test_run()
        
        # Run tests
        results = {}
        tests_completed = 0
        
        for node_id in node_ids:
            # Print test start
            self.output_manager.print_test_start(node_id)
            
            # Start timing for this test
            self.timing_tracker.start_test(node_id)
            
            # Run the test
            result = self.pytest_wrapper._run_single_test(node_id)
            
            # End timing for this test
            test_duration = self.timing_tracker.end_test(node_id)
            
            # Collect and enhance the result
            enhanced_result = self.results_collector.collect_result(result)
            
            # Store the result
            results[node_id] = result
            
            # Print test result
            self.output_manager.print_test_result(result)
            
            # Update progress
            tests_completed += 1
            self.output_manager.update_progress(tests_completed, result.outcome)
        
        # Finish progress indicator
        self.output_manager.finish_progress()
        
        # Record end time
        self.end_time = datetime.now()
        
        # End timing and results collection
        self.timing_tracker.end_run()
        self.results_collector.end_test_run()
        
        # Update test results
        self.test_results = {'specific': results}
        
        # Calculate statistics
        statistics = self.statistics_collector.calculate_statistics()
        
        # Get test summary
        summary = self.get_test_summary()
        
        # Add results to summary for HTML report
        summary['results'] = results
        
        # Print summary
        self.output_manager.print_summary(summary)
        
        return results
    
    def run_by_pattern(self, pattern: str) -> Dict[str, TestResult]:
        """
        Run tests matching a pattern.
        
        Args:
            pattern: Glob pattern to match against test node IDs.
            
        Returns:
            A dictionary mapping node IDs to TestResult objects.
        """
        # Ensure tests are discovered
        if not self.discovered_tests:
            self.output_manager.print("Discovering tests...",
                                    level=OutputLevel.NORMAL,
                                    formatter="console",
                                    status="info")
            self.discover_tests()
            
        # Filter tests by pattern
        self.output_manager.print(f"Filtering tests using pattern: {pattern}",
                                level=OutputLevel.NORMAL,
                                formatter="console",
                                status="info")
        node_ids = self.test_discovery.filter_tests_by_pattern(pattern)
        
        if not node_ids:
            self.output_manager.print(f"No tests found matching pattern: {pattern}",
                                    level=OutputLevel.MINIMAL,
                                    formatter="console",
                                    status="warning")
            return {}
            
        self.output_manager.print(f"Found {len(node_ids)} tests matching pattern",
                                level=OutputLevel.NORMAL,
                                formatter="console",
                                status="info")
        
        # Run filtered tests
        return self.run_specific_tests(node_ids)
    
    def get_test_summary(self) -> Dict[str, Any]:
        """
        Get a summary of test results.
        
        Returns:
            A dictionary containing summary information about the test run.
        """
        if not self.test_results:
            return {
                'status': 'No tests run',
                'total': 0,
                'passed': 0,
                'failed': 0,
                'skipped': 0,
                'error': 0,
                'duration': 0,
            }
        
        # Use statistics collector to get detailed statistics
        stats_summary = self.statistics_collector.get_statistics_summary()
        
        # Calculate overall status
        status = 'passed' if stats_summary.get('failed_tests', 0) == 0 and stats_summary.get('error_tests', 0) == 0 else 'failed'
        
        # Build summary dictionary
        summary = {
            'status': status,
            'total': stats_summary.get('total_tests', 0),
            'passed': stats_summary.get('passed_tests', 0),
            'failed': stats_summary.get('failed_tests', 0),
            'skipped': stats_summary.get('skipped_tests', 0),
            'error': stats_summary.get('error_tests', 0),
            'duration': stats_summary.get('total_duration', 0),
            'total_duration': self.timing_tracker.get_total_duration(),
            'start_time': self.start_time,
            'end_time': self.end_time,
            'average_duration': stats_summary.get('average_duration', 0),
            'slowest_tests': stats_summary.get('slowest_tests', []),
        }
        
        # Add category statistics if available
        if 'categories' in stats_summary:
            summary['categories'] = stats_summary['categories']
        
        return summary
    
    def get_failed_tests(self) -> Dict[str, TestResult]:
        """
        Get all failed tests.
        
        Returns:
            A dictionary mapping node IDs to TestResult objects for failed tests.
        """
        # Use results collector to get failed results
        failed_results = self.results_collector.get_failed_results()
        
        # Convert EnhancedTestResult objects back to TestResult objects for backward compatibility
        return {node_id: result for node_id, result in failed_results.items()}
    
    def rerun_failed_tests(self) -> Dict[str, TestResult]:
        """
        Rerun failed tests.
        
        Returns:
            A dictionary mapping node IDs to TestResult objects for the rerun tests.
        """
        self.output_manager.print("Identifying failed tests...",
                                level=OutputLevel.NORMAL,
                                formatter="console",
                                status="info")
        
        failed_tests = self.get_failed_tests()
        
        if not failed_tests:
            self.output_manager.print("No failed tests to rerun",
                                    level=OutputLevel.MINIMAL,
                                    formatter="console",
                                    status="info")
            return {}
        
        self.output_manager.print(f"Rerunning {len(failed_tests)} failed tests",
                                level=OutputLevel.MINIMAL,
                                formatter="console",
                                status="header")
            
        return self.run_specific_tests(list(failed_tests.keys()))
    
    def get_config(self) -> TestRunnerConfig:
        """
        Get the current configuration.
        
        Returns:
            The current TestRunnerConfig object.
        """
        return self.config
    
    def update_config(self, updates: Dict[str, Any]) -> TestRunnerConfig:
        """
        Update the configuration.
        
        Args:
            updates: Dictionary with values to update in the config.
            
        Returns:
            The updated TestRunnerConfig object.
        """
        self.config_manager._update_config(self.config, updates)
        
        # Reinitialize components with updated config
        self.test_discovery = TestDiscovery(self.config)
        self.test_categorizer = TestCategorizer(self.config)
        self.pytest_wrapper = PyTestWrapper(self.config)
        
        # Reinitialize output formatting components
        if hasattr(self, 'output_manager'):
            self.output_manager.close()  # Close any open file handles
        self.output_manager = OutputManager(self.config)
        self.console_formatter = ConsoleFormatter(self.config)
        self.output_manager.register_formatter("console", self.console_formatter)
        
        # Reinitialize report generators if enabled
        if hasattr(self.config, 'generate_html_report') and self.config.generate_html_report:
            self.html_report_generator = HTMLReportGenerator(self.config)
            
        if hasattr(self.config, 'generate_json_report') and self.config.generate_json_report:
            self.json_report_generator = JSONReportGenerator(self.config)
        
        # Reinitialize docstring extractor
        self.docstring_extractor = DocstringExtractor(self.config)
        
        # Reinitialize results collection and statistics components
        self.results_collector = ResultsCollector(self.config)
        self.timing_tracker = TimingTracker(self.config)
        self.statistics_collector = StatisticsCollector(
            self.config, self.results_collector, self.timing_tracker
        )
        
        return self.config