#!/usr/bin/env python3
"""
GödelOS Test Runner Comprehensive Demo

This script provides a comprehensive demonstration of the GödelOS Test Runner's
capabilities, including:

1. Test discovery and explicit registration
2. Tests with detailed docstrings explaining purpose, expected behavior, and edge cases
3. Different test categories
4. Tests with different outcomes (pass, fail, error, skip)
5. Different verbosity levels
6. HTML and JSON report generation
7. Tests with timing differences (fast vs. slow)
8. Tests with different docstring formats

Run this demo to see all features in action and generate comprehensive reports.
"""

import os
import sys
import time
import unittest
import random
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from godelOS.test_runner import (
    TestRunner, 
    TestRunnerConfig,
    OutputLevel
)


# ============================================================================
# Sample Test Classes with Different Docstring Formats and Outcomes
# ============================================================================

class SimpleTests(unittest.TestCase):
    """A collection of simple tests with basic docstrings.
    
    This test class demonstrates basic test cases with simple docstrings
    and different outcomes (pass, fail, error, skip).
    """
    
    def test_simple_pass(self):
        """A simple test that always passes."""
        self.assertTrue(True)
    
    def test_simple_fail(self):
        """A simple test that always fails."""
        self.assertTrue(False)
    
    def test_simple_error(self):
        """A simple test that raises an error.
        
        This test demonstrates error handling in the test runner.
        """
        # Deliberately cause an error
        raise ValueError("This is a deliberate error for demonstration")
    
    @unittest.skip("Skipped for demonstration purposes")
    def test_simple_skip(self):
        """A simple test that is skipped.
        
        This test demonstrates the skip functionality.
        """
        self.assertTrue(True)


class DetailedTests(unittest.TestCase):
    """Tests with detailed Google-style docstrings.
    
    This test class demonstrates tests with Google-style docstrings that include
    detailed descriptions of purpose, expected behavior, and edge cases.
    """
    
    def test_detailed_pass(self):
        """Tests a simple addition operation.
        
        This test verifies that the addition operator works correctly for
        integer values. It adds two positive integers and checks the result.
        
        Expected behavior:
            The test should pass, demonstrating that 1 + 1 equals 2.
            
        Edge cases:
            This test does not cover edge cases like integer overflow or
            adding negative numbers, which would be covered in separate tests.
        """
        self.assertEqual(1 + 1, 2)
    
    def test_detailed_fail(self):
        """Tests string comparison with deliberate failure.
        
        This test demonstrates a failing test with a detailed docstring.
        It compares two strings that are intentionally different.
        
        Expected behavior:
            The test should fail because the strings don't match.
            
        Edge cases:
            This test doesn't handle edge cases like empty strings or
            Unicode characters, which would be covered in separate tests.
        """
        self.assertEqual("hello", "world")


class ReStructuredTextTests(unittest.TestCase):
    """Tests with reStructuredText-style docstrings.
    
    This test class demonstrates tests with reStructuredText-style docstrings.
    """
    
    def test_rst_format(self):
        """Test with reStructuredText format docstring.
        
        :Purpose: Demonstrate reStructuredText docstring parsing
        :Expected behavior: The test should pass and the docstring should be properly parsed
        :Edge cases: None for this demonstration
        
        This test verifies that the test runner can properly parse and display
        reStructuredText-style docstrings.
        """
        self.assertTrue(True)
    
    def test_rst_with_code(self):
        """Test with reStructuredText format including code examples.
        
        :Purpose: Demonstrate code examples in docstrings
        :Expected behavior: The test should pass and code should be displayed properly
        
        Example::
            
            # This is a code example
            result = 1 + 1
            assert result == 2
        
        The test runner should properly format this code block in the output.
        """
        self.assertEqual(1 + 1, 2)


