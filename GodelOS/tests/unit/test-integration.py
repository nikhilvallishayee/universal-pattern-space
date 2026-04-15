#!/usr/bin/env python3
"""
Integration Test Suite for GödelOS Web Demonstration Interface
Tests the complete frontend-backend integration
"""

import asyncio
import json
import time
import requests
import websockets
from typing import Dict, Any
import sys
import subprocess
import signal
import os

class IntegrationTester:
    def __init__(self):
        self.backend_url = "http://localhost:8000"
        self.websocket_url = "ws://localhost:8000/ws/unified-cognitive-stream"
        self.frontend_url = "http://localhost:3000"
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": time.time()
        })
    
    def test_backend_health(self) -> bool:
        """Test backend health endpoint"""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log_test("Backend Health Check", True, f"Status: {data.get('status', 'unknown')}")
                return True
            else:
                self.log_test("Backend Health Check", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Backend Health Check", False, str(e))
            return False
    
    def test_backend_info(self) -> bool:
        """Test backend info endpoint"""
        try:
            response = requests.get(f"{self.backend_url}/", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log_test("Backend Info", True, f"Version: {data.get('version', 'unknown')}")
                return True
            else:
                self.log_test("Backend Info", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Backend Info", False, str(e))
            return False
    
    def test_query_processing(self) -> bool:
        """Test natural language query processing"""
        try:
            query_data = {
                "query": "What is artificial intelligence?",
                "context": {"test": True},
                "include_reasoning": True
            }
            
            response = requests.post(
                f"{self.backend_url}/api/query",
                json=query_data,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["response", "confidence", "reasoning_steps", "inference_time_ms"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    self.log_test("Query Processing", True, 
                                f"Response length: {len(data['response'])}, "
                                f"Confidence: {data['confidence']:.2f}, "
                                f"Steps: {len(data['reasoning_steps'])}")
                    return True
                else:
                    self.log_test("Query Processing", False, f"Missing fields: {missing_fields}")
                    return False
            else:
                self.log_test("Query Processing", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Query Processing", False, str(e))
            return False
    
    def test_knowledge_retrieval(self) -> bool:
        """Test knowledge base retrieval"""
        try:
            response = requests.get(f"{self.backend_url}/api/knowledge?limit=10", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["facts", "rules", "concepts", "total_count"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    self.log_test("Knowledge Retrieval", True, 
                                f"Total items: {data['total_count']}")
                    return True
                else:
                    self.log_test("Knowledge Retrieval", False, f"Missing fields: {missing_fields}")
                    return False
            else:
                self.log_test("Knowledge Retrieval", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Knowledge Retrieval", False, str(e))
            return False
    
    def test_cognitive_state(self) -> bool:
        """Test cognitive state endpoint"""
        try:
            response = requests.get(f"{self.backend_url}/api/cognitive-state", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["manifest_consciousness", "agentic_processes", "daemon_threads"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    self.log_test("Cognitive State", True, 
                                f"Processes: {len(data['agentic_processes'])}, "
                                f"Daemons: {len(data['daemon_threads'])}")
                    return True
                else:
                    self.log_test("Cognitive State", False, f"Missing fields: {missing_fields}")
                    return False
            else:
                self.log_test("Cognitive State", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Cognitive State", False, str(e))
            return False
    
    async def test_websocket_connection(self) -> bool:
        """Test WebSocket connection and messaging"""
        try:
            async with websockets.connect(self.websocket_url) as websocket:
                # Wait for initial message
                initial_message = await asyncio.wait_for(websocket.recv(), timeout=10)
                data = json.loads(initial_message)
                
                if data.get("type") == "initial_state":
                    self.log_test("WebSocket Connection", True, "Received initial state")
                    return True
                else:
                    self.log_test("WebSocket Connection", False, f"Unexpected initial message: {data.get('type')}")
                    return False
                    
        except Exception as e:
            self.log_test("WebSocket Connection", False, str(e))
            return False
    
    def test_frontend_accessibility(self) -> bool:
        """Test if frontend is accessible"""
        try:
            response = requests.get(self.frontend_url, timeout=10)
            if response.status_code == 200:
                content = response.text
                if "GödelOS" in content and "Query Interface" in content:
                    self.log_test("Frontend Accessibility", True, "Frontend loaded successfully")
                    return True
                else:
                    self.log_test("Frontend Accessibility", False, "Frontend content incomplete")
                    return False
            else:
                self.log_test("Frontend Accessibility", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Frontend Accessibility", False, str(e))
            return False
    
    async def run_all_tests(self):
        """Run all integration tests"""
        print("🧪 Starting GödelOS Integration Tests...")
        print("=" * 50)
        
        # Test backend endpoints
        backend_tests = [
            self.test_backend_health(),
            self.test_backend_info(),
            self.test_query_processing(),
            self.test_knowledge_retrieval(),
            self.test_cognitive_state()
        ]
        
        # Test WebSocket
        websocket_test = await self.test_websocket_connection()
        
        # Test frontend
        frontend_test = self.test_frontend_accessibility()
        
        # Calculate results
        all_tests = backend_tests + [websocket_test, frontend_test]
        passed = sum(all_tests)
        total = len(all_tests)
        
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All integration tests passed! System is ready.")
            return True
        else:
            print("⚠️  Some tests failed. Check the logs above.")
            return False
    
    def generate_report(self):
        """Generate a detailed test report"""
        report = {
            "timestamp": time.time(),
            "total_tests": len(self.test_results),
            "passed_tests": sum(1 for result in self.test_results if result["success"]),
            "failed_tests": sum(1 for result in self.test_results if not result["success"]),
            "tests": self.test_results
        }
        
        with open("integration_test_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: integration_test_report.json")

async def main():
    """Main test runner"""
    tester = IntegrationTester()
    
    print("⏳ Waiting for services to be ready...")
    time.sleep(5)  # Give services time to start
    
    success = await tester.run_all_tests()
    tester.generate_report()
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)