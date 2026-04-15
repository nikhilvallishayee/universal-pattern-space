#!/usr/bin/env python3
"""
Script to test each GödelOS module one by one.

This script runs tests for each module category separately and collects
the results in a structured format for analysis.
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime
from typing import Dict, List, Any

# Add the current directory to the Python path to ensure imports work correctly
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from godelOS.test_runner import TestRunner


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Run tests for each GödelOS module one by one')
    parser.add_argument('--output-dir', default='out', help='Directory to store test results')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    parser.add_argument('--generate-html', action='store_true', help='Generate HTML reports')
    parser.add_argument('--generate-json', action='store_true', help='Generate JSON reports')
    parser.add_argument('--categories', nargs='+', help='Specific categories to test (default: all)')
    return parser.parse_args()


def run_tests_by_category(category: str, runner: TestRunner, verbose: bool = False) -> Dict[str, Any]:
    """
    Run tests for a specific category.
    
    Args:
        category: The category to run tests for
        runner: The TestRunner instance
        verbose: Whether to enable verbose output
        
    Returns:
        A dictionary containing test results and summary information
    """
    print(f"\n{'='*80}")
    print(f"Running tests for category: {category}")
    print(f"{'='*80}")
    
    # Run tests for this category
    start_time = time.time()
    results = runner.run_tests([category])
    end_time = time.time()
    
    # Get summary
    summary = runner.get_test_summary()
    
    # Print summary
    print(f"\nSummary for {category}:")
    print(f"  Total tests: {summary['total']}")
    print(f"  Passed: {summary['passed']}")
    print(f"  Failed: {summary['failed']}")
    print(f"  Skipped: {summary['skipped']}")
    print(f"  Error: {summary['error']}")
    print(f"  Duration: {summary['duration']:.2f} seconds")
    
    # Return results and summary
    return {
        'category': category,
        'results': results,
        'summary': summary,
        'start_time': start_time,
        'end_time': end_time,
        'duration': end_time - start_time
    }


def main():
    """Main entry point."""
    args = parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Create TestRunner
    config = {
        'verbose': args.verbose,
        'generate_html_report': args.generate_html,
        'generate_json_report': args.generate_json,
        'output_dir': args.output_dir,
    }
    runner = TestRunner()
    runner.update_config(config)
    
    # Discover and categorize tests
    runner.discover_tests()
    categories = runner.categorize_tests()
    
    # Get list of categories to test
    if args.categories:
        categories_to_test = [cat for cat in args.categories if cat in categories]
        if not categories_to_test:
            print("No valid categories specified. Available categories:")
            for cat in categories:
                print(f"  - {cat} ({len(categories[cat])} tests)")
            return 1
    else:
        # Default categories (main modules)
        categories_to_test = [
            'core_kr',
            'inference',
            'learning',
            'common_sense',
            'metacognition',
            'nlu_nlg',
            'ontology',
            'scalability',
            'symbol_grounding'
        ]
        # Filter to only include categories that have tests
        categories_to_test = [cat for cat in categories_to_test if cat in categories and categories[cat]]
    
    # Run tests for each category
    all_results = []
    for category in categories_to_test:
        category_result = run_tests_by_category(category, runner, args.verbose)
        all_results.append(category_result)
    
    # Save overall results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = os.path.join(args.output_dir, f"test_results_{timestamp}.json")
    with open(results_file, 'w') as f:
        json.dump({
            'timestamp': timestamp,
            'categories_tested': categories_to_test,
            'results': [
                {
                    'category': r['category'],
                    'total': r['summary']['total'],
                    'passed': r['summary']['passed'],
                    'failed': r['summary']['failed'],
                    'skipped': r['summary']['skipped'],
                    'error': r['summary']['error'],
                    'duration': r['duration']
                }
                for r in all_results
            ]
        }, f, indent=2)
    
    print(f"\nOverall results saved to {results_file}")
    
    # Print overall summary
    total_tests = sum(r['summary']['total'] for r in all_results)
    total_passed = sum(r['summary']['passed'] for r in all_results)
    total_failed = sum(r['summary']['failed'] for r in all_results)
    total_skipped = sum(r['summary']['skipped'] for r in all_results)
    total_error = sum(r['summary']['error'] for r in all_results)
    total_duration = sum(r['duration'] for r in all_results)
    
    print("\nOverall Summary:")
    print(f"  Categories tested: {len(categories_to_test)}")
    print(f"  Total tests: {total_tests}")
    print(f"  Passed: {total_passed}")
    print(f"  Failed: {total_failed}")
    print(f"  Skipped: {total_skipped}")
    print(f"  Error: {total_error}")
    print(f"  Total duration: {total_duration:.2f} seconds")
    
    # Return exit code based on test results
    return 1 if total_failed > 0 or total_error > 0 else 0


if __name__ == '__main__':
    sys.exit(main())