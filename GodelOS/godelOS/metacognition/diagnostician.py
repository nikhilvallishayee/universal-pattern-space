"""
Cognitive Diagnostician (CD) for GödelOS.

This module implements the CognitiveDiagnostician component (Module 7.3) of the Metacognition & 
Self-Improvement System, which is responsible for analyzing monitoring data to diagnose
cognitive issues and identify potential improvements.

The CognitiveDiagnostician:
1. Analyzes monitoring data to diagnose cognitive issues
2. Identifies performance bottlenecks
3. Detects reasoning failures and their causes
4. Generates diagnostic reports
5. Recommends potential improvements
"""

import logging
import time
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Callable
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import statistics

from godelOS.metacognition.self_monitoring import (
    SelfMonitoringModule,
    PerformanceAnomaly,
    AnomalyType,
    ReasoningEvent
)
from godelOS.metacognition.meta_knowledge import (
    MetaKnowledgeBase,
    MetaKnowledgeType,
    ComponentPerformanceModel,
    ReasoningStrategyModel,
    ResourceUsagePattern,
    FailurePattern,
    OptimizationHint
)

logger = logging.getLogger(__name__)


class DiagnosisType(Enum):
    """Enum representing types of cognitive diagnoses."""
    PERFORMANCE_BOTTLENECK = "performance_bottleneck"
    REASONING_FAILURE = "reasoning_failure"
    RESOURCE_CONTENTION = "resource_contention"
    PATTERN_MISMATCH = "pattern_mismatch"
    STRATEGY_INEFFECTIVENESS = "strategy_ineffectiveness"
    KNOWLEDGE_GAP = "knowledge_gap"
    ARCHITECTURAL_LIMITATION = "architectural_limitation"


