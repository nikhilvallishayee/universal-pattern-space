"""
Lightweight coordination interface for cross-component cognitive orchestration.

Defines event/decision structures and a simple coordinator with minimal
heuristics suitable for integration without disruptive changes.
"""

from dataclasses import dataclass, asdict, field
from typing import Any, Dict, Optional
import time


@dataclass
class CoordinationEvent:
    name: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=lambda: time.time())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CoordinationDecision:
    action: str = "proceed"
    params: Dict[str, Any] = field(default_factory=dict)
    rationale: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SimpleCoordinator:
    """Minimal heuristic-based coordinator.

    Currently focuses on confidence-threshold based nudges that can be used to
    augment context or trigger additional reasoning steps. Safe no-op defaults.
    """

    def __init__(self, *, min_confidence: float = 0.6):
        self.min_confidence = min_confidence

    async def notify(self, event: CoordinationEvent) -> CoordinationDecision:
        # Heuristic: if initial reasoning confidence is low, suggest augmentation
        if event.name == "initial_reasoning_complete":
            conf = None
            try:
                conf = float(event.data.get("confidence", 0.0))
            except Exception:
                conf = 0.0
            if conf < self.min_confidence:
                return CoordinationDecision(
                    action="augment_context",
                    params={"suggested_sources": event.data.get("knowledge_context", {}).get("sources", [])},
                    rationale=f"Confidence {conf:.2f} below threshold {self.min_confidence:.2f}"
                )
        # Default
        return CoordinationDecision(action="proceed", rationale="No coordination change required")

