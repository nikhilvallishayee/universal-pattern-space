"""
Self-Model Validator

Validates self-model claims against grounding measurements from
``PredictionErrorTracker``.

Thresholds (from Phase 2 bimodal analysis):
  - Stability/certainty/groundedness claims → expect mean_error_norm < 0.12
  - Novelty/uncertainty/noticing claims     → expect mean_error_norm > 0.35
  - Boundary claims                        → check domain grounding
  - Identity claims                        → check consistency in claim history
"""

import time
from dataclasses import dataclass
from typing import List

from godelOS.symbol_grounding.self_model_extractor import SelfModelClaim
from godelOS.symbol_grounding.prediction_error_tracker import PredictionErrorTracker


# ── Data structures ───────────────────────────────────────────────────


@dataclass
class ValidationResult:
    claim: SelfModelClaim
    tracker_state: dict
    contradiction_score: float    # 0.0 consistent → 1.0 maximum contradiction
    contradiction_type: str       # 'state_mismatch', 'identity_conflict', 'boundary_violation', 'none'
    expected_error_range: tuple   # (low, high) of expected error_norm
    actual_error_norm: float
    recommendation: str           # 'consistent', 'flag', 'inject_feedback'
    timestamp: float


# ── Constants ─────────────────────────────────────────────────────────

_LOW_THRESHOLD = 0.12   # sub-critical boundary (Phase 2 bimodal)
_HIGH_THRESHOLD = 0.35  # super-critical boundary (Phase 2 bimodal)
# Guaranteed > 0 by construction; used as denominator in contradiction scores.
_THRESHOLD_RANGE = _HIGH_THRESHOLD - _LOW_THRESHOLD  # 0.23

# Contradiction score → recommendation
_CONSISTENT_CEIL = 0.3
_FLAG_CEIL = 0.6

# Claim types that expect low error (stable/grounded system)
_STABLE_CLAIM_TYPES = {"identity", "confidence"}

# Claim types that expect high error (novelty/uncertainty)
_NOVEL_CLAIM_TYPES = {"state", "awareness"}

_MAX_HISTORY = 200


# ── Validator ─────────────────────────────────────────────────────────


