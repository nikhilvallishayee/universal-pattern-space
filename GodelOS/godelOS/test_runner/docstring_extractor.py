"""
Docstring Extractor Module for the GödelOS Test Runner.

This module provides functionality to extract and parse docstrings from test
functions, enhancing test results with documentation information.
"""

import inspect
import re
from typing import Dict, Optional, Any

from godelOS.test_runner.results_collector import EnhancedTestResult


class DocstringExtractor:
    """
    Extracts and parses docstrings from test functions.
    
    This class is responsible for extracting docstrings from test functions and
    methods, parsing them to identify purpose, expected behavior, and edge cases,
    and enhancing test results with this information.
    """
    
    def __init__(self, config: Any):
        """
        Initialize the DocstringExtractor.
        
        Args:
            config: Configuration object containing docstring extraction settings.
        """
        self.config = config
    
    def extract_docstring(self, func: Any) -> Optional[str]:
        """
        Extract the docstring from a function or method.
        
        Args:
            func: The function or method object to extract the docstring from.
            
        Returns:
            The docstring as a string, or None if no docstring is found.
        """
        if not func:
            return None
            
        return inspect.getdoc(func)
    
    def parse_docstring(self, docstring: Optional[str]) -> Dict[str, str]:
        """
        Parse a docstring to extract structured information.
        
        This method attempts to identify sections in the docstring that describe:
        - Purpose: The main purpose of the test
        - Expected behavior: What the test expects to happen
        - Edge cases: Special cases the test handles
        - Parameters: Test parameters and their descriptions
        - Returns: Expected return values
        - Raises: Exceptions that might be raised
        
        Args:
            docstring: The docstring to parse.
            
        Returns:
            A dictionary with keys for extracted information categories,
            with corresponding extracted text as values.
        """
        if not docstring:
            return {
                'purpose': '',
                'expected_behavior': '',
                'edge_cases': '',
                'parameters': '',
                'returns': '',
                'raises': ''
            }
        
        # Initialize result dictionary
        result = {
            'purpose': '',
            'expected_behavior': '',
            'edge_cases': '',
            'parameters': '',
            'returns': '',
            'raises': ''
        }
        
        # Extract purpose (first paragraph of the docstring)
        paragraphs = docstring.split('\n\n')
        if paragraphs:
            result['purpose'] = paragraphs[0].strip()
        
        # Look for sections that might indicate expected behavior
        behavior_patterns = [
            r'(?:Expected behavior|Expects|Should|Expected result|Expected output):(.*?)(?:\n\n|\Z)',
            r'(?:This test (?:expects|verifies|checks|ensures|tests|validates)):(.*?)(?:\n\n|\Z)',
            r'(?:This test (?:expects|verifies|checks|ensures|tests|validates))(.*?)(?:\n\n|\Z)',
            r'(?:Verifies that|Ensures that|Checks that|Tests that|Validates that)(.*?)(?:\n\n|\Z)'
        ]
        
        for pattern in behavior_patterns:
            match = re.search(pattern, docstring, re.DOTALL | re.IGNORECASE)
            if match:
                result['expected_behavior'] = match.group(1).strip()
                break
        
        # Look for sections that might indicate edge cases
        edge_patterns = [
            r'(?:Edge cases|Corner cases|Special cases|Boundary conditions|Limits):(.*?)(?:\n\n|\Z)',
            r'(?:Also handles|Also tests|Additionally tests|Edge conditions|Special conditions):(.*?)(?:\n\n|\Z)',
            r'(?:Test handles|Test covers)(?:.*?)(?:edge cases?|corner cases?|special cases?|boundary conditions?)(.*?)(?:\n\n|\Z)'
        ]
        
        for pattern in edge_patterns:
            match = re.search(pattern, docstring, re.DOTALL | re.IGNORECASE)
            if match:
                result['edge_cases'] = match.group(1).strip()
                break
        
        # Extract parameters section
        params_match = re.search(r'(?:Parameters|Args|Arguments):(.*?)(?:(?:Returns|Raises|Yields|Examples|Notes):|$)',
                               docstring, re.DOTALL | re.IGNORECASE)
        if params_match:
            result['parameters'] = params_match.group(1).strip()
        
        # Extract returns section
        returns_match = re.search(r'(?:Returns|Return value):(.*?)(?:(?:Raises|Yields|Examples|Notes):|$)',
                                docstring, re.DOTALL | re.IGNORECASE)
        if returns_match:
            result['returns'] = returns_match.group(1).strip()
        
        # Extract raises section
        raises_match = re.search(r'(?:Raises|Exceptions|Errors):(.*?)(?:(?:Returns|Yields|Examples|Notes):|$)',
                               docstring, re.DOTALL | re.IGNORECASE)
        if raises_match:
            result['raises'] = raises_match.group(1).strip()
        
        # Try to extract information from reStructuredText or Google style docstrings
        if not result['expected_behavior']:
            # Look for descriptions after parameter sections
            for line in docstring.split('\n'):
                if re.match(r'\s*:param\s+\w+:\s*(.*)', line, re.IGNORECASE):
                    param_desc = re.match(r'\s*:param\s+\w+:\s*(.*)', line, re.IGNORECASE).group(1)
                    if 'expect' in param_desc.lower() or 'should' in param_desc.lower():
                        result['expected_behavior'] += param_desc + ' '
        
        return result
    
    def enhance_result_with_docstring(self, result: EnhancedTestResult, func: Any = None) -> EnhancedTestResult:
        """
        Enhance a test result with docstring information.
        
        This method extracts the docstring from the test function, parses it to identify
        key sections like purpose and expected behavior, and adds this information to
        the test result object.
        
        Args:
            result: The EnhancedTestResult object to enhance.
            func: Optional function object. If not provided, the function will be
                 looked up based on the node_id in the result.
                 
        Returns:
            The enhanced test result with docstring information added.
        """
        if not func:
            # In a real implementation, we would need to look up the function
            # based on the node_id in the result. This is a placeholder.
            return result
        
        # Extract and parse the docstring
        docstring = self.extract_docstring(func)
        parsed_docstring = self.parse_docstring(docstring)
        
        # Enhance the result
        result.docstring = docstring
        result.parsed_docstring = parsed_docstring
        
        # Try to infer test metadata from docstring if not already set
        if not result.category and parsed_docstring.get('purpose'):
            # Try to infer category from purpose
            purpose_lower = parsed_docstring['purpose'].lower()
            if 'integration' in purpose_lower:
                result.category = 'integration'
            elif 'unit' in purpose_lower:
                result.category = 'unit'
            elif 'performance' in purpose_lower or 'benchmark' in purpose_lower:
                result.category = 'performance'
        
        # Extract tags from docstring if available
        if parsed_docstring.get('purpose') or parsed_docstring.get('expected_behavior'):
            combined_text = f"{parsed_docstring.get('purpose', '')} {parsed_docstring.get('expected_behavior', '')}"
            # Look for common tag indicators like [tag], #tag, @tag
            tag_matches = re.findall(r'[\[\(]([a-zA-Z0-9_-]+)[\]\)]|#([a-zA-Z0-9_-]+)|@([a-zA-Z0-9_-]+)', combined_text)
            if tag_matches:
                for match in tag_matches:
                    # Each match is a tuple with possible matches from different patterns
                    tag = next((t for t in match if t), None)
                    if tag and tag not in result.tags:
                        result.tags.append(tag)
        
        return result