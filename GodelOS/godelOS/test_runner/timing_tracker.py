"""
Timing Tracker Module for the GödelOS Test Runner.

This module provides functionality to track and analyze execution time of tests
and test suites.
"""

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Set, Any, Callable, Tuple, Union

from godelOS.test_runner.results_collector import EnhancedTestResult


@dataclass
class TimingEntry:
    """Data class representing a timing entry for a test or category."""
    
    name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    children: Dict[str, 'TimingEntry'] = field(default_factory=dict)
    
    def stop(self) -> float:
        """
        Stop the timing entry and calculate duration.
        
        Returns:
            The duration in seconds.
        """
        self.end_time = datetime.now()
        self.duration = (self.end_time - self.start_time).total_seconds()
        return self.duration
    
    def add_child(self, name: str) -> 'TimingEntry':
        """
        Add a child timing entry.
        
        Args:
            name: The name of the child entry.
            
        Returns:
            The created child entry.
        """
        child = TimingEntry(name=name, start_time=datetime.now())
        self.children[name] = child
        return child
    
    def get_total_duration(self) -> float:
        """
        Get the total duration including all children.
        
        Returns:
            The total duration in seconds.
        """
        if self.duration is None:
            return 0.0
        
        return self.duration


class TimingTracker:
    """
    Tracks execution time for individual tests and test suites.
    
    This class provides methods to start and stop timing for tests and categories,
    and to analyze the timing data.
    """
    
    def __init__(self, config: Any):
        """
        Initialize the TimingTracker.
        
        Args:
            config: Configuration object containing timing settings.
        """
        self.config = config
        self.current_run: Optional[TimingEntry] = None
        self.historical_data: Dict[str, List[TimingEntry]] = {}
        self.active_timers: Dict[str, TimingEntry] = {}
        
        # Maximum history to keep per test
        self.max_history = getattr(config, 'timing_history_limit', 10)
        
        # Whether to track detailed timing
        self.detailed_timing = getattr(config, 'detailed_timing', False)
    
    def start_run(self) -> TimingEntry:
        """
        Start timing a new test run.
        
        Returns:
            The TimingEntry for the run.
        """
        run_name = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.current_run = TimingEntry(name=run_name, start_time=datetime.now())
        return self.current_run
    
    def end_run(self) -> float:
        """
        End timing for the current test run.
        
        Returns:
            The duration of the run in seconds.
        """
        if self.current_run:
            duration = self.current_run.stop()
            
            # Clear active timers
            self.active_timers = {}
            
            return duration
        return 0.0
    
    def start_category(self, category: str) -> TimingEntry:
        """
        Start timing a test category.
        
        Args:
            category: The name of the category.
            
        Returns:
            The TimingEntry for the category.
        """
        if not self.current_run:
            self.start_run()
        
        category_timer = self.current_run.add_child(category)
        self.active_timers[f"category:{category}"] = category_timer
        return category_timer
    
    def end_category(self, category: str) -> float:
        """
        End timing for a test category.
        
        Args:
            category: The name of the category.
            
        Returns:
            The duration of the category in seconds.
        """
        timer_key = f"category:{category}"
        if timer_key in self.active_timers:
            timer = self.active_timers[timer_key]
            duration = timer.stop()
            del self.active_timers[timer_key]
            return duration
        return 0.0
    
    def start_test(self, node_id: str) -> TimingEntry:
        """
        Start timing a test.
        
        Args:
            node_id: The pytest node ID of the test.
            
        Returns:
            The TimingEntry for the test.
        """
        if not self.current_run:
            self.start_run()
        
        # Find the parent category timer if any
        parent_timer = self.current_run
        for timer_key, timer in self.active_timers.items():
            if timer_key.startswith("category:"):
                parent_timer = timer
                break
        
        # Create the test timer
        test_timer = parent_timer.add_child(node_id)
        self.active_timers[f"test:{node_id}"] = test_timer
        
        return test_timer
    
    def end_test(self, node_id: str) -> float:
        """
        End timing for a test.
        
        Args:
            node_id: The pytest node ID of the test.
            
        Returns:
            The duration of the test in seconds.
        """
        timer_key = f"test:{node_id}"
        if timer_key in self.active_timers:
            timer = self.active_timers[timer_key]
            duration = timer.stop()
            
            # Store in historical data
            if self.detailed_timing:
                if node_id not in self.historical_data:
                    self.historical_data[node_id] = []
                
                self.historical_data[node_id].append(timer)
                
                # Limit history size
                if len(self.historical_data[node_id]) > self.max_history:
                    self.historical_data[node_id] = self.historical_data[node_id][-self.max_history:]
            
            del self.active_timers[timer_key]
            return duration
        return 0.0
    
    def get_test_history(self, node_id: str) -> List[TimingEntry]:
        """
        Get timing history for a test.
        
        Args:
            node_id: The pytest node ID of the test.
            
        Returns:
            A list of TimingEntry objects for the test.
        """
        return self.historical_data.get(node_id, [])
    
    def get_average_duration(self, node_id: str) -> float:
        """
        Get the average duration for a test.
        
        Args:
            node_id: The pytest node ID of the test.
            
        Returns:
            The average duration in seconds.
        """
        history = self.get_test_history(node_id)
        if not history:
            return 0.0
        
        durations = [entry.duration for entry in history if entry.duration is not None]
        if not durations:
            return 0.0
        
        return sum(durations) / len(durations)
    
    def get_duration_trend(self, node_id: str) -> List[float]:
        """
        Get the duration trend for a test.
        
        Args:
            node_id: The pytest node ID of the test.
            
        Returns:
            A list of durations in chronological order.
        """
        history = self.get_test_history(node_id)
        return [entry.duration for entry in history if entry.duration is not None]
    
    def get_slowest_tests(self, limit: int = 10) -> List[Tuple[str, float]]:
        """
        Get the slowest tests from the current run.
        
        Args:
            limit: Maximum number of tests to return.
            
        Returns:
            A list of (node_id, duration) tuples, sorted by duration (descending).
        """
        if not self.current_run:
            return []
        
        # Collect all test timers
        test_timers = []
        for category_name, category_timer in self.current_run.children.items():
            for test_name, test_timer in category_timer.children.items():
                if test_timer.duration is not None:
                    test_timers.append((test_name, test_timer.duration))
        
        # Sort by duration (descending)
        test_timers.sort(key=lambda x: x[1], reverse=True)
        
        return test_timers[:limit]
    
    def get_category_durations(self) -> Dict[str, float]:
        """
        Get the duration for each category in the current run.
        
        Returns:
            A dictionary mapping category names to durations.
        """
        if not self.current_run:
            return {}
        
        return {
            category_name: category_timer.duration
            for category_name, category_timer in self.current_run.children.items()
            if category_timer.duration is not None
        }
    
    def get_total_duration(self) -> float:
        """
        Get the total duration of the current run.
        
        Returns:
            The total duration in seconds.
        """
        if not self.current_run or self.current_run.duration is None:
            return 0.0
        
        return self.current_run.duration
    
    def update_test_result(self, result: EnhancedTestResult) -> EnhancedTestResult:
        """
        Update a test result with timing information.
        
        Args:
            result: The test result to update.
            
        Returns:
            The updated test result.
        """
        # Add historical timing data
        history = self.get_test_history(result.node_id)
        if history:
            result.previous_durations = [entry.duration for entry in history if entry.duration is not None]
        
        return result