"""
SelfModificationEngine — runtime self-modification for GödelOS.

Supports propose / apply / rollback semantics for four targets:
  * knowledge_graph    – in-memory concept store
  * inference_rules    – in-memory rule store
  * attention_weights  – per-component weight map
  * active_modules     – module enable/disable registry

All applied modifications are tracked in an ordered history log with
timestamped before/after snapshots so that rollback is fully deterministic.
"""

from __future__ import annotations

import asyncio
import copy
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Maximum number of history records kept in memory.
MAX_HISTORY_RECORDS = 1000


# ---------------------------------------------------------------------------
# Custom exceptions for distinguishing error semantics
# ---------------------------------------------------------------------------

class ProposalNotFoundError(ValueError):
    """Raised when a proposal_id does not exist."""


class ProposalStateError(ValueError):
    """Raised when an operation is invalid for the current proposal state."""


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------

@dataclass
class ModificationProposal:
    proposal_id: str
    target: str
    operation: str
    parameters: Dict[str, Any]
    status: str = "pending"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ModificationRecord:
    proposal_id: str
    target: str
    operation: str
    parameters: Dict[str, Any]
    status: str
    created_at: str
    applied_at: Optional[str] = None
    rolled_back_at: Optional[str] = None
    before_snapshot: Optional[Dict[str, Any]] = None
    after_snapshot: Optional[Dict[str, Any]] = None
    changes_summary: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "target": self.target,
            "operation": self.operation,
            "parameters": self.parameters,
            "status": self.status,
            "created_at": self.created_at,
            "applied_at": self.applied_at,
            "rolled_back_at": self.rolled_back_at,
            "changes_summary": self.changes_summary,
        }


@dataclass
class ModificationResult:
    proposal_id: str
    status: str
    changes_summary: str


