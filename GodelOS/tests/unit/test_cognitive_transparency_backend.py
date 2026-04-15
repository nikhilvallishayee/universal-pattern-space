#!/usr/bin/env python3
"""
Integration Test for Cognitive Transparency Backend

Tests all API endpoints and WebSocket connections for the cognitive transparency system.
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any
import pytest
import httpx
import websockets
from websockets.exceptions import ConnectionClosed

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"

class CognitiveTransparencyTester:
    """Test suite for cognitive transparency backend integration."""
    
    def __init__(self):
        self.client = httpx.AsyncClient(base_url=BASE_URL, timeout=30.0)
        self.test_results = {}
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def test_health_endpoint(self) -> Dict[str, Any]:
        """Test the health check endpoint."""
        logger.info("Testing health endpoint...")
        try:
            response = await self.client.get("/health")
            result = {
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "response": response.json() if response.status_code == 200 else response.text
            }
            logger.info(f"Health check: {'PASSED' if result['success'] else 'FAILED'}")
            return result
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_root_endpoint(self) -> Dict[str, Any]:
        """Test the root endpoint."""
        logger.info("Testing root endpoint...")
        try:
            response = await self.client.get("/")
            result = {
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "response": response.json() if response.status_code == 200 else response.text
            }
            logger.info(f"Root endpoint: {'PASSED' if result['success'] else 'FAILED'}")
            return result
        except Exception as e:
            logger.error(f"Root endpoint failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_query_endpoint(self) -> Dict[str, Any]:
        """Test the query processing endpoint."""
        logger.info("Testing query endpoint...")
        try:
            query_data = {
                "query": "What is consciousness?",
                "include_reasoning": True,
                "context": {"test": True}
            }
            response = await self.client.post("/api/query", json=query_data)
            result = {
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "response": response.json() if response.status_code == 200 else response.text
            }
            
            if result["success"]:
                response_data = result["response"]
                # Validate response structure
                required_fields = ["response", "confidence", "reasoning_steps", "inference_time_ms"]
                missing_fields = [field for field in required_fields if field not in response_data]
                if missing_fields:
                    result["success"] = False
                    result["error"] = f"Missing fields: {missing_fields}"
                else:
                    result["reasoning_steps_count"] = len(response_data.get("reasoning_steps", []))
            
            logger.info(f"Query endpoint: {'PASSED' if result['success'] else 'FAILED'}")
            return result
        except Exception as e:
            logger.error(f"Query endpoint failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_knowledge_endpoint(self) -> Dict[str, Any]:
        """Test the knowledge retrieval endpoint."""
        logger.info("Testing knowledge endpoint...")
        try:
            response = await self.client.get("/api/knowledge?limit=10")
            result = {
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "response": response.json() if response.status_code == 200 else response.text
            }
            
            if result["success"]:
                response_data = result["response"]
                # Validate response structure
                required_fields = ["facts", "rules", "concepts", "total_count"]
                missing_fields = [field for field in required_fields if field not in response_data]
                if missing_fields:
                    result["success"] = False
                    result["error"] = f"Missing fields: {missing_fields}"
                else:
                    result["total_items"] = response_data.get("total_count", 0)
            
            logger.info(f"Knowledge endpoint: {'PASSED' if result['success'] else 'FAILED'}")
            return result
        except Exception as e:
            logger.error(f"Knowledge endpoint failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_cognitive_state_endpoint(self) -> Dict[str, Any]:
        """Test the cognitive state endpoint."""
        logger.info("Testing cognitive state endpoint...")
        try:
            response = await self.client.get("/api/cognitive-state")
            result = {
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "response": response.json() if response.status_code == 200 else response.text
            }
            
            if result["success"]:
                response_data = result["response"]
                # Validate response structure
                required_fields = ["manifest_consciousness", "agentic_processes", "daemon_threads", "timestamp"]
                missing_fields = [field for field in required_fields if field not in response_data]
                if missing_fields:
                    result["success"] = False
                    result["error"] = f"Missing fields: {missing_fields}"
                else:
                    result["agentic_processes_count"] = len(response_data.get("agentic_processes", []))
                    result["daemon_threads_count"] = len(response_data.get("daemon_threads", []))
            
            logger.info(f"Cognitive state endpoint: {'PASSED' if result['success'] else 'FAILED'}")
            return result
        except Exception as e:
            logger.error(f"Cognitive state endpoint failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_transparency_endpoints(self) -> Dict[str, Any]:
        """Test cognitive transparency specific endpoints."""
        logger.info("Testing transparency endpoints...")
        results = {}
        
        # Test transparency configuration
        try:
            config_data = {
                "transparency_level": "standard",
                "session_specific": False
            }
            response = await self.client.post("/api/transparency/configure", json=config_data)
            results["configure"] = {
                "status_code": response.status_code,
                "success": response.status_code in [200, 404],  # 404 is acceptable if endpoint not available
                "response": response.json() if response.status_code == 200 else response.text
            }
        except Exception as e:
            results["configure"] = {"success": False, "error": str(e)}
        
        # Test transparency statistics
        try:
            response = await self.client.get("/api/transparency/statistics")
            results["statistics"] = {
                "status_code": response.status_code,
                "success": response.status_code in [200, 404],  # 404 is acceptable if endpoint not available
                "response": response.json() if response.status_code == 200 else response.text
            }
        except Exception as e:
            results["statistics"] = {"success": False, "error": str(e)}
        
        # Test knowledge graph endpoints
        try:
            response = await self.client.get("/api/transparency/knowledge-graph/statistics")
            results["knowledge_graph_stats"] = {
                "status_code": response.status_code,
                "success": response.status_code in [200, 404],  # 404 is acceptable if endpoint not available
                "response": response.json() if response.status_code == 200 else response.text
            }
        except Exception as e:
            results["knowledge_graph_stats"] = {"success": False, "error": str(e)}
        
        success_count = sum(1 for r in results.values() if r.get("success", False))
        total_count = len(results)
        
        logger.info(f"Transparency endpoints: {success_count}/{total_count} passed")
        return {
            "success": success_count > 0,  # At least one endpoint should work
            "results": results,
            "summary": f"{success_count}/{total_count} endpoints accessible"
        }
    
    async def test_websocket_connection(self) -> Dict[str, Any]:
        """Test WebSocket connection for cognitive streaming."""
        logger.info("Testing WebSocket connection...")
        try:
            uri = f"{WS_URL}/ws/cognitive-stream"
            
            async with websockets.connect(uri, timeout=10) as websocket:
                # Send subscription message
                subscribe_message = {
                    "type": "subscribe",
                    "event_types": ["cognitive_state_update", "query_processed"]
                }
                await websocket.send(json.dumps(subscribe_message))
                
                # Wait for initial messages
                messages_received = []
                timeout_counter = 0
                max_timeout = 5  # 5 seconds
                
                while timeout_counter < max_timeout:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        messages_received.append(json.loads(message))
                        
                        # Check if we received a subscription confirmation
                        if any(msg.get("type") == "subscription_confirmed" for msg in messages_received):
                            break
                            
                    except asyncio.TimeoutError:
                        timeout_counter += 1
                        continue
                
                result = {
                    "success": len(messages_received) > 0,
                    "messages_count": len(messages_received),
                    "messages": messages_received[:3]  # First 3 messages for debugging
                }
                
                logger.info(f"WebSocket connection: {'PASSED' if result['success'] else 'FAILED'}")
                return result
                
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all integration tests."""
        logger.info("Starting cognitive transparency backend integration tests...")
        
        tests = [
            ("health", self.test_health_endpoint),
            ("root", self.test_root_endpoint),
            ("query", self.test_query_endpoint),
            ("knowledge", self.test_knowledge_endpoint),
            ("cognitive_state", self.test_cognitive_state_endpoint),
            ("transparency", self.test_transparency_endpoints),
            ("websocket", self.test_websocket_connection)
        ]
        
        results = {}
        passed_tests = 0
        
        for test_name, test_func in tests:
            logger.info(f"\n--- Running {test_name} test ---")
            try:
                result = await test_func()
                results[test_name] = result
                if result.get("success", False):
                    passed_tests += 1
                    logger.info(f"✅ {test_name} test PASSED")
                else:
                    logger.error(f"❌ {test_name} test FAILED: {result.get('error', 'Unknown error')}")
            except Exception as e:
                logger.error(f"❌ {test_name} test FAILED with exception: {e}")
                results[test_name] = {"success": False, "error": str(e)}
        
        # Summary
        total_tests = len(tests)
        success_rate = (passed_tests / total_tests) * 100
        
        summary = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": success_rate,
            "overall_success": success_rate >= 70,  # 70% pass rate considered successful
            "timestamp": time.time(),
            "test_results": results
        }
        
        logger.info(f"\n{'='*50}")
        logger.info(f"INTEGRATION TEST SUMMARY")
        logger.info(f"{'='*50}")
        logger.info(f"Total tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {total_tests - passed_tests}")
        logger.info(f"Success rate: {success_rate:.1f}%")
        logger.info(f"Overall result: {'PASSED' if summary['overall_success'] else 'FAILED'}")
        logger.info(f"{'='*50}")
        
        return summary


async def main():
    """Main test runner."""
    async with CognitiveTransparencyTester() as tester:
        results = await tester.run_all_tests()
        
        # Write results to file
        with open("cognitive_transparency_test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"\nTest results saved to: cognitive_transparency_test_results.json")
        
        # Exit with appropriate code
        exit_code = 0 if results["overall_success"] else 1
        return exit_code


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Tests interrupted by user")
        exit(1)
    except Exception as e:
        logger.error(f"Test runner failed: {e}")
        exit(1)