#!/usr/bin/env python3
"""
Enhanced Test Runner Example

This script demonstrates how to use the enhanced GödelOS Test Runner with
the new features such as HTML reports, docstring extraction, and improved
console output formatting.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from godelOS.test_runner import (
    TestRunner, 
    ConfigurationManager, 
    TestRunnerConfig
)


def run_with_default_config():
    """
    Run tests with the default configuration.
    """
    print("\n=== Running tests with default configuration ===\n")
    
    # Create a test runner with default configuration
    runner = TestRunner()
    
    # Run all tests
    runner.run_tests()


def run_with_custom_config():
    """
    Run tests with a custom configuration that enables the new features.
    """
    print("\n=== Running tests with custom configuration ===\n")
    
    # Create a custom configuration
    config = TestRunnerConfig(
        # Test discovery patterns
        test_patterns=["test_*.py"],
        test_dirs=["tests"],
        
        # Output options
        verbose=True,
        output_dir="test_output",
        output_level="NORMAL",
        use_colors=True,
        use_emoji=True,
        
        # New display options
        show_docstrings=True,
        show_phase_separation=True,
        
        # HTML report options
        generate_html_report=True,
        html_report_path="test_output/test_report.html",
    )
    
    # Create a test runner with the custom configuration
    runner = TestRunner(config_path=None, cli_args=[])
    runner.update_config(config.__dict__)
    
    # Run specific categories of tests
    runner.run_tests(categories=["core_kr", "inference"])


def run_with_cli_args():
    """
    Run tests with command-line arguments that enable the new features.
    """
    print("\n=== Running tests with command-line arguments ===\n")
    
    # Define command-line arguments
    cli_args = [
        "--verbose",
        "--output-dir", "test_output",
        "--output-level", "NORMAL",
        "--generate-html-report",
        "--html-report-path", "test_output/test_report_cli.html",
    ]
    
    # Create a test runner with the command-line arguments
    runner = TestRunner(cli_args=cli_args)
    
    # Run tests by pattern
    runner.run_by_pattern("test_inference_engine.py")


def main():
    """
    Main function to demonstrate different ways to use the enhanced test runner.
    """
    # Create output directory if it doesn't exist
    os.makedirs("test_output", exist_ok=True)
    
    # Run examples
    run_with_default_config()
    run_with_custom_config()
    run_with_cli_args()


if __name__ == "__main__":
    main()