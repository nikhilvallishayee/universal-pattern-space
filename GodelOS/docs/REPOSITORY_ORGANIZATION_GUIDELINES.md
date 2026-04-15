# GödelOS Repository Organization Guidelines

This document provides comprehensive guidelines for maintaining a clean, organized, and efficient GödelOS repository. Following these guidelines ensures code quality, reduces technical debt, and improves developer experience.

## 📁 Directory Structure

### Core Directories

```
GödelOS/
├── backend/                     # Python backend services
│   ├── cognitive_architecture/  # Core cognitive systems
│   ├── knowledge_management/    # Knowledge processing
│   ├── transparency/           # System transparency features
│   └── config/                 # Configuration files
├── svelte-frontend/            # Svelte.js frontend
│   ├── src/
│   │   ├── components/         # Reusable UI components
│   │   ├── stores/            # State management
│   │   ├── utils/             # Utility functions
│   │   └── routes/            # Page routes
│   └── tests/                 # Frontend tests
├── tests/                     # Backend test suites
│   ├── unit/                  # Unit tests
│   ├── integration/           # Integration tests
│   ├── e2e/                   # End-to-end tests
│   └── fixtures/              # Test data fixtures
├── scripts/                   # Automation and utility scripts
├── docs/                      # Documentation
└── examples/                  # Example code and tutorials
```

## 🧹 File Naming Conventions

