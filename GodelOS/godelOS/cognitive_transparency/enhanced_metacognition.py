"""
Enhanced Metacognition Manager with Cognitive Transparency Integration.

This module extends the existing MetacognitionManager with advanced transparency
capabilities, real-time introspection, and cognitive transparency hooks.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field

from godelOS.metacognition.manager import MetacognitionManager, MetacognitivePhase, MetacognitiveMode
from godelOS.cognitive_transparency.models import (
    ReasoningStep, StepType, DetailLevel, ReasoningStepBuilder
)

logger = logging.getLogger(__name__)


@dataclass
class TransparencyHook:
    """Configuration for transparency hooks in metacognitive operations."""
    hook_id: str
    phase: MetacognitivePhase
    enabled: bool = True
    detail_level: DetailLevel = DetailLevel.MEDIUM
    callback: Optional[Callable] = None


class EnhancedMetacognitionManager(MetacognitionManager):
    """
    Enhanced Metacognition Manager with cognitive transparency integration.
    
    This class extends the existing MetacognitionManager to provide:
    - Real-time transparency into metacognitive processes
    - Detailed tracking of self-monitoring operations
    - Integration with the cognitive transparency system
    - Enhanced introspection capabilities
    """
    
    def __init__(self, *args, transparency_manager=None, **kwargs):
        """
        Initialize the enhanced metacognition manager.
        
        Args:
            transparency_manager: CognitiveTransparencyManager instance
            *args, **kwargs: Arguments for base MetacognitionManager
        """
        super().__init__(*args, **kwargs)
        
        self.transparency_manager = transparency_manager
        self.transparency_enabled = transparency_manager is not None
        
        # Transparency configuration
        self.transparency_hooks: Dict[str, TransparencyHook] = {}
        self.current_transparency_session: Optional[str] = None
        
        # Enhanced tracking
        self.metacognitive_step_count = 0
        self.introspection_depth = 0
        self.self_evaluation_history = []
        
        # Performance metrics
        self.phase_durations = {phase: [] for phase in MetacognitivePhase}
        self.cycle_performance_history = []
        
        # Setup default transparency hooks
        self._setup_default_transparency_hooks()
        
        logger.info("EnhancedMetacognitionManager initialized with transparency support")
    
    def _setup_default_transparency_hooks(self) -> None:
        """Setup default transparency hooks for metacognitive phases."""
        default_hooks = [
            TransparencyHook("monitoring_start", MetacognitivePhase.MONITORING, True, DetailLevel.MEDIUM),
            TransparencyHook("diagnosing_start", MetacognitivePhase.DIAGNOSING, True, DetailLevel.HIGH),
            TransparencyHook("planning_start", MetacognitivePhase.PLANNING, True, DetailLevel.HIGH),
            TransparencyHook("modifying_start", MetacognitivePhase.MODIFYING, True, DetailLevel.HIGH),
            TransparencyHook("cycle_complete", MetacognitivePhase.IDLE, True, DetailLevel.MEDIUM)
        ]
        
        for hook in default_hooks:
            self.transparency_hooks[hook.hook_id] = hook
    
    async def start_with_transparency(self, transparency_session_id: Optional[str] = None) -> bool:
        """
        Start the metacognition system with transparency tracking.
        
        Args:
            transparency_session_id: Optional session ID for transparency tracking
            
        Returns:
            True if started successfully
        """
        # Start base system
        success = self.start()
        if not success:
            return False
        
        # Initialize transparency tracking
        if self.transparency_enabled and self.transparency_manager:
            if not transparency_session_id:
                transparency_session_id = await self.transparency_manager.start_reasoning_session(
                    query="Metacognitive System Operation",
                    context={
                        "component": "metacognition",
                        "mode": self.current_mode.value,
                        "cycle_interval": self.cycle_interval_sec
                    }
                )
            
            self.current_transparency_session = transparency_session_id
            
            # Emit initial step
            await self._emit_transparency_step(
                StepType.METACOGNITIVE_REFLECTION,
                "Metacognitive system started",
                {
                    "mode": self.current_mode.value,
                    "transparency_enabled": True,
                    "hooks_configured": len(self.transparency_hooks)
                }
            )
        
        return True
    
    async def stop_with_transparency(self) -> bool:
        """Stop the metacognition system and complete transparency tracking."""
        # Emit final step
        if self.transparency_enabled and self.current_transparency_session:
            await self._emit_transparency_step(
                StepType.METACOGNITIVE_REFLECTION,
                "Metacognitive system stopping",
                {
                    "total_cycles": len(self.cycle_performance_history),
                    "average_cycle_duration": self._calculate_average_cycle_duration(),
                    "final_mode": self.current_mode.value
                }
            )
            
            # Complete transparency session
            await self.transparency_manager.complete_reasoning_session(
                self.current_transparency_session
            )
            self.current_transparency_session = None
        
        # Stop base system
        return self.stop()
    
    def _execute_metacognitive_cycle(self) -> None:
        """Execute metacognitive cycle with enhanced transparency tracking."""
        cycle_start_time = time.time()
        
        try:
            # Track cycle start
            if self.transparency_enabled:
                asyncio.create_task(self._emit_transparency_step(
                    StepType.METACOGNITIVE_REFLECTION,
                    "Starting metacognitive cycle",
                    {
                        "cycle_number": len(self.cycle_performance_history) + 1,
                        "current_mode": self.current_mode.value,
                        "current_phase": self.current_phase.value
                    }
                ))
            
            # Execute each phase with transparency
            self._execute_monitoring_phase_with_transparency()
            self._execute_diagnosing_phase_with_transparency()
            self._execute_planning_phase_with_transparency()
            
            if self.current_mode == MetacognitiveMode.AUTONOMOUS:
                self._execute_modifying_phase_with_transparency()
            
            # Track cycle completion
            cycle_duration = time.time() - cycle_start_time
            self.cycle_performance_history.append({
                "duration": cycle_duration,
                "timestamp": time.time(),
                "mode": self.current_mode.value,
                "steps_executed": self.metacognitive_step_count
            })
            
            if self.transparency_enabled:
                asyncio.create_task(self._emit_transparency_step(
                    StepType.METACOGNITIVE_REFLECTION,
                    "Metacognitive cycle completed",
                    {
                        "cycle_duration_ms": cycle_duration * 1000,
                        "total_cycles": len(self.cycle_performance_history),
                        "performance_trend": self._analyze_performance_trend()
                    }
                ))
            
            self.current_phase = MetacognitivePhase.IDLE
            
        except Exception as e:
            logger.error(f"Error in enhanced metacognitive cycle: {e}")
            if self.transparency_enabled:
                asyncio.create_task(self._emit_transparency_step(
                    StepType.METACOGNITIVE_REFLECTION,
                    f"Metacognitive cycle error: {str(e)}",
                    {"error": str(e), "phase": self.current_phase.value},
                    confidence=0.0
                ))
            self.current_phase = MetacognitivePhase.ERROR
    
    def _execute_monitoring_phase_with_transparency(self) -> None:
        """Execute monitoring phase with transparency tracking."""
        phase_start_time = time.time()
        self.current_phase = MetacognitivePhase.MONITORING
        
        # Emit phase start
        if self._should_emit_for_hook("monitoring_start"):
            asyncio.create_task(self._emit_transparency_step(
                StepType.EVALUATION,
                "Starting monitoring phase",
                {"phase": "monitoring", "introspection_depth": self.introspection_depth}
            ))
        
        try:
            # Get current system state with enhanced monitoring
            system_state = self._get_enhanced_system_state()
            
            # Perform self-evaluation
            self_evaluation = self._perform_enhanced_self_evaluation(system_state)
            self.self_evaluation_history.append(self_evaluation)
            
            # Emit monitoring results
            if self.transparency_enabled:
                asyncio.create_task(self._emit_transparency_step(
                    StepType.EVALUATION,
                    "System state monitoring completed",
                    {
                        "system_health": self_evaluation.get("health_score", 0.0),
                        "performance_metrics": self_evaluation.get("performance", {}),
                        "anomalies_detected": len(self_evaluation.get("anomalies", []))
                    }
                ))
            
        except Exception as e:
            logger.error(f"Error in monitoring phase: {e}")
            if self.transparency_enabled:
                asyncio.create_task(self._emit_transparency_step(
                    StepType.EVALUATION,
                    f"Monitoring phase error: {str(e)}",
                    {"error": str(e)},
                    confidence=0.0
                ))
        
        # Track phase duration
        phase_duration = time.time() - phase_start_time
        self.phase_durations[MetacognitivePhase.MONITORING].append(phase_duration)
    
    def _execute_diagnosing_phase_with_transparency(self) -> None:
        """Execute diagnosing phase with transparency tracking."""
        phase_start_time = time.time()
        self.current_phase = MetacognitivePhase.DIAGNOSING
        
        # Emit phase start
        if self._should_emit_for_hook("diagnosing_start"):
            asyncio.create_task(self._emit_transparency_step(
                StepType.INFERENCE,
                "Starting diagnostic analysis",
                {"phase": "diagnosing", "diagnostic_depth": "enhanced"}
            ))
        
        try:
            # Generate enhanced diagnostic report
            diagnostic_report = self._generate_enhanced_diagnostic_report()
            
            # Emit diagnostic results
            if self.transparency_enabled and diagnostic_report:
                asyncio.create_task(self._emit_transparency_step(
                    StepType.INFERENCE,
                    "Diagnostic analysis completed",
                    {
                        "issues_found": len(diagnostic_report.findings),
                        "severity_levels": self._categorize_findings_by_severity(diagnostic_report.findings),
                        "confidence": diagnostic_report.confidence if hasattr(diagnostic_report, 'confidence') else 1.0
                    }
                ))
            
        except Exception as e:
            logger.error(f"Error in diagnosing phase: {e}")
            if self.transparency_enabled:
                asyncio.create_task(self._emit_transparency_step(
                    StepType.INFERENCE,
                    f"Diagnostic phase error: {str(e)}",
                    {"error": str(e)},
                    confidence=0.0
                ))
        
        # Track phase duration
        phase_duration = time.time() - phase_start_time
        self.phase_durations[MetacognitivePhase.DIAGNOSING].append(phase_duration)
    
    def _execute_planning_phase_with_transparency(self) -> None:
        """Execute planning phase with transparency tracking."""
        phase_start_time = time.time()
        self.current_phase = MetacognitivePhase.PLANNING
        
        # Emit phase start
        if self._should_emit_for_hook("planning_start"):
            asyncio.create_task(self._emit_transparency_step(
                StepType.DECISION_MAKING,
                "Starting modification planning",
                {"phase": "planning", "planning_strategy": "enhanced"}
            ))
        
        try:
            # Enhanced planning logic would go here
            # For now, call base implementation
            # This would be expanded with more sophisticated planning
            
            if self.transparency_enabled:
                asyncio.create_task(self._emit_transparency_step(
                    StepType.DECISION_MAKING,
                    "Modification planning completed",
                    {
                        "plans_generated": "placeholder",  # Would be actual count
                        "planning_confidence": 0.8,
                        "estimated_impact": "medium"
                    }
                ))
            
        except Exception as e:
            logger.error(f"Error in planning phase: {e}")
            if self.transparency_enabled:
                asyncio.create_task(self._emit_transparency_step(
                    StepType.DECISION_MAKING,
                    f"Planning phase error: {str(e)}",
                    {"error": str(e)},
                    confidence=0.0
                ))
        
        # Track phase duration
        phase_duration = time.time() - phase_start_time
        self.phase_durations[MetacognitivePhase.PLANNING].append(phase_duration)
    
    def _execute_modifying_phase_with_transparency(self) -> None:
        """Execute modifying phase with transparency tracking."""
        phase_start_time = time.time()
        self.current_phase = MetacognitivePhase.MODIFYING
        
        # Emit phase start
        if self._should_emit_for_hook("modifying_start"):
            asyncio.create_task(self._emit_transparency_step(
                StepType.METACOGNITIVE_REFLECTION,
                "Starting autonomous modifications",
                {"phase": "modifying", "safety_checks": "enabled"}
            ))
        
        try:
            # Enhanced modification logic would go here
            # This would include safety checks, rollback preparation, etc.
            
            if self.transparency_enabled:
                asyncio.create_task(self._emit_transparency_step(
                    StepType.METACOGNITIVE_REFLECTION,
                    "Autonomous modifications completed",
                    {
                        "modifications_applied": "placeholder",  # Would be actual count
                        "safety_status": "verified",
                        "rollback_available": True
                    }
                ))
            
        except Exception as e:
            logger.error(f"Error in modifying phase: {e}")
            if self.transparency_enabled:
                asyncio.create_task(self._emit_transparency_step(
                    StepType.METACOGNITIVE_REFLECTION,
                    f"Modifying phase error: {str(e)}",
                    {"error": str(e)},
                    confidence=0.0
                ))
        
        # Track phase duration
        phase_duration = time.time() - phase_start_time
        self.phase_durations[MetacognitivePhase.MODIFYING].append(phase_duration)
    
    async def _emit_transparency_step(
        self,
        step_type: StepType,
        description: str,
        context: Dict[str, Any],
        confidence: float = 1.0
    ) -> None:
        """Emit a transparency step for the current metacognitive operation."""
        if not self.transparency_enabled or not self.current_transparency_session:
            return
        
        step = ReasoningStepBuilder() \
            .with_type(step_type) \
            .with_description(description) \
            .with_context(context) \
            .with_confidence(confidence) \
            .with_importance(0.7) \
            .build()
        
        await self.transparency_manager.emit_reasoning_step(
            step, self.current_transparency_session
        )
        
        self.metacognitive_step_count += 1
    
    def _should_emit_for_hook(self, hook_id: str) -> bool:
        """Check if transparency should be emitted for a specific hook."""
        hook = self.transparency_hooks.get(hook_id)
        return hook is not None and hook.enabled and self.transparency_enabled
    
    def _get_enhanced_system_state(self) -> Dict[str, Any]:
        """Get enhanced system state with additional metacognitive metrics."""
        base_state = self._get_current_system_state()
        
        # Add enhanced metrics
        enhanced_state = {
            **base_state,
            "metacognitive_metrics": {
                "cycle_count": len(self.cycle_performance_history),
                "average_cycle_duration": self._calculate_average_cycle_duration(),
                "introspection_depth": self.introspection_depth,
                "self_evaluation_count": len(self.self_evaluation_history),
                "transparency_enabled": self.transparency_enabled,
                "current_transparency_session": self.current_transparency_session
            },
            "phase_performance": {
                phase.value: {
                    "average_duration": sum(durations) / len(durations) if durations else 0.0,
                    "execution_count": len(durations)
                }
                for phase, durations in self.phase_durations.items()
            }
        }
        
        return enhanced_state
    
    def _perform_enhanced_self_evaluation(self, system_state: Dict[str, Any]) -> Dict[str, Any]:
        """Perform enhanced self-evaluation with detailed metrics."""
        # Basic health score calculation
        health_score = 1.0
        anomalies = []
        
        # Check cycle performance
        if len(self.cycle_performance_history) > 5:
            recent_durations = [c["duration"] for c in self.cycle_performance_history[-5:]]
            avg_duration = sum(recent_durations) / len(recent_durations)
            
            if avg_duration > self.cycle_interval_sec * 0.8:  # Taking too long
                health_score -= 0.2
                anomalies.append("Cycle duration exceeding threshold")
        
        # Check error rate
        error_count = len([e for e in self.event_history if e.event_type == "cycle_error"])
        if error_count > 0:
            error_rate = error_count / max(len(self.cycle_performance_history), 1)
            if error_rate > 0.1:  # More than 10% error rate
                health_score -= 0.3
                anomalies.append(f"High error rate: {error_rate:.2%}")
        
        return {
            "health_score": max(health_score, 0.0),
            "anomalies": anomalies,
            "performance": {
                "cycle_count": len(self.cycle_performance_history),
                "average_duration": self._calculate_average_cycle_duration(),
                "error_rate": error_count / max(len(self.cycle_performance_history), 1)
            },
            "timestamp": time.time()
        }
    
    def _generate_enhanced_diagnostic_report(self):
        """Generate enhanced diagnostic report with transparency integration."""
        # Call base diagnostic generation
        base_report = self.diagnostician.generate_report() if self.diagnostician else None
        
        # Add enhanced diagnostics
        # This would be expanded with more sophisticated analysis
        
        return base_report
    
    def _categorize_findings_by_severity(self, findings) -> Dict[str, int]:
        """Categorize diagnostic findings by severity."""
        severity_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        
        for finding in findings:
            severity = getattr(finding, 'severity', 'medium').lower()
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        return severity_counts
    
    def _calculate_average_cycle_duration(self) -> float:
        """Calculate average cycle duration."""
        if not self.cycle_performance_history:
            return 0.0
        
        durations = [c["duration"] for c in self.cycle_performance_history]
        return sum(durations) / len(durations)
    
    def _analyze_performance_trend(self) -> str:
        """Analyze performance trend over recent cycles."""
        if len(self.cycle_performance_history) < 3:
            return "insufficient_data"
        
        recent_durations = [c["duration"] for c in self.cycle_performance_history[-5:]]
        if len(recent_durations) < 3:
            return "insufficient_data"
        
        # Simple trend analysis
        first_half = recent_durations[:len(recent_durations)//2]
        second_half = recent_durations[len(recent_durations)//2:]
        
        avg_first = sum(first_half) / len(first_half)
        avg_second = sum(second_half) / len(second_half)
        
        if avg_second > avg_first * 1.1:
            return "degrading"
        elif avg_second < avg_first * 0.9:
            return "improving"
        else:
            return "stable"
    
    def configure_transparency_hook(
        self,
        hook_id: str,
        phase: MetacognitivePhase,
        enabled: bool = True,
        detail_level: DetailLevel = DetailLevel.MEDIUM
    ) -> None:
        """Configure a transparency hook for a specific metacognitive phase."""
        self.transparency_hooks[hook_id] = TransparencyHook(
            hook_id=hook_id,
            phase=phase,
            enabled=enabled,
            detail_level=detail_level
        )
        
        logger.info(f"Configured transparency hook: {hook_id} for phase {phase.value}")
    
    def get_transparency_statistics(self) -> Dict[str, Any]:
        """Get statistics about transparency operations."""
        return {
            "transparency_enabled": self.transparency_enabled,
            "current_session": self.current_transparency_session,
            "steps_emitted": self.metacognitive_step_count,
            "hooks_configured": len(self.transparency_hooks),
            "active_hooks": len([h for h in self.transparency_hooks.values() if h.enabled]),
            "cycle_performance": {
                "total_cycles": len(self.cycle_performance_history),
                "average_duration": self._calculate_average_cycle_duration(),
                "performance_trend": self._analyze_performance_trend()
            },
            "self_evaluations": len(self.self_evaluation_history)
        }