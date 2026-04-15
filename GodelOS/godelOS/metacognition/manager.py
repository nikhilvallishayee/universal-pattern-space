"""
Metacognition Manager for GödelOS.

This module implements the MetacognitionManager component (Module 7.6) of the Metacognition & 
Self-Improvement System, which is responsible for coordinating the different metacognition
components and implementing the metacognitive cycle.

The MetacognitionManager:
1. Coordinates the different metacognition components
2. Provides a unified API for the rest of GödelOS to interact with
3. Manages configuration of the metacognition components
4. Handles initialization and shutdown of components
5. Implements the metacognitive cycle (monitor → diagnose → plan → modify)
"""

import logging
import time
import threading
import os
import json
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Callable
from enum import Enum
from dataclasses import dataclass, field

from godelOS.metacognition.self_monitoring import SelfMonitoringModule
from godelOS.metacognition.meta_knowledge import MetaKnowledgeBase
from godelOS.metacognition.diagnostician import (
    CognitiveDiagnostician,
    DiagnosticReport,
    DiagnosticFinding
)
from godelOS.metacognition.modification_planner import (
    SelfModificationPlanner,
    ModificationProposal,
    ExecutionPlan,
    ModificationResult,
    ModificationStatus
)
from godelOS.metacognition.module_library import (
    ModuleLibraryActivator,
    ModuleMetadata
)
from godelOS.symbol_grounding.internal_state_monitor import InternalStateMonitor
from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface
from godelOS.core_kr.type_system.manager import TypeSystemManager

logger = logging.getLogger(__name__)


class MetacognitivePhase(Enum):
    """Enum representing phases of the metacognitive cycle."""
    IDLE = "idle"
    MONITORING = "monitoring"
    DIAGNOSING = "diagnosing"
    PLANNING = "planning"
    MODIFYING = "modifying"
    ERROR = "error"


class MetacognitiveMode(Enum):
    """Enum representing operational modes of the metacognition system."""
    PASSIVE = "passive"  # Only monitoring, no autonomous modifications
    SEMI_AUTONOMOUS = "semi_autonomous"  # Propose modifications, but require approval
    AUTONOMOUS = "autonomous"  # Autonomously implement modifications
    MAINTENANCE = "maintenance"  # Special mode for maintenance tasks
    DISABLED = "disabled"  # Metacognition system is disabled


@dataclass
class MetacognitiveEvent:
    """Represents an event in the metacognitive system."""
    event_type: str
    timestamp: float = field(default_factory=time.time)
    details: Dict[str, Any] = field(default_factory=dict)
    source_component: str = ""


