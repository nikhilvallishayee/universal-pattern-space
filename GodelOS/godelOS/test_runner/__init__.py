"""
GödelOS Test Runner Package.

This package provides a comprehensive test runner for the GödelOS project,
with support for test discovery, categorization, execution, and reporting.
"""

from godelOS.test_runner.config_manager import ConfigurationManager, TestRunnerConfig
from godelOS.test_runner.test_discovery import TestDiscovery
from godelOS.test_runner.test_categorizer import TestCategorizer
from godelOS.test_runner.pytest_wrapper import PyTestWrapper, TestResult
from godelOS.test_runner.output_manager import OutputManager, OutputLevel
from godelOS.test_runner.console_formatter import ConsoleFormatter
from godelOS.test_runner.results_collector import ResultsCollector, EnhancedTestResult
from godelOS.test_runner.timing_tracker import TimingTracker
from godelOS.test_runner.statistics_collector import StatisticsCollector, TestStatistics
from godelOS.test_runner.test_runner import TestRunner
from godelOS.test_runner.docstring_extractor import DocstringExtractor
from godelOS.test_runner.html_report_generator import HTMLReportGenerator

__all__ = [
    'ConfigurationManager',
    'TestRunnerConfig',
    'TestDiscovery',
    'TestCategorizer',
    'PyTestWrapper',
    'TestResult',
    'OutputManager',
    'OutputLevel',
    'ConsoleFormatter',
    'ResultsCollector',
    'EnhancedTestResult',
    'TimingTracker',
    'StatisticsCollector',
    'TestStatistics',
    'TestRunner',
    'DocstringExtractor',
    'HTMLReportGenerator',
]