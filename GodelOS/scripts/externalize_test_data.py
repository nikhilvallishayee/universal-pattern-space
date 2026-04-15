#!/usr/bin/env python3
"""
Test Data Externalization Utility

This script identifies hardcoded test data in the codebase and provides
utilities to externalize it into proper test fixtures.
"""

import os
import re
import json
import ast
from pathlib import Path
from typing import Dict, List, Tuple, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestDataExternalizer:
    """Utility to find and externalize hardcoded test data"""
    
    def __init__(self, repo_root: str):
        self.repo_root = Path(repo_root)
        self.test_fixtures_dir = self.repo_root / "tests" / "fixtures"
        
        # Patterns that indicate hardcoded test data
        self.hardcoded_patterns = [
            # Python patterns
            r'test_.*=\s*["\'].*["\']',  # test variables with string values
            r'assert.*==\s*["\'].*["\']',  # assertions with hardcoded strings
            r'mock.*return_value\s*=\s*.*',  # mock return values
            r'expected\s*=\s*[\[\{].*[\]\}]',  # expected results
            r'sample_.*=\s*.*',  # sample data variables
            
            # JavaScript/TypeScript patterns
            r'const\s+test.*=\s*["\'].*["\']',  # const test variables
            r'expect.*toBe\(["\'].*["\']\)',  # expect assertions
            r'mockReturnValue\(.*\)',  # mock return values
            
            # Common test data indicators
            r'dummy.*=.*',
            r'fake.*=.*',
            r'mock.*=.*'
        ]
        
        # File extensions to scan
        self.scan_extensions = {'.py', '.js', '.ts', '.svelte'}
        
        # Results
        self.findings = {}
        
    def create_fixtures_structure(self):
        """Create test fixtures directory structure"""
        self.test_fixtures_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for different types of fixtures
        subdirs = ['api_responses', 'sample_data', 'mock_objects', 'cognitive_states']
        for subdir in subdirs:
            (self.test_fixtures_dir / subdir).mkdir(exist_ok=True)
        
        # Create fixture index
        index_file = self.test_fixtures_dir / "index.json"
        if not index_file.exists():
            with open(index_file, 'w') as f:
                json.dump({
                    "description": "Test fixtures for GödelOS",
                    "fixtures": {},
                    "last_updated": "auto-generated"
                }, f, indent=2)

    def scan_file(self, file_path: Path) -> List[Dict]:
        """Scan a single file for hardcoded test data"""
        findings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                
            for i, line in enumerate(lines):
                for pattern in self.hardcoded_patterns:
                    matches = re.finditer(pattern, line, re.IGNORECASE)
                    for match in matches:
                        findings.append({
                            'file': str(file_path.relative_to(self.repo_root)),
                            'line_number': i + 1,
                            'line_content': line.strip(),
                            'pattern': pattern,
                            'match': match.group(),
                            'suggestion': self.generate_suggestion(match.group(), file_path.suffix)
                        })
                        
        except Exception as e:
            logger.error(f"Error scanning {file_path}: {e}")
            
        return findings

    def generate_suggestion(self, match: str, file_ext: str) -> str:
        """Generate suggestion for externalizing the hardcoded data"""
        if file_ext == '.py':
            return "Consider moving to tests/fixtures/ and importing with load_fixture()"
        elif file_ext in ['.js', '.ts']:
            return "Consider moving to tests/fixtures/ and importing as JSON"
        elif file_ext == '.svelte':
            return "Consider using test data store or external JSON"
        else:
            return "Consider externalizing to test fixtures"

    def scan_repository(self):
        """Scan the entire repository for hardcoded test data"""
        logger.info("🔍 Scanning repository for hardcoded test data...")
        
        total_findings = 0
        
        for file_path in self.repo_root.rglob("*"):
            if (file_path.is_file() and 
                file_path.suffix in self.scan_extensions and
                not self.should_skip_file(file_path)):
                
                file_findings = self.scan_file(file_path)
                if file_findings:
                    self.findings[str(file_path.relative_to(self.repo_root))] = file_findings
                    total_findings += len(file_findings)
                    
        logger.info(f"Found {total_findings} potential hardcoded test data instances")
        return self.findings

    def should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped during scanning"""
        skip_dirs = {'.git', 'node_modules', '__pycache__', 'dist', 'build'}
        return any(skip_dir in file_path.parts for skip_dir in skip_dirs)

    def generate_fixture_files(self):
        """Generate example fixture files based on findings"""
        logger.info("📝 Generating fixture file examples...")
        
        # Python fixture loader
        python_loader = '''"""
Test fixture utilities for GödelOS

