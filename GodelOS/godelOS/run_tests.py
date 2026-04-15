#!/usr/bin/env python
"""
Standalone script to run the GödelOS test runner.

This script provides a convenient way to run the test runner from the command line.
It can be executed directly or through the Python interpreter.

Usage:
    ./run_tests.py [options]
    python run_tests.py [options]
"""

import sys
from godelOS.test_runner.cli import main

if __name__ == "__main__":
    sys.exit(main())