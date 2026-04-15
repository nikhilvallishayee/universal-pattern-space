# GödelOS Test Suite Documentation

Comprehensive test suite for the GödelOS cognitive architecture system, covering backend API functionality, frontend components, and end-to-end integration workflows.

## 📋 Test Coverage Overview

### Backend Test Suite (`tests/backend/`)
- **API Endpoint Tests** (`test_api_endpoints.py`) - 598 lines
  - Health checks and system status validation
  - Query processing endpoints with various scenarios
  - Knowledge management operations (CRUD)
  - Cognitive state monitoring endpoints
  - Import/export functionality testing
  - Error handling and edge cases
  - Performance benchmarks for response times

- **WebSocket Tests** (`test_websocket.py`) - 456 lines
  - Connection establishment and management
  - Real-time cognitive event streaming
  - Message broadcasting and subscription handling
  - Connection cleanup and error scenarios
  - Concurrent connection testing
  - Performance under load

- **Knowledge Management Tests** (`test_knowledge_management.py`) - 652 lines
  - Knowledge search engine functionality
  - Category management operations
  - Storage and retrieval operations
  - Search relevance and filtering
  - Knowledge statistics and analytics
  - Import request validation

- **GödelOS Integration Tests** (`test_godelos_integration.py`) - 502 lines
  - Core cognitive architecture functionality
  - Natural language processing pipeline
  - Inference engine operations
  - Metacognitive monitoring capabilities
  - Learning and adaptation features
  - System health and performance monitoring

### Frontend Test Suite (`tests/frontend/`)
- **Frontend Module Tests** (`test_frontend_modules.py`) - 449 lines
  - JavaScript module structure validation
  - Syntax checking for all JS files
  - Module loading and initialization
  - UI component functionality
  - Knowledge graph visualization components
  - Progressive complexity features
  - Performance monitoring capabilities

### Integration Test Suite (`tests/integration/`)
- **End-to-End Workflows** (`test_end_to_end_workflows.py`) - 503 lines
  - Complete user journey testing
  - Knowledge ingestion pipeline validation
  - WebSocket integration testing
  - Multi-user concurrent access scenarios
  - System stability under load
  - Error handling across integrated components

### Test Utilities (`tests/utils/`)
- **Test Fixtures** (`fixtures.py`) - 485 lines
  - Common test data and mock objects
  - Pytest fixtures for consistent testing
  - Mock services for external APIs
  - Test data generators
  - Utility functions for assertions

### Test Configuration
- **Global Configuration** (`conftest.py`) - 118 lines
  - Pytest configuration and setup
  - Custom markers and test categorization
  - Environment setup and cleanup
  - Conditional test skipping logic

- **Enhanced Pytest Config** (`pytest.ini`) - Updated configuration
  - Test discovery patterns
  - Coverage reporting setup
  - Marker definitions
  - Asyncio support
  - Logging configuration

## 🚀 Quick Start

### Prerequisites
```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov pytest-html requests websockets

# Or install all dependencies
python tests/run_tests.py --install-deps
```

### Running Tests

#### Quick Smoke Tests
```bash
python tests/run_tests.py quick
```

#### Unit Tests Only
```bash
python tests/run_tests.py unit
```

#### Integration Tests (requires running backend)
```bash
python tests/run_tests.py integration --check-backend
```

#### All Tests with Coverage
```bash
python tests/run_tests.py all
```

#### Generate Comprehensive Report
```bash
python tests/run_tests.py report
```

### Direct Pytest Commands

#### Run specific test file
```bash
pytest tests/backend/test_api_endpoints.py -v
```

#### Run tests with specific markers
```bash
pytest -m "unit and not slow" -v
```

#### Run tests with coverage
```bash
pytest --cov=backend --cov=godelOS --cov-report=html
```

## 🏗️ Test Architecture

### Test Categories (Markers)

- `unit` - Unit tests for individual components
- `integration` - Integration tests requiring multiple components
- `e2e` - End-to-end tests for complete workflows
- `performance` - Performance and load testing
- `slow` - Tests that take longer to execute
- `requires_backend` - Tests requiring running backend service
- `requires_frontend` - Tests requiring running frontend service

### Test Structure

```
tests/
├── backend/           # Backend API and service tests
├── frontend/          # Frontend component and module tests
├── integration/       # Cross-component integration tests
├── utils/            # Common fixtures and utilities
├── conftest.py       # Global pytest configuration
├── run_tests.py      # Test runner script
└── README.md         # This documentation
```