This module provides utilities for loading test fixtures in a consistent way.
"""

import json
from pathlib import Path
from typing import Any, Dict

FIXTURES_DIR = Path(__file__).parent / "fixtures"

def load_fixture(fixture_name: str, subfolder: str = None) -> Any:
    """Load a test fixture from JSON file"""
    if subfolder:
        fixture_path = FIXTURES_DIR / subfolder / f"{fixture_name}.json"
    else:
        fixture_path = FIXTURES_DIR / f"{fixture_name}.json"
    
    if not fixture_path.exists():
        raise FileNotFoundError(f"Fixture not found: {fixture_path}")
    
    with open(fixture_path) as f:
        return json.load(f)

def load_cognitive_state(state_name: str = "default") -> Dict:
    """Load a cognitive state fixture"""
    return load_fixture(state_name, "cognitive_states")

def load_api_response(endpoint: str) -> Dict:
    """Load an API response fixture"""
    return load_fixture(endpoint, "api_responses")

def load_sample_data(data_type: str) -> Any:
    """Load sample data fixture"""
    return load_fixture(data_type, "sample_data")
'''
        
        loader_file = self.test_fixtures_dir.parent / "fixture_loader.py"
        with open(loader_file, 'w') as f:
            f.write(python_loader)
        
        # Create sample fixture files
        self.create_sample_fixtures()
        
        # JavaScript fixture loader
        js_loader = '''/**
 * Test fixture utilities for frontend tests
 */

export class FixtureLoader {
  static async loadFixture(fixtureName, subfolder = null) {
    const path = subfolder 
      ? `./fixtures/${subfolder}/${fixtureName}.json`
      : `./fixtures/${fixtureName}.json`;
    
    const response = await fetch(path);
    if (!response.ok) {
      throw new Error(`Fixture not found: ${path}`);
    }
    return response.json();
  }
  
  static async loadCognitiveState(stateName = 'default') {
    return this.loadFixture(stateName, 'cognitive_states');
  }
  
  static async loadApiResponse(endpoint) {
    return this.loadFixture(endpoint, 'api_responses');
  }
  
  static async loadSampleData(dataType) {
    return this.loadFixture(dataType, 'sample_data');
  }
}
'''
        
        js_loader_file = self.test_fixtures_dir.parent / "fixture_loader.js"
        with open(js_loader_file, 'w') as f:
            f.write(js_loader)

    def create_sample_fixtures(self):
        """Create sample fixture files"""
        
        # Cognitive state fixture
        cognitive_state = {
            "manifestConsciousness": {
                "attention": "Test query processing",
                "workingMemory": ["Test item 1", "Test item 2"],
                "processingLoad": 0.5,
                "currentQuery": "Test query",
                "focusDepth": "surface"
            },
            "agenticProcesses": [],
            "daemonThreads": [],
            "systemHealth": {
                "inferenceEngine": 0.9,
                "knowledgeStore": 0.95,
                "reflectionEngine": 0.8,
                "learningModules": 0.85,
                "websocketConnection": 1.0
            },
            "alerts": [],
            "capabilities": {
                "reasoning": 0.9,
                "knowledge": 0.95,
                "creativity": 0.7,
                "reflection": 0.8,
                "learning": 0.85
            }
        }
        
        with open(self.test_fixtures_dir / "cognitive_states" / "default.json", 'w') as f:
            json.dump(cognitive_state, f, indent=2)
        
        # API response fixtures
        api_responses = {
            "health": {
                "status": "healthy",
                "version": "1.0.0",
                "uptime": 3600
            },
            "knowledge_graph": {
                "nodes": [
                    {"id": "test_node_1", "label": "Test Node 1", "type": "concept"},
                    {"id": "test_node_2", "label": "Test Node 2", "type": "concept"}
                ],
                "edges": [
                    {"source": "test_node_1", "target": "test_node_2", "type": "relation"}
                ]
            }
        }
        
        for endpoint, response in api_responses.items():
            with open(self.test_fixtures_dir / "api_responses" / f"{endpoint}.json", 'w') as f:
                json.dump(response, f, indent=2)
        
        # Sample data fixtures
        sample_data = {
            "test_documents": [
                {
                    "title": "Test Document 1",
                    "content": "This is test content for document 1",
                    "metadata": {"author": "Test Author", "date": "2024-01-01"}
                }
            ],
            "test_queries": [
                "What is consciousness?",
                "How does machine learning work?",
                "Explain quantum computing"
            ]
        }
        
        for data_type, data in sample_data.items():
            with open(self.test_fixtures_dir / "sample_data" / f"{data_type}.json", 'w') as f:
                json.dump(data, f, indent=2)

    def generate_report(self) -> Dict:
        """Generate a report of findings and recommendations"""
        report = {
            "scan_summary": {
                "total_files_scanned": len(self.findings),
                "total_findings": sum(len(findings) for findings in self.findings.values()),
                "files_with_issues": list(self.findings.keys())
            },
            "findings_by_file": self.findings,
            "recommendations": [
                "Use the generated fixture_loader.py for Python tests",
                "Use the generated fixture_loader.js for frontend tests",
                "Store test data in tests/fixtures/ subdirectories",
                "Replace hardcoded values with fixture loader calls",
                "Update existing tests to use external fixtures"
            ],
            "next_steps": [
                "Review findings for false positives",
                "Migrate critical test data to fixtures",
                "Update test files to use fixture loaders",
                "Add fixture validation to CI/CD pipeline"
            ]
        }
        
        report_file = self.repo_root / "test_data_externalization_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Report saved to: {report_file}")
        return report

    def run_analysis(self):
        """Run the complete test data externalization analysis"""
        logger.info("🚀 Starting test data externalization analysis...")
        
        # Create fixtures structure
        self.create_fixtures_structure()
        
        # Scan repository
        self.scan_repository()
        
        # Generate fixture files
        self.generate_fixture_files()
        
        # Generate report
        report = self.generate_report()
        
        # Print summary
        logger.info("✅ Analysis completed!")
        logger.info(f"Files scanned: {report['scan_summary']['total_files_scanned']}")
        logger.info(f"Total findings: {report['scan_summary']['total_findings']}")
        logger.info(f"Fixture structure created in: {self.test_fixtures_dir}")
        
        return report


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Data Externalization Utility")
    parser.add_argument("--repo-root", default=".", help="Repository root directory")
    
    args = parser.parse_args()
    
    try:
        analyzer = TestDataExternalizer(args.repo_root)
        analyzer.run_analysis()
        return 0
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())