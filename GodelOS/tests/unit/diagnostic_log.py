#!/usr/bin/env python
"""
Diagnostic script to validate issues with the GödelOS test suite.

This script checks for:
1. Missing classes that are imported by tests
2. Syntax errors in test files
3. Sample test runs with detailed error logging
"""

import sys
import os
import traceback
import importlib
import ast
import re
from pathlib import Path

def check_class_existence():
    """Check if the problematic classes exist."""
    print("\n=== Checking for Missing Classes ===")
    
    # Check for QueryResult
    print("\nChecking for QueryResult class...")
    try:
        # Try to import directly
        from godelOS.core_kr.knowledge_store.interface import QueryResult
        print("✓ QueryResult class found")
    except ImportError as e:
        print(f"✗ QueryResult class not found: {e}")
        
        # Check if it's defined but not exported
        try:
            import inspect
            from godelOS.core_kr.knowledge_store import interface
            
            print("Examining interface module content:")
            for name, obj in inspect.getmembers(interface):
                if inspect.isclass(obj):
                    print(f"  Found class: {name}")
        except Exception as e:
            print(f"Error examining interface module: {e}")
    
    # Check for LogicParser vs FormalLogicParser
    print("\nChecking for LogicParser class...")
    try:
        from godelOS.core_kr.formal_logic_parser.parser import LogicParser
        print("✓ LogicParser class found")
    except ImportError as e:
        print(f"✗ LogicParser class not found: {e}")
        
        try:
            from godelOS.core_kr.formal_logic_parser.parser import FormalLogicParser
            print("✓ FormalLogicParser class found instead")
            print("  This suggests a class name mismatch in imports")
        except ImportError:
            print("✗ FormalLogicParser class not found either")
    
    # Check for ParametricType
    print("\nChecking for ParametricType class...")
    try:
        from godelOS.core_kr.type_system.types import ParametricType
        print("✓ ParametricType class found")
    except ImportError as e:
        print(f"✗ ParametricType class not found: {e}")
        
        try:
            from godelOS.core_kr.type_system import types
            print("Related classes in type_system.types:")
            for name, obj in inspect.getmembers(types):
                if inspect.isclass(obj) and 'Type' in name:
                    print(f"  Found class: {name}")
        except Exception as e:
            print(f"Error examining types module: {e}")

def check_syntax_errors():
    """Check for syntax errors in test files."""
    print("\n=== Checking for Syntax Errors ===")
    
    # Files to check
    files_to_check = [
        "tests/test_modal_tableau_prover_enhanced.py",
        "tests/test_knowledge_store_enhanced.py",
        "tests/test_parser_enhanced.py"
    ]
    
    for file_path in files_to_check:
        print(f"\nChecking {file_path}...")
        try:
            with open(file_path, "r") as f:
                file_content = f.read()
                
            # Try to compile the file to check for syntax errors
            compile(file_content, file_path, "exec")
            print(f"✓ No syntax errors found in {file_path}")
            
            # Check for indentation issues specifically
            lines = file_content.split('\n')
            for i, line in enumerate(lines, 1):
                if re.match(r'^def\s+\w+.*:$', line) and i < len(lines):
                    next_line = lines[i].rstrip()
                    if next_line and not re.match(r'^\s+', next_line):
                        print(f"⚠ Potential indentation issue at line {i+1}: {next_line}")
            
        except SyntaxError as e:
            print(f"✗ Syntax error found in {file_path}:")
            print(f"  Line {e.lineno}, column {e.offset}: {e.text}")
        except Exception as e:
            print(f"✗ Error checking {file_path}: {e}")

def examine_import_statements():
    """Examine import statements in test files to find patterns."""
    print("\n=== Examining Import Statements ===")
    
    # Find all test files
    test_files = list(Path("tests").glob("**/*.py"))
    
    # Classes we're interested in
    target_classes = ["QueryResult", "LogicParser", "ParametricType"]
    
    for file_path in test_files:
        try:
            with open(file_path, "r") as f:
                file_content = f.read()
            
            # Parse the file
            tree = ast.parse(file_content)
            
            # Find import statements
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    module = node.module
                    for name in node.names:
                        if name.name in target_classes:
                            print(f"Found import of {name.name} from {module} in {file_path}")
        except Exception as e:
            print(f"Error examining {file_path}: {e}")

def run_sample_tests():
    """Run a few sample tests with detailed error logging."""
    print("\n=== Running Sample Tests with Detailed Logging ===")
    
    # Sample test files to run
    test_files = [
        "tests/test_knowledge_store_enhanced.py",
        "tests/test_parser_enhanced.py",
        "tests/test_modal_tableau_prover_enhanced.py"
    ]
    
    for test_file in test_files:
        print(f"\nRunning test: {test_file}")
        try:
            # Use pytest directly to run a single test file
            import pytest
            result = pytest.main(["-v", test_file])
            print(f"Test result: {result}")
        except Exception as e:
            print(f"Error running test {test_file}: {e}")
            traceback.print_exc()

def main():
    """Main function to run all diagnostic checks."""
    print("=== GödelOS Test Suite Diagnostic Log ===")
    print(f"Current working directory: {os.getcwd()}")
    
    # Run all checks
    check_class_existence()
    check_syntax_errors()
    examine_import_statements()
    run_sample_tests()
    
    print("\n=== Diagnostic Complete ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())