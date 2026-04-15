"""
GödelOS Test Suite Runner

Comprehensive test runner for the GödelOS system with options for different
test types, coverage reporting, and CI/CD integration.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description=""):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"✅ {description} completed successfully")
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        return False


def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = [
        "pytest",
        "pytest-asyncio",
        "pytest-cov",
        "requests",
        "fastapi",
        "pydantic",
        "spacy",
        "websockets"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("Install them with: pip install " + " ".join(missing_packages))
        return False
    
    return True


def run_unit_tests(coverage=True, verbose=True):
    """Run unit tests for backend and frontend."""
    cmd = ["python", "-m", "pytest"]
    
    # Add test paths
    cmd.extend([
        "tests/backend/",
        "tests/frontend/"
    ])
    
    # Add markers
    cmd.extend(["-m", "unit"])
    
    # Add options
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend([
            "--cov=backend",
            "--cov=godelOS",
            "--cov-report=term-missing",
            "--cov-report=html:test_output/coverage_html"
        ])
    
    return run_command(cmd, "Unit Tests")


def run_integration_tests(verbose=True):
    """Run integration tests."""
    cmd = ["python", "-m", "pytest"]
    
    # Add test paths
    cmd.append("tests/integration/")
    
    # Add markers
    cmd.extend(["-m", "integration"])
    
    # Add options
    if verbose:
        cmd.append("-v")
    
    cmd.extend([
        "--tb=short",
        "--maxfail=5"
    ])
    
    return run_command(cmd, "Integration Tests")


def run_e2e_tests(verbose=True):
    """Run end-to-end tests."""
    cmd = ["python", "-m", "pytest"]
    
    # Add test paths
    cmd.append("tests/e2e/")
    
    # Add markers
    cmd.extend(["-m", "e2e"])
    
    # Add options
    if verbose:
        cmd.append("-v")
    
    cmd.extend([
        "--tb=line",
        "--maxfail=3"
    ])
    
    return run_command(cmd, "End-to-End Tests")


def run_performance_tests(verbose=True):
    """Run performance tests."""
    cmd = ["python", "-m", "pytest"]
    
    # Add markers
    cmd.extend(["-m", "performance"])
    
    # Add options
    if verbose:
        cmd.append("-v")
    
    cmd.extend([
        "--tb=line",
        "--durations=0"
    ])
    
    return run_command(cmd, "Performance Tests")


def run_all_tests(coverage=True, verbose=True):
    """Run all test suites."""
    cmd = ["python", "-m", "pytest"]
    
    # Add test directory
    cmd.append("tests/")
    
    # Add options
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend([
            "--cov=backend",
            "--cov=godelOS",
            "--cov-report=term-missing",
            "--cov-report=html:test_output/coverage_html",
            "--cov-report=xml:test_output/coverage.xml"
        ])
    
    cmd.extend([
        "--tb=short",
        "--maxfail=10"
    ])
    
    return run_command(cmd, "All Tests")


def run_quick_tests():
    """Run quick smoke tests."""
    cmd = ["python", "-m", "pytest"]
    
    # Run only fast tests
    cmd.extend([
        "tests/backend/test_api_endpoints.py::TestHealthEndpoints",
        "tests/frontend/test_frontend_modules.py::TestFrontendModuleStructure",
        "-v",
        "--tb=line",
        "--maxfail=3"
    ])
    
    return run_command(cmd, "Quick Smoke Tests")


def check_backend_status():
    """Check if backend is running."""
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code in [200, 503]:
            print("✅ Backend is accessible")
            return True
        else:
            print(f"⚠️ Backend returned status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend not accessible: {e}")
        return False


def generate_test_report():
    """Generate a comprehensive test report."""
    print("\n" + "="*60)
    print("GENERATING TEST REPORT")
    print("="*60)
    
    # Run tests with report generation
    cmd = [
        "python", "-m", "pytest",
        "tests/",
        "--html=test_output/report.html",
        "--self-contained-html",
        "--cov=backend",
        "--cov=godelOS",
        "--cov-report=html:test_output/coverage_html",
        "--cov-report=xml:test_output/coverage.xml",
        "--junit-xml=test_output/junit.xml",
        "-v"
    ]
    
    success = run_command(cmd, "Test Report Generation")
    
    if success:
        print("\n📋 Test reports generated:")
        print("   - HTML Report: test_output/report.html")
        print("   - Coverage Report: test_output/coverage_html/index.html")
        print("   - JUnit XML: test_output/junit.xml")
        print("   - Coverage XML: test_output/coverage.xml")
    
    return success


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="GödelOS Test Suite Runner")
    
    parser.add_argument(
        "test_type",
        choices=["unit", "integration", "e2e", "performance", "all", "quick", "report"],
        help="Type of tests to run"
    )
    
    parser.add_argument(
        "--no-coverage",
        action="store_true",
        help="Disable coverage reporting"
    )
    
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Run tests in quiet mode"
    )
    
    parser.add_argument(
        "--check-backend",
        action="store_true",
        help="Check backend status before running tests"
    )
    
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Install required dependencies"
    )
    
    args = parser.parse_args()
    
    # Set up test environment
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Create output directory
    output_dir = project_root / "test_output"
    output_dir.mkdir(exist_ok=True)
    
    print("🧪 GödelOS Test Suite Runner")
    print(f"📁 Project root: {project_root}")
    print(f"📊 Output directory: {output_dir}")
    
    # Install dependencies if requested
    if args.install_deps:
        print("\n📦 Installing dependencies...")
        subprocess.run([
            sys.executable, "-m", "pip", "install",
            "pytest", "pytest-asyncio", "pytest-cov", "pytest-html",
            "requests", "websockets"
        ])
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Dependency check failed. Use --install-deps to install required packages.")
        return 1
    
    # Check backend status if requested
    if args.check_backend:
        backend_status = check_backend_status()
        if not backend_status and args.test_type in ["integration", "e2e", "all"]:
            print("\n⚠️ Backend is not running. Integration and E2E tests may fail.")
            print("Start the backend with: python -m backend.main")
    
    # Configure options
    coverage = not args.no_coverage
    verbose = not args.quiet
    
    # Run selected tests
    success = False
    
    if args.test_type == "unit":
        success = run_unit_tests(coverage=coverage, verbose=verbose)
    elif args.test_type == "integration":
        success = run_integration_tests(verbose=verbose)
    elif args.test_type == "e2e":
        success = run_e2e_tests(verbose=verbose)
    elif args.test_type == "performance":
        success = run_performance_tests(verbose=verbose)
    elif args.test_type == "all":
        success = run_all_tests(coverage=coverage, verbose=verbose)
    elif args.test_type == "quick":
        success = run_quick_tests()
    elif args.test_type == "report":
        success = generate_test_report()
    
    # Print summary
    print("\n" + "="*60)
    if success:
        print("✅ TEST SUITE COMPLETED SUCCESSFULLY")
    else:
        print("❌ TEST SUITE COMPLETED WITH FAILURES")
    print("="*60)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())