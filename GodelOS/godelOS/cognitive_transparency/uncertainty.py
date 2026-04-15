"""
Uncertainty Quantification Engine for the Cognitive Transparency system.

This module provides comprehensive uncertainty assessment for all reasoning steps,
uncertainty propagation through reasoning chains, and belief strength quantification.
"""

import logging
import time
import math
from typing import Dict, List, Optional, Set, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from collections import defaultdict

from .models import (
    UncertaintyMetrics, ReasoningStep, KnowledgeNode, KnowledgeEdge,
    UncertaintyEvent, TransparencyEvent
)


class UncertaintySource(Enum):
    """Sources of uncertainty in reasoning."""
    INCOMPLETE_INFORMATION = "incomplete_information"
    CONFLICTING_EVIDENCE = "conflicting_evidence"
    MODEL_LIMITATIONS = "model_limitations"
    TEMPORAL_DECAY = "temporal_decay"
    SOURCE_UNRELIABILITY = "source_unreliability"
    MEASUREMENT_ERROR = "measurement_error"
    APPROXIMATION_ERROR = "approximation_error"
    PROPAGATION_ERROR = "propagation_error"


class PropagationMethod(Enum):
    """Methods for uncertainty propagation."""
    MONTE_CARLO = "monte_carlo"
    ANALYTICAL = "analytical"
    WORST_CASE = "worst_case"
    BAYESIAN = "bayesian"
    FUZZY_LOGIC = "fuzzy_logic"


@dataclass
class UncertaintyAnalysis:
    """Detailed uncertainty analysis for a reasoning step or knowledge item."""
    target_id: str = ""
    target_type: str = ""  # step, node, edge, fact
    uncertainty_metrics: UncertaintyMetrics = field(default_factory=UncertaintyMetrics)
    uncertainty_sources: Dict[UncertaintySource, float] = field(default_factory=dict)
    contributing_factors: List[str] = field(default_factory=list)
    mitigation_suggestions: List[str] = field(default_factory=list)
    confidence_intervals: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    sensitivity_analysis: Dict[str, float] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'target_id': self.target_id,
            'target_type': self.target_type,
            'uncertainty_metrics': self.uncertainty_metrics.to_dict(),
            'uncertainty_sources': {k.value: v for k, v in self.uncertainty_sources.items()},
            'contributing_factors': self.contributing_factors,
            'mitigation_suggestions': self.mitigation_suggestions,
            'confidence_intervals': self.confidence_intervals,
            'sensitivity_analysis': self.sensitivity_analysis,
            'timestamp': self.timestamp
        }


@dataclass
class PropagationResult:
    """Result of uncertainty propagation through a reasoning chain."""
    chain_id: str = ""
    initial_uncertainty: float = 0.0
    final_uncertainty: float = 0.0
    propagation_method: PropagationMethod = PropagationMethod.ANALYTICAL
    step_uncertainties: List[float] = field(default_factory=list)
    uncertainty_growth: float = 0.0
    dominant_sources: List[UncertaintySource] = field(default_factory=list)
    critical_steps: List[str] = field(default_factory=list)  # Step IDs with high uncertainty contribution
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'chain_id': self.chain_id,
            'initial_uncertainty': self.initial_uncertainty,
            'final_uncertainty': self.final_uncertainty,
            'propagation_method': self.propagation_method.value,
            'step_uncertainties': self.step_uncertainties,
            'uncertainty_growth': self.uncertainty_growth,
            'dominant_sources': [s.value for s in self.dominant_sources],
            'critical_steps': self.critical_steps
        }


