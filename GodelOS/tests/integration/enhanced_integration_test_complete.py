#!/usr/bin/env python3
"""
End-to-End Integration Test for Enhanced GödelOS System
Tests all components including the new ProvenanceTracker and enhanced integrations
"""

import asyncio
import json
import time
import requests
from typing import Dict, Any, List
import sys
import os

# Add the backend directory to the path
sys.path.append('/Users/oli/code/GödelOS.md/backend')
sys.path.append('/Users/oli/code/GödelOS.md')

API_BASE = "http://localhost:8000"

class EnhancedSystemTester:
    def __init__(self):
        self.test_results = {
            'backend_health': {},
            'frontend_access': {},
            'smart_import': {},
            'reasoning_sessions': {},
            'provenance_tracker': {},
            'integration_flow': {},
            'summary': {}
        }
        self.start_time = time.time()

    def log(self, message: str, test_category: str = "general"):
        """Log test progress with category"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] [{test_category.upper()}] {message}")

    def test_backend_health(self) -> bool:
        """Test all backend endpoints for health"""
        self.log("Testing backend health and API endpoints", "backend")
        
        endpoints = [
            "/health",
            "/api/transparency/statistics", 
            "/api/transparency/sessions/active",
            "/api/transparency/provenance/statistics",
            "/api/transparency/knowledge-graph/statistics"
        ]
        
        healthy = True
        for endpoint in endpoints:
            try:
                response = requests.get(f"{API_BASE}{endpoint}", timeout=5)
                success = response.status_code in [200, 201]
                self.test_results['backend_health'][endpoint] = {
                    'status': response.status_code,
                    'success': success,
                    'response_size': len(response.text)
                }
                if success:
                    self.log(f"✅ {endpoint} - OK ({response.status_code})", "backend")
                else:
                    self.log(f"❌ {endpoint} - FAILED ({response.status_code})", "backend")
                    healthy = False
            except Exception as e:
                self.log(f"❌ {endpoint} - ERROR: {str(e)}", "backend")
                self.test_results['backend_health'][endpoint] = {
                    'status': 'error',
                    'success': False,
                    'error': str(e)
                }
                healthy = False
        
        return healthy

    def test_frontend_access(self) -> bool:
        """Test frontend accessibility"""
        self.log("Testing frontend accessibility", "frontend")
        
        try:
            response = requests.get("http://localhost:3001", timeout=5)
            success = response.status_code == 200
            self.test_results['frontend_access'] = {
                'status': response.status_code,
                'success': success,
                'content_length': len(response.text),
                'has_godelos_content': ('GödelOS' in response.text or 'Cognitive Transparency Interface' in response.text)
            }
            
            if success:
                self.log("✅ Frontend accessible", "frontend")
                return True
            else:
                self.log(f"❌ Frontend not accessible ({response.status_code})", "frontend")
                return False
        except Exception as e:
            self.log(f"❌ Frontend error: {str(e)}", "frontend")
            self.test_results['frontend_access'] = {'success': False, 'error': str(e)}
            return False

    def test_smart_import_enhanced(self) -> bool:
        """Test the enhanced SmartImport component integration"""
        self.log("Testing enhanced SmartImport component", "import")
        
        test_cases = [
            {
                'name': 'Text Import',
                'endpoint': '/api/knowledge/import/text',
                'data': {
                    'content': 'This is a test knowledge import for the enhanced system.',
                    'title': 'Enhanced System Test',
                    'category': 'test'
                }
            }
        ]
        import_id = None
        all_passed = True
        for test in test_cases:
            try:
                response = requests.post(
                    f"{API_BASE}{test['endpoint']}", 
                    json=test.get('data', {}),
                    timeout=10
                )
                success = response.status_code in [200, 201, 202]
                result_json = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text[:200]
                self.test_results['smart_import'][test['name']] = {
                    'status': response.status_code,
                    'success': success,
                    'response': result_json
                }
                if success:
                    self.log(f"✅ {test['name']} - OK", "import")
                    # Try to extract import_id for progress check
                    if isinstance(result_json, dict) and 'import_id' in result_json:
                        import_id = result_json['import_id']
                else:
                    self.log(f"❌ {test['name']} - FAILED ({response.status_code})", "import")
                    all_passed = False
            except Exception as e:
                self.log(f"❌ {test['name']} - ERROR: {str(e)}", "import")
                self.test_results['smart_import'][test['name']] = {'success': False, 'error': str(e)}
                all_passed = False
        # Progress check (only if import_id is available)
        if import_id:
            try:
                progress_endpoint = f"/api/knowledge/import/progress/{import_id}"
                response = requests.get(f"{API_BASE}{progress_endpoint}", timeout=10)
                success = response.status_code in [200, 201, 202]
                self.test_results['smart_import']['Import Progress Check'] = {
                    'status': response.status_code,
                    'success': success,
                    'response': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text[:200]
                }
                if success:
                    self.log(f"✅ Import Progress Check - OK", "import")
                else:
                    self.log(f"❌ Import Progress Check - FAILED ({response.status_code})", "import")
                    all_passed = False
            except Exception as e:
                self.log(f"❌ Import Progress Check - ERROR: {str(e)}", "import")
                self.test_results['smart_import']['Import Progress Check'] = {'success': False, 'error': str(e)}
                all_passed = False
        else:
            self.log("❌ Import Progress Check - SKIPPED (no import_id)", "import")
            self.test_results['smart_import']['Import Progress Check'] = {'success': False, 'error': 'No import_id returned from import'}
        return all_passed

    def test_reasoning_sessions_enhanced(self) -> bool:
        """Test the enhanced ReasoningSessionViewer component"""
        self.log("Testing enhanced ReasoningSessionViewer", "reasoning")
        
        try:
            # Test session creation
            session_data = {
                'query': 'Enhanced Integration Test Session',
                'transparency_level': 'detailed',
                'context': {
                    'components': ['reasoning', 'knowledge', 'uncertainty', 'provenance']
                }
            }
            
            create_response = requests.post(
                f"{API_BASE}/api/transparency/session/start",
                json=session_data,
                timeout=10
            )
            
            if create_response.status_code in [200, 201]:
                session_info = create_response.json()
                session_id = session_info.get('session_id')
                self.log(f"✅ Session created: {session_id}", "reasoning")
                
                # Test session retrieval
                get_response = requests.get(
                    f"{API_BASE}/api/transparency/sessions/active",
                    timeout=5
                )
                
                active_sessions = get_response.json() if get_response.status_code == 200 else {}
                
                self.test_results['reasoning_sessions'] = {
                    'session_creation': {
                        'success': True,
                        'session_id': session_id,
                        'response': session_info
                    },
                    'active_sessions_fetch': {
                        'success': get_response.status_code == 200,
                        'count': len(active_sessions.get('sessions', [])),
                        'status': get_response.status_code
                    }
                }
                
                self.log(f"✅ Active sessions retrieved: {len(active_sessions.get('sessions', []))}", "reasoning")
                return True
            else:
                self.log(f"❌ Session creation failed ({create_response.status_code})", "reasoning")
                self.test_results['reasoning_sessions'] = {
                    'session_creation': {'success': False, 'status': create_response.status_code}
                }
                return False
                
        except Exception as e:
            self.log(f"❌ Reasoning sessions error: {str(e)}", "reasoning")
            self.test_results['reasoning_sessions'] = {'success': False, 'error': str(e)}
            return False

    def test_provenance_tracker_new(self) -> bool:
        """Test the new ProvenanceTracker component and backend integration"""
        self.log("Testing new ProvenanceTracker component", "provenance")
        
        test_cases = [
            {
                'name': 'Provenance Query',
                'method': 'POST',
                'endpoint': '/api/transparency/provenance/query',
                'data': {
                    'target_id': 'enhanced_test_target',
                    'query_type': 'backward_trace',
                    'max_depth': 5
                }
            },
            {
                'name': 'Provenance Statistics',
                'method': 'GET',
                'endpoint': '/api/transparency/provenance/statistics'
            },
            {
                'name': 'Attribution Chain',
                'method': 'GET',
                'endpoint': '/api/transparency/provenance/attribution/test_entity'
            },
            {
                'name': 'Knowledge Snapshot',
                'method': 'POST',
                'endpoint': '/api/transparency/provenance/snapshot',
                'data': {}
            }
        ]
        
        all_passed = True
        for test in test_cases:
            try:
                if test['method'] == 'GET':
                    response = requests.get(f"{API_BASE}{test['endpoint']}", timeout=10)
                else:
                    response = requests.post(
                        f"{API_BASE}{test['endpoint']}", 
                        json=test.get('data', {}),
                        timeout=10
                    )
                
                success = response.status_code in [200, 201]
                response_data = None
                try:
                    response_data = response.json()
                except:
                    response_data = response.text[:100]
                
                self.test_results['provenance_tracker'][test['name']] = {
                    'status': response.status_code,
                    'success': success,
                    'response': response_data
                }
                
                if success:
                    self.log(f"✅ {test['name']} - OK", "provenance")
                else:
                    self.log(f"❌ {test['name']} - FAILED ({response.status_code})", "provenance")
                    all_passed = False
                    
            except Exception as e:
                self.log(f"❌ {test['name']} - ERROR: {str(e)}", "provenance")
                self.test_results['provenance_tracker'][test['name']] = {'success': False, 'error': str(e)}
                all_passed = False
        
        return all_passed

    def test_integration_flow(self) -> bool:
        """Test the complete enhanced integration flow"""
        self.log("Testing complete enhanced integration flow", "integration")
        
        try:
            # 1. Import some knowledge
            import_response = requests.post(
                f"{API_BASE}/api/knowledge/import/text",
                json={
                    'content': 'Enhanced GödelOS system with provenance tracking and improved transparency.',
                    'title': 'Integration Test Knowledge',
                    'category': 'system_test'
                },
                timeout=10
            )
            
            # 2. Create a reasoning session
            session_response = requests.post(
                f"{API_BASE}/api/transparency/session/start",
                json={
                    'query': 'Integration Flow Test - Enhanced GödelOS system test',
                    'transparency_level': 'detailed',
                    'context': {
                        'test_type': 'integration_flow',
                        'components': ['reasoning', 'knowledge', 'provenance']
                    }
                },
                timeout=10
            )
            
            # 3. Query provenance for the imported knowledge
            provenance_response = requests.post(
                f"{API_BASE}/api/transparency/provenance/query",
                json={
                    'target_id': 'Integration Test Knowledge',
                    'query_type': 'backward_trace',
                    'max_depth': 3
                },
                timeout=10
            )
            
            # 4. Get system statistics
            stats_response = requests.get(f"{API_BASE}/api/transparency/statistics", timeout=5)
            
            flow_results = {
                'import_success': import_response.status_code in [200, 201, 202],
                'session_success': session_response.status_code in [200, 201],
                'provenance_success': provenance_response.status_code in [200, 201],
                'stats_success': stats_response.status_code == 200
            }
            
            overall_success = all(flow_results.values())
            
            self.test_results['integration_flow'] = {
                'overall_success': overall_success,
                'steps': flow_results,
                'details': {
                    'import_status': import_response.status_code,
                    'session_status': session_response.status_code,
                    'provenance_status': provenance_response.status_code,
                    'stats_status': stats_response.status_code
                }
            }
            
            if overall_success:
                self.log("✅ Complete integration flow - SUCCESS", "integration")
            else:
                self.log("❌ Integration flow - PARTIAL FAILURE", "integration")
            
            return overall_success
            
        except Exception as e:
            self.log(f"❌ Integration flow error: {str(e)}", "integration")
            self.test_results['integration_flow'] = {'success': False, 'error': str(e)}
            return False

    def generate_summary(self) -> Dict[str, Any]:
        """Generate comprehensive test summary"""
        end_time = time.time()
        duration = end_time - self.start_time
        
        # Count successes and failures
        total_tests = 0
        successful_tests = 0
        
        for category, results in self.test_results.items():
            if category == 'summary':
                continue
            
            if isinstance(results, dict):
                for test_name, result in results.items():
                    if isinstance(result, dict) and 'success' in result:
                        total_tests += 1
                        if result['success']:
                            successful_tests += 1
                    elif isinstance(result, bool):
                        total_tests += 1
                        if result:
                            successful_tests += 1
        
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        summary = {
            'test_duration_seconds': round(duration, 2),
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'failed_tests': total_tests - successful_tests,
            'success_rate_percent': round(success_rate, 1),
            'overall_status': 'PASS' if success_rate >= 85 else 'PARTIAL' if success_rate >= 70 else 'FAIL',
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'components_tested': [
                'Backend Health',
                'Frontend Access', 
                'Enhanced SmartImport',
                'Enhanced ReasoningSessionViewer',
                'New ProvenanceTracker',
                'Complete Integration Flow'
            ]
        }
        
        self.test_results['summary'] = summary
        return summary

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all enhanced system tests"""
        self.log("🚀 Starting Enhanced GödelOS System Integration Tests", "test")
        
        # Run all test categories
        tests = [
            ('Backend Health', self.test_backend_health),
            ('Frontend Access', self.test_frontend_access),
            ('Enhanced SmartImport', self.test_smart_import_enhanced),
            ('Enhanced ReasoningSessionViewer', self.test_reasoning_sessions_enhanced),
            ('New ProvenanceTracker', self.test_provenance_tracker_new),
            ('Integration Flow', self.test_integration_flow)
        ]
        
        for test_name, test_func in tests:
            self.log(f"Running {test_name} tests...", "test")
            try:
                result = test_func()
                status = "✅ PASSED" if result else "❌ FAILED"
                self.log(f"{test_name}: {status}", "test")
            except Exception as e:
                self.log(f"{test_name}: ❌ ERROR - {str(e)}", "test")
        
        # Generate summary
        summary = self.generate_summary()
        
        self.log("📊 TEST SUMMARY", "summary")
        self.log(f"Duration: {summary['test_duration_seconds']}s", "summary")
        self.log(f"Tests: {summary['successful_tests']}/{summary['total_tests']} passed ({summary['success_rate_percent']}%)", "summary")
        self.log(f"Overall Status: {summary['overall_status']}", "summary")
        
        return self.test_results

def main():
    """Main test execution"""
    tester = EnhancedSystemTester()
    results = tester.run_all_tests()
    
    # Save results to file
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    results_file = f"/Users/oli/code/GödelOS.md/enhanced_integration_test_results_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📁 Detailed results saved to: {results_file}")
    
    # Return appropriate exit code
    summary = results.get('summary', {})
    success_rate = summary.get('success_rate_percent', 0)
    
    if success_rate >= 85:
        print("\n🎉 ENHANCED GODELOS SYSTEM: INTEGRATION TESTS PASSED!")
        return 0
    elif success_rate >= 70:
        print("\n⚠️  ENHANCED GODELOS SYSTEM: PARTIAL SUCCESS - Minor issues detected")
        return 1
    else:
        print("\n❌ ENHANCED GODELOS SYSTEM: INTEGRATION TESTS FAILED - Major issues detected")
        return 2

if __name__ == "__main__":
    exit(main())
