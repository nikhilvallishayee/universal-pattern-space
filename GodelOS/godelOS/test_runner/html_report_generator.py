"""
HTML Report Generator Module for the GödelOS Test Runner.

This module provides functionality to generate clean, minimal HTML reports
for test results.
"""

import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

from godelOS.test_runner.results_collector import EnhancedTestResult


class HTMLReportGenerator:
    """
    Generates clean, minimal HTML reports for test results.
    
    This class is responsible for generating HTML reports that display test
    results in a clean, minimal format, focusing on basic pass/fail information.
    """
    
    def __init__(self, config: Any):
        """
        Initialize the HTMLReportGenerator.
        
        Args:
            config: Configuration object containing HTML report settings.
        """
        self.config = config
        
        # Define colors for different test statuses
        self.status_colors = {
            'passed': '#4CAF50',  # Green
            'failed': '#F44336',  # Red
            'skipped': '#FFC107',  # Amber
            'xpassed': '#FF9800',  # Orange
            'xfailed': '#FF9800',  # Orange
            'error': '#F44336',   # Red
        }
        
        # Define emoji for different test statuses (as HTML entities)
        self.status_emoji = {
            'passed': '✅',
            'failed': '❌',
            'skipped': '⏭️',
            'xpassed': '⚠️',
            'xfailed': '⚠️',
            'error': '💥',
        }
    
    def format_text(self, text: str, status: Optional[str] = None, error: bool = False) -> str:
        """
        Format text with HTML styling based on status.
        
        Args:
            text: The text to format.
            status: Optional status to determine styling.
            error: Whether this is an error message.
            
        Returns:
            The HTML-formatted text.
        """
        if error:
            return f'<span style="color: #F44336;">{text}</span>'
        
        if status and status in self.status_colors:
            return f'<span style="color: {self.status_colors[status]};">{text}</span>'
        
        return text
    
    def generate_report(self, results: Dict[str, Dict[str, EnhancedTestResult]], 
                        summary: Dict[str, Any], output_path: Optional[str] = None) -> str:
        """
        Generate an HTML report for test results.
        
        Args:
            results: Dictionary mapping category names to dictionaries of test results.
            summary: Dictionary containing summary information.
            output_path: Optional path to save the report to.
            
        Returns:
            The path to the generated report.
        """
        # Create HTML content
        html_content = self._create_html_content(results, summary)
        
        # Determine output path
        if not output_path:
            if hasattr(self.config, 'html_report_path') and self.config.html_report_path:
                output_path = self.config.html_report_path
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_dir = getattr(self.config, 'output_dir', '.')
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(output_dir, f"test_report_{timestamp}.html")
        
        # Write to file
        with open(output_path, 'w') as f:
            f.write(html_content)
        
        return output_path
    
    def _create_html_content(self, results: Dict[str, Dict[str, EnhancedTestResult]], 
                           summary: Dict[str, Any]) -> str:
        """
        Create the HTML content for the report.
        
        Args:
            results: Dictionary mapping category names to dictionaries of test results.
            summary: Dictionary containing summary information.
            
        Returns:
            The HTML content as a string.
        """
        # Start with HTML header
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Report - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1, h2, h3 {{
            margin-top: 20px;
            margin-bottom: 10px;
        }}
        .summary {{
            background-color: #f5f5f5;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 20px;
        }}
        .summary-item {{
            margin-bottom: 5px;
        }}
        .category {{
            margin-bottom: 30px;
        }}
        .test-result {{
            margin-bottom: 10px;
            padding: 10px;
            border-radius: 5px;
            border-left: 5px solid #ddd;
        }}
        .test-passed {{
            border-left-color: #4CAF50;
            background-color: rgba(76, 175, 80, 0.1);
        }}
        .test-failed {{
            border-left-color: #F44336;
            background-color: rgba(244, 67, 54, 0.1);
        }}
        .test-skipped {{
            border-left-color: #FFC107;
            background-color: rgba(255, 193, 7, 0.1);
        }}
        .test-error {{
            border-left-color: #F44336;
            background-color: rgba(244, 67, 54, 0.1);
        }}
        .test-header {{
            font-weight: bold;
            display: flex;
            justify-content: space-between;
        }}
        .test-details {{
            margin-top: 5px;
            font-size: 0.9em;
        }}
        .test-message {{
            margin-top: 10px;
            font-family: monospace;
            white-space: pre-wrap;
            background-color: #f8f8f8;
            padding: 10px;
            border-radius: 3px;
        }}
        .docstring {{
            margin-top: 10px;
            font-style: italic;
            color: #666;
        }}
    </style>
