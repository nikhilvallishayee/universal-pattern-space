# GödelOS Test Quick Reference Guide

This quick reference guide provides essential information for working with the GödelOS testing infrastructure. It covers common commands, test runner options, result interpretation, and guidelines for adding new tests.

## Common Commands for Running Tests

### Basic Test Execution

Run all tests:
```bash
python -m godelOS.run_tests
```

Run enhanced tests:
```bash
python run_enhanced_tests.py
```

Run tests for a specific module:
```bash
python -m godelOS.run_tests tests/metacognition/
```

Run a specific test file:
```bash
python -m godelOS.run_tests tests/metacognition/test_meta_knowledge.py
```

Run a specific test:
```bash
python -m godelOS.run_tests tests/metacognition/test_meta_knowledge.py::TestMetaKnowledge::test_initialize_meta_knowledge
```

### Running Tests by Category

Run tests in the "metacognition" category:
```bash
python -m godelOS.run_tests --category metacognition
```

Run tests in multiple categories:
```bash
python -m godelOS.run_tests --category metacognition,inference
```

Run integration tests:
```bash
python -m godelOS.run_tests --category integration
```

Run tests with a specific marker:
```bash
python -m godelOS.run_tests -m "slow"
```

### Running Tests with Different Verbosity

Run with minimal output:
```bash
python -m godelOS.run_tests --quiet
```

Run with verbose output:
```bash
python -m godelOS.run_tests -v
```

Run with very verbose output:
```bash
python -m godelOS.run_tests -vv
```

### Generating Test Reports

Generate HTML report:
```bash
python -m godelOS.run_tests --html=report.html
```

Generate JSON report:
```bash
python -m godelOS.run_tests --json=report.json
```

Generate both HTML and JSON reports:
```bash
python -m godelOS.run_tests --html=report.html --json=report.json
```

## Test Runner Options and Examples

### Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `--config` | Path to configuration file | None |
| `--output-dir` | Directory to store test reports | test_output |
| `-v`, `--verbose` | Enable verbose output | False |
| `--category` | Run tests in specific categories | None |
| `-m` | Run tests with specific markers | None |
| `--html` | Generate HTML report | None |
| `--json` | Generate JSON report | None |
| `--quiet` | Minimize output | False |
| `--parallel` | Run tests in parallel | False |
| `--workers` | Number of parallel workers | auto |
| `--timeout` | Test timeout in seconds | 300 |

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GODEL_TEST_CONFIG` | Path to configuration file | None |
| `GODEL_TEST_OUTPUT_DIR` | Directory to store test reports | test_output |
| `GODEL_TEST_VERBOSE` | Enable verbose output | False |
| `GODEL_TEST_PARALLEL` | Run tests in parallel | False |
| `GODEL_TEST_WORKERS` | Number of parallel workers | auto |

### Example Usage Patterns

Run tests with custom configuration:
```bash
python -m godelOS.run_tests --config=my_config.json
```

Run tests with parallel execution:
```bash
python -m godelOS.run_tests --parallel --workers=4
```

Run tests with timeout:
```bash
python -m godelOS.run_tests --timeout=60
```

Run tests with specific categories and generate reports:
```bash
python -m godelOS.run_tests --category=metacognition,inference --html=report.html --json=report.json
```

Run tests with environment variables:
```bash
GODEL_TEST_VERBOSE=1 GODEL_TEST_PARALLEL=1 python -m godelOS.run_tests
```

## Interpreting Test Results and Reports

### Console Output

The console output includes:

- **Summary statistics**: Total tests, passed, failed, skipped, error
- **Test results**: Each test with status (passed, failed, skipped, error)
- **Error details**: For failed tests, the error message and traceback
- **Timing information**: Duration of each test and total duration

Example console output:
```
============================= test session starts ==============================
platform linux -- Python 3.8.10, pytest-6.2.5, py-1.10.0, pluggy-0.13.1
rootdir: /path/to/godelOS
collected 120 tests

