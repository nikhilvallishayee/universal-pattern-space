# Repository Maintenance Scripts

This directory contains comprehensive utilities for maintaining the GödelOS repository in optimal condition. These scripts automate cleanup, monitoring, and organization tasks to ensure code quality and developer productivity.

## 🧹 cleanup_repository.py

Comprehensive repository cleanup utility that removes orphaned files, duplicates, and unwanted artifacts.

### Features
- Remove orphaned directories (`project_archive/`, `untracked/`)
- Clean backup files (`*.bak`, `*_backup*`, `*_old*`)
- Eliminate duplicate components and files
- Clear test artifacts and temporary files
- Safe operation with automatic backups
- Detailed logging and reporting

### Usage

```bash
# Dry run to see what would be cleaned (safe)
python scripts/cleanup_repository.py --dry-run

# Execute actual cleanup
python scripts/cleanup_repository.py --execute

# Verbose output
python scripts/cleanup_repository.py --execute --verbose
```

### Example Output
```
🚀 Starting GödelOS repository cleanup...
🗂️  Cleaning orphaned directories...
Found orphaned directory: project_archive (211 items)
Removed orphaned directory: project_archive
🧹 Cleaning backup and temporary files...
Removed backup file: svelte-frontend/src/App_backup.svelte
✅ Cleanup completed!
Files removed: 67
Space freed: 2.07 MB
```

## 🧪 externalize_test_data.py

Analyzes codebase for hardcoded test data and provides utilities to externalize it into proper fixtures.

### Features
- Scan for hardcoded test data patterns
- Generate test fixture structure
- Create fixture loader utilities
- Provide externalization recommendations
- Support for Python, JavaScript, and TypeScript

### Usage

```bash
# Run full analysis
python scripts/externalize_test_data.py

# Specify repository root
python scripts/externalize_test_data.py --repo-root /path/to/repo
```

### Generated Structure
```
tests/
├── fixtures/
│   ├── api_responses/      # Mock API responses
│   ├── cognitive_states/   # Test cognitive states
│   ├── sample_data/        # Sample documents/data
│   └── index.json         # Fixture index
├── fixture_loader.py      # Python fixture utilities
└── fixture_loader.js      # JavaScript fixture utilities
```

### Example Usage in Tests

Python:
```python
from tests.fixture_loader import load_cognitive_state, load_api_response

def test_cognitive_processing():
    state = load_cognitive_state('default')
    response = load_api_response('health')
    # Test with external fixtures
```

JavaScript:
```javascript
import { FixtureLoader } from '../tests/fixture_loader.js';

test('api integration', async () => {
  const mockResponse = await FixtureLoader.loadApiResponse('health');
  // Test with external fixtures
});
```

## 🔍 monitor_repository_health.py

Continuous repository health monitoring with automated maintenance and quality checks.

### Features
- File size monitoring
- Code quality analysis
- Git status checks
- Dependency analysis
- Forbidden pattern detection
- Auto-fix capabilities
- Health scoring (0-100)
- Watch mode for continuous monitoring

### Usage

```bash
# Single health check
python scripts/monitor_repository_health.py

# Auto-fix issues
python scripts/monitor_repository_health.py --auto-fix

# Continuous monitoring
python scripts/monitor_repository_health.py --watch

# Custom check interval (seconds)
python scripts/monitor_repository_health.py --watch --interval 600
```

### Health Checks

1. **File Sizes**: Detects oversized files (>10MB default)
2. **Forbidden Patterns**: Finds backup/temporary files
3. **Code Quality**: Analyzes complexity and file size
4. **Git Status**: Checks for uncommitted changes and large files
5. **Dependencies**: Validates requirements and lockfiles

### Example Report
```json
{
  "health_score": 87,
  "total_issues": 3,
  "severity_breakdown": {
    "error": 0,
    "warning": 2,
    "info": 1
  },
  "recommendations": [
    "🔧 2 issue(s) can be automatically fixed",
    "🧹 Run cleanup script to remove backup files"
  ]
}
```