</head>
<body>
    <h1>Test Report</h1>
"""
        
        # Add summary section
        html += self.format_summary(summary)
        
        # Add results by category
        for category, category_results in results.items():
            html += self.format_category_results(category, category_results)
        
        # Close HTML
        html += """
</body>
</html>
"""
        
        return html
    
    def format_summary(self, summary: Dict[str, Any]) -> str:
        """
        Format the summary section of the report.
        
        Args:
            summary: Dictionary containing summary information.
            
        Returns:
            The HTML for the summary section.
        """
        status = summary.get('status', 'unknown')
        total = summary.get('total', 0)
        passed = summary.get('passed', 0)
        failed = summary.get('failed', 0)
        skipped = summary.get('skipped', 0)
        error = summary.get('error', 0)
        duration = summary.get('duration', 0)
        
        # Calculate pass rate
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        # Format summary HTML
        html = """
    <div class="summary">
        <h2>Summary</h2>
"""
        
        html += f'        <div class="summary-item">Status: {self.format_text(status.upper(), status)}</div>\n'
        html += f'        <div class="summary-item">Total Tests: {total}</div>\n'
        html += f'        <div class="summary-item">Passed: {self.format_text(str(passed), "passed")} ({pass_rate:.1f}%)</div>\n'
        
        if failed > 0:
            html += f'        <div class="summary-item">Failed: {self.format_text(str(failed), "failed")}</div>\n'
        
        if skipped > 0:
            html += f'        <div class="summary-item">Skipped: {self.format_text(str(skipped), "skipped")}</div>\n'
        
        if error > 0:
            html += f'        <div class="summary-item">Error: {self.format_text(str(error), "error")}</div>\n'
        
        html += f'        <div class="summary-item">Duration: {duration:.2f} seconds</div>\n'
        html += f'        <div class="summary-item">Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>\n'
        
        html += """    </div>
"""
        
        return html
    
    def format_category_results(self, category: str, results: Dict[str, EnhancedTestResult]) -> str:
        """
        Format the results for a category.
        
        Args:
            category: The name of the category.
            results: Dictionary mapping node IDs to test results.
            
        Returns:
            The HTML for the category results.
        """
        if not results:
            return ""
        
        html = f"""
    <div class="category">
        <h2>Category: {category}</h2>
"""
        
        # Sort results by outcome (failed first, then error, then the rest)
        sorted_results = sorted(
            results.items(),
            key=lambda x: (
                0 if x[1].outcome == 'failed' else
                1 if x[1].outcome == 'error' else
                2
            )
        )
        
        for node_id, result in sorted_results:
            html += self.format_test_result(result)
        
        html += """    </div>
"""
        
        return html
    
    def format_test_result(self, result: EnhancedTestResult) -> str:
        """
        Format a single test result.
        
        Args:
            result: The EnhancedTestResult object to format.
            
        Returns:
            The HTML for the test result.
        """
        # Determine CSS class based on outcome
        css_class = f"test-{result.outcome}" if result.outcome in self.status_colors else "test-result"
        
        # Format test result HTML
        html = f"""
        <div class="test-result {css_class}">
            <div class="test-header">
                <span>{self.status_emoji.get(result.outcome, '')} {result.node_id}</span>
                <span>{result.duration:.2f}s</span>
            </div>
"""
        
        # Add docstring if available
        if hasattr(result, 'docstring') and result.docstring:
            html += f'            <div class="docstring">{result.docstring}</div>\n'
        
        # Add parsed docstring if available
        if hasattr(result, 'parsed_docstring') and result.parsed_docstring:
            parsed = result.parsed_docstring
            if parsed.get('purpose'):
                html += f'            <div class="test-details">Purpose: {parsed["purpose"]}</div>\n'
            if parsed.get('expected_behavior'):
                html += f'            <div class="test-details">Expected: {parsed["expected_behavior"]}</div>\n'
            if parsed.get('edge_cases'):
                html += f'            <div class="test-details">Edge Cases: {parsed["edge_cases"]}</div>\n'
        
        # Add message and traceback for non-passing tests
        if result.outcome not in ('passed', 'skipped') and result.message:
            html += f'            <div class="test-message">{result.message}</div>\n'
        
        html += """        </div>
"""
        
        return html