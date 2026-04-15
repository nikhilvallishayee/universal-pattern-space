# GödelOS Test Coverage Analysis Tools

This directory contains a set of tools for analyzing the test coverage of the GödelOS project, with a particular focus on the metacognition and inference engine components.

## Overview

The analysis tools consist of three Python scripts and a shell script runner:

1. **test_coverage_analyzer.py**: Analyzes component-level test coverage, identifying which components have tests and which don't.
2. **method_coverage_analyzer.py**: Performs a more detailed method-level analysis, identifying which methods within each class are tested.
3. **generate_coverage_report.py**: Generates an HTML report from the JSON data produced by the test_coverage_analyzer.py script.
4. **run_test_coverage_analysis.sh**: A shell script that runs all three analysis scripts in sequence.

## Prerequisites

- Python 3.6 or higher
- Access to the GödelOS project source code

## Usage

### Running the Complete Analysis

The simplest way to run the complete analysis is to use the shell script:

```bash
./run_test_coverage_analysis.sh
```

This will run all three analysis scripts in sequence and generate the following reports:
- `test_coverage_report.json`: Basic component test coverage data
- `test_coverage_report.html`: Interactive HTML report of component test coverage
- `method_coverage_report.json`: Detailed method-level test coverage data

### Running Individual Scripts

You can also run each script individually:

```bash
# Basic component-level analysis
python3 test_coverage_analyzer.py

# Method-level analysis
python3 method_coverage_analyzer.py

# Generate HTML report (requires test_coverage_report.json)
python3 generate_coverage_report.py
```

## Output Files

### test_coverage_report.json

This file contains a JSON representation of the component-level test coverage analysis, including:
- Summary statistics (total components, components with/without tests, average coverage)
- Detailed information for each component (classes, functions, test files, coverage percentage)

### method_coverage_report.json

This file contains a more detailed JSON representation of the method-level test coverage analysis, including:
- Summary statistics (total classes, total methods, tested/untested methods)
- Detailed information for each component, class, and method
- Method complexity and test status

### test_coverage_report.html

This is an interactive HTML report generated from the test_coverage_report.json data. It provides a user-friendly visualization of the test coverage analysis, including:
- Summary statistics
- Component coverage overview
- Detailed component analysis
- Visual indicators of test coverage levels

## Customization

### Analyzing Different Modules

By default, the analysis focuses on the metacognition and inference engine modules. To analyze different modules, modify the `module_paths` parameter in the `main()` function of each script:

```python
# In test_coverage_analyzer.py and method_coverage_analyzer.py
analyzer.find_source_files(['godelOS/your_module_1', 'godelOS/your_module_2'])
```

### Customizing the HTML Report

The HTML report generation can be customized by modifying the `generate_html_report()` function in the `generate_coverage_report.py` script. You can adjust the styling, layout, and content of the report as needed.

## Interpreting the Results

The analysis results provide insights into the current state of test coverage in the GödelOS project:

- **Components without tests**: These are components that have no corresponding test files.
- **Low coverage components**: These are components with test files, but low test coverage.
- **Untested methods**: These are specific methods within classes that are not covered by tests.
- **Complex untested methods**: These are methods with high complexity that are not tested, which may be particularly risky.

Use these insights to prioritize areas for improving test coverage, focusing on critical components and complex methods.

## Limitations

- The method-level analysis uses a simple text-matching approach to determine if a method is tested, which may produce false positives or negatives.
- The complexity calculation is a simple approximation and may not accurately reflect the true complexity of methods.
- The analysis does not measure code coverage in terms of lines or branches executed during tests.

## Next Steps

After running the analysis, you can use the results to:
1. Identify critical components with insufficient test coverage
2. Prioritize which tests to write first
3. Track improvements in test coverage over time by running the analysis periodically