class TimingTests(unittest.TestCase):
    """Tests with different execution times.
    
    This test class demonstrates tests with varying execution times to show
    how the test runner tracks and reports timing information.
    """
    
    def test_fast(self):
        """A fast test that completes quickly.
        
        Expected behavior:
            This test should complete very quickly (< 10ms).
        """
        # Fast operation
        result = sum(range(10))
        self.assertEqual(result, 45)
    
    def test_medium(self):
        """A medium-speed test.
        
        Expected behavior:
            This test should take a moderate amount of time (around 100ms).
        """
        # Medium operation
        time.sleep(0.1)
        result = sum(range(1000))
        self.assertEqual(result, 499500)
    
    def test_slow(self):
        """A slow test that takes significant time.
        
        Expected behavior:
            This test should be identified as a slow test (> 500ms).
        """
        # Slow operation
        time.sleep(0.5)
        result = sum(range(10000))
        self.assertEqual(result, 49995000)


class CategoryTests(unittest.TestCase):
    """Tests demonstrating category features.
    
    This test class demonstrates how tests can be categorized using markers,
    naming conventions, and explicit registration.
    """
    
    def test_math_category(self):
        """[math] Test in the math category.
        
        This test is tagged with [math] to demonstrate category assignment
        based on docstring tags.
        """
        self.assertEqual(2 * 3, 6)
    
    def test_string_category(self):
        """[string] Test in the string category.
        
        This test is tagged with [string] to demonstrate category assignment
        based on docstring tags.
        """
        self.assertEqual("hello " + "world", "hello world")
    
    @unittest.skipIf(random.random() < 0.5, "Randomly skipped")
    def test_random_skip(self):
        """Test that might be skipped randomly.
        
        This test has a 50% chance of being skipped to demonstrate
        how the test runner handles conditional skipping.
        """
        self.assertTrue(True)


# ============================================================================
# Demo Runner Functions
# ============================================================================

def run_with_discovery():
    """Run tests using automatic test discovery."""
    print("\n=== Running tests with automatic discovery ===\n")
    
    # Create output directory
    output_dir = "test_output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Create a configuration for test discovery
    config = TestRunnerConfig(
        # Test discovery will find all test classes in this module
        test_patterns=["test_runner_demo.py"],
        test_dirs=["examples"],
        
        # Output options
        verbose=True,
        output_dir=output_dir,
        output_level="NORMAL",
        use_colors=True,
        use_emoji=True,
        
        # Display options
        show_docstrings=True,
        show_phase_separation=True,
        
        # Report options
        generate_html_report=True,
        html_report_path=os.path.join(output_dir, "discovery_report.html"),
        generate_json_report=True,
        json_report_path=os.path.join(output_dir, "discovery_report.json"),
    )
    
    # Create a test runner with the configuration
    runner = TestRunner()
    runner.update_config(config.__dict__)
    
    # Discover and run tests
    runner.discover_tests()
    runner.run_tests()
    
    print("\nTest discovery report generated at:")
    print(f"  HTML: {os.path.join(output_dir, 'discovery_report.html')}")
    print(f"  JSON: {os.path.join(output_dir, 'discovery_report.json')}")


def run_with_explicit_registration():
    """Run tests using explicit test registration."""
    print("\n=== Running tests with explicit registration ===\n")
    
    # Create output directory
    output_dir = "test_output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Create a configuration for explicit test registration
    config = TestRunnerConfig(
        # Output options
        verbose=True,
        output_dir=output_dir,
        output_level="NORMAL",
        use_colors=True,
        use_emoji=True,
        
        # Display options
        show_docstrings=True,
        show_phase_separation=True,
        
        # Report options
        generate_html_report=True,
        html_report_path=os.path.join(output_dir, "explicit_report.html"),
        generate_json_report=True,
        json_report_path=os.path.join(output_dir, "explicit_report.json"),
    )
    
    # Create a test runner with the configuration
    runner = TestRunner()
    runner.update_config(config.__dict__)
    
    # Explicitly register tests
    test_suite = unittest.TestSuite()
    test_suite.addTest(SimpleTests('test_simple_pass'))
    test_suite.addTest(DetailedTests('test_detailed_pass'))
    test_suite.addTest(ReStructuredTextTests('test_rst_format'))
    test_suite.addTest(TimingTests('test_fast'))
    test_suite.addTest(TimingTests('test_slow'))
    
    # Convert the test suite to node IDs
    node_ids = [f"{test.__class__.__module__}::{test.__class__.__name__}::{test._testMethodName}" 
                for test in test_suite]
    
    # Run the explicitly registered tests
    runner.run_specific_tests(node_ids)
    
    print("\nExplicit registration report generated at:")
    print(f"  HTML: {os.path.join(output_dir, 'explicit_report.html')}")
    print(f"  JSON: {os.path.join(output_dir, 'explicit_report.json')}")


