"""
Test Categorizer Module for the GödelOS Test Runner.

This module provides functionality to categorize tests based on various criteria
such as module path, markers, and custom rules.
"""

import fnmatch
import os
import re
from typing import Dict, List, Optional, Set, Any, Callable

class TestCategorizer:
    """
    Categorizes tests into logical groups.
    
    This class is responsible for organizing tests into categories based on
    various criteria such as directory structure, test markers, naming patterns,
    and custom rules.
    """
    
    def __init__(self, config: Any):
        """
        Initialize the TestCategorizer.
        
        Args:
            config: Configuration object containing categorization settings.
        """
        self.config = config
        self.categories = getattr(config, 'categories', {})
        # Add default categories if not present
        if not self.categories:
            self.categories = self._create_default_categories()
    
    def _create_default_categories(self) -> Dict[str, List[str]]:
        """
        Create default test categories based on the GödelOS project structure.
        
        Returns:
            A dictionary mapping category names to patterns that match tests in that category.
        """
        return {
            "core_kr": ["tests/test_ast.py", "tests/test_knowledge_store.py", 
                       "tests/test_parser.py", "tests/test_type_system.py", 
                       "tests/test_unification.py", "tests/test_belief_revision.py", 
                       "tests/test_probabilistic_logic.py"],
            "inference": ["tests/test_inference_engine.py", "tests/test_resolution_prover.py", 
                         "tests/test_modal_tableau_prover.py", "tests/test_clp_module.py", 
                         "tests/test_smt_interface.py", "tests/test_analogical_reasoning_engine.py"],
            "learning": ["tests/test_explanation_based_learner.py", "tests/test_ilp_engine.py", 
                        "tests/test_meta_control_rl_module.py", "tests/test_template_evolution_module.py"],
            "common_sense": ["tests/common_sense/*"],
            "metacognition": ["tests/metacognition/*"],
            "nlu_nlg": ["tests/nlu_nlg/*"],
            "ontology": ["tests/ontology/*"],
            "scalability": ["tests/scalability/*"],
            "symbol_grounding": ["tests/symbol_grounding/*"],
            "integration": ["tests/**/test_integration.py"],
            "unit": ["tests/test_*.py"],
        }
    
    def categorize_tests(self, test_files_info: Dict[str, Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Categorize tests based on configured categories.
        
        Args:
            test_files_info: Dictionary mapping file paths to test file information.
            
        Returns:
            A dictionary mapping category names to lists of test node IDs.
        """
        categorized_tests = {category: [] for category in self.categories}
        
        # Process each test file
        for file_path, file_info in test_files_info.items():
            if 'error' in file_info:
                continue
                
            # Get test node IDs from this file
            test_node_ids = [item['full_name'] for item in file_info.get('test_items', [])]
            
            # Assign tests to categories
            for category, patterns in self.categories.items():
                matching_tests = self._match_tests_to_category(file_path, test_node_ids, patterns)
                categorized_tests[category].extend(matching_tests)
        
        # Remove duplicates and sort
        for category in categorized_tests:
            categorized_tests[category] = sorted(set(categorized_tests[category]))
        
        return categorized_tests
    
    def _match_tests_to_category(self, file_path: str, test_node_ids: List[str], patterns: List[str]) -> List[str]:
        """
        Match tests to a category based on patterns.
        
        Args:
            file_path: Path to the test file.
            test_node_ids: List of test node IDs from the file.
            patterns: List of patterns that define the category.
            
        Returns:
            A list of test node IDs that match the category.
        """
        matching_tests = []
        
        for pattern in patterns:
            # Check if the pattern matches the file path
            if self._match_pattern(file_path, pattern):
                matching_tests.extend(test_node_ids)
                continue
                
            # Check if the pattern matches any test node ID
            for node_id in test_node_ids:
                if self._match_pattern(node_id, pattern):
                    matching_tests.append(node_id)
        
        return matching_tests
    
    def _match_pattern(self, string: str, pattern: str) -> bool:
        """
        Check if a string matches a pattern.
        
        The pattern can be:
        - A glob pattern (e.g., "tests/test_*.py")
        - A regex pattern if it starts with "regex:" (e.g., "regex:test_.*_function")
        - A marker pattern if it starts with "marker:" (e.g., "marker:slow")
        
        Args:
            string: The string to check.
            pattern: The pattern to match against.
            
        Returns:
            True if the string matches the pattern, False otherwise.
        """
        # Check for regex pattern
        if pattern.startswith("regex:"):
            regex = pattern[6:]
            return bool(re.search(regex, string))
            
        # Check for marker pattern (not applicable for file paths)
        elif pattern.startswith("marker:"):
            # Marker matching is handled separately when we have test metadata
            return False
            
        # Default to glob pattern
        else:
            return fnmatch.fnmatch(string, pattern)
    
    def categorize_by_module(self, test_files_info: Dict[str, Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Categorize tests by module/package structure.
        
        Args:
            test_files_info: Dictionary mapping file paths to test file information.
            
        Returns:
            A dictionary mapping module names to lists of test node IDs.
        """
        module_categories = {}
        
        for file_path, file_info in test_files_info.items():
            if 'error' in file_info:
                continue
                
            # Extract module name from file path
            # Assuming tests are organized in a structure that mirrors the module structure
            # e.g., tests/module_name/test_file.py -> module_name
            parts = file_path.split(os.sep)
            if len(parts) >= 2 and parts[0] == 'tests':
                if len(parts) >= 3:
                    module_name = parts[1]
                else:
                    # For tests at the root level, use the filename without "test_" prefix
                    filename = parts[-1]
                    if filename.startswith('test_'):
                        module_name = filename[5:].split('.')[0]
                    else:
                        module_name = 'core'
                
                # Get test node IDs from this file
                test_node_ids = [item['full_name'] for item in file_info.get('test_items', [])]
                
                # Add to module category
                if module_name not in module_categories:
                    module_categories[module_name] = []
                module_categories[module_name].extend(test_node_ids)
        
        # Remove duplicates and sort
        for module_name in module_categories:
            module_categories[module_name] = sorted(set(module_categories[module_name]))
        
        return module_categories
    
    def categorize_by_markers(self, test_files_info: Dict[str, Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Categorize tests by pytest markers.
        
        Args:
            test_files_info: Dictionary mapping file paths to test file information.
            
        Returns:
            A dictionary mapping marker names to lists of test node IDs.
        """
        marker_categories = {}
        
        for file_path, file_info in test_files_info.items():
            if 'error' in file_info:
                continue
                
            # Process each test item
            for test_item in file_info.get('test_items', []):
                for marker in test_item.get('markers', []):
                    if marker not in marker_categories:
                        marker_categories[marker] = []
                    marker_categories[marker].append(test_item['full_name'])
        
        # Remove duplicates and sort
        for marker in marker_categories:
            marker_categories[marker] = sorted(set(marker_categories[marker]))
        
        return marker_categories
    
    def get_category_tests(self, category: str) -> List[str]:
        """
        Get all tests in a specific category.
        
        Args:
            category: Name of the category.
            
        Returns:
            A list of test node IDs in the category.
        """
        if not hasattr(self, 'categorized_tests'):
            return []
            
        return self.categorized_tests.get(category, [])
    
    def add_custom_category(self, name: str, patterns: List[str]) -> None:
        """
        Add a custom test category.
        
        Args:
            name: Name of the category.
            patterns: List of patterns that define the category.
        """
        self.categories[name] = patterns