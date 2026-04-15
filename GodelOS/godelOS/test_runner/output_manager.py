"""
Output Manager Module for the GödelOS Test Runner.

This module provides the OutputManager class that controls overall output
configuration and delegates to specific formatters.
"""

import enum
import os
import sys
from typing import Dict, List, Optional, Set, Any, Callable, Tuple, Union, TextIO

from godelOS.test_runner.pytest_wrapper import TestResult
from godelOS.test_runner.html_report_generator import HTMLReportGenerator
from godelOS.test_runner.json_report_generator import JSONReportGenerator


class OutputLevel(enum.Enum):
    """
    Enumeration of output verbosity levels.
    
    Levels:
    - MINIMAL: Only essential information (final summary)
    - NORMAL: Standard information (test progress and results)
    - VERBOSE: Detailed information (including test output)
    - DEBUG: Maximum information (including internal details)
    """
    MINIMAL = 0
    NORMAL = 1
    VERBOSE = 2
    DEBUG = 3


class OutputManager:
    """
    Controls overall output configuration and delegates to specific formatters.
    
    This class is responsible for managing the output of the test runner,
    including selecting appropriate formatters, handling output streams,
    and controlling verbosity levels.
    """
    
    def __init__(self, config: Any):
        """
        Initialize the OutputManager.
        
        Args:
            config: Configuration object containing output settings.
        """
        self.config = config
        self.formatters = {}
        self.output_level = self._determine_output_level()
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        self.file_output = None
        
        # Initialize output file if specified
        if hasattr(config, 'output_dir') and config.output_dir:
            os.makedirs(config.output_dir, exist_ok=True)
            output_file = os.path.join(config.output_dir, 'test_output.log')
            self.file_output = open(output_file, 'w')
            
        # Initialize report generators if enabled
        self.html_report_generator = None
        if hasattr(config, 'generate_html_report') and config.generate_html_report:
            self.html_report_generator = HTMLReportGenerator(config)
            
        self.json_report_generator = None
        if hasattr(config, 'generate_json_report') and config.generate_json_report:
            self.json_report_generator = JSONReportGenerator(config)
    
    def _determine_output_level(self) -> OutputLevel:
        """
        Determine the output level based on configuration.
        
        Returns:
            The appropriate OutputLevel enum value.
        """
        if hasattr(self.config, 'verbose') and self.config.verbose:
            return OutputLevel.VERBOSE
        
        # Check for custom output level in custom_options
        if hasattr(self.config, 'custom_options'):
            if 'output_level' in self.config.custom_options:
                level_str = self.config.custom_options['output_level'].upper()
                try:
                    return OutputLevel[level_str]
                except KeyError:
                    pass  # Fall back to default if invalid
            
            if 'debug' in self.config.custom_options and self.config.custom_options['debug']:
                return OutputLevel.DEBUG
        
        return OutputLevel.NORMAL
    
    def register_formatter(self, name: str, formatter: Any) -> None:
        """
        Register a formatter with the OutputManager.
        
        Args:
            name: Name to identify the formatter.
            formatter: The formatter object to register.
        """
        self.formatters[name] = formatter
    
    def get_formatter(self, name: str) -> Optional[Any]:
        """
        Get a registered formatter by name.
        
        Args:
            name: Name of the formatter to retrieve.
            
        Returns:
            The formatter object, or None if not found.
        """
        return self.formatters.get(name)
    
    def print(self, message: str, level: OutputLevel = OutputLevel.NORMAL, 
              formatter: Optional[str] = None, **kwargs) -> None:
        """
        Print a message at the specified output level.
        
        Args:
            message: The message to print.
            level: The minimum output level at which to print the message.
            formatter: Optional name of formatter to use for formatting the message.
            **kwargs: Additional arguments to pass to the formatter.
        """
        if level.value > self.output_level.value:
            return  # Skip if message's level is higher than current output level
        
        # Apply formatting if a formatter is specified
        if formatter and formatter in self.formatters:
            message = self.formatters[formatter].format_text(message, **kwargs)
        
        # Write to stdout
        print(message, file=self.stdout)
        
        # Write to file if configured
        if self.file_output:
            # Strip ANSI color codes for file output
            clean_message = self._strip_ansi_codes(message)
            print(clean_message, file=self.file_output)
    
    def print_error(self, message: str, level: OutputLevel = OutputLevel.NORMAL, 
                   formatter: Optional[str] = None, **kwargs) -> None:
        """
        Print an error message at the specified output level.
        
        Args:
            message: The error message to print.
            level: The minimum output level at which to print the message.
            formatter: Optional name of formatter to use for formatting the message.
            **kwargs: Additional arguments to pass to the formatter.
        """
        if level.value > self.output_level.value:
            return  # Skip if message's level is higher than current output level
        
        # Apply formatting if a formatter is specified
        if formatter and formatter in self.formatters:
            message = self.formatters[formatter].format_text(message, error=True, **kwargs)
        
        # Write to stderr
        print(message, file=self.stderr)
        
        # Write to file if configured
        if self.file_output:
            # Strip ANSI color codes for file output
            clean_message = self._strip_ansi_codes(message)
            print(clean_message, file=self.file_output)
    
    def _strip_ansi_codes(self, text: str) -> str:
        """
        Strip ANSI color codes from text for plain file output.
        
        Args:
            text: The text containing ANSI codes.
            
        Returns:
            The text with ANSI codes removed.
        """
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)
    
    def print_test_start(self, test_id: str) -> None:
        """
        Print a message indicating a test is starting.
        
        Args:
            test_id: The ID of the test that is starting.
        """
        self.print(f"Starting test: {test_id}",
                   level=OutputLevel.NORMAL,
                   formatter="console",
                   status="running")
                   
        # Print setup phase header if phase separation is enabled
        if hasattr(self.config, 'show_phase_separation') and self.config.show_phase_separation:
            console_formatter = self.get_formatter("console")
            if console_formatter and hasattr(console_formatter, 'format_phase_header'):
                self.print(console_formatter.format_phase_header("Setup"),
                          level=OutputLevel.VERBOSE,
                          formatter=None)
    
    def print_test_result(self, result: TestResult) -> None:
        """
        Print the result of a test.
        
        Args:
            result: The TestResult object containing the test result.
        """
        # Format the basic result
        self.print(f"Test {result.node_id}: {result.outcome.upper()} ({result.duration:.2f}s)",
                   level=OutputLevel.NORMAL,
                   formatter="console",
                   status=result.outcome)
        
        # Print docstring details if available and enabled
        console_formatter = self.get_formatter("console")
        if (hasattr(self.config, 'show_docstrings') and self.config.show_docstrings and
            console_formatter and hasattr(console_formatter, 'format_test_details') and
            hasattr(result, 'parsed_docstring')):
            details = console_formatter.format_test_details(result)
            if details:
                self.print(details,
                          level=OutputLevel.NORMAL,
                          formatter=None)
        
        # Print additional details for non-passing tests
        if result.outcome not in ('passed', 'skipped') and self.output_level.value >= OutputLevel.NORMAL.value:
            if result.message:
                self.print(f"  Message: {result.message}",
                           level=OutputLevel.NORMAL,
                           formatter="console",
                           status="info")
            
            if result.traceback and self.output_level.value >= OutputLevel.VERBOSE.value:
                self.print(f"  Traceback:\n{result.traceback}",
                           level=OutputLevel.VERBOSE,
                           formatter="console",
                           status="info")
        
        # Print stdout/stderr in verbose mode
        if self.output_level.value >= OutputLevel.VERBOSE.value:
            if result.stdout:
                self.print(f"  Stdout:\n{result.stdout}",
                           level=OutputLevel.VERBOSE,
                           formatter="console",
                           status="info")
            
            if result.stderr:
                self.print(f"  Stderr:\n{result.stderr}",
                           level=OutputLevel.VERBOSE,
                           formatter="console",
                           status="info")
    
    def print_summary(self, summary: Dict[str, Any]) -> None:
        """
        Print a summary of test results.
        
        Args:
            summary: Dictionary containing summary information.
        """
        status = summary.get('status', 'unknown')
        total = summary.get('total', 0)
        passed = summary.get('passed', 0)
        failed = summary.get('failed', 0)
        skipped = summary.get('skipped', 0)
        error = summary.get('error', 0)
        duration = summary.get('total_duration', 0)
        
        # Print overall status
        self.print("\n=== Test Summary ===",
                   level=OutputLevel.MINIMAL,
                   formatter="console",
                   status="header")
        
        self.print(f"Status: {status.upper()}",
                   level=OutputLevel.MINIMAL,
                   formatter="console",
                   status=status)
        
        # Print counts
        self.print(f"Total: {total} tests",
                   level=OutputLevel.MINIMAL,
                   formatter="console",
                   status="info")
        
        self.print(f"Passed: {passed} tests",
                   level=OutputLevel.MINIMAL,
                   formatter="console",
                   status="passed")
        
        if failed > 0:
            self.print(f"Failed: {failed} tests",
                       level=OutputLevel.MINIMAL,
                       formatter="console",
                       status="failed")
        
        if skipped > 0:
            self.print(f"Skipped: {skipped} tests",
                       level=OutputLevel.MINIMAL,
                       formatter="console",
                       status="skipped")
        
        if error > 0:
            self.print(f"Error: {error} tests",
                       level=OutputLevel.MINIMAL,
                       formatter="console",
                       status="error")
        
        # Print duration
        self.print(f"Duration: {duration:.2f} seconds",
                   level=OutputLevel.MINIMAL,
                   formatter="console",
                   status="info")
        
        # Generate reports if enabled
        results = summary.get('results', {})
        
        # Generate HTML report
        if self.html_report_generator:
            try:
                report_path = self.html_report_generator.generate_report(results, summary)
                self.print(f"HTML report generated: {report_path}",
                          level=OutputLevel.MINIMAL,
                          formatter="console",
                          status="info")
            except Exception as e:
                self.print(f"Error generating HTML report: {str(e)}",
                          level=OutputLevel.MINIMAL,
                          formatter="console",
                          status="error")
                
        # Generate JSON report
        if self.json_report_generator:
            try:
                report_path = self.json_report_generator.generate_report(results, summary)
                self.print(f"JSON report generated: {report_path}",
                          level=OutputLevel.MINIMAL,
                          formatter="console",
                          status="info")
            except Exception as e:
                self.print(f"Error generating JSON report: {str(e)}",
                          level=OutputLevel.MINIMAL,
                          formatter="console",
                          status="error")
    
    def start_progress(self, total: int) -> None:
        """
        Start a progress indicator for test execution.
        
        Args:
            total: The total number of tests to be executed.
        """
        for name, formatter in self.formatters.items():
            if hasattr(formatter, 'start_progress'):
                formatter.start_progress(total)
    
    def update_progress(self, current: int, status: str = None) -> None:
        """
        Update the progress indicator.
        
        Args:
            current: The current number of completed tests.
            status: Optional status to display (e.g., 'passed', 'failed').
        """
        for name, formatter in self.formatters.items():
            if hasattr(formatter, 'update_progress'):
                formatter.update_progress(current, status)
    
    def finish_progress(self) -> None:
        """Finish and clear the progress indicator."""
        for name, formatter in self.formatters.items():
            if hasattr(formatter, 'finish_progress'):
                formatter.finish_progress()
    
    def close(self) -> None:
        """Close any open file handles."""
        if self.file_output:
            self.file_output.close()
            self.file_output = None
            
    def generate_html_report(self, results: Dict[str, Dict[str, TestResult]], summary: Dict[str, Any]) -> Optional[str]:
        """
        Generate an HTML report for test results.
        
        Args:
            results: Dictionary mapping category names to dictionaries of test results.
            summary: Dictionary containing summary information.
            
        Returns:
            The path to the generated report, or None if HTML reports are not enabled.
        """
        if not self.html_report_generator:
            return None
            
        try:
            return self.html_report_generator.generate_report(results, summary)
        except Exception as e:
            self.print_error(f"Error generating HTML report: {str(e)}",
                            level=OutputLevel.MINIMAL,
                            formatter="console",
                            status="error")
            return None
            
    def generate_json_report(self, results: Dict[str, Dict[str, TestResult]], summary: Dict[str, Any]) -> Optional[str]:
        """
        Generate a JSON report for test results.
        
        Args:
            results: Dictionary mapping category names to dictionaries of test results.
            summary: Dictionary containing summary information.
            
        Returns:
            The path to the generated report, or None if JSON reports are not enabled.
        """
        if not self.json_report_generator:
            return None
            
        try:
            return self.json_report_generator.generate_report(results, summary)
        except Exception as e:
            self.print_error(f"Error generating JSON report: {str(e)}",
                            level=OutputLevel.MINIMAL,
                            formatter="console",
                            status="error")
            return None