def run_with_different_verbosity_levels():
    """Run tests with different verbosity levels."""
    print("\n=== Running tests with different verbosity levels ===\n")
    
    # Create output directory
    output_dir = "test_output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Define verbosity levels to demonstrate
    verbosity_levels = ["MINIMAL", "NORMAL", "VERBOSE", "DEBUG"]
    
    for level in verbosity_levels:
        print(f"\n--- Verbosity Level: {level} ---\n")
        
        # Create a configuration with the current verbosity level
        config = TestRunnerConfig(
            # Test discovery patterns
            test_patterns=["test_runner_demo.py"],
            test_dirs=["examples"],
            
            # Output options
            verbose=(level != "MINIMAL"),
            output_dir=output_dir,
            output_level=level,
            use_colors=True,
            use_emoji=True,
            
            # Display options
            show_docstrings=(level != "MINIMAL"),
            show_phase_separation=(level in ["VERBOSE", "DEBUG"]),
            
            # Only generate reports for NORMAL level as an example
            generate_html_report=(level == "NORMAL"),
            html_report_path=os.path.join(output_dir, f"{level.lower()}_report.html"),
            generate_json_report=(level == "NORMAL"),
            json_report_path=os.path.join(output_dir, f"{level.lower()}_report.json"),
        )
        
        # Create a test runner with the configuration
        runner = TestRunner()
        runner.update_config(config.__dict__)
        
        # Run a subset of tests to keep the output manageable
        if level == "DEBUG":
            # Run fewer tests for DEBUG level to avoid excessive output
            runner.run_specific_tests([
                "examples.test_runner_demo::SimpleTests::test_simple_pass",
                "examples.test_runner_demo::TimingTests::test_fast"
            ])
        else:
            # Run all tests from SimpleTests class
            runner.run_by_pattern("examples.test_runner_demo::SimpleTests")
        
        if level == "NORMAL":
            print(f"\nVerbosity level {level} reports generated at:")
            print(f"  HTML: {os.path.join(output_dir, f'{level.lower()}_report.html')}")
            print(f"  JSON: {os.path.join(output_dir, f'{level.lower()}_report.json')}")


def run_with_custom_categories():
    """Run tests with custom categories."""
    print("\n=== Running tests with custom categories ===\n")
    
    # Create output directory
    output_dir = "test_output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Create a configuration with custom categories
    config = TestRunnerConfig(
        # Test discovery patterns
        test_patterns=["test_runner_demo.py"],
        test_dirs=["examples"],
        
        # Output options
        verbose=True,
        output_dir=output_dir,
        output_level="NORMAL",
        use_colors=True,
        use_emoji=True,
        
        # Display options
        show_docstrings=True,
        show_phase_separation=True,
        
        # Custom categories
        categories={
            "simple": ["examples.test_runner_demo::SimpleTests::*"],
            "detailed": ["examples.test_runner_demo::DetailedTests::*"],
            "rst": ["examples.test_runner_demo::ReStructuredTextTests::*"],
            "timing": ["examples.test_runner_demo::TimingTests::*"],
            "category": ["examples.test_runner_demo::CategoryTests::*"],
            "math": ["regex:.*\\[math\\].*"],  # Tests tagged with [math]
            "string": ["regex:.*\\[string\\].*"],  # Tests tagged with [string]
            "fast": ["examples.test_runner_demo::TimingTests::test_fast"],
            "slow": ["examples.test_runner_demo::TimingTests::test_slow"],
        },
        
        # Report options
        generate_html_report=True,
        html_report_path=os.path.join(output_dir, "categories_report.html"),
        generate_json_report=True,
        json_report_path=os.path.join(output_dir, "categories_report.json"),
    )
    
    # Create a test runner with the configuration
    runner = TestRunner()
    runner.update_config(config.__dict__)
    
    # Discover and categorize tests
    runner.discover_tests()
    categories = runner.categorize_tests()
    
    # Print available categories
    print("\nAvailable categories:")
    for category, tests in categories.items():
        print(f"  {category}: {len(tests)} tests")
    
    # Run tests by category
    print("\nRunning tests by category:")
    for category in ["simple", "math", "string", "fast", "slow"]:
        print(f"\n--- Category: {category} ---\n")
        runner.run_tests(categories=[category])
    
    print("\nCategories report generated at:")
    print(f"  HTML: {os.path.join(output_dir, 'categories_report.html')}")
    print(f"  JSON: {os.path.join(output_dir, 'categories_report.json')}")


