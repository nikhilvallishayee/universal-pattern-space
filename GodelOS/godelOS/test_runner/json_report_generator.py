"""
JSON Report Generator Module for the GödelOS Test Runner.

This module provides functionality to generate comprehensive JSON reports
for test results, including detailed test information, timing, and statistics.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

from godelOS.test_runner.results_collector import EnhancedTestResult


class JSONReportGenerator:
    """
    Generates comprehensive JSON reports for test results.
    
    This class is responsible for generating detailed JSON reports that include
    complete test information, timing data, and statistics, suitable for
    programmatic analysis or visualization.
    """
    
    def __init__(self, config: Any):
        """
        Initialize the JSONReportGenerator.
        
        Args:
            config: Configuration object containing JSON report settings.
        """
        self.config = config
    
    def generate_report(self, results: Dict[str, Dict[str, EnhancedTestResult]], 
                       summary: Dict[str, Any], output_path: Optional[str] = None) -> str:
        """
        Generate a JSON report for test results.
        
        Args:
            results: Dictionary mapping category names to dictionaries of test results.
            summary: Dictionary containing summary information.
            output_path: Optional path to save the report to.
            
        Returns:
            The path to the generated report.
        """
        # Create JSON content
        json_content = self._create_json_content(results, summary)
        
        # Determine output path
        if not output_path:
            if hasattr(self.config, 'json_report_path') and self.config.json_report_path:
                output_path = self.config.json_report_path
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_dir = getattr(self.config, 'output_dir', '.')
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(output_dir, f"test_report_{timestamp}.json")
        
        # Write to file
        with open(output_path, 'w') as f:
            json.dump(json_content, f, indent=2)
        
        return output_path
    
    def _create_json_content(self, results: Dict[str, Dict[str, EnhancedTestResult]], 
                           summary: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create the JSON content for the report.
        
        Args:
            results: Dictionary mapping category names to dictionaries of test results.
            summary: Dictionary containing summary information.
            
        Returns:
            A dictionary containing the JSON content.
        """
        # Start with basic report metadata
        report = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "version": "1.0.0"
            },
            "summary": self._format_summary(summary),
            "categories": {},
            "tests": []
        }
        
        # Add results by category
        for category, category_results in results.items():
            category_data = self._format_category_results(category, category_results)
            report["categories"][category] = category_data
            
            # Add individual test results to the flat list
            for node_id, result in category_results.items():
                test_data = self._format_test_result(result)
                report["tests"].append(test_data)
        
        return report
    
    def _format_summary(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format the summary section of the report.
        
        Args:
            summary: Dictionary containing summary information.
            
        Returns:
            A dictionary containing the formatted summary.
        """
        formatted_summary = {
            "status": summary.get('status', 'unknown'),
            "total_tests": summary.get('total', 0),
            "passed_tests": summary.get('passed', 0),
            "failed_tests": summary.get('failed', 0),
            "skipped_tests": summary.get('skipped', 0),
            "error_tests": summary.get('error', 0),
            "total_duration": summary.get('duration', 0),
            "start_time": summary.get('start_time', '').isoformat() if summary.get('start_time') else None,
            "end_time": summary.get('end_time', '').isoformat() if summary.get('end_time') else None,
            "pass_rate": summary.get('passed', 0) / summary.get('total', 1) if summary.get('total', 0) > 0 else 0
        }
        
        # Add timing statistics if available
        if 'average_duration' in summary:
            formatted_summary['average_duration'] = summary['average_duration']
        
        # Add slowest tests if available
        if 'slowest_tests' in summary:
            formatted_summary['slowest_tests'] = [
                {"node_id": node_id, "duration": duration}
                for node_id, duration in summary['slowest_tests']
            ]
        
        # Add category statistics if available
        if 'categories' in summary:
            formatted_summary['categories'] = summary['categories']
        
        return formatted_summary
    
    def _format_category_results(self, category: str, results: Dict[str, EnhancedTestResult]) -> Dict[str, Any]:
        """
        Format the results for a category.
        
        Args:
            category: The name of the category.
            results: Dictionary mapping node IDs to test results.
            
        Returns:
            A dictionary containing the formatted category results.
        """
        # Count results by outcome
        outcomes = {"passed": 0, "failed": 0, "skipped": 0, "error": 0, "xpassed": 0, "xfailed": 0}
        total_duration = 0.0
        
        for result in results.values():
            if result.outcome in outcomes:
                outcomes[result.outcome] += 1
            if result.duration is not None:
                total_duration += result.duration
        
        # Calculate pass rate
        total_tests = len(results)
        pass_rate = outcomes["passed"] / total_tests if total_tests > 0 else 0
        
        return {
            "name": category,
            "total_tests": total_tests,
            "outcomes": outcomes,
            "total_duration": total_duration,
            "pass_rate": pass_rate,
            "tests": list(results.keys())
        }
    
    def _format_test_result(self, result: EnhancedTestResult) -> Dict[str, Any]:
        """
        Format a single test result.
        
        Args:
            result: The EnhancedTestResult object to format.
            
        Returns:
            A dictionary containing the formatted test result.
        """
        formatted_result = {
            "node_id": result.node_id,
            "outcome": result.outcome,
            "duration": result.duration,
            "module_name": result.module_name,
            "class_name": result.class_name,
            "function_name": result.function_name,
            "category": result.category
        }
        
        # Add timing information if available
        if hasattr(result, 'start_time') and result.start_time:
            formatted_result['start_time'] = result.start_time.isoformat()
        if hasattr(result, 'end_time') and result.end_time:
            formatted_result['end_time'] = result.end_time.isoformat()
        
        # Add phase timing if available
        if hasattr(result, 'setup_time') and result.setup_time is not None:
            formatted_result['setup_time'] = result.setup_time
        if hasattr(result, 'execution_time') and result.execution_time is not None:
            formatted_result['execution_time'] = result.execution_time
        if hasattr(result, 'teardown_time') and result.teardown_time is not None:
            formatted_result['teardown_time'] = result.teardown_time
        
        # Add docstring information if available
        if hasattr(result, 'docstring') and result.docstring:
            formatted_result['docstring'] = result.docstring
        if hasattr(result, 'parsed_docstring') and result.parsed_docstring:
            formatted_result['parsed_docstring'] = result.parsed_docstring
        
        # Add error information if applicable
        if result.outcome in ('failed', 'error') and result.message:
            formatted_result['message'] = result.message
        if result.traceback:
            formatted_result['traceback'] = result.traceback
        
        # Add stdout/stderr if available
        if result.stdout:
            formatted_result['stdout'] = result.stdout
        if result.stderr:
            formatted_result['stderr'] = result.stderr
        
        # Add historical data if available
        if hasattr(result, 'previous_outcomes') and result.previous_outcomes:
            formatted_result['previous_outcomes'] = result.previous_outcomes
        if hasattr(result, 'previous_durations') and result.previous_durations:
            formatted_result['previous_durations'] = result.previous_durations
        
        return formatted_result