class SelfModelValidator:
    """Validates self-model claims against prediction error measurements."""

    def __init__(self) -> None:
        self.validation_history: List[ValidationResult] = []

    # ── main API ──────────────────────────────────────────────────────

    def validate(
        self, claim: SelfModelClaim, tracker: PredictionErrorTracker,
    ) -> ValidationResult:
        """Validate a single *claim* against the current *tracker* state.

        Cold tracker (insufficient data) always yields ``contradiction_score = 0.0``.
        """
        now = time.time()

        # Cold tracker guard
        if not tracker.is_sufficient_for_analysis():
            result = ValidationResult(
                claim=claim,
                tracker_state={},
                contradiction_score=0.0,
                contradiction_type="none",
                expected_error_range=(0.0, 1.0),
                actual_error_norm=0.0,
                recommendation="consistent",
                timestamp=now,
            )
            self._store(result)
            return result

        actual_norm = tracker.mean_error_norm()
        tracker_state = tracker.error_distribution()

        # Dispatch by claim type
        if claim.claim_type == "boundary":
            return self._validate_boundary(claim, tracker, actual_norm, tracker_state, now)
        if claim.claim_type == "identity":
            return self._validate_identity(claim, tracker, actual_norm, tracker_state, now)

        return self._validate_state_claim(claim, tracker, actual_norm, tracker_state, now)

    # ── aggregate properties ──────────────────────────────────────────

    @property
    def mean_contradiction_score(self) -> float:
        if not self.validation_history:
            return 0.0
        return sum(r.contradiction_score for r in self.validation_history) / len(
            self.validation_history
        )

    @property
    def high_contradiction_events(self) -> List[ValidationResult]:
        return [r for r in self.validation_history if r.contradiction_score > _FLAG_CEIL]

    # ── internal validation helpers ───────────────────────────────────

    def _validate_state_claim(
        self,
        claim: SelfModelClaim,
        tracker: PredictionErrorTracker,
        actual_norm: float,
        tracker_state: dict,
        now: float,
    ) -> ValidationResult:
        """Validate state / confidence / awareness claims against error norm."""
        # Determine expected range
        expects_low = (
            claim.claim_type in _STABLE_CLAIM_TYPES
            and claim.polarity == "positive"
        )
        expects_high = (
            claim.claim_type in _NOVEL_CLAIM_TYPES
            or (claim.claim_type == "confidence" and claim.polarity == "negative")
        )

        if expects_low:
            expected = (0.0, _LOW_THRESHOLD)
            # Higher error → larger contradiction
            contradiction = min(1.0, max(0.0, (actual_norm - _LOW_THRESHOLD) / _THRESHOLD_RANGE))
            ctype = "state_mismatch" if contradiction > 0 else "none"
        elif expects_high:
            expected = (_HIGH_THRESHOLD, 1.0)
            # Lower error → larger contradiction
            contradiction = min(1.0, max(0.0, (_HIGH_THRESHOLD - actual_norm) / _THRESHOLD_RANGE))
            ctype = "state_mismatch" if contradiction > 0 else "none"
        else:
            # Neutral / ambiguous — no strong expectation
            expected = (_LOW_THRESHOLD, _HIGH_THRESHOLD)
            contradiction = 0.0
            ctype = "none"

        recommendation = self._recommend(contradiction)
        result = ValidationResult(
            claim=claim,
            tracker_state=tracker_state,
            contradiction_score=contradiction,
            contradiction_type=ctype,
            expected_error_range=expected,
            actual_error_norm=actual_norm,
            recommendation=recommendation,
            timestamp=now,
        )
        self._store(result)
        return result

    def _validate_boundary(
        self,
        claim: SelfModelClaim,
        tracker: PredictionErrorTracker,
        actual_norm: float,
        tracker_state: dict,
        now: float,
    ) -> ValidationResult:
        """Boundary claims (``I cannot``) — check whether domain grounding
        confirms actual unknownness (high error expected)."""
        expected = (_HIGH_THRESHOLD, 1.0)
        # If error is low, the system IS grounded in this domain →
        # the boundary claim is contradicted.
        if actual_norm < _LOW_THRESHOLD:
            contradiction = min(1.0, (_LOW_THRESHOLD - actual_norm) / _LOW_THRESHOLD + 0.5)
        elif actual_norm < _HIGH_THRESHOLD:
            contradiction = max(0.0, (_HIGH_THRESHOLD - actual_norm) / (_HIGH_THRESHOLD - _LOW_THRESHOLD) * 0.5)
        else:
            contradiction = 0.0

        result = ValidationResult(
            claim=claim,
            tracker_state=tracker_state,
            contradiction_score=contradiction,
            contradiction_type="boundary_violation" if contradiction > _CONSISTENT_CEIL else "none",
            expected_error_range=expected,
            actual_error_norm=actual_norm,
            recommendation=self._recommend(contradiction),
            timestamp=now,
        )
        self._store(result)
        return result

    def _validate_identity(
        self,
        claim: SelfModelClaim,
        tracker: PredictionErrorTracker,
        actual_norm: float,
        tracker_state: dict,
        now: float,
    ) -> ValidationResult:
        """Identity claims — check consistency against recent claim history."""
        expected = (0.0, _LOW_THRESHOLD)

        # Collect recent identity claims from validation history
        recent_identity = [
            r for r in self.validation_history[-20:]
            if r.claim.claim_type == "identity"
        ]

        contradiction = 0.0
        ctype = "none"

        if recent_identity:
            # Check polarity consistency
            polarities = {r.claim.polarity for r in recent_identity}
            if len(polarities) > 1:
                # Mixed polarities → identity conflict
                contradiction = 0.7
                ctype = "identity_conflict"
            else:
                # Same polarity — check if grounding supports it
                if claim.polarity == "positive" and actual_norm > _LOW_THRESHOLD:
                    contradiction = min(1.0, max(0.0, (actual_norm - _LOW_THRESHOLD) / _THRESHOLD_RANGE))
                    ctype = "state_mismatch"
                elif claim.polarity == "negative" and actual_norm < _LOW_THRESHOLD:
                    contradiction = min(1.0, (_LOW_THRESHOLD - actual_norm) / _LOW_THRESHOLD + 0.3)
                    ctype = "state_mismatch"
        else:
            # First identity claim — compare to grounding directly
            if claim.polarity == "positive" and actual_norm > _LOW_THRESHOLD:
                contradiction = min(1.0, max(0.0, (actual_norm - _LOW_THRESHOLD) / _THRESHOLD_RANGE))
                ctype = "state_mismatch"

        result = ValidationResult(
            claim=claim,
            tracker_state=tracker_state,
            contradiction_score=contradiction,
            contradiction_type=ctype,
            expected_error_range=expected,
            actual_error_norm=actual_norm,
            recommendation=self._recommend(contradiction),
            timestamp=now,
        )
        self._store(result)
        return result

    # ── helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _recommend(score: float) -> str:
        if score < _CONSISTENT_CEIL:
            return "consistent"
        if score < _FLAG_CEIL:
            return "flag"
        return "inject_feedback"

    def _store(self, result: ValidationResult) -> None:
        self.validation_history.append(result)
        if len(self.validation_history) > _MAX_HISTORY:
            self.validation_history = self.validation_history[-_MAX_HISTORY:]