## 🚀 Quick Start Guide

### Initial Repository Cleanup

1. **Analyze current state**:
   ```bash
   python scripts/monitor_repository_health.py
   ```

2. **Run cleanup in dry-run mode**:
   ```bash
   python scripts/cleanup_repository.py --dry-run
   ```

3. **Execute cleanup**:
   ```bash
   python scripts/cleanup_repository.py --execute
   ```

4. **Externalize test data**:
   ```bash
   python scripts/externalize_test_data.py
   ```

5. **Verify improvements**:
   ```bash
   python scripts/monitor_repository_health.py
   ```

### Ongoing Maintenance

1. **Daily monitoring**:
   ```bash
   python scripts/monitor_repository_health.py --auto-fix
   ```

2. **Weekly cleanup**:
   ```bash
   python scripts/cleanup_repository.py --execute
   ```

3. **Continuous monitoring** (development):
   ```bash
   python scripts/monitor_repository_health.py --watch --interval 300
   ```

## 🔧 Configuration

### Health Monitor Configuration

Create `.repo_health_config.json` in repository root:

```json
{
  "max_file_size_mb": 10,
  "max_line_count": 1000,
  "blocked_patterns": ["*.bak", "*_backup*", "*_old*"],
  "quality_thresholds": {
    "test_coverage": 0.8,
    "complexity_max": 10
  }
}
```

### Cleanup Configuration

Modify `cleanup_repository.py` constants:

```python
self.orphaned_directories = ["project_archive", "untracked"]
self.backup_patterns = ["*.bak", "*_backup*", "*_old*"]
self.duplicate_file_patterns = ["App_backup.svelte"]
```

## 📊 Integration with CI/CD

### GitHub Actions Example

```yaml
name: Repository Health Check
on: [push, pull_request]
jobs:
  health-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.8'
      - name: Run health check
        run: python scripts/monitor_repository_health.py
      - name: Validate cleanliness
        run: python scripts/cleanup_repository.py --dry-run
```

### Pre-commit Hook

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash
python scripts/monitor_repository_health.py --auto-fix
if [ $? -ne 0 ]; then
  echo "Repository health check failed. Please fix issues before committing."
  exit 1
fi
```

## 🆘 Troubleshooting

### Common Issues

1. **Permission Errors**:
   ```bash
   chmod +x scripts/*.py
   ```

2. **Python Module Not Found**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Git Not Found**:
   Ensure git is installed and repository is initialized

4. **Large Cleanup Backup**:
   ```bash
   # Clean up backup directories if needed
   rm -rf tmp/cleanup_backup/
   ```

### Recovery Procedures

1. **Restore from cleanup backup**:
   ```bash
   # If cleanup removed something important
   cp -r tmp/cleanup_backup/TIMESTAMP/* .
   ```

2. **Reset health configuration**:
   ```bash
   rm .repo_health_config.json
   ```

3. **Emergency cleanup rollback**:
   ```bash
   git checkout HEAD -- .
   ```

## 📈 Metrics and Monitoring

### Health Score Interpretation

- **90-100**: Excellent repository health
- **80-89**: Good, minor issues
- **70-79**: Fair, needs attention
- **60-69**: Poor, requires maintenance
- **<60**: Critical, immediate action needed

### Key Performance Indicators

- Files removed per cleanup
- Health score trend over time
- Auto-fix success rate
- Test coverage improvement
- Build time optimization

## 🔮 Future Enhancements

Planned improvements for the maintenance scripts:

1. **Machine Learning**: Predict maintenance needs
2. **Integration**: IDE plugins and VS Code extensions
3. **Metrics**: Detailed analytics and trending
4. **Automation**: Smart auto-fixes and optimizations
5. **Security**: Vulnerability scanning and fixes

---

*These scripts are maintained as part of the GödelOS project. For issues or feature requests, please file a GitHub issue with the `maintenance` label.*