tests/metacognition/test_meta_knowledge.py::TestMetaKnowledge::test_initialize_meta_knowledge PASSED [ 0%]
...
tests/metacognition/test_meta_knowledge.py::TestMetaKnowledge::test_update_meta_knowledge FAILED [ 1%]

FAILED tests/metacognition/test_meta_knowledge.py::TestMetaKnowledge::test_update_meta_knowledge
    def test_update_meta_knowledge():
>       assert meta_knowledge.update("reasoning_capability", {"name": "resolution", "performance": 0.9})
E       AssertionError: assert False
E        +  where False = <bound method MetaKnowledge.update of <MetaKnowledge object at 0x7f8b1c3e6d30>>('reasoning_capability', {'name': 'resolution', 'performance': 0.9})

...

======================= 118 passed, 2 failed in 3.45s ========================
```

### HTML Reports

The HTML report includes:

- **Summary**: Overview of test results with charts
- **Test results**: Detailed results for each test
- **Filters**: Options to filter by status, category, or module
- **Timing information**: Timing data with slow tests highlighted
- **Error details**: Detailed error information for failed tests

### JSON Reports

The JSON report structure:

```json
{
  "summary": {
    "total": 120,
    "passed": 118,
    "failed": 2,
    "skipped": 0,
    "error": 0,
    "duration": 3.45
  },
  "tests": [
    {
      "id": "tests/metacognition/test_meta_knowledge.py::TestMetaKnowledge::test_initialize_meta_knowledge",
      "name": "test_initialize_meta_knowledge",
      "class": "TestMetaKnowledge",
      "file": "tests/metacognition/test_meta_knowledge.py",
      "status": "passed",
      "duration": 0.01,
      "message": null
    },
    {
      "id": "tests/metacognition/test_meta_knowledge.py::TestMetaKnowledge::test_update_meta_knowledge",
      "name": "test_update_meta_knowledge",
      "class": "TestMetaKnowledge",
      "file": "tests/metacognition/test_meta_knowledge.py",
      "status": "failed",
      "duration": 0.02,
      "message": "AssertionError: assert False\n +  where False = <bound method MetaKnowledge.update of <MetaKnowledge object at 0x7f8b1c3e6d30>>('reasoning_capability', {'name': 'resolution', 'performance': 0.9})"
    }
  ],
  "categories": {
    "metacognition": {
      "total": 45,
      "passed": 43,
      "failed": 2,
      "skipped": 0,
      "error": 0
    },
    "inference": {
      "total": 35,
      "passed": 35,
      "failed": 0,
      "skipped": 0,
      "error": 0
    }
  }
}
```

### Test Coverage Reports

The test coverage reports include:

- **Component coverage**: Which components have tests and which don't
- **Method coverage**: Which methods are tested and which aren't
- **Coverage metrics**: Coverage percentages for each component
- **Prioritization**: Suggestions for which components to test next

## Adding New Tests to the System

### Quick Guide to Creating New Test Files

1. Create a new test file in the appropriate directory:
   - For component tests: `tests/<module>/test_<component_name>.py`
   - For enhanced tests: `tests/<module>/test_<component_name>_enhanced.py`
   - For integration tests: `tests/<module>/test_integration.py`

2. Import the necessary modules:
   ```python
   import pytest
   from godelOS.<module>.<component> import <Component>
   ```

3. Create test fixtures if needed:
   ```python
   @pytest.fixture
   def component_instance():
       return Component()
   ```

4. Create a test class:
   ```python
   class TestComponent:
       def test_functionality(self, component_instance):
           # Test code
           assert component_instance.function() == expected_result
   ```

5. Run the tests to verify:
   ```bash
   python -m godelOS.run_tests tests/<module>/test_<component_name>.py
   ```

### Template for Test Classes and Methods

```python
"""
Tests for the <Component> component.

This module contains tests for the <Component> class and related functionality.
"""

import pytest
from godelOS.<module>.<component> import <Component>