def run_comprehensive_demo():
    """Run a comprehensive demo of all features."""
    print("\n=== Running comprehensive demo of all features ===\n")
    
    # Create output directory
    output_dir = "test_output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Create a configuration with all features enabled
    config = TestRunnerConfig(
        # Test discovery patterns
        test_patterns=["test_runner_demo.py"],
        test_dirs=["examples"],
        
        # Output options
        verbose=True,
        output_dir=output_dir,
        output_level="VERBOSE",
        use_colors=True,
        use_emoji=True,
        
        # Display options
        show_docstrings=True,
        show_phase_separation=True,
        terminal_width=100,
        
        # Timing options
        detailed_timing=True,
        
        # Report options
        generate_html_report=True,
        html_report_path=os.path.join(output_dir, "comprehensive_report.html"),
        generate_json_report=True,
        json_report_path=os.path.join(output_dir, "comprehensive_report.json"),
    )
    
    # Create a test runner with the configuration
    runner = TestRunner()
    runner.update_config(config.__dict__)
    
    # Discover and run all tests
    runner.discover_tests()
    runner.run_tests()
    
    # Get and print test summary
    summary = runner.get_test_summary()
    print("\nTest Summary:")
    print(f"  Total tests: {summary['total']}")
    print(f"  Passed: {summary['passed']}")
    print(f"  Failed: {summary['failed']}")
    print(f"  Errors: {summary['error']}")
    print(f"  Skipped: {summary['skipped']}")
    print(f"  Total duration: {summary['duration']:.2f} seconds")
    
    # Print slowest tests
    if 'slowest_tests' in summary:
        print("\nSlowest Tests:")
        for test, duration in summary['slowest_tests'][:3]:
            print(f"  {test}: {duration:.4f} seconds")
    
    print("\nComprehensive report generated at:")
    print(f"  HTML: {os.path.join(output_dir, 'comprehensive_report.html')}")
    print(f"  JSON: {os.path.join(output_dir, 'comprehensive_report.json')}")


def main():
    """
    Main function to run the comprehensive test runner demo.
    
    This function runs multiple demonstrations of the test runner's capabilities:
    1. Automatic test discovery
    2. Explicit test registration
    3. Different verbosity levels
    4. Custom test categories
    5. Comprehensive demo of all features
    
    Each demonstration generates its own HTML and JSON reports.
    """
    print("=" * 80)
    print("GödelOS Test Runner Comprehensive Demo")
    print("=" * 80)
    
    # Create output directory
    output_dir = "test_output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Run the demonstrations
    run_with_discovery()
    run_with_explicit_registration()
    run_with_different_verbosity_levels()
    run_with_custom_categories()
    run_comprehensive_demo()
    
    print("\n" + "=" * 80)
    print("Demo completed successfully!")
    print("=" * 80)
    print("\nAll reports have been generated in the 'test_output' directory.")
    print("To view the HTML reports, open them in a web browser.")
    print("To analyze the JSON reports, use any JSON viewer or parser.")
    print("\nExample commands:")
    print("  # View HTML report")
    print("  open test_output/comprehensive_report.html")
    print("\n  # View JSON report")
    print("  cat test_output/comprehensive_report.json | python -m json.tool")
    print("=" * 80)


if __name__ == "__main__":
    main()