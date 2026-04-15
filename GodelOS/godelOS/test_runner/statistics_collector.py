"""
Statistics Collector Module for the GödelOS Test Runner.

This module provides functionality to calculate summary statistics from test results,
including pass/fail rates, average durations, and trends.
"""

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any, Callable, Tuple, Union

from godelOS.test_runner.results_collector import ResultsCollector, EnhancedTestResult
from godelOS.test_runner.timing_tracker import TimingTracker


@dataclass
class TestStatistics:
    """Data class representing statistics for a set of tests."""
    
    # Basic counts
    total: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    error: int = 0
    xpassed: int = 0
    xfailed: int = 0
    
    # Timing statistics
    total_duration: float = 0.0
    average_duration: float = 0.0
    min_duration: float = 0.0
    max_duration: float = 0.0
    median_duration: float = 0.0
    stddev_duration: float = 0.0
    
    # Pass/fail rates
    pass_rate: float = 0.0
    fail_rate: float = 0.0
    skip_rate: float = 0.0
    error_rate: float = 0.0
    
    # Slowest tests
    slowest_tests: List[Tuple[str, float]] = field(default_factory=list)
    
    # Most failing tests
    most_failing_tests: List[Tuple[str, int]] = field(default_factory=list)
    
    # Category statistics
    category_stats: Dict[str, 'TestStatistics'] = field(default_factory=dict)


