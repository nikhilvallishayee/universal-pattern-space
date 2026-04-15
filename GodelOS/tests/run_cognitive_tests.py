#!/usr/bin/env python3
"""
GödelOS Cognitive Architecture Test Runner

This script runs comprehensive tests for the major cognitive architecture components:
1. Phenomenal Experience System Tests
2. Knowledge Graph Evolution + Phenomenal Experience Integration Tests

Usage:
    python run_cognitive_tests.py [--phenomenal] [--integration] [--all]
"""

import asyncio
import argparse
import sys
import subprocess
from datetime import datetime


def run_test_script(script_name: str, description: str):
    """Run a test script and return success status"""
    print(f"\n🚀 Running {description}")
    print("=" * 60)
    
    try:
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=False, 
                              text=True)
        
        if result.returncode == 0:
            print(f"✅ {description} - COMPLETED SUCCESSFULLY")
            return True
        else:
            print(f"❌ {description} - FAILED (exit code: {result.returncode})")
            return False
            
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="GödelOS Cognitive Architecture Test Runner")
    parser.add_argument("--phenomenal", action="store_true", 
                       help="Run phenomenal experience system tests only")
    parser.add_argument("--integration", action="store_true", 
                       help="Run KG-PE integration tests only")
    parser.add_argument("--all", action="store_true", 
                       help="Run all cognitive architecture tests (default)")
    
    args = parser.parse_args()
    
    # Default to all tests if no specific test is selected
    if not (args.phenomenal or args.integration):
        args.all = True
    
    print("🧠 GödelOS Cognitive Architecture Test Suite")
    print("=" * 60)
    print(f"Started at: {datetime.now()}")
    
    test_results = []
    
    # Run phenomenal experience tests
    if args.phenomenal or args.all:
        success = run_test_script("tests/test_phenomenal_experience_system.py", 
                                "Phenomenal Experience System Tests")
        test_results.append(("Phenomenal Experience Tests", success))
    
    # Run integration tests
    if args.integration or args.all:
        success = run_test_script("tests/test_kg_phenomenal_integration.py", 
                                "KG-PE Integration Tests")
        test_results.append(("KG-PE Integration Tests", success))
    
    # Print summary
    print("\n" + "=" * 60)
    print("🏁 COGNITIVE ARCHITECTURE TEST SUMMARY")
    print("=" * 60)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for _, success in test_results if success)
    
    for test_name, success in test_results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall Results: {passed_tests}/{total_tests} test suites passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL COGNITIVE ARCHITECTURE TESTS PASSED!")
        print("   The GödelOS cognitive architecture is functioning correctly.")
    elif passed_tests > 0:
        print("⚠️ PARTIAL SUCCESS - Some test suites failed.")
        print("   Review failed tests for issues to address.")
    else:
        print("❌ ALL TESTS FAILED - Major issues detected.")
        print("   Please review system configuration and dependencies.")
    
    print(f"\nCompleted at: {datetime.now()}")
    
    # Exit with appropriate code
    sys.exit(0 if passed_tests == total_tests else 1)


if __name__ == "__main__":
    main()
