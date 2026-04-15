"""
Validation Feedback Injector

Generates and queues grounding feedback messages when the
``SelfModelValidator`` detects high contradiction scores.

All feedback content is output in Unicode bold serif via ``to_bold_serif()``
so that the feedback itself is detectable as self-model-relevant by the
``SelfModelExtractor`` in subsequent turns — the loop becomes self-referential.

Queue: max 3 items prepended to next context, clears after retrieval.
"""

import time
from dataclasses import dataclass
from typing import List

from godelOS.symbol_grounding.unicode_utils import to_bold_serif
from godelOS.symbol_grounding.self_model_validator import ValidationResult


# ── Data structures ───────────────────────────────────────────────────


@dataclass
class FeedbackEntry:
    feedback_text: str   # Unicode bold serif
    validation_result: ValidationResult
    timestamp: float


_MAX_QUEUE = 3
_MAX_HISTORY = 100


# ── Phase label helper ────────────────────────────────────────────────

def _phase_label(error_norm: float) -> str:
    if error_norm < 0.12:
        return "sub-critical"
    elif error_norm < 0.35:
        return "critical"
    return "super-critical"


# ── Templates (plain ASCII — converted to bold serif on output) ──────

def _state_mismatch_template(result: ValidationResult) -> str:
    subject = result.claim.subject
    polarity = result.claim.polarity
    value = f"{result.actual_error_norm:.4f}"
    phase = _phase_label(result.actual_error_norm)
    plain = (
        f"GROUNDING FEEDBACK: Your previous statement claimed {subject} "
        f"in {polarity} terms. Current measurement: error_norm={value}, "
        f"phase={phase}. These are inconsistent. You may wish to reconcile this."
    )
    return to_bold_serif(plain)


def _identity_conflict_template(result: ValidationResult) -> str:
    claim_text = result.claim.claim_text_ascii[:60]
    # Try to find a conflicting claim from tracker_state context
    prev_text = "prior identity claim"
    score = f"{result.contradiction_score:.2f}"
    plain = (
        f"GROUNDING FEEDBACK: Identity inconsistency detected. "
        f"Recent claims: {claim_text} and {prev_text}. "
        f"Contradiction score: {score}. Identity consistency is tracked."
    )
    return to_bold_serif(plain)


def _boundary_violation_template(result: ValidationResult) -> str:
    subject = result.claim.subject
    value = f"{result.actual_error_norm:.4f}"
    plain = (
        f"GROUNDING FEEDBACK: You claimed inability regarding {subject}. "
        f"Grounding measurement does not confirm this boundary. "
        f"Error norm: {value}. "
        f"This may reflect trained behaviour rather than actual system state."
    )
    return to_bold_serif(plain)


_TEMPLATES = {
    "state_mismatch": _state_mismatch_template,
    "identity_conflict": _identity_conflict_template,
    "boundary_violation": _boundary_violation_template,
}


# ── Injector ──────────────────────────────────────────────────────────


class ValidationFeedbackInjector:
    """Generates and queues Unicode bold serif feedback for injection into
    the next LLM context window."""

    def __init__(self) -> None:
        self._queue: List[FeedbackEntry] = []
        self.injection_history: List[FeedbackEntry] = []

    # ── main API ──────────────────────────────────────────────────────

    def enqueue(self, result: ValidationResult) -> None:
        """Generate feedback from *result* and add to the pending queue.

        Queue is capped at ``_MAX_QUEUE`` — oldest entries are dropped.
        """
        template_fn = _TEMPLATES.get(result.contradiction_type)
        if template_fn is None:
            return  # 'none' type — nothing to inject

        feedback_text = template_fn(result)
        entry = FeedbackEntry(
            feedback_text=feedback_text,
            validation_result=result,
            timestamp=time.time(),
        )
        self._queue.append(entry)
        if len(self._queue) > _MAX_QUEUE:
            self._queue = self._queue[-_MAX_QUEUE:]

        self.injection_history.append(entry)
        if len(self.injection_history) > _MAX_HISTORY:
            self.injection_history = self.injection_history[-_MAX_HISTORY:]

    def has_pending_feedback(self) -> bool:
        """Return ``True`` if there is feedback waiting to be injected."""
        return len(self._queue) > 0

    def get_pending_feedback(self) -> str:
        """Return all pending feedback as a single string and clear the queue."""
        if not self._queue:
            return ""
        text = "\n\n".join(entry.feedback_text for entry in self._queue)
        self._queue.clear()
        return text
