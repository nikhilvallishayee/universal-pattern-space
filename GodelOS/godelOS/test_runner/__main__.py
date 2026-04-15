"""
Main entry point for the GödelOS Test Runner.

This module allows the test runner to be executed directly using:
python -m godelOS.test_runner [options]
"""

import sys
from godelOS.test_runner.cli import main

if __name__ == "__main__":
    sys.exit(main())