### Python Files
- **Modules**: `snake_case.py` (e.g., `cognitive_state_manager.py`)
- **Classes**: `PascalCase` (e.g., `CognitiveStateManager`)
- **Functions/Variables**: `snake_case` (e.g., `process_query`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_PROCESSING_DEPTH`)

### Frontend Files
- **Components**: `PascalCase.svelte` (e.g., `CognitiveStateMonitor.svelte`)
- **Utilities**: `camelCase.js` (e.g., `websocketManager.js`)
- **Stores**: `camelCase.js` (e.g., `cognitiveState.js`)
- **Tests**: `*.spec.js` or `*.test.js`

### Configuration Files
- Use descriptive names: `database.yml`, `api_endpoints.json`
- Include environment in name when needed: `config.dev.yml`, `config.prod.yml`

## 🚫 Files and Patterns to Avoid

### Prohibited File Patterns
```bash
# Backup files (use git instead)
*.bak
*_backup.*
*_old.*
*.orig

# Temporary files
*.tmp
*~
*.swp
*.swo

# OS-specific files
.DS_Store
Thumbs.db

# Editor files
*.rej
*.patch
*.diff

# Build artifacts (should be in .gitignore)
__pycache__/
*.pyc
node_modules/
dist/
build/
```

### Directories to Avoid
- `old/`, `backup/`, `archive/` - Use git history instead
- `temp/`, `tmp/` - Clean up temporary files regularly
- `test_data/` in root - Use `tests/fixtures/` instead

## ✅ Clean Code Practices

### File Organization
1. **Single Responsibility**: Each file should have one clear purpose
2. **Logical Grouping**: Related functionality in same directory
3. **Clear Hierarchy**: Nested directories for sub-modules
4. **Consistent Structure**: Follow established patterns

### Code Quality
```python
# Good: Clear, descriptive naming
def process_cognitive_query(query_text: str, options: QueryOptions) -> QueryResult:
    """Process a cognitive query with specified options."""
    pass

# Bad: Unclear, abbreviated naming
def proc_q(q: str, opts: dict) -> dict:
    pass
```

### Import Organization
```python
# Standard library imports
import os
import sys
from typing import Dict, List, Optional

# Third-party imports
import fastapi
import pydantic

# Local imports
from backend.cognitive_architecture import CognitiveEngine
from backend.knowledge_management import KnowledgeStore
```

## 🧪 Test Organization

### Test Structure
```
tests/
├── fixtures/                  # Reusable test data
│   ├── api_responses/        # Mock API responses
│   ├── cognitive_states/     # Test cognitive states
│   └── sample_data/          # Sample documents/data
├── unit/                     # Unit tests
│   ├── test_cognitive_engine.py
│   └── test_knowledge_store.py
├── integration/              # Integration tests
│   ├── test_api_endpoints.py
│   └── test_cognitive_pipeline.py
└── e2e/                      # End-to-end tests
    ├── test_user_workflows.py
    └── test_system_integration.py
```

### Test Data Management
- **External Fixtures**: No hardcoded test data in test files
- **Fixture Loaders**: Use centralized fixture loading utilities
- **Realistic Data**: Test data should reflect real-world scenarios
- **Cleanup**: Tests should clean up after themselves

Example:
```python
# Good: Using external fixtures
def test_cognitive_processing():
    cognitive_state = load_fixture('cognitive_states/default.json')
    result = process_query("test query", cognitive_state)
    assert result.confidence > 0.5

# Bad: Hardcoded test data
def test_cognitive_processing():
    cognitive_state = {
        "attention": "hardcoded value",
        "memory": ["item1", "item2"]
    }
    # ... rest of test
```

## 🔄 Git Workflow

### Branch Naming
- **Features**: `feature/cognitive-enhancement`
- **Fixes**: `fix/websocket-connection-issue`
- **Cleanup**: `cleanup/remove-legacy-code`
- **Documentation**: `docs/api-documentation-update`

### Commit Messages
```bash
# Good: Clear, descriptive commits
feat: add real-time cognitive state streaming
fix: resolve WebSocket reconnection issues  
cleanup: remove orphaned project archive files
docs: update API documentation for knowledge endpoints

# Bad: Unclear commits
update stuff
fix bug
changes
```

### File Management
- **No Binary Files**: Avoid committing large binary files
- **Use .gitignore**: Properly configure exclusions
- **Clean History**: Squash commits when appropriate
- **Review Changes**: Use `git diff` before committing

## 📚 Documentation Standards

### Code Documentation
```python
def process_cognitive_query(
    query: str, 
    cognitive_state: CognitiveState,
    options: QueryOptions = None
) -> QueryResult:
    """
    Process a cognitive query using the current system state.
    
    Args:
        query: The natural language query to process
        cognitive_state: Current state of the cognitive system
        options: Optional processing configuration
        
    Returns:
        QueryResult containing the processed response and metadata
        
    Raises:
        CognitiveProcessingError: If query processing fails
        InvalidStateError: If cognitive state is invalid
    """
    pass
```

### README Files
Each major directory should have a README.md explaining:
- Purpose and functionality
- Key components
- Usage examples
- Dependencies
- Testing instructions

## 🛠️ Automation and Tooling

### Required Scripts
- `scripts/cleanup_repository.py` - Repository cleanup automation
- `scripts/externalize_test_data.py` - Test data management
- `scripts/validate_code_quality.py` - Code quality checks
- `scripts/generate_documentation.py` - Documentation generation

### CI/CD Integration
```yaml
# Example GitHub Actions workflow
name: Repository Quality Check
on: [push, pull_request]
jobs:
  quality-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run cleanup check
        run: python scripts/cleanup_repository.py --dry-run
      - name: Validate test data
        run: python scripts/externalize_test_data.py --validate
      - name: Check code quality
        run: python scripts/validate_code_quality.py
```

### Development Tools
- **Linting**: Use `black`, `isort`, `mypy` for Python
- **Frontend**: Use `prettier`, `eslint` for JavaScript/Svelte
- **Testing**: Automated test execution and coverage reporting
- **Documentation**: Automated API documentation generation

## 🔍 Quality Metrics

### Code Quality Indicators
- **Test Coverage**: Minimum 80% for critical components
- **Cyclomatic Complexity**: Keep functions under 10 complexity
- **File Size**: Modules should typically be under 500 lines
- **Duplication**: Avoid code duplication above 5%

### Repository Health
- **File Count**: Monitor growth of total files
- **Binary Files**: Minimize binary file count and size
- **Orphaned Files**: Regular cleanup of unused files
- **Documentation Coverage**: All public APIs documented

## 🚀 Performance Considerations

### Loading States
- **Always Show**: Provide feedback for async operations
- **Progressive**: Show progress where possible
- **Graceful Failure**: Handle errors elegantly
- **Timeout Handling**: Set reasonable timeouts

### Resource Management
- **Memory Usage**: Monitor memory consumption
- **File Handles**: Properly close file handles
- **Network Connections**: Implement connection pooling
- **Caching**: Use appropriate caching strategies

## 🔧 Maintenance Procedures

### Daily Maintenance
- Review new files added to repository
- Check for large files or inappropriate commits
- Monitor test failures and address promptly
- Update dependencies with security patches

### Weekly Maintenance
- Run repository cleanup scripts
- Review and merge dependency updates
- Analyze code quality metrics
- Update documentation as needed

### Monthly Maintenance
- Comprehensive code review and refactoring
- Performance analysis and optimization
- Security audit and vulnerability assessment
- Backup strategy review and testing

## 🎯 Best Practices Summary

### Do's ✅
- Use descriptive, meaningful names
- Keep files focused and modular
- Write comprehensive tests with external fixtures
- Document public APIs and complex logic
- Use automated tooling for quality assurance
- Follow consistent coding standards
- Clean up temporary files and artifacts
- Use git history instead of backup files

### Don'ts ❌
- Don't commit backup files or temporary artifacts
- Don't use hardcoded test data in test files
- Don't create orphaned directories like `old/` or `backup/`
- Don't commit large binary files
- Don't ignore failing tests
- Don't skip documentation for public APIs
- Don't duplicate code across modules
- Don't use unclear or abbreviated names

## 🆘 Emergency Procedures

### Broken Build
1. Identify the breaking commit using `git bisect`
2. Create hotfix branch from last known good state
3. Apply minimal fix with thorough testing
4. Merge hotfix and update all affected branches

### Repository Corruption
1. Clone fresh copy from remote
2. Compare with local changes using diff tools
3. Carefully reapply legitimate changes
4. Use cleanup scripts to ensure repository health

### Large File Cleanup
1. Use `git filter-branch` or BFG Repo-Cleaner
2. Force push cleaned history (coordinate with team)
3. All developers re-clone repository
4. Update CI/CD to prevent future large file commits

---

*This document is maintained by the GödelOS development team and should be updated as the project evolves. All contributors are expected to follow these guidelines to maintain repository quality and team productivity.*