## 📊 Coverage Targets

### Backend Coverage
- **API Endpoints**: 95%+ coverage
- **WebSocket Functionality**: 90%+ coverage
- **Knowledge Management**: 85%+ coverage
- **GödelOS Integration**: 80%+ coverage

### Frontend Coverage
- **Module Loading**: 100% (all modules exist and load)
- **Syntax Validation**: 100% (no syntax errors)
- **Component Structure**: 90%+ (proper organization)

### Integration Coverage
- **Critical User Paths**: 100% (core workflows work)
- **Error Scenarios**: 85%+ (proper error handling)
- **Performance Thresholds**: 90%+ (meets performance targets)

## 🔧 Test Environment Setup

### For Backend Tests
1. **Start the backend service**:
   ```bash
   cd backend
   python main.py
   ```

2. **Verify backend is running**:
   ```bash
   curl http://localhost:8000/health
   ```

### For Integration Tests
1. **Start both backend and frontend services**
2. **Run integration tests**:
   ```bash
   python tests/run_tests.py integration
   ```

### For CI/CD
```bash
# Install dependencies
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov pytest-html

# Run tests with XML output for CI
pytest --junit-xml=test_output/junit.xml --cov-report=xml
```

## 📈 Performance Benchmarks

### API Response Time Targets
- Health checks: < 200ms
- Simple queries: < 2000ms
- Complex queries: < 5000ms
- Knowledge operations: < 1000ms

### WebSocket Performance
- Connection establishment: < 100ms
- Message latency: < 50ms
- Concurrent connections: Support 50+ users

### System Resources
- Memory usage: < 1GB under normal load
- CPU usage: < 50% during peak operations

## 🐛 Debugging Test Failures

### Common Issues

1. **Backend Not Running**
   ```
   ConnectionError: Backend not accessible
   ```
   Solution: Start backend with `python backend/main.py`

2. **Import Errors**
   ```
   ModuleNotFoundError: No module named 'backend'
   ```
   Solution: Run tests from project root directory

3. **Async Test Issues**
   ```
   RuntimeError: Event loop is closed
   ```
   Solution: Use `pytest-asyncio` and `@pytest.mark.asyncio`

4. **WebSocket Connection Failures**
   ```
   WebSocketException: Connection failed
   ```
   Solution: Ensure backend WebSocket endpoint is accessible

### Debug Mode
```bash
# Run with debug logging
pytest -v --log-cli-level=DEBUG

# Run single test with detailed output
pytest tests/backend/test_api_endpoints.py::TestHealthEndpoints::test_health_check_healthy -v -s
```

## 📝 Contributing New Tests

### Adding Backend Tests
1. Create test file in `tests/backend/`
2. Use fixtures from `tests/utils/fixtures.py`
3. Add appropriate markers
4. Include both positive and negative test cases

### Adding Frontend Tests
1. Create test file in `tests/frontend/`
2. Test module structure and functionality
3. Validate JavaScript syntax and dependencies
4. Test UI component interactions

### Adding Integration Tests
1. Create test file in `tests/integration/`
2. Test complete workflows
3. Include error scenarios
4. Test with realistic data volumes

### Test Naming Conventions
- Test files: `test_*.py`
- Test classes: `Test*`
- Test methods: `test_*`
- Descriptive names: `test_api_endpoint_returns_valid_response`

## 🎯 Test Quality Standards

### Test Requirements
- **Fast**: Unit tests < 1s, Integration tests < 10s
- **Reliable**: Tests should pass consistently
- **Independent**: Tests should not depend on each other
- **Readable**: Clear test names and documentation
- **Maintainable**: Easy to update when code changes

### Code Coverage Standards
- New features: 90%+ coverage required
- Bug fixes: Add regression tests
- Critical paths: 100% coverage required

## 📧 Support

For test-related issues:
1. Check this documentation
2. Review test output and logs
3. Check backend/frontend service status
4. Create issue with reproduction steps

---

**Total Test Suite Stats:**
- **Backend Tests**: 4 files, ~2,207 lines of test code
- **Frontend Tests**: 1 file, ~449 lines of test code  
- **Integration Tests**: 1 file, ~503 lines of test code
- **Test Utilities**: 2 files, ~603 lines of support code
- **Total Coverage**: ~3,762 lines of comprehensive test coverage

This test suite validates both individual components and integrated system functionality, ensuring the GödelOS cognitive architecture system works reliably for the 0.2 beta release.