@dataclass
class RollbackResult:
    proposal_id: str
    status: str


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class SelfModificationEngine:
    """Lightweight, fully in-memory self-modification engine."""

    # Default module registry used on initialisation
    _DEFAULT_MODULES: Dict[str, Dict[str, Any]] = {
        "reasoning": {"enabled": True, "description": "Core reasoning module"},
        "memory": {"enabled": True, "description": "Memory management module"},
        "learning": {"enabled": True, "description": "Adaptive learning module"},
        "metacognition": {"enabled": True, "description": "Meta-cognitive awareness module"},
    }

    def __init__(self, max_history: int = MAX_HISTORY_RECORDS) -> None:
        # Per-target in-memory stores
        self._knowledge_graph: Dict[str, Dict[str, Any]] = {}
        self._inference_rules: Dict[str, Dict[str, Any]] = {}
        self._attention_weights: Dict[str, float] = {}
        self._active_modules: Dict[str, Dict[str, Any]] = copy.deepcopy(self._DEFAULT_MODULES)

        # Proposal / history stores
        self._proposals: Dict[str, ModificationProposal] = {}
        self._records: Dict[str, ModificationRecord] = {}
        self._history_order: List[str] = []  # ordered proposal IDs

        # Concurrency guard
        self._lock = asyncio.Lock()

        # Retention cap
        self._max_history = max_history

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def propose_modification(
        self,
        target: str,
        operation: str,
        parameters: Dict[str, Any],
    ) -> ModificationProposal:
        """Create and store a new pending modification proposal."""
        if not isinstance(parameters, dict):
            raise ValueError("'parameters' must be a JSON object (dict)")

        self._validate_target(target)
        self._validate_operation(target, operation)

        async with self._lock:
            proposal_id = str(uuid.uuid4())
            proposal = ModificationProposal(
                proposal_id=proposal_id,
                target=target,
                operation=operation,
                parameters=parameters,
            )
            self._proposals[proposal_id] = proposal
        return proposal

    async def apply_modification(self, proposal_id: str) -> ModificationResult:
        """Apply a pending proposal, snapshotting before/after state."""
        async with self._lock:
            proposal = self._proposals.get(proposal_id)
            if proposal is None:
                raise ProposalNotFoundError(f"Proposal '{proposal_id}' not found")
            if proposal.status != "pending":
                raise ProposalStateError(
                    f"Proposal '{proposal_id}' cannot be applied (status: {proposal.status})"
                )

            before_snapshot = self._capture_snapshot(proposal.target)
            changes_summary = self._apply_to_target(
                proposal.target, proposal.operation, proposal.parameters
            )
            after_snapshot = self._capture_snapshot(proposal.target)

            applied_at = datetime.now(timezone.utc).isoformat()
            proposal.status = "applied"

            record = ModificationRecord(
                proposal_id=proposal_id,
                target=proposal.target,
                operation=proposal.operation,
                parameters=proposal.parameters,
                status="applied",
                created_at=proposal.created_at,
                applied_at=applied_at,
                before_snapshot=before_snapshot,
                after_snapshot=after_snapshot,
                changes_summary=changes_summary,
            )
            self._records[proposal_id] = record
            if proposal_id not in self._history_order:
                self._history_order.append(proposal_id)

            self._enforce_history_limit()

        return ModificationResult(
            proposal_id=proposal_id,
            status="applied",
            changes_summary=changes_summary,
        )

    async def rollback_modification(self, proposal_id: str) -> RollbackResult:
        """Restore the before-snapshot for an applied modification."""
        async with self._lock:
            record = self._records.get(proposal_id)
            if record is None:
                raise ProposalNotFoundError(
                    f"No applied modification found for proposal '{proposal_id}'"
                )
            if record.status != "applied":
                raise ProposalStateError(
                    f"Modification '{proposal_id}' cannot be rolled back "
                    f"(status: {record.status})"
                )

            self._restore_snapshot(record.target, record.before_snapshot or {})

            record.status = "rolled_back"
            record.rolled_back_at = datetime.now(timezone.utc).isoformat()

            proposal = self._proposals.get(proposal_id)
            if proposal:
                proposal.status = "rolled_back"

            if proposal_id not in self._history_order:
                self._history_order.append(proposal_id)

        return RollbackResult(proposal_id=proposal_id, status="rolled_back")

    async def get_history(self) -> List[ModificationRecord]:
        """Return all modification records in application order."""
        async with self._lock:
            return [
                self._records[pid]
                for pid in self._history_order
                if pid in self._records
            ]

    # ------------------------------------------------------------------
    # Read helpers for integration with server endpoints
    # ------------------------------------------------------------------

    def get_knowledge_items(self) -> List[Dict[str, Any]]:
        """Return all knowledge items currently in the engine's store."""
        return list(self._knowledge_graph.values())

    def get_modules_status(self) -> Dict[str, Any]:
        """Return the current active-modules registry."""
        return copy.deepcopy(self._active_modules)

    def get_inference_rules(self) -> List[Dict[str, Any]]:
        return list(self._inference_rules.values())

    def get_attention_weights(self) -> Dict[str, float]:
        return dict(self._attention_weights)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _validate_target(self, target: str) -> None:
        valid = {"knowledge_graph", "inference_rules", "attention_weights", "active_modules"}
        if target not in valid:
            raise ValueError(f"Unknown target '{target}'. Valid targets: {sorted(valid)}")

    def _validate_operation(self, target: str, operation: str) -> None:
        valid_ops: Dict[str, set] = {
            "knowledge_graph": {"add", "remove", "modify"},
            "inference_rules": {"add", "remove", "modify"},
            "attention_weights": {"add", "modify", "remove"},
            "active_modules": {"add", "remove", "enable", "disable"},
        }
        allowed = valid_ops.get(target, set())
        if operation not in allowed:
            raise ValueError(
                f"Operation '{operation}' is not valid for target '{target}'. "
                f"Allowed: {sorted(allowed)}"
            )

    def _capture_snapshot(self, target: str) -> Dict[str, Any]:
        if target == "knowledge_graph":
            return {"items": copy.deepcopy(self._knowledge_graph)}
        if target == "inference_rules":
            return {"rules": copy.deepcopy(self._inference_rules)}
        if target == "attention_weights":
            return {"weights": dict(self._attention_weights)}
        if target == "active_modules":
            return {"modules": copy.deepcopy(self._active_modules)}
        return {}

    def _restore_snapshot(self, target: str, snapshot: Dict[str, Any]) -> None:
        if target == "knowledge_graph":
            self._knowledge_graph = copy.deepcopy(snapshot.get("items", {}))
        elif target == "inference_rules":
            self._inference_rules = copy.deepcopy(snapshot.get("rules", {}))
        elif target == "attention_weights":
            self._attention_weights = dict(snapshot.get("weights", {}))
        elif target == "active_modules":
            self._active_modules = copy.deepcopy(snapshot.get("modules", {}))

    def _apply_to_target(
        self, target: str, operation: str, parameters: Dict[str, Any]
    ) -> str:
        if target == "knowledge_graph":
            return self._modify_knowledge_graph(operation, parameters)
        if target == "inference_rules":
            return self._modify_inference_rules(operation, parameters)
        if target == "attention_weights":
            return self._modify_attention_weights(operation, parameters)
        if target == "active_modules":
            return self._modify_active_modules(operation, parameters)
        raise ValueError(f"Unknown target: {target}")

    def _enforce_history_limit(self) -> None:
        """Evict oldest records when history exceeds the retention cap."""
        while len(self._history_order) > self._max_history:
            oldest_pid = self._history_order.pop(0)
            self._records.pop(oldest_pid, None)
            self._proposals.pop(oldest_pid, None)

    # ---- target-specific handlers ----

    def _modify_knowledge_graph(
        self, operation: str, parameters: Dict[str, Any]
    ) -> str:
        if operation == "add":
            item_id = parameters.get("id") or str(uuid.uuid4())
            concept = parameters.get("concept", "")
            self._knowledge_graph[item_id] = {
                "id": item_id,
                "concept": concept,
                "definition": parameters.get("definition", ""),
                "category": parameters.get("category", "general"),
                "added_at": datetime.now(timezone.utc).isoformat(),
            }
            return f"Added knowledge item '{concept or item_id}'"
        if operation == "remove":
            item_id = parameters.get("id", "")
            removed = self._knowledge_graph.pop(item_id, None)
            return (
                f"Removed knowledge item '{item_id}'"
                if removed
                else f"Knowledge item '{item_id}' not found"
            )
        if operation == "modify":
            item_id = parameters.get("id", "")
            if item_id not in self._knowledge_graph:
                raise ValueError(f"Knowledge item '{item_id}' not found")
            self._knowledge_graph[item_id].update(
                {k: v for k, v in parameters.items() if k != "id"}
            )
            return f"Modified knowledge item '{item_id}'"
        raise ValueError(f"Unknown operation '{operation}' for knowledge_graph")

    def _modify_inference_rules(
        self, operation: str, parameters: Dict[str, Any]
    ) -> str:
        if operation == "add":
            rule_id = parameters.get("id") or str(uuid.uuid4())
            name = parameters.get("name", rule_id)
            self._inference_rules[rule_id] = {
                "id": rule_id,
                "name": name,
                "condition": parameters.get("condition", ""),
                "action": parameters.get("action", ""),
                "added_at": datetime.now(timezone.utc).isoformat(),
            }
            return f"Added inference rule '{name}'"
        if operation == "remove":
            rule_id = parameters.get("id", "")
            removed = self._inference_rules.pop(rule_id, None)
            return (
                f"Removed inference rule '{rule_id}'"
                if removed
                else f"Inference rule '{rule_id}' not found"
            )
        if operation == "modify":
            rule_id = parameters.get("id", "")
            if rule_id not in self._inference_rules:
                raise ValueError(f"Inference rule '{rule_id}' not found")
            self._inference_rules[rule_id].update(
                {k: v for k, v in parameters.items() if k != "id"}
            )
            return f"Modified inference rule '{rule_id}'"
        raise ValueError(f"Unknown operation '{operation}' for inference_rules")

    def _modify_attention_weights(
        self, operation: str, parameters: Dict[str, Any]
    ) -> str:
        component = parameters.get("component", "")
        if not component:
            raise ValueError(
                "Parameter 'component' is required for attention_weights operations"
            )
        if operation in ("add", "modify"):
            raw_weight = parameters.get("weight", 0.5)
            try:
                weight = float(raw_weight)
            except (TypeError, ValueError):
                raise ValueError(
                    f"Invalid 'weight' value for attention_weights: {raw_weight!r}"
                )
            self._attention_weights[component] = weight
            return f"Set attention weight for '{component}' to {weight}"
        if operation == "remove":
            removed = self._attention_weights.pop(component, None)
            return (
                f"Removed attention weight for '{component}'"
                if removed is not None
                else f"Component '{component}' not found"
            )
        raise ValueError(f"Unknown operation '{operation}' for attention_weights")

    def _modify_active_modules(
        self, operation: str, parameters: Dict[str, Any]
    ) -> str:
        # Accept either "module" or "id" as the module identifier
        module_name = parameters.get("module") or parameters.get("id") or ""
        if operation in ("enable", "disable", "remove") and not module_name:
            raise ValueError(
                f"A non-empty module identifier is required for '{operation}' operation"
            )
        if operation == "enable":
            if module_name not in self._active_modules:
                self._active_modules[module_name] = {
                    "enabled": True,
                    "description": parameters.get("description", ""),
                }
            else:
                self._active_modules[module_name]["enabled"] = True
            return f"Enabled module '{module_name}'"
        if operation == "disable":
            if module_name not in self._active_modules:
                raise ValueError(f"Module '{module_name}' not found")
            self._active_modules[module_name]["enabled"] = False
            return f"Disabled module '{module_name}'"
        if operation == "add":
            module_id = parameters.get("id") or module_name or str(uuid.uuid4())
            self._active_modules[module_id] = {
                "enabled": parameters.get("enabled", True),
                "description": parameters.get("description", ""),
            }
            return f"Added module '{module_id}'"
        if operation == "remove":
            removed = self._active_modules.pop(module_name, None)
            return (
                f"Removed module '{module_name}'"
                if removed
                else f"Module '{module_name}' not found"
            )
        raise ValueError(f"Unknown operation '{operation}' for active_modules")
