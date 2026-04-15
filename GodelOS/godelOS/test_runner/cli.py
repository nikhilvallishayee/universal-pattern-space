"""
Command-Line Interface for the GödelOS Test Runner.

This module provides a command-line interface for the test runner utility,
allowing users to discover, categorize, and execute tests with various options.
"""

import argparse
import sys
from typing import List, Optional, Dict, Any

from godelOS.test_runner import (
    TestRunner,
    OutputLevel,
    ConfigurationManager
)


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """
    Parse command-line arguments for the test runner.
    
    Args:
        args: Optional list of command-line arguments. If None, sys.argv is used.
        
    Returns:
        Parsed arguments as a Namespace object.
    """
    parser = argparse.ArgumentParser(
        description="GödelOS Test Runner - A comprehensive test suite runner utility",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Test selection options
    selection_group = parser.add_argument_group("Test Selection")
    selection_group.add_argument(
        "--pattern", "-p", 
        help="Run tests matching this pattern (glob pattern for test file paths or test names)"
    )
    selection_group.add_argument(
        "--category", "-c", action="append",
        help="Run tests in specified category (can be specified multiple times)"
    )
    selection_group.add_argument(
        "--test", "-t", action="append",
        help="Run specific test by node ID (can be specified multiple times)"
    )
    selection_group.add_argument(
        "--rerun-failed", action="store_true",
        help="Rerun failed tests from the previous run"
    )
    
    # Test discovery options
    discovery_group = parser.add_argument_group("Test Discovery")
    discovery_group.add_argument(
        "--test-pattern", action="append", dest="test_patterns",
        help="Pattern to match test files (can be specified multiple times)"
    )
    discovery_group.add_argument(
        "--test-dir", action="append", dest="test_dirs",
        help="Directory to search for tests (can be specified multiple times)"
    )
    
    # Output options
    output_group = parser.add_argument_group("Output Options")
    output_group.add_argument(
        "--verbose", "-v", action="store_true",
        help="Enable verbose output"
    )
    output_group.add_argument(
        "--quiet", "-q", action="store_true",
        help="Minimal output (only summary)"
    )
    output_group.add_argument(
        "--debug", action="store_true",
        help="Enable debug output"
    )
    output_group.add_argument(
        "--output-dir",
        help="Directory for test output files"
    )
    output_group.add_argument(
        "--no-color", action="store_true",
        help="Disable colored output"
    )
    output_group.add_argument(
        "--no-emoji", action="store_true",
        help="Disable emoji in output"
    )
    output_group.add_argument(
        "--failures-only", action="store_true",
        help="Only print failing tests grouped by module to stdout"
    )
    
    # Test execution options
    execution_group = parser.add_argument_group("Test Execution")
    execution_group.add_argument(
        "--parallel", action="store_true",
        help="Run tests in parallel"
    )
    execution_group.add_argument(
        "--max-workers", type=int,
        help="Maximum number of parallel workers"
    )
    execution_group.add_argument(
        "--timeout", type=int,
        help="Timeout for test execution in seconds"
    )
    
    # Results and statistics options
    results_group = parser.add_argument_group("Results and Statistics")
    results_group.add_argument(
        "--store-results", action="store_true",
        help="Store results for later analysis"
    )
    results_group.add_argument(
        "--results-dir",
        help="Directory to store test results"
    )
    results_group.add_argument(
        "--detailed-timing", action="store_true",
        help="Track detailed timing information"
    )
    
    # Report options
    report_group = parser.add_argument_group("Report Options")
    report_group.add_argument(
        "--generate-html-report", action="store_true",
        help="Generate HTML report"
    )
    report_group.add_argument(
        "--html-report-path",
        help="Path to save HTML report"
    )
    report_group.add_argument(
        "--generate-json-report", action="store_true",
        help="Generate JSON report"
    )
    report_group.add_argument(
        "--json-report-path",
        help="Path to save JSON report"
    )
    
    # Display options
    display_group = parser.add_argument_group("Display Options")
    display_group.add_argument(
        "--no-docstrings", action="store_true",
        help="Disable docstring display"
    )
    display_group.add_argument(
        "--no-phase-separation", action="store_true",
        help="Disable test phase separation"
    )
    display_group.add_argument(
        "--terminal-width", type=int,
        help="Terminal width for formatting"
    )
    
    # Configuration options
    config_group = parser.add_argument_group("Configuration")
    config_group.add_argument(
        "--config",
        help="Path to configuration file"
    )
    
    # Parse arguments
    parsed_args = parser.parse_args(args)
    
    return parsed_args


def convert_args_to_config(args: argparse.Namespace) -> Dict[str, Any]:
    """
    Convert parsed arguments to a configuration dictionary.
    
    Args:
        args: Parsed command-line arguments.
        
    Returns:
        Dictionary with configuration values.
    """
    config = {}
    
    # Convert all non-None values from args to config
    for key, value in vars(args).items():
        if value is not None:
            config[key] = value
    
    # Handle special cases and conversions
    if args.quiet:
        config["output_level"] = "MINIMAL"
    elif args.verbose:
        config["output_level"] = "VERBOSE"
    elif args.debug:
        config["output_level"] = "DEBUG"
    
    if args.no_color:
        config["use_colors"] = False
    
    if args.no_emoji:
        config["use_emoji"] = False
        
    # Handle display options
    if args.no_docstrings:
        config["show_docstrings"] = False
        
    if args.no_phase_separation:
        config["show_phase_separation"] = False
        
    if args.terminal_width:
        config["terminal_width"] = args.terminal_width
        
    # Handle report options
    if args.generate_html_report:
        config["generate_html_report"] = True
        
    if args.html_report_path:
        config["html_report_path"] = args.html_report_path
        
    if args.generate_json_report:
        config["generate_json_report"] = True
        
    if args.json_report_path:
        config["json_report_path"] = args.json_report_path
    
    return config


def run_tests(args: argparse.Namespace) -> int:
    """
    Run tests based on command-line arguments.
    
    Args:
        args: Parsed command-line arguments.
        
    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    # Convert arguments to configuration
    config_dict = convert_args_to_config(args)
    
    # Create test runner
    config_path = args.config if hasattr(args, 'config') else None
    # Don't pass raw CLI args to TestRunner, use the parsed config instead
    runner = TestRunner(config_path=config_path)

    # Suppress all output except failures summary if --failures-only is set
    if getattr(args, "failures_only", False):
        # Patch output_manager to suppress all output except the failures summary
        def _suppress_print(*_a, **_kw): pass
        runner.output_manager.print = _suppress_print
        runner.output_manager.print_test_start = _suppress_print
        runner.output_manager.print_test_result = _suppress_print
        runner.output_manager.print_summary = _suppress_print
        runner.output_manager.start_progress = _suppress_print
        runner.output_manager.update_progress = _suppress_print
        runner.output_manager.finish_progress = _suppress_print

    # Update runner configuration with parsed arguments
    if config_dict:
        runner.update_config(config_dict)

    # Determine which tests to run
    if args.rerun_failed:
        # Rerun failed tests from previous run
        results = runner.rerun_failed_tests()
    elif args.test:
        # Run specific tests by node ID
        results = runner.run_specific_tests(args.test)
    elif args.pattern:
        # Run tests matching pattern
        results = runner.run_by_pattern(args.pattern)
    elif args.category:
        # Run tests in specified categories
        runner.discover_tests()
        runner.categorize_tests()
        results = runner.run_tests(args.category)
    else:
        # Run all tests
        runner.discover_tests()
        runner.categorize_tests()
        results = runner.run_tests()
    
    # If --failures-only is set, only print failing tests grouped by module and exit
    if getattr(args, "failures_only", False):
        runner.print_failing_tests_by_module()
        # Exit code: 0 if no failures, 1 if any failures
        all_results = runner.results_collector.get_all_results()
        any_failures = any(
            hasattr(result, "outcome") and result.outcome == "failed"
            for result in all_results.values()
        )
        return 1 if any_failures else 0

    # Get test summary
    summary = runner.get_test_summary()
    
    # Determine exit code based on test results
    if summary.get('status') == 'passed':
        return 0
    else:
        return 1


def main(args: Optional[List[str]] = None) -> int:
    """
    Main entry point for the test runner CLI.
    
    Args:
        args: Optional list of command-line arguments. If None, sys.argv[1:] is used.
        
    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    try:
        parsed_args = parse_args(args)
        return run_tests(parsed_args)
    except KeyboardInterrupt:
        print("\nTest run interrupted by user", file=sys.stderr)
        return 130  # Standard exit code for SIGINT
    except Exception as e:
        print(f"Error running tests: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())