class StatisticsCollector:
    """
    Calculates summary statistics from test results.
    
    This class is responsible for analyzing test results and calculating
    various statistics, such as pass/fail rates, average durations, and trends.
    """
    
    def __init__(self, config: Any, results_collector: ResultsCollector, timing_tracker: TimingTracker):
        """
        Initialize the StatisticsCollector.
        
        Args:
            config: Configuration object containing statistics settings.
            results_collector: ResultsCollector instance to get results from.
            timing_tracker: TimingTracker instance to get timing data from.
        """
        self.config = config
        self.results_collector = results_collector
        self.timing_tracker = timing_tracker
        
        # Number of slowest tests to track
        self.num_slowest = getattr(config, 'num_slowest_tests', 10)
        
        # Number of most failing tests to track
        self.num_most_failing = getattr(config, 'num_most_failing_tests', 10)
        
        # Historical data for trend analysis
        self.historical_runs: List[TestStatistics] = []
        self.max_history = getattr(config, 'statistics_history_limit', 10)
    
    def calculate_statistics(self) -> TestStatistics:
        """
        Calculate statistics for the current test run.
        
        Returns:
            A TestStatistics object containing the calculated statistics.
        """
        # Get all test results
        results = self.results_collector.get_all_results()
        
        # Initialize statistics
        stats = TestStatistics()
        
        # Basic counts
        stats.total = len(results)
        stats.passed = len([r for r in results.values() if r.outcome == 'passed'])
        stats.failed = len([r for r in results.values() if r.outcome == 'failed'])
        stats.skipped = len([r for r in results.values() if r.outcome == 'skipped'])
        stats.error = len([r for r in results.values() if r.outcome == 'error'])
        stats.xpassed = len([r for r in results.values() if r.outcome == 'xpassed'])
        stats.xfailed = len([r for r in results.values() if r.outcome == 'xfailed'])
        
        # Pass/fail rates
        if stats.total > 0:
            stats.pass_rate = stats.passed / stats.total
            stats.fail_rate = stats.failed / stats.total
            stats.skip_rate = stats.skipped / stats.total
            stats.error_rate = stats.error / stats.total
        
        # Timing statistics
        durations = [r.duration for r in results.values() if r.duration is not None]
        if durations:
            stats.total_duration = sum(durations)
            stats.average_duration = stats.total_duration / len(durations)
            stats.min_duration = min(durations)
            stats.max_duration = max(durations)
            
            # Calculate median
            sorted_durations = sorted(durations)
            middle = len(sorted_durations) // 2
            if len(sorted_durations) % 2 == 0:
                stats.median_duration = (sorted_durations[middle - 1] + sorted_durations[middle]) / 2
            else:
                stats.median_duration = sorted_durations[middle]
            
            # Calculate standard deviation
            if len(durations) > 1:
                variance = sum((d - stats.average_duration) ** 2 for d in durations) / len(durations)
                stats.stddev_duration = math.sqrt(variance)
        
        # Slowest tests
        slowest_tests = [(node_id, result.duration) 
                         for node_id, result in results.items() 
                         if result.duration is not None]
        slowest_tests.sort(key=lambda x: x[1], reverse=True)
        stats.slowest_tests = slowest_tests[:self.num_slowest]
        
        # Calculate per-category statistics
        for category, category_results in self.results_collector.categorized_results.items():
            category_stats = self._calculate_category_statistics(category_results)
            stats.category_stats[category] = category_stats
        
        # Store in historical data
        self.historical_runs.append(stats)
        if len(self.historical_runs) > self.max_history:
            self.historical_runs = self.historical_runs[-self.max_history:]
        
        return stats
    
    def _calculate_category_statistics(self, results: Dict[str, EnhancedTestResult]) -> TestStatistics:
        """
        Calculate statistics for a specific category.
        
        Args:
            results: Dictionary of test results for the category.
            
        Returns:
            A TestStatistics object for the category.
        """
        # Initialize statistics
        stats = TestStatistics()
        
        # Basic counts
        stats.total = len(results)
        stats.passed = len([r for r in results.values() if r.outcome == 'passed'])
        stats.failed = len([r for r in results.values() if r.outcome == 'failed'])
        stats.skipped = len([r for r in results.values() if r.outcome == 'skipped'])
        stats.error = len([r for r in results.values() if r.outcome == 'error'])
        stats.xpassed = len([r for r in results.values() if r.outcome == 'xpassed'])
        stats.xfailed = len([r for r in results.values() if r.outcome == 'xfailed'])
        
        # Pass/fail rates
        if stats.total > 0:
            stats.pass_rate = stats.passed / stats.total
            stats.fail_rate = stats.failed / stats.total
            stats.skip_rate = stats.skipped / stats.total
            stats.error_rate = stats.error / stats.total
        
        # Timing statistics
        durations = [r.duration for r in results.values() if r.duration is not None]
        if durations:
            stats.total_duration = sum(durations)
            stats.average_duration = stats.total_duration / len(durations)
            stats.min_duration = min(durations)
            stats.max_duration = max(durations)
            
            # Calculate median
            sorted_durations = sorted(durations)
            middle = len(sorted_durations) // 2
            if len(sorted_durations) % 2 == 0:
                stats.median_duration = (sorted_durations[middle - 1] + sorted_durations[middle]) / 2
            else:
                stats.median_duration = sorted_durations[middle]
            
            # Calculate standard deviation
            if len(durations) > 1:
                variance = sum((d - stats.average_duration) ** 2 for d in durations) / len(durations)
                stats.stddev_duration = math.sqrt(variance)
        
        # Slowest tests
        slowest_tests = [(node_id, result.duration) 
                         for node_id, result in results.items() 
                         if result.duration is not None]
        slowest_tests.sort(key=lambda x: x[1], reverse=True)
        stats.slowest_tests = slowest_tests[:self.num_slowest]
        
        return stats
    
    def get_trend_data(self) -> Dict[str, List[float]]:
        """
        Get trend data from historical runs.
        
        Returns:
            A dictionary mapping metric names to lists of values.
        """
        if not self.historical_runs:
            return {}
        
        trends = {
            'pass_rate': [run.pass_rate for run in self.historical_runs],
            'fail_rate': [run.fail_rate for run in self.historical_runs],
            'average_duration': [run.average_duration for run in self.historical_runs],
            'total_duration': [run.total_duration for run in self.historical_runs],
        }
        
        return trends
    
    def get_category_comparison(self) -> Dict[str, Dict[str, float]]:
        """
        Get a comparison of statistics across categories.
        
        Returns:
            A dictionary mapping categories to dictionaries of metrics.
        """
        if not self.historical_runs or not self.historical_runs[-1].category_stats:
            return {}
        
        latest_run = self.historical_runs[-1]
        comparison = {}
        
        for category, stats in latest_run.category_stats.items():
            comparison[category] = {
                'pass_rate': stats.pass_rate,
                'fail_rate': stats.fail_rate,
                'average_duration': stats.average_duration,
                'total_duration': stats.total_duration,
                'total_tests': stats.total,
            }
        
        return comparison
    
    def get_flaky_tests(self) -> List[Tuple[str, float]]:
        """
        Identify flaky tests based on historical data.
        
        A test is considered flaky if it has both passed and failed in recent runs.
        
        Returns:
            A list of (node_id, flakiness_score) tuples, sorted by flakiness (descending).
        """
        # This would require historical data per test, which we don't track in this implementation
        # For a real implementation, we would need to store test outcomes across multiple runs
        return []
    
    def get_statistics_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the most important statistics.
        
        Returns:
            A dictionary containing the summary statistics.
        """
        if not self.historical_runs:
            return {}
        
        latest_run = self.historical_runs[-1]
        
        summary = {
            'total_tests': latest_run.total,
            'passed_tests': latest_run.passed,
            'failed_tests': latest_run.failed,
            'skipped_tests': latest_run.skipped,
            'error_tests': latest_run.error,
            'pass_rate': latest_run.pass_rate,
            'total_duration': latest_run.total_duration,
            'average_duration': latest_run.average_duration,
            'slowest_tests': latest_run.slowest_tests[:5],  # Just the top 5
            'categories': {
                category: {
                    'total': stats.total,
                    'pass_rate': stats.pass_rate,
                    'average_duration': stats.average_duration,
                }
                for category, stats in latest_run.category_stats.items()
            }
        }
        
        return summary