class SeverityLevel(Enum):
    """Enum representing severity levels of diagnoses."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class DiagnosticFinding:
    """Represents a diagnostic finding from the cognitive diagnostician."""
    finding_id: str
    diagnosis_type: DiagnosisType
    severity: SeverityLevel
    affected_components: List[str]
    description: str
    evidence: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    recommendations: List[str] = field(default_factory=list)
    confidence: float = 1.0  # 0.0 to 1.0


@dataclass
class DiagnosticReport:
    """Represents a comprehensive diagnostic report."""
    report_id: str
    findings: List[DiagnosticFinding]
    summary: str
    system_state: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


class DiagnosticRule:
    """Base class for diagnostic rules."""
    
    def __init__(self, rule_id: str, description: str):
        """Initialize a diagnostic rule."""
        self.rule_id = rule_id
        self.description = description
    
    def evaluate(
        self,
        monitoring_data: Dict[str, Any],
        meta_knowledge: Dict[str, Any]
    ) -> Optional[DiagnosticFinding]:
        """
        Evaluate the rule against monitoring data and meta-knowledge.
        
        Args:
            monitoring_data: Monitoring data from the self-monitoring module
            meta_knowledge: Meta-knowledge from the meta-knowledge base
            
        Returns:
            A DiagnosticFinding if the rule matches, None otherwise
        """
        raise NotImplementedError("Subclasses must implement evaluate()")


class PerformanceBottleneckRule(DiagnosticRule):
    """Rule for detecting performance bottlenecks."""
    
    def __init__(
        self,
        rule_id: str,
        component_id: str,
        metric_threshold: Dict[str, float],
        severity_mapping: Dict[str, SeverityLevel]
    ):
        """Initialize a performance bottleneck rule."""
        super().__init__(rule_id, f"Performance bottleneck in {component_id}")
        self.component_id = component_id
        self.metric_threshold = metric_threshold
        self.severity_mapping = severity_mapping
    
    def evaluate(
        self,
        monitoring_data: Dict[str, Any],
        meta_knowledge: Dict[str, Any]
    ) -> Optional[DiagnosticFinding]:
        """Evaluate the performance bottleneck rule."""
        # Get component metrics from monitoring data
        module_states = monitoring_data.get("module_states", {})
        component_metrics = module_states.get(self.component_id, {}).get("metrics", {})
        
        if not component_metrics:
            return None
        
        # Check for bottlenecks
        bottleneck_metrics = {}
        for metric_name, threshold in self.metric_threshold.items():
            if metric_name in component_metrics:
                metric_value = component_metrics[metric_name]
                if metric_value > threshold:
                    bottleneck_metrics[metric_name] = {
                        "value": metric_value,
                        "threshold": threshold,
                        "ratio": metric_value / threshold
                    }
        
        if not bottleneck_metrics:
            return None
        
        # Determine severity based on the worst metric
        worst_metric = max(bottleneck_metrics.items(), key=lambda x: x[1]["ratio"])
        worst_ratio = worst_metric[1]["ratio"]
        
        severity = SeverityLevel.LOW
        for ratio_threshold, level in sorted(self.severity_mapping.items(), key=lambda x: float(x[0])):
            if worst_ratio >= float(ratio_threshold):
                severity = level
        
        # Create a diagnostic finding
        finding_id = f"bottleneck_{self.component_id}_{int(time.time())}"
        description = f"Performance bottleneck detected in {self.component_id}: "
        description += ", ".join([f"{name}={metrics['value']} (threshold: {metrics['threshold']})" 
                                 for name, metrics in bottleneck_metrics.items()])
        
        recommendations = [
            f"Optimize {self.component_id} implementation for better performance",
            f"Reduce load on {self.component_id} by distributing work",
            f"Allocate more resources to {self.component_id}"
        ]
        
        return DiagnosticFinding(
            finding_id=finding_id,
            diagnosis_type=DiagnosisType.PERFORMANCE_BOTTLENECK,
            severity=severity,
            affected_components=[self.component_id],
            description=description,
            evidence={"bottleneck_metrics": bottleneck_metrics, "component_metrics": component_metrics},
            recommendations=recommendations
        )


class ReasoningFailureRule(DiagnosticRule):
    """Rule for detecting reasoning failures."""
    
    def __init__(
        self,
        rule_id: str,
        strategy_name: str,
        failure_rate_threshold: float,
        min_sample_size: int,
        severity_mapping: Dict[str, SeverityLevel]
    ):
        """Initialize a reasoning failure rule."""
        super().__init__(rule_id, f"Reasoning failure in strategy {strategy_name}")
        self.strategy_name = strategy_name
        self.failure_rate_threshold = failure_rate_threshold
        self.min_sample_size = min_sample_size
        self.severity_mapping = severity_mapping
    
    def evaluate(
        self,
        monitoring_data: Dict[str, Any],
        meta_knowledge: Dict[str, Any]
    ) -> Optional[DiagnosticFinding]:
        """Evaluate the reasoning failure rule."""
        # Get strategy metrics from monitoring data
        reasoning_strategies = monitoring_data.get("reasoning_strategies", {})
        strategy_metrics = reasoning_strategies.get(self.strategy_name, {})
        
        if not strategy_metrics:
            return None
        
        # Check for failure rate
        success_rate = strategy_metrics.get("success_rate", 1.0)
        failure_rate = 1.0 - success_rate
        total_executions = strategy_metrics.get("total_executions", 0)
        
        if total_executions < self.min_sample_size or failure_rate < self.failure_rate_threshold:
            return None
        
        # Determine severity based on failure rate
        severity = SeverityLevel.LOW
        for rate_threshold, level in sorted(self.severity_mapping.items(), key=lambda x: float(x[0])):
            if failure_rate >= float(rate_threshold):
                severity = level
        
        # Get strategy model from meta-knowledge
        strategy_model = None
        for model in meta_knowledge.get("reasoning_strategies", []):
            if model.get("strategy_name") == self.strategy_name:
                strategy_model = model
                break
        
        # Create a diagnostic finding
        finding_id = f"reasoning_failure_{self.strategy_name}_{int(time.time())}"
        description = f"Reasoning failure detected in strategy {self.strategy_name}: "
        description += f"failure rate {failure_rate:.2f} exceeds threshold {self.failure_rate_threshold:.2f}"
        
        recommendations = [
            f"Review and improve the implementation of {self.strategy_name}",
            f"Limit the use of {self.strategy_name} to problems where it performs well",
            "Develop alternative reasoning strategies for problematic cases"
        ]
        
        if strategy_model:
            applicable_problems = strategy_model.get("applicable_problem_types", [])
            if applicable_problems:
                recommendations.append(
                    f"Ensure {self.strategy_name} is only used for appropriate problem types: {', '.join(applicable_problems)}"
                )
        
        return DiagnosticFinding(
            finding_id=finding_id,
            diagnosis_type=DiagnosisType.REASONING_FAILURE,
            severity=severity,
            affected_components=[f"ReasoningStrategy:{self.strategy_name}"],
            description=description,
            evidence={
                "failure_rate": failure_rate,
                "threshold": self.failure_rate_threshold,
                "total_executions": total_executions,
                "strategy_metrics": strategy_metrics,
                "strategy_model": strategy_model
            },
            recommendations=recommendations
        )


class ResourceContentionRule(DiagnosticRule):
    """Rule for detecting resource contention."""
    
    def __init__(
        self,
        rule_id: str,
        resource_name: str,
        usage_threshold: float,
        severity_mapping: Dict[str, SeverityLevel]
    ):
        """Initialize a resource contention rule."""
        super().__init__(rule_id, f"Resource contention for {resource_name}")
        self.resource_name = resource_name
        self.usage_threshold = usage_threshold
        self.severity_mapping = severity_mapping
    
    def evaluate(
        self,
        monitoring_data: Dict[str, Any],
        meta_knowledge: Dict[str, Any]
    ) -> Optional[DiagnosticFinding]:
        """Evaluate the resource contention rule."""
        # Get resource metrics from monitoring data
        system_resources = monitoring_data.get("system_resources", {})
        resource_metrics = system_resources.get(self.resource_name, {})
        
        if not resource_metrics:
            return None
        
        # Check for resource contention
        usage = resource_metrics.get("value", 0.0)
        
        if usage < self.usage_threshold:
            return None
        
        # Determine severity based on usage
        severity = SeverityLevel.LOW
        for usage_threshold, level in sorted(self.severity_mapping.items(), key=lambda x: float(x[0])):
            if usage >= float(usage_threshold):
                severity = level
        
        # Get active components from monitoring data
        active_components = []
        for component_id, state in monitoring_data.get("module_states", {}).items():
            if state.get("status") in ["active", "busy"]:
                active_components.append(component_id)
        
        # Create a diagnostic finding
        finding_id = f"resource_contention_{self.resource_name}_{int(time.time())}"
        description = f"Resource contention detected for {self.resource_name}: "
        description += f"usage {usage:.2f}% exceeds threshold {self.usage_threshold:.2f}%"
        
        recommendations = [
            f"Optimize resource usage for {self.resource_name}",
            "Implement resource scheduling to prevent contention",
            "Consider scaling up the resource if possible"
        ]
        
        if active_components:
            recommendations.append(
                f"Investigate resource usage of active components: {', '.join(active_components)}"
            )
        
        return DiagnosticFinding(
            finding_id=finding_id,
            diagnosis_type=DiagnosisType.RESOURCE_CONTENTION,
            severity=severity,
            affected_components=active_components or [f"Resource:{self.resource_name}"],
            description=description,
            evidence={
                "resource_usage": usage,
                "threshold": self.usage_threshold,
                "resource_metrics": resource_metrics,
                "active_components": active_components
            },
            recommendations=recommendations
        )


class CognitiveDiagnostician:
    """
    Cognitive Diagnostician (CD) for GödelOS.
    
    The CognitiveDiagnostician analyzes monitoring data to diagnose cognitive issues,
    identify performance bottlenecks, detect reasoning failures, and recommend improvements.
    """
    
    def __init__(
        self,
        self_monitoring_module: SelfMonitoringModule,
        meta_knowledge_base: MetaKnowledgeBase,
        diagnostic_rules: Optional[List[DiagnosticRule]] = None
    ):
        """Initialize the cognitive diagnostician."""
        self.self_monitoring = self_monitoring_module
        self.meta_knowledge = meta_knowledge_base
        self.diagnostic_rules = diagnostic_rules or []
        
        # Initialize default rules if none provided
        if not diagnostic_rules:
            self._initialize_default_rules()
        
        # Cache for recent findings to avoid duplicates
        self.recent_findings = {}
        
        # History of diagnostic reports
        self.report_history = []
    
    def _initialize_default_rules(self) -> None:
        """Initialize default diagnostic rules."""
        # Performance bottleneck rules
        self.diagnostic_rules.extend([
            PerformanceBottleneckRule(
                rule_id="bottleneck_inference_engine",
                component_id="InferenceEngine",
                metric_threshold={
                    "average_proof_time_ms": 1000.0,
                    "inference_queue_length": 10
                },
                severity_mapping={
                    "1.5": SeverityLevel.LOW,
                    "2.0": SeverityLevel.MEDIUM,
                    "3.0": SeverityLevel.HIGH,
                    "5.0": SeverityLevel.CRITICAL
                }
            ),
            PerformanceBottleneckRule(
                rule_id="bottleneck_kr_system",
                component_id="KRSystem",
                metric_threshold={
                    "query_rate_per_second": 100.0,
                    "statement_count": 10000
                },
                severity_mapping={
                    "1.5": SeverityLevel.LOW,
                    "2.0": SeverityLevel.MEDIUM,
                    "3.0": SeverityLevel.HIGH,
                    "5.0": SeverityLevel.CRITICAL
                }
            )
        ])
        
        # Reasoning failure rules
        self.diagnostic_rules.extend([
            ReasoningFailureRule(
                rule_id="failure_resolution_prover",
                strategy_name="ResolutionProver",
                failure_rate_threshold=0.3,
                min_sample_size=10,
                severity_mapping={
                    "0.3": SeverityLevel.LOW,
                    "0.5": SeverityLevel.MEDIUM,
                    "0.7": SeverityLevel.HIGH,
                    "0.9": SeverityLevel.CRITICAL
                }
            ),
            ReasoningFailureRule(
                rule_id="failure_analogical_reasoning",
                strategy_name="AnalogicalReasoning",
                failure_rate_threshold=0.4,
                min_sample_size=5,
                severity_mapping={
                    "0.4": SeverityLevel.LOW,
                    "0.6": SeverityLevel.MEDIUM,
                    "0.8": SeverityLevel.HIGH,
                    "0.95": SeverityLevel.CRITICAL
                }
            )
        ])
        
        # Resource contention rules
        self.diagnostic_rules.extend([
            ResourceContentionRule(
                rule_id="contention_cpu",
                resource_name="CPU",
                usage_threshold=80.0,
                severity_mapping={
                    "80.0": SeverityLevel.LOW,
                    "90.0": SeverityLevel.MEDIUM,
                    "95.0": SeverityLevel.HIGH,
                    "98.0": SeverityLevel.CRITICAL
                }
            ),
            ResourceContentionRule(
                rule_id="contention_memory",
                resource_name="Memory",
                usage_threshold=75.0,
                severity_mapping={
                    "75.0": SeverityLevel.LOW,
                    "85.0": SeverityLevel.MEDIUM,
                    "92.0": SeverityLevel.HIGH,
                    "97.0": SeverityLevel.CRITICAL
                }
            )
        ])
    
    def add_diagnostic_rule(self, rule: DiagnosticRule) -> None:
        """Add a diagnostic rule to the diagnostician."""
        self.diagnostic_rules.append(rule)
    
    def remove_diagnostic_rule(self, rule_id: str) -> bool:
        """
        Remove a diagnostic rule by ID.
        
        Returns:
            True if the rule was found and removed, False otherwise
        """
        for i, rule in enumerate(self.diagnostic_rules):
            if rule.rule_id == rule_id:
                del self.diagnostic_rules[i]
                return True
        
        return False
    
    def diagnose(self) -> List[DiagnosticFinding]:
        """
        Perform a diagnostic analysis of the system.
        
        Returns:
            List of diagnostic findings
        """
        # Get monitoring data
        monitoring_data = self.self_monitoring.get_performance_metrics()
        
        # Get meta-knowledge
        meta_knowledge = self._prepare_meta_knowledge()
        
        # Apply diagnostic rules
        findings = []
        
        for rule in self.diagnostic_rules:
            try:
                finding = rule.evaluate(monitoring_data, meta_knowledge)
                if finding:
                    # Check if this is a duplicate of a recent finding
                    if not self._is_duplicate_finding(finding):
                        findings.append(finding)
                        self._cache_finding(finding)
            except Exception as e:
                logger.error(f"Error evaluating diagnostic rule {rule.rule_id}: {e}")
        
        return findings
    
    def generate_report(self, findings: Optional[List[DiagnosticFinding]] = None) -> DiagnosticReport:
        """
        Generate a comprehensive diagnostic report.
        
        Args:
            findings: Optional list of findings to include in the report.
                     If None, a new diagnosis will be performed.
        
        Returns:
            A DiagnosticReport object
        """
        if findings is None:
            findings = self.diagnose()
        
        # Get system state
        system_state = {
            "monitoring_data": self.self_monitoring.get_performance_metrics(),
            "recent_anomalies": [a.__dict__ for a in self.self_monitoring.get_recent_anomalies(10)],
            "timestamp": time.time()
        }
        
        # Generate summary
        summary = self._generate_report_summary(findings)
        
        # Create report
        report_id = f"diagnostic_report_{int(time.time())}"
        report = DiagnosticReport(
            report_id=report_id,
            findings=findings,
            summary=summary,
            system_state=system_state
        )
        
        # Add to history
        self.report_history.append(report)
        
        return report
    
    def get_recent_reports(self, limit: int = 10) -> List[DiagnosticReport]:
        """
        Get recent diagnostic reports.
        
        Args:
            limit: Maximum number of reports to return
            
        Returns:
            List of recent DiagnosticReport objects
        """
        return sorted(self.report_history, key=lambda r: r.timestamp, reverse=True)[:limit]
    
    def get_findings_by_component(self, component_id: str) -> List[DiagnosticFinding]:
        """
        Get all findings related to a specific component.
        
        Args:
            component_id: ID of the component
            
        Returns:
            List of DiagnosticFinding objects for the component
        """
        findings = []
        
        for report in self.report_history:
            for finding in report.findings:
                if component_id in finding.affected_components:
                    findings.append(finding)
        
        return findings
    
    def get_findings_by_type(self, diagnosis_type: DiagnosisType) -> List[DiagnosticFinding]:
        """
        Get all findings of a specific type.
        
        Args:
            diagnosis_type: Type of diagnosis
            
        Returns:
            List of DiagnosticFinding objects of the specified type
        """
        findings = []
        
        for report in self.report_history:
            for finding in report.findings:
                if finding.diagnosis_type == diagnosis_type:
                    findings.append(finding)
        
        return findings
    
    def _prepare_meta_knowledge(self) -> Dict[str, Any]:
        """
        Prepare meta-knowledge for diagnostic rules.
        
        Returns:
            Dictionary of meta-knowledge
        """
        meta_knowledge = {
            "component_performance": [],
            "reasoning_strategies": [],
            "resource_usage": [],
            "failure_patterns": [],
            "optimization_hints": []
        }
        
        # Get component performance models
        for model in self.meta_knowledge.get_entries_by_type(
            MetaKnowledgeType.COMPONENT_PERFORMANCE
        ):
            if isinstance(model, ComponentPerformanceModel):
                meta_knowledge["component_performance"].append({
                    "component_id": model.component_id,
                    "average_response_time_ms": model.average_response_time_ms,
                    "throughput_per_second": model.throughput_per_second,
                    "failure_rate": model.failure_rate,
                    "resource_usage": model.resource_usage,
                    "performance_factors": model.performance_factors
                })
        
        # Get reasoning strategy models
        for model in self.meta_knowledge.get_entries_by_type(
            MetaKnowledgeType.REASONING_STRATEGY
        ):
            if isinstance(model, ReasoningStrategyModel):
                meta_knowledge["reasoning_strategies"].append({
                    "strategy_name": model.strategy_name,
                    "success_rate": model.success_rate,
                    "average_duration_ms": model.average_duration_ms,
                    "applicable_problem_types": model.applicable_problem_types,
                    "preconditions": model.preconditions,
                    "resource_requirements": model.resource_requirements,
                    "effectiveness_by_domain": model.effectiveness_by_domain
                })
        
        # Get resource usage patterns
        for pattern in self.meta_knowledge.get_entries_by_type(
            MetaKnowledgeType.RESOURCE_USAGE
        ):
            if isinstance(pattern, ResourceUsagePattern):
                meta_knowledge["resource_usage"].append({
                    "resource_name": pattern.resource_name,
                    "average_usage": pattern.average_usage,
                    "peak_usage": pattern.peak_usage,
                    "usage_trend": pattern.usage_trend,
                    "periodic_patterns": pattern.periodic_patterns,
                    "correlations": pattern.correlations
                })
        
        # Get failure patterns
        for pattern in self.meta_knowledge.get_entries_by_type(
            MetaKnowledgeType.FAILURE_PATTERN
        ):
            if isinstance(pattern, FailurePattern):
                meta_knowledge["failure_patterns"].append({
                    "pattern_name": pattern.pattern_name,
                    "affected_components": pattern.affected_components,
                    "symptoms": pattern.symptoms,
                    "root_causes": pattern.root_causes,
                    "frequency": pattern.frequency,
                    "severity": pattern.severity,
                    "mitigation_strategies": pattern.mitigation_strategies
                })
        
        # Get optimization hints
        for hint in self.meta_knowledge.get_entries_by_type(
            MetaKnowledgeType.OPTIMIZATION_HINT
        ):
            if isinstance(hint, OptimizationHint):
                meta_knowledge["optimization_hints"].append({
                    "target_component": hint.target_component,
                    "optimization_type": hint.optimization_type,
                    "expected_improvement": hint.expected_improvement,
                    "implementation_difficulty": hint.implementation_difficulty,
                    "preconditions": hint.preconditions,
                    "side_effects": hint.side_effects
                })
        
        return meta_knowledge
    
    def _is_duplicate_finding(self, finding: DiagnosticFinding) -> bool:
        """
        Check if a finding is a duplicate of a recent finding.
        
        Args:
            finding: The finding to check
            
        Returns:
            True if the finding is a duplicate, False otherwise
        """
        # Check if we have a recent finding of the same type for the same components
        key = (finding.diagnosis_type, tuple(sorted(finding.affected_components)))
        
        if key in self.recent_findings:
            recent_finding = self.recent_findings[key]
            
            # If the finding is less than 10 minutes old, consider it a duplicate
            age = time.time() - recent_finding.timestamp
            if age < 600:  # 10 minutes in seconds
                return True
        
        return False
    
    def _cache_finding(self, finding: DiagnosticFinding) -> None:
        """
        Cache a finding to avoid duplicates.
        
        Args:
            finding: The finding to cache
        """
        key = (finding.diagnosis_type, tuple(sorted(finding.affected_components)))
        self.recent_findings[key] = finding
    
    def _generate_report_summary(self, findings: List[DiagnosticFinding]) -> str:
        """
        Generate a summary for a diagnostic report.
        
        Args:
            findings: List of findings in the report
            
        Returns:
            A summary string
        """
        if not findings:
            return "No cognitive issues detected. All systems operating within normal parameters."
        
        # Count findings by severity
        severity_counts = {level: 0 for level in SeverityLevel}
        for finding in findings:
            severity_counts[finding.severity] += 1
        
        # Count findings by type
        type_counts = {}
        for finding in findings:
            type_name = finding.diagnosis_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        
        # Generate summary
        summary = f"Diagnostic report generated at {datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')}.\n\n"
        
        summary += "Summary of findings:\n"
        summary += f"- Total issues detected: {len(findings)}\n"
        
        for level in [SeverityLevel.CRITICAL, SeverityLevel.HIGH, SeverityLevel.MEDIUM, SeverityLevel.LOW]:
            if severity_counts[level] > 0:
                summary += f"- {level.value.title()} severity issues: {severity_counts[level]}\n"
        
        summary += "\nIssues by type:\n"
        for type_name, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            summary += f"- {type_name.replace('_', ' ').title()}: {count}\n"
        
        # Add critical and high severity findings to the summary
        critical_high_findings = [f for f in findings if f.severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH]]
        if critical_high_findings:
            summary += "\nCritical and high severity issues:\n"
            for i, finding in enumerate(critical_high_findings):
                summary += f"{i+1}. {finding.description}\n"
        
        return summary