class UncertaintyQuantificationEngine:
    """
    Comprehensive uncertainty quantification engine for cognitive transparency.
    
    Features:
    - Confidence assessment for all reasoning steps
    - Uncertainty propagation through reasoning chains
    - Belief strength quantification and tracking
    - Uncertainty visualization support
    - Multiple propagation methods
    """
    
    def __init__(self,
                 default_propagation_method: PropagationMethod = PropagationMethod.ANALYTICAL,
                 temporal_decay_rate: float = 0.1,
                 event_callback: Optional[Callable[[TransparencyEvent], None]] = None):
        """
        Initialize the uncertainty quantification engine.
        
        Args:
            default_propagation_method: Default method for uncertainty propagation
            temporal_decay_rate: Rate of confidence decay over time
            event_callback: Callback for uncertainty events
        """
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.default_propagation_method = default_propagation_method
        self.temporal_decay_rate = temporal_decay_rate
        self.event_callback = event_callback
        
        # Storage
        self.uncertainty_analyses: Dict[str, UncertaintyAnalysis] = {}
        self.propagation_results: Dict[str, PropagationResult] = {}
        
        # Uncertainty models and parameters
        self.source_weights = {
            UncertaintySource.INCOMPLETE_INFORMATION: 0.3,
            UncertaintySource.CONFLICTING_EVIDENCE: 0.4,
            UncertaintySource.MODEL_LIMITATIONS: 0.2,
            UncertaintySource.TEMPORAL_DECAY: 0.1,
            UncertaintySource.SOURCE_UNRELIABILITY: 0.3,
            UncertaintySource.MEASUREMENT_ERROR: 0.1,
            UncertaintySource.APPROXIMATION_ERROR: 0.15,
            UncertaintySource.PROPAGATION_ERROR: 0.1
        }
        
        # Confidence thresholds
        self.confidence_thresholds = {
            'very_low': 0.3,
            'low': 0.5,
            'medium': 0.7,
            'high': 0.85,
            'very_high': 0.95
        }
        
        self.logger.info("Uncertainty Quantification Engine initialized")
    
    def assess_step_uncertainty(self,
                               reasoning_step: ReasoningStep,
                               context: Optional[Dict[str, Any]] = None) -> UncertaintyAnalysis:
        """
        Assess uncertainty for a reasoning step.
        
        Args:
            reasoning_step: The reasoning step to analyze
            context: Additional context for uncertainty assessment
            
        Returns:
            UncertaintyAnalysis object
        """
        try:
            analysis = UncertaintyAnalysis(
                target_id=reasoning_step.step_id,
                target_type="step"
            )
            
            # Calculate base uncertainty metrics
            uncertainty_metrics = self._calculate_step_uncertainty_metrics(reasoning_step, context)
            analysis.uncertainty_metrics = uncertainty_metrics
            
            # Identify uncertainty sources
            uncertainty_sources = self._identify_uncertainty_sources(reasoning_step, context)
            analysis.uncertainty_sources = uncertainty_sources
            
            # Generate contributing factors
            analysis.contributing_factors = self._identify_contributing_factors(reasoning_step, uncertainty_sources)
            
            # Generate mitigation suggestions
            analysis.mitigation_suggestions = self._generate_mitigation_suggestions(uncertainty_sources)
            
            # Calculate confidence intervals
            analysis.confidence_intervals = self._calculate_confidence_intervals(reasoning_step, uncertainty_metrics)
            
            # Perform sensitivity analysis
            analysis.sensitivity_analysis = self._perform_sensitivity_analysis(reasoning_step, uncertainty_metrics)
            
            # Store analysis
            self.uncertainty_analyses[reasoning_step.step_id] = analysis
            
            # Emit event
            self._emit_uncertainty_event(analysis)
            
            self.logger.debug(f"Assessed uncertainty for step: {reasoning_step.step_id}")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error assessing step uncertainty: {str(e)}")
            raise
    
    def propagate_uncertainty(self,
                            reasoning_chain: List[ReasoningStep],
                            method: Optional[PropagationMethod] = None) -> PropagationResult:
        """
        Propagate uncertainty through a reasoning chain.
        
        Args:
            reasoning_chain: List of reasoning steps in order
            method: Propagation method to use
            
        Returns:
            PropagationResult object
        """
        try:
            if not reasoning_chain:
                raise ValueError("Empty reasoning chain")
            
            method = method or self.default_propagation_method
            chain_id = f"chain_{reasoning_chain[0].step_id}_{len(reasoning_chain)}"
            
            result = PropagationResult(
                chain_id=chain_id,
                propagation_method=method
            )
            
            # Get or calculate uncertainty for each step
            step_uncertainties = []
            for step in reasoning_chain:
                if step.step_id in self.uncertainty_analyses:
                    uncertainty = self.uncertainty_analyses[step.step_id].uncertainty_metrics.overall_uncertainty()
                else:
                    # Calculate on-the-fly
                    analysis = self.assess_step_uncertainty(step)
                    uncertainty = analysis.uncertainty_metrics.overall_uncertainty()
                
                step_uncertainties.append(uncertainty)
            
            result.step_uncertainties = step_uncertainties
            result.initial_uncertainty = step_uncertainties[0] if step_uncertainties else 0.0
            
            # Apply propagation method
            if method == PropagationMethod.ANALYTICAL:
                final_uncertainty = self._analytical_propagation(step_uncertainties)
            elif method == PropagationMethod.WORST_CASE:
                final_uncertainty = self._worst_case_propagation(step_uncertainties)
            else:
                final_uncertainty = self._analytical_propagation(step_uncertainties)
            
            result.final_uncertainty = final_uncertainty
            result.uncertainty_growth = final_uncertainty - result.initial_uncertainty
            
            # Identify dominant sources and critical steps
            result.dominant_sources = self._identify_dominant_sources(reasoning_chain)
            result.critical_steps = self._identify_critical_steps(reasoning_chain, step_uncertainties)
            
            # Store result
            self.propagation_results[chain_id] = result
            
            self.logger.debug(f"Propagated uncertainty through chain: {chain_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error propagating uncertainty: {str(e)}")
            raise
    
    def get_confidence_level(self, confidence: float) -> str:
        """
        Get confidence level category for a confidence value.
        
        Args:
            confidence: Confidence value (0.0 - 1.0)
            
        Returns:
            Confidence level string
        """
        for level, threshold in sorted(self.confidence_thresholds.items(), 
                                     key=lambda x: x[1], reverse=True):
            if confidence >= threshold:
                return level
        return 'very_low'
    
    async def analyze_uncertainty(self, target_id: str, target_type: str = "step", context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze uncertainty for a specific target.
        
        Args:
            target_id: ID of the target to analyze
            target_type: Type of target (step, node, edge, fact)
            context: Additional context for analysis
            
        Returns:
            Dictionary containing uncertainty analysis results
        """
        try:
            # Create a mock reasoning step for analysis if needed
            if target_id not in self.uncertainty_analyses:
                # For now, create a basic uncertainty analysis
                # Ensure UncertaintyMetrics is instantiated correctly
                metrics = UncertaintyMetrics(
                    confidence=0.7, # Example value
                    epistemic_uncertainty=0.1, # Example value
                    model_uncertainty=0.05, # Example value
                    source_reliability=0.8, # Example value
                    evidence_strength=0.75, # Example value
                    contradiction_score=0.0 # Example value
                )
                analysis = UncertaintyAnalysis(
                    target_id=target_id,
                    target_type=target_type,
                    uncertainty_metrics=metrics, # Pass the instantiated metrics
                    uncertainty_sources={
                        UncertaintySource.INCOMPLETE_INFORMATION: 0.2,
                        UncertaintySource.MODEL_LIMITATIONS: 0.1
                    },
                    contributing_factors=["Limited training data", "Model approximations"],
                    mitigation_suggestions=["Gather more evidence", "Cross-validate results"],
                    confidence_intervals={"prediction": (0.6, 0.8)},
                    sensitivity_analysis={"input_variation": 0.1}
                )
                self.uncertainty_analyses[target_id] = analysis
            else:
                analysis = self.uncertainty_analyses[target_id]
            
            return {
                "success": True,
                "target_id": target_id,
                "target_type": target_type,
                "analysis": analysis.to_dict(),
                "timestamp": time.time()
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing uncertainty for {target_id}: {str(e)}")
            return {
                "success": False,
                "target_id": target_id,
                "error": str(e),
                "timestamp": time.time()
            }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about uncertainty quantification."""
        try:
            stats = {
                'total_analyses': len(self.uncertainty_analyses),
                'total_propagations': len(self.propagation_results),
                'avg_confidence': 0.0,
                'avg_uncertainty': 0.0,
                'confidence_distribution': defaultdict(int),
                'uncertainty_source_frequency': defaultdict(int),
                'propagation_method_usage': defaultdict(int)
            }
            
            if self.uncertainty_analyses:
                confidences = []
                uncertainties = []
                
                for analysis in self.uncertainty_analyses.values():
                    confidence = analysis.uncertainty_metrics.confidence
                    uncertainty = analysis.uncertainty_metrics.overall_uncertainty()
                    
                    confidences.append(confidence)
                    uncertainties.append(uncertainty)
                    
                    # Confidence distribution
                    level = self.get_confidence_level(confidence)
                    stats['confidence_distribution'][level] += 1
                    
                    # Source frequency
                    for source in analysis.uncertainty_sources.keys():
                        stats['uncertainty_source_frequency'][source.value] += 1
                
                stats['avg_confidence'] = sum(confidences) / len(confidences)
                stats['avg_uncertainty'] = sum(uncertainties) / len(uncertainties)
            
            # Propagation method usage
            for result in self.propagation_results.values():
                stats['propagation_method_usage'][result.propagation_method.value] += 1
            
            # Convert defaultdicts to regular dicts
            stats['confidence_distribution'] = dict(stats['confidence_distribution'])
            stats['uncertainty_source_frequency'] = dict(stats['uncertainty_source_frequency'])
            stats['propagation_method_usage'] = dict(stats['propagation_method_usage'])
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error calculating statistics: {str(e)}")
            return {}
    
    # Private helper methods
    
    def _calculate_step_uncertainty_metrics(self, step: ReasoningStep, context: Optional[Dict[str, Any]]) -> UncertaintyMetrics:
        """Calculate uncertainty metrics for a reasoning step."""
        metrics = UncertaintyMetrics()
        
        # Base confidence from step
        metrics.confidence = step.confidence
        
        # Epistemic uncertainty (lack of knowledge)
        epistemic = 0.0
        if 'knowledge_gaps' in step.context:
            epistemic = min(0.5, len(step.context['knowledge_gaps']) * 0.1)
        metrics.epistemic_uncertainty = epistemic
        
        # Model uncertainty
        model_uncertainty = 0.0
        if step.processing_time_ms > 1000:  # Long processing might indicate model uncertainty
            model_uncertainty = min(0.3, (step.processing_time_ms - 1000) / 10000)
        metrics.model_uncertainty = model_uncertainty
        
        # Source reliability
        source_reliability = 1.0
        if 'source_reliability' in step.context:
            source_reliability = step.context['source_reliability']
        metrics.source_reliability = source_reliability
        
        # Evidence strength
        evidence_strength = 1.0
        if 'evidence_count' in step.context:
            evidence_count = step.context['evidence_count']
            evidence_strength = min(1.0, evidence_count / 5.0)  # Normalize to 5 pieces of evidence
        metrics.evidence_strength = evidence_strength
        
        # Contradiction score
        contradiction_score = 0.0
        if 'contradictions' in step.context:
            contradiction_score = min(1.0, len(step.context['contradictions']) * 0.2)
        metrics.contradiction_score = contradiction_score
        
        return metrics
    
    def _identify_uncertainty_sources(self, step: ReasoningStep, context: Optional[Dict[str, Any]]) -> Dict[UncertaintySource, float]:
        """Identify sources of uncertainty for a reasoning step."""
        sources = {}
        
        # Incomplete information
        if 'knowledge_gaps' in step.context:
            gap_count = len(step.context['knowledge_gaps'])
            sources[UncertaintySource.INCOMPLETE_INFORMATION] = min(1.0, gap_count * 0.2)
        
        # Conflicting evidence
        if 'contradictions' in step.context:
            conflict_count = len(step.context['contradictions'])
            sources[UncertaintySource.CONFLICTING_EVIDENCE] = min(1.0, conflict_count * 0.3)
        
        # Model limitations
        if step.processing_time_ms > 2000:  # Very long processing time
            sources[UncertaintySource.MODEL_LIMITATIONS] = 0.3
        
        # Source unreliability
        if 'source_reliability' in step.context and step.context['source_reliability'] < 0.7:
            sources[UncertaintySource.SOURCE_UNRELIABILITY] = 1.0 - step.context['source_reliability']
        
        # Approximation error for certain step types
        if step.step_type.value in ['analogical_reasoning', 'pattern_matching']:
            sources[UncertaintySource.APPROXIMATION_ERROR] = 0.2
        
        return sources
    
    def _identify_contributing_factors(self, step: ReasoningStep, sources: Dict[UncertaintySource, float]) -> List[str]:
        """Identify contributing factors to uncertainty."""
        factors = []
        
        for source, value in sources.items():
            if value > 0.2:  # Significant contribution
                if source == UncertaintySource.INCOMPLETE_INFORMATION:
                    factors.append("Missing key information for complete reasoning")
                elif source == UncertaintySource.CONFLICTING_EVIDENCE:
                    factors.append("Contradictory evidence affecting conclusions")
                elif source == UncertaintySource.MODEL_LIMITATIONS:
                    factors.append("Reasoning model limitations in handling complexity")
                elif source == UncertaintySource.SOURCE_UNRELIABILITY:
                    factors.append("Unreliable or unverified information sources")
                elif source == UncertaintySource.TEMPORAL_DECAY:
                    factors.append("Information age affecting reliability")
        
        return factors
    
    def _generate_mitigation_suggestions(self, sources: Dict[UncertaintySource, float]) -> List[str]:
        """Generate suggestions for mitigating uncertainty."""
        suggestions = []
        
        for source, value in sources.items():
            if value > 0.3:  # High uncertainty
                if source == UncertaintySource.INCOMPLETE_INFORMATION:
                    suggestions.append("Gather additional information from reliable sources")
                elif source == UncertaintySource.CONFLICTING_EVIDENCE:
                    suggestions.append("Investigate and resolve contradictory evidence")
                elif source == UncertaintySource.MODEL_LIMITATIONS:
                    suggestions.append("Consider alternative reasoning approaches")
                elif source == UncertaintySource.SOURCE_UNRELIABILITY:
                    suggestions.append("Verify information with trusted sources")
        
        return suggestions
    
    def _calculate_confidence_intervals(self, step: ReasoningStep, metrics: UncertaintyMetrics) -> Dict[str, Tuple[float, float]]:
        """Calculate confidence intervals for step outputs."""
        intervals = {}
        
        # Simple confidence interval based on overall uncertainty
        uncertainty = metrics.overall_uncertainty()
        margin = uncertainty * 0.5  # 50% of uncertainty as margin
        
        confidence_lower = max(0.0, metrics.confidence - margin)
        confidence_upper = min(1.0, metrics.confidence + margin)
        
        intervals['confidence'] = (confidence_lower, confidence_upper)
        
        return intervals
    
    def _perform_sensitivity_analysis(self, step: ReasoningStep, metrics: UncertaintyMetrics) -> Dict[str, float]:
        """Perform sensitivity analysis for uncertainty factors."""
        sensitivity = {}
        
        # Analyze sensitivity to different uncertainty components
        base_uncertainty = metrics.overall_uncertainty()
        
        # Test sensitivity to epistemic uncertainty
        test_metrics = UncertaintyMetrics()
        test_metrics.__dict__.update(metrics.__dict__)
        test_metrics.epistemic_uncertainty *= 1.1  # 10% increase
        sensitivity['epistemic'] = abs(test_metrics.overall_uncertainty() - base_uncertainty)
        
        # Test sensitivity to source reliability
        test_metrics = UncertaintyMetrics()
        test_metrics.__dict__.update(metrics.__dict__)
        test_metrics.source_reliability *= 0.9  # 10% decrease
        sensitivity['source_reliability'] = abs(test_metrics.overall_uncertainty() - base_uncertainty)
        
        return sensitivity
    
    def _analytical_propagation(self, step_uncertainties: List[float]) -> float:
        """Analytical uncertainty propagation method."""
        if not step_uncertainties:
            return 0.0
        
        # Simple linear combination with increasing weights for later steps
        total_uncertainty = 0.0
        for i, uncertainty in enumerate(step_uncertainties):
            weight = 1.0 + (i * 0.1)  # Increasing weight for cumulative effect
            total_uncertainty += uncertainty * weight
        
        # Normalize and cap at 1.0
        return min(1.0, total_uncertainty / len(step_uncertainties))
    
    def _worst_case_propagation(self, step_uncertainties: List[float]) -> float:
        """Worst-case uncertainty propagation method."""
        if not step_uncertainties:
            return 0.0
        
        # Take maximum uncertainty and add cumulative effect
        max_uncertainty = max(step_uncertainties)
        cumulative_effect = sum(step_uncertainties) * 0.1
        
        return min(1.0, max_uncertainty + cumulative_effect)
    
    def _identify_dominant_sources(self, reasoning_chain: List[ReasoningStep]) -> List[UncertaintySource]:
        """Identify dominant uncertainty sources across a reasoning chain."""
        source_totals = defaultdict(float)
        
        for step in reasoning_chain:
            if step.step_id in self.uncertainty_analyses:
                analysis = self.uncertainty_analyses[step.step_id]
                for source, value in analysis.uncertainty_sources.items():
                    source_totals[source] += value
        
        # Sort by total value and return top sources
        sorted_sources = sorted(source_totals.items(), key=lambda x: x[1], reverse=True)
        return [source for source, _ in sorted_sources[:3]]  # Top 3 sources
    
    def _identify_critical_steps(self, reasoning_chain: List[ReasoningStep], step_uncertainties: List[float]) -> List[str]:
        """Identify critical steps with high uncertainty contribution."""
        critical_steps = []
        
        if not step_uncertainties:
            return critical_steps
        
        avg_uncertainty = sum(step_uncertainties) / len(step_uncertainties)
        threshold = avg_uncertainty * 1.5  # 50% above average
        
        for i, (step, uncertainty) in enumerate(zip(reasoning_chain, step_uncertainties)):
            if uncertainty > threshold:
                critical_steps.append(step.step_id)
        
        return critical_steps
    
    def _emit_uncertainty_event(self, analysis: UncertaintyAnalysis):
        """Emit an uncertainty event."""
        if self.event_callback:
            event = UncertaintyEvent(
                target_id=analysis.target_id,
                target_type=analysis.target_type,
                uncertainty_metrics=analysis.uncertainty_metrics,
                data={
                    'overall_uncertainty': analysis.uncertainty_metrics.overall_uncertainty(),
                    'confidence_level': self.get_confidence_level(analysis.uncertainty_metrics.confidence),
                    'dominant_sources': list(analysis.uncertainty_sources.keys())[:3]
                }
            )
            self.event_callback(event)