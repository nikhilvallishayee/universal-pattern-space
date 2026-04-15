"""
Unit tests for the SelfModificationPlanner.
"""

import unittest
from unittest.mock import MagicMock, patch
import time

from godelOS.metacognition.modification_planner import (
    SelfModificationPlanner,
    ModificationProposal,
    ModificationParameter,
    ExecutionPlan,
    ModificationResult,
    ModificationType,
    ModificationStatus,
    SafetyRiskLevel,
    SafetyChecker,
    ModificationEvaluator
)
from godelOS.metacognition.diagnostician import (
    DiagnosticFinding,
    DiagnosticReport,
    DiagnosisType,
    SeverityLevel
)


class TestSelfModificationPlanner(unittest.TestCase):
    """Test cases for the SelfModificationPlanner."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mocks
        self.mock_diagnostician = MagicMock()
        self.mock_meta_knowledge = MagicMock()
        self.mock_safety_checker = MagicMock(spec=SafetyChecker)
        self.mock_evaluator = MagicMock(spec=ModificationEvaluator)
        
        # Configure mocks
        self.mock_safety_checker.assess_risk.return_value = (
            SafetyRiskLevel.LOW,
            {"overall_risk": 0.3, "risk_factors": {}}
        )
        self.mock_safety_checker.is_safe_to_apply.return_value = (True, "Safe to apply")
        
        self.mock_evaluator.evaluate_proposal.return_value = {
            "expected_benefits": {"benefit1": {"description": "Test benefit", "estimated_impact": 0.5}},
            "potential_drawbacks": {},
            "confidence": 0.7,
            "recommendation": "RECOMMEND",
            "alternatives": []
        }
        
        # Create SelfModificationPlanner instance
        self.planner = SelfModificationPlanner(
            diagnostician=self.mock_diagnostician,
            meta_knowledge_base=self.mock_meta_knowledge,
            safety_checker=self.mock_safety_checker,
            evaluator=self.mock_evaluator,
            max_auto_approval_risk=SafetyRiskLevel.LOW
        )
    
    def test_initialization(self):
        """Test initialization of SelfModificationPlanner."""
        # Verify attributes
        self.assertEqual(self.planner.diagnostician, self.mock_diagnostician)
        self.assertEqual(self.planner.meta_knowledge, self.mock_meta_knowledge)
        self.assertEqual(self.planner.safety_checker, self.mock_safety_checker)
        self.assertEqual(self.planner.evaluator, self.mock_evaluator)
        self.assertEqual(self.planner.max_auto_approval_risk, SafetyRiskLevel.LOW)
        self.assertEqual(len(self.planner.proposals), 0)
        self.assertEqual(len(self.planner.execution_plans), 0)
        self.assertEqual(len(self.planner.modification_results), 0)
        self.assertEqual(len(self.planner.modification_history), 0)
    
    def test_generate_proposals_from_diagnostic_report(self):
        """Test generating proposals from a diagnostic report."""
        # Create a diagnostic report
        findings = [
            DiagnosticFinding(
                finding_id="finding1",
                diagnosis_type=DiagnosisType.PERFORMANCE_BOTTLENECK,
                severity=SeverityLevel.HIGH,
                affected_components=["InferenceEngine"],
                description="Performance bottleneck in InferenceEngine",
                evidence={"bottleneck_metrics": {"average_proof_time_ms": {"value": 200, "threshold": 100}}}
            ),
            DiagnosticFinding(
                finding_id="finding2",
                diagnosis_type=DiagnosisType.RESOURCE_CONTENTION,
                severity=SeverityLevel.MEDIUM,
                affected_components=["CPU"],
                description="CPU resource contention",
                evidence={"resource_usage": 90.0, "threshold": 80.0}
            ),
            DiagnosticFinding(
                finding_id="finding3",
                diagnosis_type=DiagnosisType.REASONING_FAILURE,
                severity=SeverityLevel.HIGH,
                affected_components=["ReasoningStrategy:ResolutionProver"],
                description="High failure rate in ResolutionProver",
                evidence={"failure_rate": 0.6, "threshold": 0.3}
            )
        ]
        
        report = DiagnosticReport(
            report_id="test_report",
            findings=findings,
            summary="Test report",
            system_state={"test": "state"}
        )
        
        # Generate proposals
        proposals = self.planner.generate_proposals_from_diagnostic_report(report, {"test": "state"})
        
        # Verify proposals
        self.assertGreater(len(proposals), 0)
        self.assertEqual(len(self.planner.proposals), len(proposals))
        
        # Check proposal types
        proposal_types = [p.modification_type for p in proposals]
        self.assertIn(ModificationType.PARAMETER_TUNING, proposal_types)
        self.assertIn(ModificationType.RESOURCE_ALLOCATION, proposal_types)
        
        # Check that proposals reference the findings
        for proposal in proposals:
            self.assertGreater(len(proposal.diagnostic_findings), 0)
    
    def test_evaluate_proposal(self):
        """Test evaluating a modification proposal."""
        # Create a proposal
        proposal = ModificationProposal(
            proposal_id="test_proposal",
            modification_type=ModificationType.PARAMETER_TUNING,
            target_components=["InferenceEngine"],
            description="Tune parameters for InferenceEngine",
            rationale="Improve performance",
            expected_benefits={"performance": "Better performance"},
            potential_risks={"stability": "Might reduce stability"},
            safety_risk_level=SafetyRiskLevel.LOW,
            estimated_effort=0.3,
            status=ModificationStatus.PROPOSED
        )
        
        # Add proposal to planner
        self.planner.proposals[proposal.proposal_id] = proposal
        
        # Evaluate proposal
        evaluation = self.planner.evaluate_proposal(proposal.proposal_id, {"test": "state"})
        
        # Verify evaluation
        self.assertIsNotNone(evaluation)
        self.assertIn("expected_benefits", evaluation)
        self.assertIn("potential_drawbacks", evaluation)
        self.assertIn("confidence", evaluation)
        self.assertIn("recommendation", evaluation)
        self.assertIn("safety", evaluation)
        
        # Verify proposal was updated
        self.assertEqual(proposal.status, ModificationStatus.APPROVED)  # Auto-approved due to low risk
        self.assertIn("evaluation", proposal.metadata)
    
    def test_create_execution_plan(self):
        """Test creating an execution plan for a proposal."""
        # Create an approved proposal
        proposal = ModificationProposal(
            proposal_id="test_proposal",
            modification_type=ModificationType.PARAMETER_TUNING,
            target_components=["InferenceEngine"],
            description="Tune parameters for InferenceEngine",
            rationale="Improve performance",
            expected_benefits={"performance": "Better performance"},
            potential_risks={"stability": "Might reduce stability"},
            safety_risk_level=SafetyRiskLevel.LOW,
            estimated_effort=0.3,
            status=ModificationStatus.APPROVED,
            metadata={
                "parameters": [
                    ModificationParameter(
                        name="max_inference_steps",
                        current_value=1000,
                        proposed_value=2000,
                        value_type="int",
                        description="Maximum number of inference steps"
                    )
                ]
            }
        )
        
        # Add proposal to planner
        self.planner.proposals[proposal.proposal_id] = proposal
        
        # Create execution plan
        plan = self.planner.create_execution_plan(proposal.proposal_id)
        
        # Verify plan
        self.assertIsNotNone(plan)
        self.assertIsInstance(plan, ExecutionPlan)
        self.assertEqual(plan.proposal_id, proposal.proposal_id)
        self.assertGreater(len(plan.steps), 0)
        self.assertGreater(len(plan.rollback_steps), 0)
        
        # Verify plan was stored
        self.assertIn(plan.plan_id, self.planner.execution_plans)
        
        # Verify proposal status was updated
        self.assertEqual(proposal.status, ModificationStatus.SCHEDULED)
    
    def test_execute_plan(self):
        """Test executing a modification plan."""
        # Create a proposal
        proposal = ModificationProposal(
            proposal_id="test_proposal",
            modification_type=ModificationType.PARAMETER_TUNING,
            target_components=["InferenceEngine"],
            description="Tune parameters for InferenceEngine",
            rationale="Improve performance",
            expected_benefits={"performance": "Better performance"},
            potential_risks={"stability": "Might reduce stability"},
            safety_risk_level=SafetyRiskLevel.LOW,
            estimated_effort=0.3,
            status=ModificationStatus.SCHEDULED
        )
        
        # Create an execution plan
        plan = ExecutionPlan(
            plan_id="test_plan",
            proposal_id=proposal.proposal_id,
            steps=[
                {
                    "step_id": "step_1",
                    "description": "Update parameter max_inference_steps",
                    "action": "update_parameter",
                    "parameters": {
                        "name": "max_inference_steps",
                        "value": 2000,
                        "component": "InferenceEngine"
                    }
                }
            ],
            rollback_steps=[
                {
                    "step_id": "rollback_1",
                    "description": "Restore parameter max_inference_steps",
                    "action": "update_parameter",
                    "parameters": {
                        "name": "max_inference_steps",
                        "value": 1000,
                        "component": "InferenceEngine"
                    }
                }
            ]
        )
        
        # Add proposal and plan to planner
        self.planner.proposals[proposal.proposal_id] = proposal
        self.planner.execution_plans[plan.plan_id] = plan
        
        # Execute plan
        with patch('time.sleep'):  # Mock sleep to speed up test
            result = self.planner.execute_plan(plan.plan_id, {"test": "state"})
        
        # Verify result
        self.assertIsNotNone(result)
        self.assertIsInstance(result, ModificationResult)
        self.assertEqual(result.proposal_id, proposal.proposal_id)
        self.assertEqual(result.execution_plan_id, plan.plan_id)
        self.assertTrue(result.success)
        self.assertGreater(len(result.actual_changes), 0)
        
        # Verify result was stored
        self.assertIn(result.result_id, self.planner.modification_results)
        
        # Verify proposal and plan status were updated
        self.assertEqual(proposal.status, ModificationStatus.COMPLETED)
        self.assertEqual(plan.status, ModificationStatus.COMPLETED)
        
        # Verify modification history was updated
        self.assertEqual(len(self.planner.modification_history), 1)
        self.assertEqual(self.planner.modification_history[0]["proposal_id"], proposal.proposal_id)
    
    def test_failed_execution(self):
        """Test handling of failed execution."""
        # Create a proposal
        proposal = ModificationProposal(
            proposal_id="test_proposal",
            modification_type=ModificationType.PARAMETER_TUNING,
            target_components=["InferenceEngine"],
            description="Tune parameters for InferenceEngine",
            rationale="Improve performance",
            expected_benefits={"performance": "Better performance"},
            potential_risks={"stability": "Might reduce stability"},
            safety_risk_level=SafetyRiskLevel.LOW,
            estimated_effort=0.3,
            status=ModificationStatus.SCHEDULED
        )
        
        # Create an execution plan with a step that will fail
        plan = ExecutionPlan(
            plan_id="test_plan",
            proposal_id=proposal.proposal_id,
            steps=[
                {
                    "step_id": "step_1",
                    "description": "This step will fail",
                    "action": "will_fail",
                    "parameters": {}
                }
            ],
            rollback_steps=[]
        )
        
        # Add proposal and plan to planner
        self.planner.proposals[proposal.proposal_id] = proposal
        self.planner.execution_plans[plan.plan_id] = plan
        
        # Make the execution fail
        with patch.object(self.planner, '_perform_rollback') as mock_rollback:
            # Configure the rollback to succeed
            mock_rollback.return_value = True
            
            # Execute plan with a step that will fail
            with patch('time.sleep'):  # Mock sleep to speed up test
                result = self.planner.execute_plan(plan.plan_id, {"test": "state"})
        
        # Verify result
        self.assertIsNotNone(result)
        self.assertFalse(result.success)
        self.assertTrue(result.was_reverted)
        
        # Verify rollback was called
        mock_rollback.assert_called_once()
        
        # Verify proposal and plan status were updated
        self.assertEqual(proposal.status, ModificationStatus.FAILED)
        self.assertEqual(plan.status, ModificationStatus.FAILED)
    
    def test_safety_checker(self):
        """Test the SafetyChecker component."""
        # Create a real SafetyChecker
        safety_checker = SafetyChecker()
        
        # Create proposals with different risk levels
        low_risk_proposal = ModificationProposal(
            proposal_id="low_risk",
            modification_type=ModificationType.PARAMETER_TUNING,
            target_components=["Component1"],
            description="Low risk modification",
            rationale="Test",
            expected_benefits={},
            potential_risks={},
            safety_risk_level=SafetyRiskLevel.LOW,
            estimated_effort=0.2
        )
        
        high_risk_proposal = ModificationProposal(
            proposal_id="high_risk",
            modification_type=ModificationType.ARCHITECTURE_CHANGE,
            target_components=["CoreSystem"],
            description="High risk modification",
            rationale="Test",
            expected_benefits={},
            potential_risks={},
            safety_risk_level=SafetyRiskLevel.HIGH,
            estimated_effort=0.8
        )
        
        # Assess risk
        low_risk_level, low_risk_details = safety_checker.assess_risk(low_risk_proposal, {})
        high_risk_level, high_risk_details = safety_checker.assess_risk(high_risk_proposal, {})
        
        # Verify risk levels
        self.assertLess(
            list(SafetyRiskLevel).index(low_risk_level),
            list(SafetyRiskLevel).index(high_risk_level)
        )
        
        # Check safety
        low_risk_safe, low_risk_reason = safety_checker.is_safe_to_apply(
            low_risk_proposal, {}, SafetyRiskLevel.MODERATE
        )
        high_risk_safe, high_risk_reason = safety_checker.is_safe_to_apply(
            high_risk_proposal, {}, SafetyRiskLevel.MODERATE
        )
        
        # Verify safety checks
        self.assertTrue(low_risk_safe)
        self.assertFalse(high_risk_safe)
    
    def test_modification_evaluator(self):
        """Test the ModificationEvaluator component."""
        # Create a mock MetaKnowledgeBase
        mock_meta_knowledge = MagicMock()
        
        # Create a real ModificationEvaluator
        evaluator = ModificationEvaluator(mock_meta_knowledge)
        
        # Create a proposal to evaluate
        proposal = ModificationProposal(
            proposal_id="test_proposal",
            modification_type=ModificationType.PARAMETER_TUNING,
            target_components=["InferenceEngine"],
            description="Tune parameters for InferenceEngine",
            rationale="Improve performance",
            expected_benefits={},
            potential_risks={},
            safety_risk_level=SafetyRiskLevel.LOW,
            estimated_effort=0.3,
            metadata={
                "parameters": [
                    ModificationParameter(
                        name="max_inference_steps",
                        current_value=1000,
                        proposed_value=2000,
                        value_type="int",
                        description="Maximum number of inference steps"
                    )
                ]
            }
        )
        
        # Create system state
        system_state = {
            "module_states": {
                "InferenceEngine": {
                    "status": "active",
                    "metrics": {
                        "average_proof_time_ms": 150.0,
                        "active_tasks": 2
                    }
                }
            }
        }
        
        # Evaluate proposal
        evaluation = evaluator.evaluate_proposal(proposal, system_state)
        
        # Verify evaluation
        self.assertIsNotNone(evaluation)
        self.assertIn("expected_benefits", evaluation)
        self.assertIn("potential_drawbacks", evaluation)
        self.assertIn("confidence", evaluation)
        self.assertIn("recommendation", evaluation)
        self.assertIn("alternatives", evaluation)


if __name__ == '__main__':
    unittest.main()