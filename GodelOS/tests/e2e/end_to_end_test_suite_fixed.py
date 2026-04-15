#!/usr/bin/env python3
"""
End-to-End Test Suite for GödelOS
Maps backend functionality to frontend implementation gaps
"""

import subprocess
import time
import requests
import json
import sys
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class EndpointTest:
    """Represents a test for a specific endpoint"""
    path: str
    method: str
    description: str
    expected_status: int = 200
    test_data: Optional[Dict] = None
    headers: Optional[Dict] = None
    frontend_component: Optional[str] = None
    ui_status: str = "unknown"  # "implemented", "missing", "partial", "unknown"

@dataclass
class TestResult:
    """Represents the result of an endpoint test"""
    endpoint: str
    success: bool
    status_code: int
    response_data: Optional[Dict] = None
    error_message: Optional[str] = None
    response_time_ms: float = 0.0

class GödelOSEndToEndTester:
    """Comprehensive end-to-end testing for GödelOS"""
    
    def __init__(self, backend_url: str = "http://localhost:8000", frontend_url: str = "http://localhost:3001"):
        self.backend_url = backend_url
        self.frontend_url = frontend_url
        self.test_results: List[TestResult] = []
        self.frontend_components = self._analyze_frontend_structure()
        
    def _analyze_frontend_structure(self) -> Dict[str, str]:
        """Analyze the Svelte frontend structure to understand implemented features"""
        components = {}
        svelte_dir = Path("/Users/oli/code/GödelOS.md/svelte-frontend/src")
        
        if svelte_dir.exists():
            for file in svelte_dir.rglob("*.svelte"):
                rel_path = file.relative_to(svelte_dir)
                components[str(rel_path)] = "found"
                
        return components
    
    def get_comprehensive_test_suite(self) -> List[EndpointTest]:
        """Define comprehensive test suite covering all backend functionality"""
        return [
            # Core System Health & Status
            EndpointTest(
                "/api/health", "GET", 
                "System health check",
                frontend_component="HealthStatus.svelte",
                ui_status="implemented"
            ),
            EndpointTest(
                "/api/capabilities", "GET",
                "System capabilities overview", 
                frontend_component="SystemCapabilities.svelte",
                ui_status="missing"
            ),
            EndpointTest(
                "/api/cognitive-state", "GET",
                "Current cognitive state",
                frontend_component="CognitiveState.svelte", 
                ui_status="missing"
            ),
            
            # Knowledge Management Core
            EndpointTest(
                "/api/knowledge", "GET",
                "List all knowledge items",
                frontend_component="KnowledgeList.svelte",
                ui_status="partial"
            ),
            EndpointTest(
                "/api/knowledge/statistics", "GET", 
                "Knowledge base statistics",
                frontend_component="KnowledgeStats.svelte",
                ui_status="missing"
            ),
            EndpointTest(
                "/api/knowledge/categories", "GET",
                "Knowledge categories list",
                frontend_component="KnowledgeCategories.svelte", 
                ui_status="missing"
            ),
            EndpointTest(
                "/api/knowledge/concepts", "GET",
                "Knowledge concepts extraction",
                frontend_component="ConceptsView.svelte",
                ui_status="missing"
            ),
            
            # Knowledge Graph & Evolution
            EndpointTest(
                "/api/knowledge/graph", "GET",
                "Knowledge graph visualization data",
                frontend_component="KnowledgeGraph.svelte",
                ui_status="implemented"
            ),
            EndpointTest(
                "/api/knowledge/evolution", "GET",
                "Knowledge evolution over time",
                frontend_component="KnowledgeEvolution.svelte", 
                ui_status="implemented"
            ),
            
            # Knowledge Search & Query
            EndpointTest(
                "/api/knowledge/search", "GET",
                "Search knowledge base",
                frontend_component="KnowledgeSearch.svelte",
                ui_status="partial"
            ),
            EndpointTest(
                "/api/query", "POST",
                "Natural language query processing",
                test_data={"query": "What is knowledge representation?"},
                frontend_component="QueryInterface.svelte",
                ui_status="implemented"
            ),
            
            # Knowledge Import Operations
            EndpointTest(
                "/api/knowledge/import/text", "POST",
                "Import text content",
                test_data={"content": "Test knowledge content", "title": "Test Import"},
                frontend_component="TextImport.svelte",
                ui_status="missing"
            ),
            EndpointTest(
                "/api/knowledge/import/url", "POST", 
                "Import from URL",
                test_data={"url": "https://example.com", "title": "Test URL Import"},
                frontend_component="URLImport.svelte", 
                ui_status="missing"
            ),
            EndpointTest(
                "/api/knowledge/import/wikipedia", "POST",
                "Import from Wikipedia",
                test_data={"title": "Artificial Intelligence", "language": "en"},
                frontend_component="WikipediaImport.svelte",
                ui_status="missing"
            ),
            EndpointTest(
                "/api/knowledge/import/file", "POST",
                "Import file upload", 
                frontend_component="FileImport.svelte",
                ui_status="missing"
            ),
            
            # Knowledge Export
            EndpointTest(
                "/api/knowledge/export", "GET",
                "Export knowledge base",
                frontend_component="KnowledgeExport.svelte",
                ui_status="missing" 
            ),
            
            # Cognitive Transparency Features
            EndpointTest(
                "/api/transparency/configure", "POST",
                "Configure transparency settings",
                test_data={"reasoning_depth": "detailed", "uncertainty_tracking": True},
                frontend_component="TransparencyConfig.svelte",
                ui_status="missing"
            ),
        ]
    
    def test_endpoint(self, test: EndpointTest) -> TestResult:
        """Test a single endpoint"""
        start_time = time.time()
        
        try:
            url = f"{self.backend_url}{test.path}"
            headers = test.headers or {"Content-Type": "application/json"}
            
            if test.method == "GET":
                response = requests.get(url, headers=headers, timeout=10)
            elif test.method == "POST":
                response = requests.post(url, json=test.test_data, headers=headers, timeout=10)
            else:
                return TestResult(
                    endpoint=test.path,
                    success=False,
                    status_code=0,
                    error_message=f"Unsupported method: {test.method}"
                )
            
            response_time = (time.time() - start_time) * 1000
            
            success = response.status_code == test.expected_status
            response_data = None
            
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text[:500]}
            
            return TestResult(
                endpoint=test.path,
                success=success,
                status_code=response.status_code,
                response_data=response_data,
                response_time_ms=response_time
            )
            
        except Exception as e:
            return TestResult(
                endpoint=test.path,
                success=False,
                status_code=0,
                error_message=str(e),
                response_time_ms=(time.time() - start_time) * 1000
            )
    
    def check_backend_health(self) -> bool:
        """Check if backend is running and healthy"""
        try:
            response = requests.get(f"{self.backend_url}/api/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def check_frontend_health(self) -> bool:
        """Check if frontend is running"""
        try:
            response = requests.get(self.frontend_url, timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run all tests and generate comprehensive report"""
        print("🔧 GödelOS End-to-End Test Suite")
        print("=" * 60)
        
        # Check system status
        backend_healthy = self.check_backend_health()
        frontend_healthy = self.check_frontend_health()
        
        print(f"🔍 Backend Status: {'✅ Healthy' if backend_healthy else '❌ Unhealthy'}")
        print(f"🔍 Frontend Status: {'✅ Running' if frontend_healthy else '❌ Not Running'}")
        
        if not backend_healthy:
            print("❌ Backend is not healthy. Please start the backend first.")
            return {"error": "Backend unhealthy"}
        
        # Run endpoint tests
        test_suite = self.get_comprehensive_test_suite()
        print(f"\n🚀 Running {len(test_suite)} endpoint tests...")
        
        results_by_category = {
            "system_health": [],
            "knowledge_core": [],
            "knowledge_graph": [],
            "search_query": [],
            "import_export": [],
            "transparency": [],
        }
        
        for i, test in enumerate(test_suite, 1):
            print(f"🔍 [{i:2d}/{len(test_suite)}] Testing {test.path}...")
            result = self.test_endpoint(test)
            self.test_results.append(result)
            
            # Categorize results
            if "health" in test.path or "capabilities" in test.path or "cognitive-state" in test.path:
                category = "system_health"
            elif "knowledge/graph" in test.path or "knowledge/evolution" in test.path:
                category = "knowledge_graph" 
            elif "search" in test.path or "query" in test.path:
                category = "search_query"
            elif "import" in test.path or "export" in test.path:
                category = "import_export"
            elif "transparency" in test.path:
                category = "transparency"
            elif "knowledge" in test.path:
                category = "knowledge_core"
            
            results_by_category[category].append({
                "test": test,
                "result": result
            })
            
            status = "✅" if result.success else "❌"
            print(f"    {status} {result.status_code} ({result.response_time_ms:.1f}ms)")
            if not result.success and result.error_message:
                print(f"       Error: {result.error_message}")
        
        # Generate report
        return self.generate_comprehensive_report(results_by_category, frontend_healthy)
    
    def generate_comprehensive_report(self, results_by_category: Dict, frontend_healthy: bool) -> Dict[str, Any]:
        """Generate comprehensive analysis report"""
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r.success)
        
        print(f"\n📊 Test Results Summary")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {total_tests - successful_tests}")
        print(f"Success Rate: {(successful_tests/total_tests)*100:.1f}%")
        
        # Analyze UI implementation gaps
        ui_gaps = self.analyze_ui_gaps()
        
        print(f"\n🎨 Frontend Implementation Analysis")
        print("=" * 60)
        print(f"Components Found: {len(self.frontend_components)}")
        print(f"Missing UI Features: {len(ui_gaps['missing'])}")
        print(f"Partial Implementations: {len(ui_gaps['partial'])}")
        print(f"Complete Implementations: {len(ui_gaps['implemented'])}")
        
        # Category-wise analysis
        print(f"\n📋 Feature Category Analysis")
        print("=" * 60)
        
        for category, tests in results_by_category.items():
            if tests:
                successful = sum(1 for t in tests if t["result"].success)
                total = len(tests)
                print(f"{category.replace('_', ' ').title()}: {successful}/{total} ({'✅' if successful == total else '⚠️'})")
        
        # Generate actionable recommendations
        recommendations = self.generate_recommendations(results_by_category, ui_gaps)
        
        print(f"\n💡 Recommendations")
        print("=" * 60)
        for rec in recommendations:
            print(f"• {rec}")
        
        # Create detailed JSON report
        report = {
            "timestamp": time.time(),
            "summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "success_rate": (successful_tests/total_tests)*100,
                "frontend_running": frontend_healthy
            },
            "categories": results_by_category,
            "ui_analysis": ui_gaps,
            "recommendations": recommendations,
            "detailed_results": [
                {
                    "endpoint": r.endpoint,
                    "success": r.success,
                    "status_code": r.status_code,
                    "response_time_ms": r.response_time_ms,
                    "error": r.error_message
                } for r in self.test_results
            ]
        }
        
        # Save report
        with open("/Users/oli/code/GödelOS.md/end_to_end_test_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📁 Detailed report saved to: end_to_end_test_report.json")
        
        return report
    
    def analyze_ui_gaps(self) -> Dict[str, List[str]]:
        """Analyze UI implementation gaps"""
        test_suite = self.get_comprehensive_test_suite()
        
        gaps = {
            "implemented": [],
            "partial": [],
            "missing": [],
            "unknown": []
        }
        
        for test in test_suite:
            if test.frontend_component:
                gaps[test.ui_status].append({
                    "endpoint": test.path,
                    "component": test.frontend_component,
                    "description": test.description
                })
        
        return gaps
    
    def generate_recommendations(self, results_by_category: Dict, ui_gaps: Dict) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Backend issues
        failed_endpoints = [r for r in self.test_results if not r.success]
        if failed_endpoints:
            recommendations.append(f"Fix {len(failed_endpoints)} failing backend endpoints")
        
        # UI gaps
        if ui_gaps["missing"]:
            recommendations.append(f"Implement {len(ui_gaps['missing'])} missing UI components")
            
        if ui_gaps["partial"]:
            recommendations.append(f"Complete {len(ui_gaps['partial'])} partially implemented features")
        
        # Priority recommendations
        missing_import = not any("import" in r.endpoint for r in self.test_results if r.success)
        missing_export = not any("export" in r.endpoint for r in self.test_results if r.success)
        missing_transparency = not any("transparency" in r.endpoint for r in self.test_results if r.success)
        
        if missing_import:
            recommendations.append("HIGH PRIORITY: Implement knowledge import functionality")
            
        if missing_export:
            recommendations.append("HIGH PRIORITY: Implement knowledge export functionality")
            
        if missing_transparency:
            recommendations.append("MEDIUM PRIORITY: Implement cognitive transparency features")
        
        return recommendations

def main():
    """Run the end-to-end test suite"""
    tester = GödelOSEndToEndTester()
    report = tester.run_comprehensive_tests()
    
    if "error" not in report:
        print(f"\n🎉 End-to-end testing complete!")
        print(f"📊 Success rate: {report['summary']['success_rate']:.1f}%")
        print(f"💡 Check end_to_end_test_report.json for detailed analysis")
    else:
        print(f"\n❌ Testing failed: {report['error']}")
        sys.exit(1)

if __name__ == "__main__":
    main()
