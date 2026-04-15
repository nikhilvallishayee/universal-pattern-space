"""
Unit tests for the CognitiveDiagnostician.
"""

import unittest
from unittest.mock import MagicMock, patch
import time

from godelOS.metacognition.diagnostician import (
    CognitiveDiagnostician,
    DiagnosticFinding,
    DiagnosticReport,
    DiagnosisType,
    SeverityLevel,
    DiagnosticRule,
    PerformanceBottleneckRule,
    ReasoningFailureRule,
    ResourceContentionRule
)


class TestCognitiveDiagnostician(unittest.TestCase):
    """Test cases for the CognitiveDiagnostician."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mocks
        self.mock_self_monitoring = MagicMock()
        self.mock_meta_knowledge = MagicMock()
        
        # Configure mocks
        self.mock_self_monitoring.get_performance_metrics.return_value = {
            "system_resources": {
                "CPU": {"value": 90.0, "status": "critical"},
                "Memory": {"value": 60.0, "status": "moderate"}
            },
            "module_states": {
                "InferenceEngine": {
                    "status": "active",
                    "metrics": {
                        "active_tasks": 2,
                        "inference_steps_per_second": 100.0,
                        "average_proof_time_ms": 150.0
                    }
                },
                "KRSystem": {
                    "status": "active",
                    "metrics": {
                        "query_rate_per_second": 200.0,
                        "statement_count": 5000
                    }
                }
            },
            "reasoning_strategies": {
                "ResolutionProver": {
                    "success_rate": 0.7,
                    "average_duration_ms": 120.0,
                    "total_executions": 100
                },
                "AnalogicalReasoning": {
                    "success_rate": 0.5,
                    "average_duration_ms": 200.0,
                    "total_executions": 50
                }
            }
        }
        
        self.mock_self_monitoring.get_recent_anomalies.return_value = [
            MagicMock(
                anomaly_type="resource_saturation",
                severity=0.8,
                affected_component="CPU",
                description="CPU usage is high",
                metrics={"value": 90.0, "threshold": 80.0}
            )
        ]
        
        # Create CognitiveDiagnostician instance
        self.diagnostician = CognitiveDiagnostician(
            self_monitoring_module=self.mock_self_monitoring,
            meta_knowledge_base=self.mock_meta_knowledge
        )
    
    def test_initialization(self):
        """Test initialization of CognitiveDiagnostician."""
        # Verify attributes
        self.assertEqual(self.diagnostician.self_monitoring, self.mock_self_monitoring)
        self.assertEqual(self.diagnostician.meta_knowledge, self.mock_meta_knowledge)
        self.assertGreater(len(self.diagnostician.diagnostic_rules), 0)
        self.assertEqual(len(self.diagnostician.report_history), 0)
    
    def test_diagnose(self):
        """Test diagnosing system issues."""
        # Perform diagnosis
        findings = self.diagnostician.diagnose()
        
        # Verify findings
        self.assertGreater(len(findings), 0)
        
        # Check for CPU resource contention finding
        cpu_findings = [f for f in findings if f.diagnosis_type == DiagnosisType.RESOURCE_CONTENTION]
        self.assertGreater(len(cpu_findings), 0)
        
        # Check for reasoning failure finding (AnalogicalReasoning has 50% success rate)
        reasoning_findings = [f for f in findings if f.diagnosis_type == DiagnosisType.REASONING_FAILURE]
        self.assertGreater(len(reasoning_findings), 0)
    
    def test_generate_report(self):
        """Test generating a diagnostic report."""
        # Generate report
        report = self.diagnostician.generate_report()
        
        # Verify report
        self.assertIsInstance(report, DiagnosticReport)
        self.assertIsNotNone(report.report_id)
        self.assertGreater(len(report.findings), 0)
        self.assertIsNotNone(report.summary)
        self.assertIsNotNone(report.system_state)
        
        # Verify report was added to history
        self.assertEqual(len(self.diagnostician.report_history), 1)
        self.assertEqual(self.diagnostician.report_history[0], report)
    
    def test_get_recent_reports(self):
        """Test getting recent diagnostic reports."""
        # Generate multiple reports
        for _ in range(5):
            self.diagnostician.generate_report()
        
        # Get all reports
        all_reports = self.diagnostician.get_recent_reports()
        self.assertEqual(len(all_reports), 5)
        
        # Get limited reports
        limited_reports = self.diagnostician.get_recent_reports(limit=3)
        self.assertEqual(len(limited_reports), 3)
        
        # Verify most recent reports are returned
        self.assertEqual(limited_reports[0], self.diagnostician.report_history[-1])
        self.assertEqual(limited_reports[1], self.diagnostician.report_history[-2])
        self.assertEqual(limited_reports[2], self.diagnostician.report_history[-3])
    
    def test_get_findings_by_component(self):
        """Test getting findings by component."""
        # Create findings for different components
        finding1 = DiagnosticFinding(
            finding_id="finding1",
            diagnosis_type=DiagnosisType.PERFORMANCE_BOTTLENECK,
            severity=SeverityLevel.HIGH,
            affected_components=["ComponentA"],
            description="Issue with ComponentA",
            evidence={}
        )
        
        finding2 = DiagnosticFinding(
            finding_id="finding2",
            diagnosis_type=DiagnosisType.RESOURCE_CONTENTION,
            severity=SeverityLevel.MEDIUM,
            affected_components=["ComponentB"],
            description="Issue with ComponentB",
            evidence={}
        )
        
        finding3 = DiagnosticFinding(
            finding_id="finding3",
            diagnosis_type=DiagnosisType.REASONING_FAILURE,
            severity=SeverityLevel.LOW,
            affected_components=["ComponentA", "ComponentC"],
            description="Issue with ComponentA and ComponentC",
            evidence={}
        )
        
        # Create a report with these findings
        report = DiagnosticReport(
            report_id="test_report",
            findings=[finding1, finding2, finding3],
            summary="Test report",
            system_state={}
        )
        
        # Add report to history
        self.diagnostician.report_history.append(report)
        
        # Get findings by component
        componentA_findings = self.diagnostician.get_findings_by_component("ComponentA")
        componentB_findings = self.diagnostician.get_findings_by_component("ComponentB")
        componentC_findings = self.diagnostician.get_findings_by_component("ComponentC")
        
        # Verify findings
        self.assertEqual(len(componentA_findings), 2)
        self.assertEqual(len(componentB_findings), 1)
        self.assertEqual(len(componentC_findings), 1)
        
        self.assertIn(finding1, componentA_findings)
        self.assertIn(finding3, componentA_findings)
        self.assertIn(finding2, componentB_findings)
        self.assertIn(finding3, componentC_findings)
    
    def test_get_findings_by_type(self):
        """Test getting findings by type."""
        # Create findings of different types
        finding1 = DiagnosticFinding(
            finding_id="finding1",
            diagnosis_type=DiagnosisType.PERFORMANCE_BOTTLENECK,
            severity=SeverityLevel.HIGH,
            affected_components=["ComponentA"],
            description="Performance bottleneck",
            evidence={}
        )
        
        finding2 = DiagnosticFinding(
            finding_id="finding2",
            diagnosis_type=DiagnosisType.RESOURCE_CONTENTION,
            severity=SeverityLevel.MEDIUM,
            affected_components=["ComponentB"],
            description="Resource contention",
            evidence={}
        )
        
        finding3 = DiagnosticFinding(
            finding_id="finding3",
            diagnosis_type=DiagnosisType.PERFORMANCE_BOTTLENECK,
            severity=SeverityLevel.LOW,
            affected_components=["ComponentC"],
            description="Another performance bottleneck",
            evidence={}
        )
        
        # Create a report with these findings
        report = DiagnosticReport(
            report_id="test_report",
            findings=[finding1, finding2, finding3],
            summary="Test report",
            system_state={}
        )
        
        # Add report to history
        self.diagnostician.report_history.append(report)
        
        # Get findings by type
        bottleneck_findings = self.diagnostician.get_findings_by_type(DiagnosisType.PERFORMANCE_BOTTLENECK)
        contention_findings = self.diagnostician.get_findings_by_type(DiagnosisType.RESOURCE_CONTENTION)
        failure_findings = self.diagnostician.get_findings_by_type(DiagnosisType.REASONING_FAILURE)
        
        # Verify findings
        self.assertEqual(len(bottleneck_findings), 2)
        self.assertEqual(len(contention_findings), 1)
        self.assertEqual(len(failure_findings), 0)
        
        self.assertIn(finding1, bottleneck_findings)
        self.assertIn(finding3, bottleneck_findings)
        self.assertIn(finding2, contention_findings)
    
    def test_performance_bottleneck_rule(self):
        """Test the PerformanceBottleneckRule."""
        # Create rule
        rule = PerformanceBottleneckRule(
            rule_id="test_bottleneck_rule",
            component_id="InferenceEngine",
            metric_threshold={
                "average_proof_time_ms": 100.0,
                "active_tasks": 1
            },
            severity_mapping={
                "1.5": SeverityLevel.LOW,
                "2.0": SeverityLevel.MEDIUM,
                "3.0": SeverityLevel.HIGH
            }
        )
        
        # Create monitoring data
        monitoring_data = {
            "module_states": {
                "InferenceEngine": {
                    "status": "active",
                    "metrics": {
                        "average_proof_time_ms": 150.0,  # Exceeds threshold
                        "active_tasks": 2  # Exceeds threshold
                    }
                }
            }
        }
        
        # Evaluate rule
        finding = rule.evaluate(monitoring_data, {})
        
        # Verify finding
        self.assertIsNotNone(finding)
        self.assertEqual(finding.diagnosis_type, DiagnosisType.PERFORMANCE_BOTTLENECK)
        self.assertEqual(finding.affected_components, ["InferenceEngine"])
        
        # Both metrics exceed threshold, average_proof_time_ms by 1.5x and active_tasks by 2x
        # So severity should be MEDIUM based on the mapping
        self.assertEqual(finding.severity, SeverityLevel.MEDIUM)
    
    def test_reasoning_failure_rule(self):
        """Test the ReasoningFailureRule."""
        # Create rule
        rule = ReasoningFailureRule(
            rule_id="test_reasoning_rule",
            strategy_name="AnalogicalReasoning",
            failure_rate_threshold=0.4,
            min_sample_size=10,
            severity_mapping={
                "0.4": SeverityLevel.LOW,
                "0.6": SeverityLevel.MEDIUM,
                "0.8": SeverityLevel.HIGH
            }
        )
        
        # Create monitoring data
        monitoring_data = {
            "reasoning_strategies": {
                "AnalogicalReasoning": {
                    "success_rate": 0.5,  # 50% success rate = 50% failure rate
                    "total_executions": 50
                }
            }
        }
        
        # Evaluate rule
        finding = rule.evaluate(monitoring_data, {})
        
        # Verify finding
        self.assertIsNotNone(finding)
        self.assertEqual(finding.diagnosis_type, DiagnosisType.REASONING_FAILURE)
        self.assertEqual(finding.affected_components, ["ReasoningStrategy:AnalogicalReasoning"])
        
        # Failure rate is 0.5, which is between 0.4 and 0.6, so severity should be LOW
        self.assertEqual(finding.severity, SeverityLevel.LOW)
    
    def test_resource_contention_rule(self):
        """Test the ResourceContentionRule."""
        # Create rule
        rule = ResourceContentionRule(
            rule_id="test_resource_rule",
            resource_name="CPU",
            usage_threshold=80.0,
            severity_mapping={
                "80.0": SeverityLevel.LOW,
                "90.0": SeverityLevel.MEDIUM,
                "95.0": SeverityLevel.HIGH
            }
        )
        
        # Create monitoring data
        monitoring_data = {
            "system_resources": {
                "CPU": {"value": 92.0, "status": "critical"}
            },
            "module_states": {
                "InferenceEngine": {"status": "active"},
                "KRSystem": {"status": "active"}
            }
        }
        
        # Evaluate rule
        finding = rule.evaluate(monitoring_data, {})
        
        # Verify finding
        self.assertIsNotNone(finding)
        self.assertEqual(finding.diagnosis_type, DiagnosisType.RESOURCE_CONTENTION)
        self.assertEqual(finding.affected_components, ["InferenceEngine", "KRSystem"])
        
        # CPU usage is 92%, which is between 90% and 95%, so severity should be MEDIUM
        self.assertEqual(finding.severity, SeverityLevel.MEDIUM)


if __name__ == '__main__':
    unittest.main()