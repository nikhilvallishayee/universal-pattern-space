# 🚀 GödelOS Enhanced Test Runner ✨

> _Test smarter, not harder. Make your CI pop with style and substance._ 😎

- Modern, visually stunning test output
- Effortless configuration for any workflow
- Built for devs who love clarity, speed, and a touch of flair

--- GödelOS Enhanced Test Runner

The GödelOS Test Runner is a comprehensive Python test suite runner utility designed to provide visually appealing, informative test output with extensive configuration options.

## Features

### Visually Appealing Output
- Color-coded console output with emoji indicators for test status
- Clear phase separation between test setup, execution, and teardown
- Progress bars and spinners for real-time test execution feedback
- Configurable verbosity levels from minimal to debug

### Descriptive Test Cases
- Automatic extraction of test docstrings to understand test purpose
- Display of expected behavior and edge cases from docstrings
- Support for structured docstring formats (Google style, reStructuredText)

### Test Organization
- Automatic test discovery based on configurable patterns
- Test categorization by module, package, or custom categories
- Support for pytest markers for additional categorization
- Filtering tests by pattern or category

### Comprehensive Reporting
- Detailed timing information for each test phase
- Summary statistics including pass/fail rates and execution times
- Identification of slow tests and performance bottlenecks
- HTML and JSON report generation for sharing and analysis

### Flexible Configuration
- Command-line interface with extensive options
- Configuration file support for persistent settings
- Environment variable support for CI/CD integration
- Programmatic API for integration into other tools

## Installation

The test runner is included as part of the GödelOS package:

```bash
pip install godelOS
```

## Basic Usage

### Command Line Interface

Run all tests in the project:

```bash
python -m godelOS.test_runner
```

Run tests with enhanced output:

```bash
python -m godelOS.test_runner --verbose --generate-html-report --show-phase-separation
```

Run specific categories of tests:

```bash
python -m godelOS.test_runner --category inference --category learning
```

Run tests matching a pattern:

```bash
python -m godelOS.test_runner --pattern "test_inference*.py"
```

### Programmatic API

```python
from godelOS.test_runner import TestRunner, TestRunnerConfig

# Create a configuration
config = TestRunnerConfig(
    verbose=True,
    generate_html_report=True,
    html_report_path="test_output/report.html",
    show_phase_separation=True
)

# Create a test runner
runner = TestRunner()
runner.update_config(config.__dict__)

# Run tests
runner.discover_tests()
runner.categorize_tests()
results = runner.run_tests()

# Get summary
summary = runner.get_test_summary()
print(f"Passed: {summary['passed']}/{summary['total']} tests")
```

## Configuration Options

The test runner supports numerous configuration options:

### Test Discovery
- `test_patterns`: List of glob patterns to match test files (default: `["test_*.py"]`)
- `test_dirs`: List of directories to search for tests (default: `["tests"]`)

### Output Options
- `verbose`: Enable verbose output (default: `False`)
- `output_dir`: Directory for test output files (default: `None`)
- `output_level`: Output verbosity level (`"MINIMAL"`, `"NORMAL"`, `"VERBOSE"`, `"DEBUG"`)
- `use_colors`: Enable colored output (default: `True`)
- `use_emoji`: Enable emoji in output (default: `True`)

### Display Options
- `show_docstrings`: Show docstrings in output (default: `True`)
- `show_phase_separation`: Show test phase separation (default: `True`)
- `terminal_width`: Terminal width for formatting (default: `80`)

### Report Options
- `generate_html_report`: Generate HTML report (default: `False`)
- `html_report_path`: Path to save HTML report (default: `None`)
- `generate_json_report`: Generate JSON report (default: `False`)
- `json_report_path`: Path to save JSON report (default: `None`)

### Execution Options
- `parallel`: Run tests in parallel (default: `False`)
- `max_workers`: Maximum number of parallel workers (default: `1`)
- `timeout`: Timeout for test execution in seconds (default: `300`)

## Examples

See the `examples/` directory for sample usage:

- `examples/enhanced_test_runner_example.py`: Basic usage with different configurations
- `examples/test_runner_demo.py`: Comprehensive demo of all features
- `examples/test_runner_demo_README.md`: Detailed documentation for the comprehensive demo

The comprehensive demo showcases all capabilities of the test runner including:
- Test discovery and explicit registration
- Tests with different outcomes (pass, fail, error, skip)
- Different docstring formats and detailed test documentation
- Custom test categories and filtering
- Timing analysis for performance testing
- HTML and JSON report generation
- Multiple verbosity levels

## Contributing

Contributions to the test runner are welcome! See the `CONTRIBUTING.md` file for guidelines.