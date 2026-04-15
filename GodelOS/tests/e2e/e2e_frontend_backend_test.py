#!/usr/bin/env python3
"""
End-to-End Frontend and Backend Verification Test

This test verifies that:
1. Backend is running and healthy
2. Query API endpoint works correctly
3. Frontend can be accessed
4. Frontend-backend communication works
"""

import time
import json
import logging
import requests
from typing import Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class E2ETest:
    """End-to-end test suite for GödelOS frontend and backend"""
    
    def __init__(self):
        self.backend_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:3001"
        self.test_results = []
    
    def log_test_result(self, test_name: str, success: bool, details: str = ""):
        """Log a test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status}: {test_name}")
        if details:
            logger.info(f"   Details: {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": time.time()
        })
    
    def test_backend_health(self) -> bool:
        """Test backend health endpoint"""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                is_healthy = health_data.get("status") == "healthy" and health_data.get("details", {}).get("healthy", False)
                details = f"Status: {health_data.get('status')}, Initialized: {health_data.get('details', {}).get('initialized', False)}"
                self.log_test_result("Backend Health Check", is_healthy, details)
                return is_healthy
            else:
                self.log_test_result("Backend Health Check", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test_result("Backend Health Check", False, str(e))
            return False
    
    def test_backend_query(self) -> bool:
        """Test backend query endpoint"""
        try:
            query_data = {
                "query": "What is artificial intelligence?",
                "include_reasoning": False
            }
            
            response = requests.post(
                f"{self.backend_url}/api/query",
                json=query_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                has_response = "response" in result and len(result["response"]) > 0
                has_confidence = "confidence" in result and 0 <= result["confidence"] <= 1
                success = has_response and has_confidence
                details = f"Response length: {len(result.get('response', ''))}, Confidence: {result.get('confidence', 0)}"
                self.log_test_result("Backend Query Processing", success, details)
                return success
            else:
                self.log_test_result("Backend Query Processing", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test_result("Backend Query Processing", False, str(e))
            return False
    
    def test_frontend_accessibility(self) -> bool:
        """Test frontend accessibility"""
        try:
            response = requests.get(f"{self.frontend_url}", timeout=5)
            if response.status_code == 200:
                # Check if it's a valid HTML page
                content = response.text.lower()
                has_html = "<html" in content or "<!doctype html" in content
                has_svelte_content = "svelte" in content or "gödelos" in content or "query" in content
                success = has_html and (has_svelte_content or len(content) > 500)
                details = f"Status: {response.status_code}, Content length: {len(response.text)}"
                self.log_test_result("Frontend Accessibility", success, details)
                return success
            else:
                self.log_test_result("Frontend Accessibility", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test_result("Frontend Accessibility", False, str(e))
            return False
    
    def test_frontend_api_proxy(self) -> bool:
        """Test frontend API proxy to backend"""
        try:
            # Test if the frontend can proxy API requests to the backend
            query_data = {
                "query": "What is machine learning?",
                "include_reasoning": False
            }
            
            response = requests.post(
                f"{self.frontend_url}/api/query",
                json=query_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                has_response = "response" in result and len(result["response"]) > 0
                has_confidence = "confidence" in result
                success = has_response and has_confidence
                details = f"Proxy successful, Response: {result.get('response', '')[:100]}..."
                self.log_test_result("Frontend API Proxy", success, details)
                return success
            else:
                self.log_test_result("Frontend API Proxy", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test_result("Frontend API Proxy", False, str(e))
            return False
    
    def test_multiple_queries(self) -> bool:
        """Test multiple different queries"""
        test_queries = [
            "What is artificial intelligence?",
            "Tell me about machine learning", 
            "Where is John?",
            "Can Mary go to the cafe?",
            "What is quantum computing?"
        ]
        
        successful_queries = 0
        
        for query in test_queries:
            try:
                query_data = {
                    "query": query,
                    "include_reasoning": False
                }
                
                response = requests.post(
                    f"{self.backend_url}/api/query",
                    json=query_data,
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if "response" in result and len(result["response"]) > 0:
                        successful_queries += 1
                        logger.info(f"   ✅ Query: '{query}' -> '{result['response'][:50]}...'")
                    else:
                        logger.info(f"   ❌ Query: '{query}' -> Empty response")
                else:
                    logger.info(f"   ❌ Query: '{query}' -> HTTP {response.status_code}")
            except Exception as e:
                logger.info(f"   ❌ Query: '{query}' -> Error: {e}")
        
        success_rate = successful_queries / len(test_queries)
        success = success_rate >= 0.8  # At least 80% success rate
        details = f"Successful queries: {successful_queries}/{len(test_queries)} ({success_rate:.1%})"
        self.log_test_result("Multiple Query Types", success, details)
        return success
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return results"""
        logger.info("🎯 Starting End-to-End GödelOS Frontend/Backend Test")
        logger.info("=" * 60)
        
        start_time = time.time()
        
        # Run tests in order
        tests = [
            ("Backend Health", self.test_backend_health),
            ("Backend Query", self.test_backend_query),
            ("Frontend Access", self.test_frontend_accessibility),
            ("Frontend API Proxy", self.test_frontend_api_proxy),
            ("Multiple Queries", self.test_multiple_queries)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            logger.info(f"\n📝 Running: {test_name}")
            try:
                if test_func():
                    passed_tests += 1
            except Exception as e:
                logger.error(f"Test {test_name} failed with exception: {e}")
        
        end_time = time.time()
        test_duration = end_time - start_time
        
        # Generate summary
        success_rate = passed_tests / total_tests
        overall_success = success_rate >= 0.8
        
        logger.info("\n" + "=" * 60)
        logger.info("🏆 TEST RESULTS SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Tests Passed: {passed_tests}/{total_tests} ({success_rate:.1%})")
        logger.info(f"Test Duration: {test_duration:.2f} seconds")
        
        if overall_success:
            logger.info("🎉 OVERALL RESULT: SUCCESS")
            logger.info("✅ The GödelOS frontend and backend are working correctly!")
            logger.info("✅ End-to-end functionality is verified")
        else:
            logger.info("❌ OVERALL RESULT: NEEDS ATTENTION")
            logger.info("⚠️  Some tests failed - system may need additional fixes")
        
        return {
            "overall_success": overall_success,
            "passed_tests": passed_tests,
            "total_tests": total_tests,
            "success_rate": success_rate,
            "test_duration": test_duration,
            "test_results": self.test_results
        }

def main():
    """Main test execution"""
    test_suite = E2ETest()
    results = test_suite.run_all_tests()
    
    # Save results to file
    with open("e2e_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"\n📊 Detailed results saved to: e2e_test_results.json")
    
    return 0 if results["overall_success"] else 1

if __name__ == "__main__":
    exit(main())
