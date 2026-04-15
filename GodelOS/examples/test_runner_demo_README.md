# GödelOS Test Runner Comprehensive Demo

This document provides instructions for running and understanding the comprehensive test runner demo. The demo showcases all the capabilities of the GödelOS Test Runner, serving as both documentation and a practical example for users.

## Overview

The `test_runner_demo.py` script demonstrates the following features of the GödelOS Test Runner:

1. **Test Discovery and Registration**
   - Automatic test discovery based on patterns
   - Explicit test registration for fine-grained control

2. **Rich Docstring Support**
   - Tests with detailed docstrings explaining purpose, expected behavior, and edge cases
   - Support for different docstring formats (Google-style, reStructuredText)
   - Automatic extraction of test metadata from docstrings

3. **Test Categorization**
   - Categorization by module structure
   - Categorization by docstring tags
   - Custom category definitions
   - Running tests by category

4. **Test Outcomes**
   - Passing tests
   - Failing tests
   - Tests with errors
   - Skipped tests (unconditional and conditional)

5. **Verbosity Levels**
   - MINIMAL: Basic pass/fail information
   - NORMAL: Standard output with test details
   - VERBOSE: Detailed output with phase separation
   - DEBUG: Maximum information for troubleshooting

6. **Report Generation**
   - HTML reports with detailed test information
   - JSON reports for programmatic analysis
   - Customizable report paths

7. **Timing Analysis**
   - Fast vs. slow tests
   - Timing breakdown by test phase
   - Identification of performance bottlenecks

## Running the Demo

To run the comprehensive demo, follow these steps:

1. Ensure you're in the project root directory
2. Run the demo script:

```bash
python examples/test_runner_demo.py
```

This will execute all the demonstration functions in sequence, showing different aspects of the test runner's capabilities.

## Demo Components

The demo is organized into several demonstration functions:

### 1. Automatic Test Discovery

```bash
# This part demonstrates how tests are automatically discovered
```

Demonstrates how the test runner can automatically find and run tests based on patterns. The test runner will:
- Find all test classes in the demo file
- Categorize them automatically
- Run all discovered tests
- Generate HTML and JSON reports

### 2. Explicit Test Registration

```bash
# This part demonstrates explicit test registration
```

Shows how to explicitly register specific tests to run. This approach:
- Gives you fine-grained control over which tests run
- Allows you to create custom test suites
- Is useful for focused testing of specific functionality

### 3. Different Verbosity Levels

```bash
# This part demonstrates different verbosity levels
```

Runs the same tests with different verbosity settings:
- MINIMAL: Basic output suitable for CI/CD pipelines
- NORMAL: Standard output with test details
- VERBOSE: Detailed output with phase separation
- DEBUG: Maximum information for troubleshooting

### 4. Custom Categories

```bash
# This part demonstrates custom test categories
```

Shows how to define and use custom test categories:
- Define categories based on test patterns
- Define categories based on docstring tags
- Run tests by category
- Generate reports for specific categories

### 5. Comprehensive Demo

```bash
# This part runs a comprehensive demo of all features
```

Runs all tests with all features enabled:
- Full verbosity
- Detailed timing information
- Complete docstring extraction
- HTML and JSON report generation

## Understanding the Reports

The demo generates several HTML and JSON reports in the `test_output` directory:

### HTML Reports

HTML reports provide a user-friendly view of test results, including:
- Overall test summary
- Test categorization
- Detailed test results with docstrings
- Timing information
- Failure details

To view an HTML report, open it in any web browser:

```bash
# On macOS
open test_output/comprehensive_report.html

# On Linux
xdg-open test_output/comprehensive_report.html

# On Windows
start test_output/comprehensive_report.html
```

### JSON Reports

JSON reports provide structured test data for programmatic analysis:
- Machine-readable format
- Complete test information
- Suitable for integration with other tools

To view a JSON report in a formatted way:

```bash
cat test_output/comprehensive_report.json | python -m json.tool
```

## Sample Tests

The demo includes several test classes that demonstrate different aspects of the test runner:

1. **SimpleTests**: Basic tests with different outcomes (pass, fail, error, skip)
2. **DetailedTests**: Tests with Google-style docstrings
3. **ReStructuredTextTests**: Tests with reStructuredText-style docstrings
4. **TimingTests**: Tests with different execution times
5. **CategoryTests**: Tests demonstrating category features

Each test is documented with detailed docstrings explaining its purpose, expected behavior, and any edge cases it covers.

## Extending the Demo

You can extend this demo to test your own specific use cases:

1. Add new test classes to demonstrate additional features
2. Modify the configuration options to test different settings
3. Create custom categories for your specific testing needs
4. Add new demonstration functions for specialized features

## Troubleshooting

If you encounter issues running the demo:

1. Ensure you're running from the project root directory
2. Check that the GödelOS package is properly installed
3. Verify that the output directory is writable
4. Check for any error messages in the console output

For more detailed information about the test runner, refer to the main documentation in `godelOS/test_runner/README.md`.