class MetacognitionManager:
    """
    Metacognition Manager for GödelOS.
    
    The MetacognitionManager coordinates the different metacognition components
    and implements the metacognitive cycle.
    """
    
    def __init__(
        self,
        kr_system_interface: KnowledgeStoreInterface,
        type_system: TypeSystemManager,
        internal_state_monitor: Optional[InternalStateMonitor] = None,
        config_path: Optional[str] = None,
        modules_directory: Optional[str] = None
    ):
        """Initialize the metacognition manager."""
        self.kr_interface = kr_system_interface
        self.type_system = type_system
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Initialize components
        self.internal_state_monitor = internal_state_monitor
        self.self_monitoring = None
        self.meta_knowledge = None
        self.diagnostician = None
        self.modification_planner = None
        self.module_library = None
        
        # Initialize state
        self.current_phase = MetacognitivePhase.IDLE
        self.current_mode = MetacognitiveMode(self.config.get("initial_mode", "passive"))
        self.is_initialized = False
        self.is_running = False
        self.cycle_interval_sec = self.config.get("cycle_interval_sec", 60.0)
        
        # Initialize cycle thread
        self.cycle_thread = None
        self.stop_cycle = threading.Event()
        
        # Event history
        self.event_history = []
        self.max_event_history = self.config.get("max_event_history", 1000)
        
        # Event subscribers
        self.event_subscribers = {}
        
        # Initialize modules directory
        self.modules_directory = modules_directory or self.config.get("modules_directory", "metacognition_modules")
        os.makedirs(self.modules_directory, exist_ok=True)
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from file or use defaults."""
        default_config = {
            "initial_mode": "passive",
            "cycle_interval_sec": 60.0,
            "max_event_history": 1000,
            "modules_directory": "metacognition_modules",
            "component_config": {
                "self_monitoring": {
                    "history_window_size": 100,
                    "anomaly_detection_interval_sec": 10.0,
                    "performance_metrics_interval_sec": 5.0
                },
                "meta_knowledge": {
                    "persistence_directory": "meta_knowledge_store"
                },
                "modification_planner": {
                    "max_auto_approval_risk": "low"
                }
            }
        }
        
        if not config_path or not os.path.exists(config_path):
            logger.info("Using default metacognition configuration")
            return default_config
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            logger.info(f"Loaded metacognition configuration from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Error loading configuration from {config_path}: {e}")
            return default_config
    
    def initialize(self) -> bool:
        """
        Initialize the metacognition system.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        if self.is_initialized:
            logger.warning("Metacognition system is already initialized")
            return True
        
        try:
            # Initialize MetaKnowledgeBase
            meta_knowledge_config = self.config.get("component_config", {}).get("meta_knowledge", {})
            persistence_directory = meta_knowledge_config.get("persistence_directory")
            
            if persistence_directory:
                os.makedirs(persistence_directory, exist_ok=True)
            
            self.meta_knowledge = MetaKnowledgeBase(
                kr_system_interface=self.kr_interface,
                type_system=self.type_system,
                persistence_directory=persistence_directory
            )
            
            # Initialize SelfMonitoringModule
            if not self.internal_state_monitor:
                self.internal_state_monitor = InternalStateMonitor(
                    kr_system_interface=self.kr_interface,
                    type_system=self.type_system
                )
            
            monitoring_config = self.config.get("component_config", {}).get("self_monitoring", {})
            
            self.self_monitoring = SelfMonitoringModule(
                internal_state_monitor=self.internal_state_monitor,
                kr_system_interface=self.kr_interface,
                type_system=self.type_system,
                history_window_size=monitoring_config.get("history_window_size", 100),
                anomaly_detection_interval_sec=monitoring_config.get("anomaly_detection_interval_sec", 10.0),
                performance_metrics_interval_sec=monitoring_config.get("performance_metrics_interval_sec", 5.0)
            )
            
            # Initialize CognitiveDiagnostician
            self.diagnostician = CognitiveDiagnostician(
                self_monitoring_module=self.self_monitoring,
                meta_knowledge_base=self.meta_knowledge
            )
            
            # Initialize ModuleLibraryActivator
            self.module_library = ModuleLibraryActivator(
                modules_directory=self.modules_directory
            )
            
            # Initialize SelfModificationPlanner
            planner_config = self.config.get("component_config", {}).get("modification_planner", {})
            
            self.modification_planner = SelfModificationPlanner(
                diagnostician=self.diagnostician,
                meta_knowledge_base=self.meta_knowledge
            )
            
            # Set up event subscriptions
            self._setup_event_subscriptions()
            
            self.is_initialized = True
            self._log_event("system_initialized", {"status": "success"})
            logger.info("Metacognition system initialized successfully")
            
            return True
        except Exception as e:
            logger.error(f"Error initializing metacognition system: {e}")
            self._log_event("system_initialized", {"status": "failed", "error": str(e)})
            self.current_phase = MetacognitivePhase.ERROR
            return False
    
    def _setup_event_subscriptions(self) -> None:
        """Set up event subscriptions between components."""
        # Subscribe to anomaly events from self-monitoring
        self.self_monitoring.register_anomaly_callback(self._on_anomaly_detected)
    
    def start(self) -> bool:
        """
        Start the metacognition system.
        
        Returns:
            True if the system was started successfully, False otherwise
        """
        if not self.is_initialized:
            success = self.initialize()
            if not success:
                return False
        
        if self.is_running:
            logger.warning("Metacognition system is already running")
            return True
        
        try:
            # Start internal state monitor
            self.internal_state_monitor.start_monitoring()
            
            # Start self-monitoring
            self.self_monitoring.start_monitoring()
            
            # Start metacognitive cycle
            self.stop_cycle.clear()
            self.cycle_thread = threading.Thread(
                target=self._metacognitive_cycle_loop,
                daemon=True
            )
            self.cycle_thread.start()
            
            self.is_running = True
            self._log_event("system_started", {"mode": self.current_mode.value})
            logger.info(f"Metacognition system started in {self.current_mode.value} mode")
            
            return True
        except Exception as e:
            logger.error(f"Error starting metacognition system: {e}")
            self._log_event("system_start_failed", {"error": str(e)})
            return False
    
    def stop(self) -> bool:
        """
        Stop the metacognition system.
        
        Returns:
            True if the system was stopped successfully, False otherwise
        """
        if not self.is_running:
            logger.warning("Metacognition system is not running")
            return True
        
        try:
            # Stop metacognitive cycle
            self.stop_cycle.set()
            if self.cycle_thread:
                self.cycle_thread.join(timeout=2.0)
            
            # Stop self-monitoring
            if self.self_monitoring:
                self.self_monitoring.stop_monitoring()
            
            # Stop internal state monitor
            if self.internal_state_monitor:
                self.internal_state_monitor.stop_monitoring()
            
            self.is_running = False
            self._log_event("system_stopped", {})
            logger.info("Metacognition system stopped")
            
            return True
        except Exception as e:
            logger.error(f"Error stopping metacognition system: {e}")
            self._log_event("system_stop_failed", {"error": str(e)})
            return False
    
    def set_mode(self, mode: Union[str, MetacognitiveMode]) -> bool:
        """
        Set the operational mode of the metacognition system.
        
        Args:
            mode: The new mode (either a string or MetacognitiveMode enum)
            
        Returns:
            True if the mode was set successfully, False otherwise
        """
        try:
            if isinstance(mode, str):
                mode = MetacognitiveMode(mode.lower())
            
            old_mode = self.current_mode
            self.current_mode = mode
            
            self._log_event("mode_changed", {"old_mode": old_mode.value, "new_mode": mode.value})
            logger.info(f"Metacognition mode changed from {old_mode.value} to {mode.value}")
            
            return True
        except Exception as e:
            logger.error(f"Error setting metacognition mode: {e}")
            return False
    
    def _metacognitive_cycle_loop(self) -> None:
        """Main loop for the metacognitive cycle."""
        while not self.stop_cycle.is_set():
            try:
                self._execute_metacognitive_cycle()
            except Exception as e:
                logger.error(f"Error in metacognitive cycle: {e}")
                self.current_phase = MetacognitivePhase.ERROR
                self._log_event("cycle_error", {"error": str(e)})
            
            # Sleep until next cycle
            self.stop_cycle.wait(self.cycle_interval_sec)
    
    def _execute_metacognitive_cycle(self) -> None:
        """Execute one iteration of the metacognitive cycle."""
        # Skip cycle if in disabled mode
        if self.current_mode == MetacognitiveMode.DISABLED:
            return
        
        # 1. Monitoring phase
        self.current_phase = MetacognitivePhase.MONITORING
        self._log_event("phase_started", {"phase": self.current_phase.value})
        
        # Get current system state
        system_state = self._get_current_system_state()
        
        # 2. Diagnosing phase
        self.current_phase = MetacognitivePhase.DIAGNOSING
        self._log_event("phase_started", {"phase": self.current_phase.value})
        
        # Generate diagnostic report
        diagnostic_report = self.diagnostician.generate_report()
        
        # Always log the diagnostic report generation
        self._log_event("diagnostic_report_generated", {
            "report_id": diagnostic_report.report_id,
            "finding_count": len(diagnostic_report.findings)
        })
        
        # Skip remaining phases if no issues found
        if not diagnostic_report.findings:
            self._log_event("no_issues_found", {})
            self.current_phase = MetacognitivePhase.IDLE
            return
        
        # 3. Planning phase
        self.current_phase = MetacognitivePhase.PLANNING
        self._log_event("phase_started", {"phase": self.current_phase.value})
        
        # Generate modification proposals
        proposals = self.modification_planner.generate_proposals_from_diagnostic_report(
            diagnostic_report, system_state
        )
        
        # Skip remaining phases if no proposals generated
        if not proposals:
            self._log_event("no_proposals_generated", {})
            self.current_phase = MetacognitivePhase.IDLE
            return
        
        # Evaluate proposals
        evaluated_proposals = []
        for proposal in proposals:
            evaluation = self.modification_planner.evaluate_proposal(
                proposal.proposal_id, system_state
            )
            evaluated_proposals.append((proposal, evaluation))
        
        # Log planning results
        self._log_event("proposals_generated", {
            "proposal_count": len(proposals),
            "approved_count": sum(1 for p in proposals if p.status == ModificationStatus.APPROVED)
        })
        
        # 4. Modifying phase (if in autonomous mode)
        if self.current_mode == MetacognitiveMode.AUTONOMOUS:
            self.current_phase = MetacognitivePhase.MODIFYING
            self._log_event("phase_started", {"phase": self.current_phase.value})
            
            # Implement approved modifications
            for proposal in proposals:
                if proposal.status == ModificationStatus.APPROVED:
                    # Create execution plan
                    plan = self.modification_planner.create_execution_plan(proposal.proposal_id)
                    
                    # Execute plan
                    result = self.modification_planner.execute_plan(plan.plan_id, system_state)
                    
                    # Log result
                    self._log_event("modification_executed", {
                        "proposal_id": proposal.proposal_id,
                        "plan_id": plan.plan_id,
                        "result_id": result.result_id,
                        "success": result.success
                    })
        
        # Return to idle phase
        self.current_phase = MetacognitivePhase.IDLE
    
    def _get_current_system_state(self) -> Dict[str, Any]:
        """Get the current state of the system."""
        # Get monitoring data
        monitoring_data = self.self_monitoring.get_performance_metrics()
        
        # Get module information
        active_modules = self.module_library.get_active_modules()
        
        # Combine into system state
        system_state = {
            "monitoring_data": monitoring_data,
            "active_modules": active_modules,
            "metacognition": {
                "mode": self.current_mode.value,
                "phase": self.current_phase.value
            },
            "timestamp": time.time()
        }
        
        return system_state
    
    def _on_anomaly_detected(self, anomaly) -> None:
        """Handle anomaly detected by self-monitoring."""
        self._log_event("anomaly_detected", {
            "anomaly_type": anomaly.anomaly_type,
            "severity": anomaly.severity,
            "affected_component": anomaly.affected_component,
            "description": anomaly.description
        })
        
        # Trigger diagnostic cycle if in semi-autonomous or autonomous mode
        if (self.current_mode in [MetacognitiveMode.SEMI_AUTONOMOUS, MetacognitiveMode.AUTONOMOUS] and 
            self.current_phase == MetacognitivePhase.IDLE):
            # Start a new cycle immediately
            threading.Thread(target=self._execute_metacognitive_cycle, daemon=True).start()
    
    def _log_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """Log an event in the metacognitive system."""
        event = MetacognitiveEvent(
            event_type=event_type,
            details=details,
            source_component="MetacognitionManager"
        )
        
        # Add to history
        self.event_history.append(event)
        
        # Trim history if needed
        if len(self.event_history) > self.max_event_history:
            self.event_history = self.event_history[-self.max_event_history:]
        
        # Notify subscribers
        self._notify_event_subscribers(event)
    
    def _notify_event_subscribers(self, event: MetacognitiveEvent) -> None:
        """Notify subscribers of an event."""
        # Notify subscribers for this event type
        if event.event_type in self.event_subscribers:
            for callback in self.event_subscribers[event.event_type]:
                try:
                    callback(event)
                except Exception as e:
                    logger.error(f"Error in event subscriber callback: {e}")
        
        # Notify subscribers for all events
        if "*" in self.event_subscribers:
            for callback in self.event_subscribers["*"]:
                try:
                    callback(event)
                except Exception as e:
                    logger.error(f"Error in event subscriber callback: {e}")
    
    def subscribe_to_event(self, event_type: str, callback: Callable[[MetacognitiveEvent], None]) -> None:
        """
        Subscribe to metacognitive events.
        
        Args:
            event_type: Type of event to subscribe to, or "*" for all events
            callback: Function to call when the event occurs
        """
        if event_type not in self.event_subscribers:
            self.event_subscribers[event_type] = []
        
        self.event_subscribers[event_type].append(callback)
    
    def unsubscribe_from_event(self, event_type: str, callback: Callable[[MetacognitiveEvent], None]) -> bool:
        """
        Unsubscribe from metacognitive events.
        
        Args:
            event_type: Type of event to unsubscribe from
            callback: Function to remove from subscribers
            
        Returns:
            True if the callback was removed, False otherwise
        """
        if event_type not in self.event_subscribers:
            return False
        
        try:
            self.event_subscribers[event_type].remove(callback)
            return True
        except ValueError:
            return False
    
    def get_recent_events(self, limit: Optional[int] = None, event_type: Optional[str] = None) -> List[MetacognitiveEvent]:
        """
        Get recent metacognitive events.
        
        Args:
            limit: Maximum number of events to return
            event_type: Optional filter for event type
            
        Returns:
            List of recent MetacognitiveEvent objects
        """
        events = self.event_history
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        if limit:
            events = events[-limit:]
        
        return events
    
    def get_current_status(self) -> Dict[str, Any]:
        """
        Get the current status of the metacognition system.
        
        Returns:
            Dictionary with current status information
        """
        return {
            "is_initialized": self.is_initialized,
            "is_running": self.is_running,
            "current_mode": self.current_mode.value,
            "current_phase": self.current_phase.value,
            "cycle_interval_sec": self.cycle_interval_sec,
            "event_count": len(self.event_history),
            "components": {
                "self_monitoring": bool(self.self_monitoring),
                "meta_knowledge": bool(self.meta_knowledge),
                "diagnostician": bool(self.diagnostician),
                "modification_planner": bool(self.modification_planner),
                "module_library": bool(self.module_library)
            }
        }
    
    def get_diagnostic_reports(self, limit: int = 10) -> List[DiagnosticReport]:
        """
        Get recent diagnostic reports.
        
        Args:
            limit: Maximum number of reports to return
            
        Returns:
            List of recent DiagnosticReport objects
        """
        if not self.diagnostician:
            return []
        
        return self.diagnostician.get_recent_reports(limit)
    
    def get_modification_proposals(self, status: Optional[ModificationStatus] = None) -> List[ModificationProposal]:
        """
        Get modification proposals.
        
        Args:
            status: Optional filter for proposal status
            
        Returns:
            List of ModificationProposal objects
        """
        if not self.modification_planner:
            return []
        
        proposals = list(self.modification_planner.proposals.values())
        
        if status:
            proposals = [p for p in proposals if p.status == status]
        
        return proposals
    
    def approve_modification_proposal(self, proposal_id: str) -> bool:
        """
        Approve a modification proposal.
        
        Args:
            proposal_id: ID of the proposal to approve
            
        Returns:
            True if the proposal was approved, False otherwise
        """
        if not self.modification_planner:
            return False
        
        proposal = self.modification_planner.get_proposal(proposal_id)
        if not proposal:
            return False
        
        # Handle both enum and string status values
        if isinstance(proposal.status, str):
            if proposal.status != ModificationStatus.PROPOSED.value:
                return False
        else:
            if proposal.status != ModificationStatus.PROPOSED:
                return False
        
        # Set status to string or enum based on the original type
        if isinstance(proposal.status, str):
            proposal.status = ModificationStatus.APPROVED.value  # Use string value
        else:
            proposal.status = ModificationStatus.APPROVED  # Use enum value
            
        proposal.last_updated = time.time()
        
        self._log_event("proposal_approved", {"proposal_id": proposal_id})
        
        return True
    
    def reject_modification_proposal(self, proposal_id: str, reason: str = "") -> bool:
        """
        Reject a modification proposal.
        
        Args:
            proposal_id: ID of the proposal to reject
            reason: Optional reason for rejection
            
        Returns:
            True if the proposal was rejected, False otherwise
        """
        if not self.modification_planner:
            return False
        
        proposal = self.modification_planner.get_proposal(proposal_id)
        if not proposal:
            return False
        
        # Handle both enum and string status values
        if isinstance(proposal.status, str):
            if proposal.status != ModificationStatus.PROPOSED.value:
                return False
        else:
            if proposal.status != ModificationStatus.PROPOSED:
                return False
        
        # Set status to string or enum based on the original type
        if isinstance(proposal.status, str):
            proposal.status = ModificationStatus.REJECTED.value  # Use string value
        else:
            proposal.status = ModificationStatus.REJECTED  # Use enum value
            
        proposal.last_updated = time.time()
        
        if reason:
            if "rejection_reason" not in proposal.metadata:
                proposal.metadata["rejection_reason"] = reason
        
        self._log_event("proposal_rejected", {
            "proposal_id": proposal_id,
            "reason": reason
        })
        
        return True
    
    def execute_modification(self, proposal_id: str) -> Tuple[bool, str]:
        """
        Execute a modification proposal.
        
        Args:
            proposal_id: ID of the proposal to execute
            
        Returns:
            Tuple of (success, message)
        """
        if not self.modification_planner:
            return False, "Modification planner not initialized"
        
        proposal = self.modification_planner.get_proposal(proposal_id)
        if not proposal:
            return False, f"Proposal with ID {proposal_id} not found"
        
        # Handle both enum and string status values
        if isinstance(proposal.status, str):
            if proposal.status != ModificationStatus.APPROVED.value:
                return False, f"Proposal is not approved (status: {proposal.status})"
        else:
            if proposal.status != ModificationStatus.APPROVED:
                return False, f"Proposal is not approved (status: {proposal.status.value})"
        
        try:
            # Create execution plan
            plan = self.modification_planner.create_execution_plan(proposal_id)
            
            # Execute plan
            system_state = self._get_current_system_state()
            result = self.modification_planner.execute_plan(plan.plan_id, system_state)
            
            # Log result
            self._log_event("modification_executed", {
                "proposal_id": proposal_id,
                "plan_id": plan.plan_id,
                "result_id": result.result_id,
                "success": result.success
            })
            
            if result.success:
                return True, f"Modification executed successfully"
            else:
                return False, f"Modification execution failed: {', '.join(result.issues_encountered)}"
        except Exception as e:
            logger.error(f"Error executing modification: {e}")
            return False, f"Error executing modification: {e}"