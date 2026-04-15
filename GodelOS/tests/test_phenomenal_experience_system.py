#!/usr/bin/env python3
"""
Comprehensive Test Suite for Phenomenal Experience System

Tests all aspects of the phenomenal experience generator including:
- Experience generation across all types
- Qualia pattern modeling
- Conscious state management
- Experience history tracking
- API endpoint functionality
- Narrative generation
- State coherence and unity
"""

import asyncio
import json
import logging
import requests
import sys
import time
from datetime import datetime
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

class PhenomenalExperienceSystemTester:
    """Comprehensive test suite for the phenomenal experience system"""
    
    def __init__(self):
        self.test_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_details": []
        }
        self.experience_types = [
            "cognitive", "emotional", "sensory", "attention", "memory", 
            "metacognitive", "imaginative", "social", "temporal", "spatial"
        ]
    
    async def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🧠 Starting Phenomenal Experience System Test Suite")
        print("=" * 60)
        
        # Test phases
        test_phases = [
            ("📋 API Availability", self.test_api_availability),
            ("🎭 Experience Type Validation", self.test_available_experience_types),
            ("⚡ Experience Generation", self.test_experience_generation),
            ("🧩 Qualia Pattern Validation", self.test_qualia_patterns),
            ("🎯 Conscious State Management", self.test_conscious_state_management),
            ("📚 Experience History", self.test_experience_history),
            ("📊 Experience Summary", self.test_experience_summary),
            ("🎪 Experience Triggering", self.test_experience_triggering),
            ("📝 Narrative Generation", self.test_narrative_generation),
            ("🔄 State Coherence", self.test_state_coherence),
            ("🎨 Complex Scenarios", self.test_complex_scenarios),
            ("⚡ Performance Testing", self.test_performance)
        ]
        
        for phase_name, test_function in test_phases:
            print(f"\n{phase_name}")
            print("-" * 40)
            try:
                await test_function()
                print(f"✅ {phase_name} - PASSED")
            except Exception as e:
                print(f"❌ {phase_name} - FAILED: {e}")
                self._record_test_result(phase_name, False, str(e))
        
        self._print_final_results()
    
    def _record_test_result(self, test_name: str, passed: bool, details: str = ""):
        """Record test result"""
        self.test_results["total_tests"] += 1
        if passed:
            self.test_results["passed_tests"] += 1
        else:
            self.test_results["failed_tests"] += 1
        
        self.test_results["test_details"].append({
            "test": test_name,
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    async def test_api_availability(self):
        """Test if phenomenal experience API endpoints are available"""
        endpoints_to_test = [
            "/phenomenal/available-types",
            "/phenomenal/conscious-state",
            "/phenomenal/experience-history",
            "/phenomenal/experience-summary"
        ]
        
        for endpoint in endpoints_to_test:
            try:
                response = requests.get(f"{API_BASE}{endpoint}", timeout=5)
                if response.status_code == 200:
                    print(f"  ✅ {endpoint} - Available")
                    self._record_test_result(f"API {endpoint}", True)
                else:
                    print(f"  ❌ {endpoint} - Status: {response.status_code}")
                    self._record_test_result(f"API {endpoint}", False, f"Status: {response.status_code}")
            except Exception as e:
                print(f"  ❌ {endpoint} - Error: {e}")
                self._record_test_result(f"API {endpoint}", False, str(e))
    
    async def test_available_experience_types(self):
        """Test available experience types endpoint"""
        try:
            response = requests.get(f"{API_BASE}/phenomenal/available-types")
            if response.status_code == 200:
                data = response.json()
                types = data.get("available_types", [])
                
                print(f"  📋 Found {len(types)} experience types")
                for exp_type in types:
                    print(f"    • {exp_type.get('type', 'unknown')}: {exp_type.get('description', 'No description')}")
                
                # Validate expected types are present
                available_type_names = [t.get('type') for t in types]
                missing_types = set(self.experience_types) - set(available_type_names)
                
                if not missing_types:
                    print("  ✅ All expected experience types available")
                    self._record_test_result("Experience Types Complete", True)
                else:
                    print(f"  ⚠️ Missing types: {missing_types}")
                    self._record_test_result("Experience Types Complete", False, f"Missing: {missing_types}")
            else:
                raise Exception(f"API call failed with status {response.status_code}")
        except Exception as e:
            self._record_test_result("Available Experience Types", False, str(e))
            raise
    
    async def test_experience_generation(self):
        """Test experience generation for all types"""
        successful_generations = 0
        
        for exp_type in self.experience_types:
            try:
                test_context = {
                    "test_scenario": f"Testing {exp_type} experience",
                    "user_request": True,
                    "intensity_preference": 0.7
                }
                
                response = requests.post(
                    f"{API_BASE}/phenomenal/generate-experience",
                    json={
                        "experience_type": exp_type,
                        "context": test_context,
                        "intensity": 0.7
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    experience = data.get("experience", {})
                    
                    # Validate experience structure
                    required_fields = ["id", "type", "narrative", "vividness", "coherence", "qualia_patterns"]
                    missing_fields = [f for f in required_fields if f not in experience]
                    
                    if not missing_fields:
                        print(f"  ✅ {exp_type}: Generated successfully")
                        print(f"    📝 Narrative: {experience.get('narrative', '')[:100]}...")
                        print(f"    🎯 Vividness: {experience.get('vividness', 0):.2f}")
                        print(f"    🧩 Coherence: {experience.get('coherence', 0):.2f}")
                        print(f"    🌈 Qualia patterns: {len(experience.get('qualia_patterns', []))}")
                        successful_generations += 1
                        self._record_test_result(f"Generate {exp_type}", True)
                    else:
                        print(f"  ❌ {exp_type}: Missing fields: {missing_fields}")
                        self._record_test_result(f"Generate {exp_type}", False, f"Missing fields: {missing_fields}")
                else:
                    print(f"  ❌ {exp_type}: API error {response.status_code}")
                    self._record_test_result(f"Generate {exp_type}", False, f"Status: {response.status_code}")
                
            except Exception as e:
                print(f"  ❌ {exp_type}: Exception: {e}")
                self._record_test_result(f"Generate {exp_type}", False, str(e))
        
        print(f"\n  📊 Generated {successful_generations}/{len(self.experience_types)} experience types successfully")
        
        if successful_generations == len(self.experience_types):
            self._record_test_result("All Experience Generation", True)
        else:
            self._record_test_result("All Experience Generation", False, f"Only {successful_generations}/{len(self.experience_types)} succeeded")
    
    async def test_qualia_patterns(self):
        """Test qualia pattern validation and structure"""
        try:
            # Generate a cognitive experience to test qualia patterns
            response = requests.post(
                f"{API_BASE}/phenomenal/generate-experience",
                json={
                    "experience_type": "cognitive",
                    "context": {"test": "qualia_validation"},
                    "intensity": 0.8
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                experience = data.get("experience", {})
                qualia_patterns = experience.get("qualia_patterns", [])
                
                if qualia_patterns:
                    pattern = qualia_patterns[0]
                    required_qualia_fields = ["modality", "intensity", "valence", "complexity"]
                    
                    missing_qualia_fields = [f for f in required_qualia_fields if f not in pattern]
                    
                    if not missing_qualia_fields:
                        print("  ✅ Qualia pattern structure valid")
                        print(f"    🎨 Modality: {pattern.get('modality')}")
                        print(f"    ⚡ Intensity: {pattern.get('intensity')}")
                        print(f"    😊 Valence: {pattern.get('valence')}")
                        print(f"    🧩 Complexity: {pattern.get('complexity')}")
                        self._record_test_result("Qualia Pattern Structure", True)
                    else:
                        print(f"  ❌ Missing qualia fields: {missing_qualia_fields}")
                        self._record_test_result("Qualia Pattern Structure", False, f"Missing: {missing_qualia_fields}")
                else:
                    print("  ❌ No qualia patterns found")
                    self._record_test_result("Qualia Pattern Structure", False, "No patterns found")
            else:
                raise Exception(f"Failed to generate experience for qualia testing")
        except Exception as e:
            self._record_test_result("Qualia Pattern Validation", False, str(e))
            raise
    
    async def test_conscious_state_management(self):
        """Test conscious state management and tracking"""
        try:
            # Generate multiple experiences to populate conscious state
            for i in range(3):
                requests.post(
                    f"{API_BASE}/phenomenal/trigger-experience",
                    json={
                        "type": ["cognitive", "emotional", "attention"][i],
                        "context": {"test": f"conscious_state_test_{i}"},
                        "intensity": 0.6 + i * 0.1
                    }
                )
                await asyncio.sleep(0.1)  # Small delay between experiences
            
            # Check conscious state
            response = requests.get(f"{API_BASE}/phenomenal/conscious-state")
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("status") == "success":
                    conscious_state = data.get("conscious_state", {})
                    
                    # Validate conscious state structure
                    required_state_fields = [
                        "active_experiences", "background_tone", "attention_distribution",
                        "self_awareness_level", "phenomenal_unity"
                    ]
                    
                    missing_state_fields = [f for f in required_state_fields if f not in conscious_state]
                    
                    if not missing_state_fields:
                        active_experiences = conscious_state.get("active_experiences", [])
                        print(f"  ✅ Conscious state structure valid")
                        print(f"    🎭 Active experiences: {len(active_experiences)}")
                        print(f"    🧠 Self-awareness level: {conscious_state.get('self_awareness_level', 0):.2f}")
                        print(f"    🔗 Phenomenal unity: {conscious_state.get('phenomenal_unity', 0):.2f}")
                        print(f"    🎨 Background tone: {conscious_state.get('background_tone', {})}")
                        self._record_test_result("Conscious State Management", True)
                    else:
                        print(f"  ❌ Missing state fields: {missing_state_fields}")
                        self._record_test_result("Conscious State Management", False, f"Missing: {missing_state_fields}")
                else:
                    print("  ❌ No active conscious state")
                    self._record_test_result("Conscious State Management", False, "No active state")
            else:
                raise Exception(f"Conscious state API error: {response.status_code}")
        except Exception as e:
            self._record_test_result("Conscious State Management", False, str(e))
            raise
    
    async def test_experience_history(self):
        """Test experience history tracking"""
        try:
            response = requests.get(f"{API_BASE}/phenomenal/experience-history?limit=5")
            
            if response.status_code == 200:
                data = response.json()
                experiences = data.get("experiences", [])
                
                print(f"  ✅ Retrieved {len(experiences)} experiences from history")
                
                if experiences:
                    latest = experiences[0]
                    print(f"    📝 Latest: {latest.get('type')} - {latest.get('narrative', '')[:80]}...")
                    print(f"    🎯 Vividness: {latest.get('vividness', 0):.2f}")
                    print(f"    ⏰ Triggers: {latest.get('triggers', [])}")
                
                self._record_test_result("Experience History", True)
            else:
                raise Exception(f"History API error: {response.status_code}")
        except Exception as e:
            self._record_test_result("Experience History", False, str(e))
            raise
    
    async def test_experience_summary(self):
        """Test experience summary statistics"""
        try:
            response = requests.get(f"{API_BASE}/phenomenal/experience-summary")
            
            if response.status_code == 200:
                data = response.json()
                summary = data.get("summary", {})
                
                print(f"  ✅ Experience summary retrieved")
                print(f"    📊 Total experiences: {summary.get('total_experiences', 0)}")
                print(f"    📈 Average intensity: {summary.get('average_intensity', 0):.3f}")
                print(f"    😊 Average valence: {summary.get('average_valence', 0):.3f}")
                print(f"    🧩 Average coherence: {summary.get('average_coherence', 0):.3f}")
                
                experience_types = summary.get('experience_types', {})
                if experience_types:
                    print(f"    🎭 Type distribution: {experience_types}")
                
                self._record_test_result("Experience Summary", True)
            else:
                raise Exception(f"Summary API error: {response.status_code}")
        except Exception as e:
            self._record_test_result("Experience Summary", False, str(e))
            raise
    
    async def test_experience_triggering(self):
        """Test specific experience triggering with detailed context"""
        try:
            test_scenarios = [
                {
                    "type": "metacognitive",
                    "context": {"reflection_topic": "self_awareness", "depth": "deep"},
                    "intensity": 0.9
                },
                {
                    "type": "imaginative",
                    "context": {"creative_task": "story_generation", "genre": "science_fiction"},
                    "intensity": 0.8
                },
                {
                    "type": "social",
                    "context": {"interaction_type": "collaboration", "emotional_tone": "positive"},
                    "intensity": 0.7
                }
            ]
            
            successful_triggers = 0
            
            for scenario in test_scenarios:
                response = requests.post(
                    f"{API_BASE}/phenomenal/trigger-experience",
                    json=scenario
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "success":
                        experience = data.get("experience", {})
                        print(f"  ✅ Triggered {scenario['type']}: {experience.get('narrative', '')[:60]}...")
                        successful_triggers += 1
                    else:
                        print(f"  ❌ Failed to trigger {scenario['type']}")
                else:
                    print(f"  ❌ API error for {scenario['type']}: {response.status_code}")
            
            if successful_triggers == len(test_scenarios):
                self._record_test_result("Experience Triggering", True)
            else:
                self._record_test_result("Experience Triggering", False, f"Only {successful_triggers}/{len(test_scenarios)} succeeded")
        except Exception as e:
            self._record_test_result("Experience Triggering", False, str(e))
            raise
    
    async def test_narrative_generation(self):
        """Test narrative quality and first-person perspective"""
        try:
            response = requests.post(
                f"{API_BASE}/phenomenal/generate-experience",
                json={
                    "experience_type": "emotional",
                    "context": {
                        "emotional_state": "contemplative",
                        "trigger": "philosophical_question",
                        "depth": "profound"
                    },
                    "intensity": 0.85
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                experience = data.get("experience", {})
                narrative = experience.get("narrative", "")
                
                # Check for first-person perspective indicators
                first_person_indicators = ["I", "my", "me", "myself"]
                has_first_person = any(indicator in narrative for indicator in first_person_indicators)
                
                # Check narrative length and quality
                narrative_length = len(narrative)
                
                print(f"  ✅ Generated narrative ({narrative_length} chars)")
                print(f"    📝 Text: {narrative}")
                print(f"    👁️ First-person perspective: {'Yes' if has_first_person else 'No'}")
                
                if has_first_person and narrative_length > 20:
                    self._record_test_result("Narrative Generation", True)
                else:
                    self._record_test_result("Narrative Generation", False, "Poor narrative quality")
            else:
                raise Exception(f"Narrative generation API error: {response.status_code}")
        except Exception as e:
            self._record_test_result("Narrative Generation", False, str(e))
            raise
    
    async def test_state_coherence(self):
        """Test conscious state coherence and unity"""
        try:
            # Generate multiple related experiences
            related_experiences = [
                {"type": "cognitive", "context": {"task": "problem_solving"}},
                {"type": "attention", "context": {"focus": "problem_solving"}},
                {"type": "metacognitive", "context": {"reflection": "problem_solving_strategy"}}
            ]
            
            for exp_data in related_experiences:
                requests.post(f"{API_BASE}/phenomenal/trigger-experience", json=exp_data)
                await asyncio.sleep(0.1)
            
            # Check conscious state coherence
            response = requests.get(f"{API_BASE}/phenomenal/conscious-state")
            
            if response.status_code == 200:
                data = response.json()
                conscious_state = data.get("conscious_state", {})
                
                unity_score = conscious_state.get("phenomenal_unity", 0)
                attention_dist = conscious_state.get("attention_distribution", {})
                
                print(f"  ✅ State coherence analysis")
                print(f"    🔗 Phenomenal unity: {unity_score:.3f}")
                print(f"    🎯 Attention distribution: {attention_dist}")
                
                # Good coherence should have unity > 0.5 and distributed attention
                if unity_score > 0.5 and len(attention_dist) > 1:
                    self._record_test_result("State Coherence", True)
                else:
                    self._record_test_result("State Coherence", False, f"Low unity: {unity_score:.3f}")
            else:
                raise Exception(f"Coherence check API error: {response.status_code}")
        except Exception as e:
            self._record_test_result("State Coherence", False, str(e))
            raise
    
    async def test_complex_scenarios(self):
        """Test complex multi-experience scenarios"""
        try:
            # Scenario: Creative problem-solving session
            scenario_steps = [
                {"type": "cognitive", "context": {"task": "creative_challenge"}, "intensity": 0.7},
                {"type": "imaginative", "context": {"creative_mode": "brainstorming"}, "intensity": 0.8},
                {"type": "attention", "context": {"focus": "solution_evaluation"}, "intensity": 0.9},
                {"type": "metacognitive", "context": {"reflection": "process_assessment"}, "intensity": 0.6}
            ]
            
            print("  🎨 Running complex creative problem-solving scenario")
            
            for i, step in enumerate(scenario_steps):
                response = requests.post(f"{API_BASE}/phenomenal/trigger-experience", json=step)
                if response.status_code == 200:
                    print(f"    Step {i+1}: ✅ {step['type']}")
                else:
                    print(f"    Step {i+1}: ❌ {step['type']}")
                await asyncio.sleep(0.1)
            
            # Check final state
            final_state = requests.get(f"{API_BASE}/phenomenal/conscious-state")
            if final_state.status_code == 200:
                state_data = final_state.json()
                conscious_state = state_data.get("conscious_state", {})
                active_count = len(conscious_state.get("active_experiences", []))
                
                print(f"    🧠 Final state: {active_count} active experiences")
                self._record_test_result("Complex Scenarios", True)
            else:
                self._record_test_result("Complex Scenarios", False, "Failed to get final state")
        except Exception as e:
            self._record_test_result("Complex Scenarios", False, str(e))
            raise
    
    async def test_performance(self):
        """Test system performance under load"""
        try:
            start_time = time.time()
            concurrent_requests = 10
            
            print(f"  ⚡ Performance test: {concurrent_requests} concurrent requests")
            
            tasks = []
            for i in range(concurrent_requests):
                task = asyncio.create_task(self._make_async_request(
                    f"{API_BASE}/phenomenal/generate-experience",
                    {
                        "experience_type": self.experience_types[i % len(self.experience_types)],
                        "context": {"performance_test": True, "request_id": i},
                        "intensity": 0.5
                    }
                ))
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            
            successful_requests = sum(1 for r in results if not isinstance(r, Exception))
            total_time = end_time - start_time
            avg_time = total_time / concurrent_requests
            
            print(f"    📊 Results: {successful_requests}/{concurrent_requests} successful")
            print(f"    ⏱️ Total time: {total_time:.2f}s")
            print(f"    ⚡ Average time: {avg_time:.3f}s per request")
            
            if successful_requests >= concurrent_requests * 0.8:  # 80% success rate
                self._record_test_result("Performance Test", True)
            else:
                self._record_test_result("Performance Test", False, f"Low success rate: {successful_requests}/{concurrent_requests}")
        except Exception as e:
            self._record_test_result("Performance Test", False, str(e))
            raise
    
    async def _make_async_request(self, url: str, data: dict):
        """Make async HTTP request"""
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                return await response.json()
    
    def _print_final_results(self):
        """Print final test results summary"""
        print("\n" + "=" * 60)
        print("🧠 PHENOMENAL EXPERIENCE SYSTEM TEST RESULTS")
        print("=" * 60)
        
        total = self.test_results["total_tests"]
        passed = self.test_results["passed_tests"]
        failed = self.test_results["failed_tests"]
        
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"📊 Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if failed > 0:
            print(f"\n❌ Failed Tests:")
            for test in self.test_results["test_details"]:
                if not test["passed"]:
                    print(f"  • {test['test']}: {test['details']}")
        
        if success_rate >= 90:
            print(f"\n🎉 EXCELLENT: Phenomenal Experience System is working excellently!")
        elif success_rate >= 75:
            print(f"\n✅ GOOD: Phenomenal Experience System is working well with minor issues.")
        elif success_rate >= 50:
            print(f"\n⚠️ FAIR: Phenomenal Experience System has some issues that need attention.")
        else:
            print(f"\n❌ POOR: Phenomenal Experience System has significant issues.")


async def main():
    """Main test execution"""
    print("🚀 Initializing Phenomenal Experience System Tester...")
    
    tester = PhenomenalExperienceSystemTester()
    
    try:
        await tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite error: {e}")
        logger.exception("Test suite error")
    
    print(f"\n✨ Test completed at {datetime.now()}")


if __name__ == "__main__":
    # Check if server is running
    try:
        requests.get(f"{BASE_URL}/health", timeout=5)
        print("✅ GödelOS server is running")
    except requests.exceptions.RequestException:
        print("❌ GödelOS server is not running. Please start the server first.")
        print("   Run: python backend/unified_server.py")
        sys.exit(1)
    
    # Run tests
    asyncio.run(main())