# Test fixtures
@pytest.fixture
def component_instance():
    """Create a <Component> instance for testing."""
    return <Component>()

# Test classes
class Test<Component>:
    """Tests for the <Component> class."""
    
    def test_initialization(self, component_instance):
        """Test that <Component> initializes correctly."""
        assert component_instance is not None
        # More assertions...
    
    def test_specific_functionality(self, component_instance):
        """Test specific functionality of <Component>."""
        # Arrange
        input_data = ...
        expected_result = ...
        
        # Act
        actual_result = component_instance.function(input_data)
        
        # Assert
        assert actual_result == expected_result
```

### Required Imports and Setup

Common imports for tests:

```python
import pytest
import unittest
from unittest.mock import MagicMock, patch
import os
import tempfile
import json
```

Common setup for different types of tests:

```python
# For file-based tests
@pytest.fixture
def temp_file():
    with tempfile.NamedTemporaryFile(delete=False) as f:
        yield f.name
    os.unlink(f.name)

# For database tests
@pytest.fixture
def in_memory_db():
    db = Database(":memory:")
    db.initialize()
    yield db
    db.close()

# For mocking dependencies
@pytest.fixture
def mocked_dependency():
    with patch("godelOS.module.Dependency") as mock:
        mock.return_value.method.return_value = "mocked_result"
        yield mock
```

### Common Fixtures and Utilities

The GödelOS test suite provides several common fixtures and utilities:

```python
# Import common fixtures
from tests.conftest import knowledge_store, inference_engine, type_system

# Use fixtures in tests
def test_with_common_fixtures(knowledge_store, inference_engine):
    # Test code using common fixtures
    knowledge_store.add_statement("A")
    result = inference_engine.prove("A")
    assert result.is_proven
```

## Test Categorization Guide

### Available Test Categories

The GödelOS test suite includes the following categories:

| Category | Description |
|----------|-------------|
| core_kr | Core Knowledge Representation tests |
| inference | Inference Engine tests |
| learning | Learning System tests |
| common_sense | Common Sense tests |
| metacognition | Metacognition tests |
| nlu_nlg | NLU/NLG tests |
| ontology | Ontology tests |
| scalability | Scalability tests |
| symbol_grounding | Symbol Grounding tests |
| integration | Integration tests |
| unit | Unit tests |

### How to Assign Tests to Categories

Tests are automatically assigned to categories based on their location in the directory structure. For example, tests in the `tests/metacognition/` directory are automatically assigned to the "metacognition" category.

You can also explicitly assign tests to categories using markers:

```python
@pytest.mark.category("inference")
def test_specific_functionality():
    # Test code
```

### Using pytest Markers

Common pytest markers used in GödelOS:

| Marker | Description |
|--------|-------------|
| slow | Tests that take a long time to run |
| integration | Integration tests that test multiple components together |
| critical | Critical tests that must always pass |
| flaky | Tests that may occasionally fail due to non-deterministic behavior |

Example marker usage:

```python
@pytest.mark.slow
def test_large_scale_inference():
    # Test code for a slow test

@pytest.mark.integration
def test_metacognition_inference_integration():
    # Test code for an integration test

@pytest.mark.critical
def test_critical_functionality():
    # Test code for a critical test

@pytest.mark.flaky(reruns=3)
def test_non_deterministic_behavior():
    # Test code for a flaky test
```

### Creating Custom Categories

You can create custom categories by adding them to the test configuration:

```json
{
  "categories": {
    "custom_category": [
      "tests/path/to/test_file.py",
      "regex:test_specific_.*"
    ]
  }
}
```

Or by using custom markers:

```python
@pytest.mark.custom_category
def test_function():
    # Test code
```

### Benefits of Proper Categorization

Proper test categorization provides several benefits:

1. **Selective Testing**: Run only the tests you need
2. **Organized Results**: View test results by category
3. **Coverage Analysis**: Analyze test coverage by category
4. **Parallel Execution**: Run tests in parallel by category
5. **CI Integration**: Configure CI to run different categories in different stages