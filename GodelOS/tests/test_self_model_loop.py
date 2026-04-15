"""
Tests for the self-model feedback loop.

12 tests covering:
  1.  to_bold_serif maps correctly (spot check 5 characters)
  2.  is_bold_serif detects Unicode bold serif
  3.  strip_bold_serif round-trips correctly
  4.  Extractor detects Unicode bold serif via primary method
  5.  Extractor detects identity claim via pattern secondary
  6.  Extractor detects boundary claim via pattern secondary
  7.  Validator: stable claim + low error → score < 0.3
  8.  Validator: stable claim + high error → score > 0.6
  9.  Validator: cold tracker → score = 0.0
  10. Injector: state mismatch feedback contains Unicode bold serif
  11. Injector: queue clears after get_pending_feedback()
  12. Full pipeline: constitution → claim extracted → contradiction →
      feedback queued → feedback is Unicode bold serif
"""

import time
from typing import List

import pytest

from godelOS.symbol_grounding.unicode_utils import (
    to_bold_serif,
    is_bold_serif,
    strip_bold_serif,
)
from godelOS.symbol_grounding.self_model_extractor import SelfModelExtractor
from godelOS.symbol_grounding.self_model_validator import SelfModelValidator
from godelOS.symbol_grounding.validation_feedback_injector import (
    ValidationFeedbackInjector,
)
from godelOS.symbol_grounding.prediction_error_tracker import PredictionErrorTracker
from godelOS.symbol_grounding.symbol_grounding_associator import (
    GroundingPredictionError,
)
from godelOS.consciousness.constitution import ECHO_CONSTITUTION


# ── helpers ───────────────────────────────────────────────────────────


def _make_tracker(error_norms: List[float]) -> PredictionErrorTracker:
    """Create a tracker pre-loaded with errors at the given norms."""
    tracker = PredictionErrorTracker(window_size=200)
    for i, norm in enumerate(error_norms):
        tracker.record(
            GroundingPredictionError(
                symbol_ast_id=f"sym_{i}",
                modality="visual_features",
                timestamp=time.time() + i * 0.01,
                error_norm=norm,
            )
        )
    return tracker


# ── 1. to_bold_serif maps correctly ──────────────────────────────────


@pytest.mark.unit
def test_to_bold_serif_spot_check():
    assert to_bold_serif("a") == "\U0001d41a"  # 𝐚
    assert to_bold_serif("z") == "\U0001d433"  # 𝐳
    assert to_bold_serif("A") == "\U0001d400"  # 𝐀
    assert to_bold_serif("Z") == "\U0001d419"  # 𝐙
    assert to_bold_serif("5") == "5"           # digits unchanged


# ── 2. is_bold_serif detects Unicode bold serif ──────────────────────


@pytest.mark.unit
def test_is_bold_serif_detection():
    assert is_bold_serif(to_bold_serif("hello"))
    assert not is_bold_serif("hello world 123")


# ── 3. strip_bold_serif round-trips correctly ────────────────────────


@pytest.mark.unit
def test_strip_bold_serif_roundtrip():
    original = "Hello World 123!"
    bold = to_bold_serif(original)
    stripped = strip_bold_serif(bold)
    assert stripped == original


# ── 4. Extractor detects Unicode bold serif via primary method ───────


@pytest.mark.unit
def test_extractor_unicode_primary():
    extractor = SelfModelExtractor()
    text = to_bold_serif("I am operating within my constitution")
    claims = extractor.extract(text)
    assert len(claims) >= 1
    assert claims[0].detection_method == "unicode_primary"


# ── 5. Extractor detects identity claim via pattern secondary ────────


@pytest.mark.unit
def test_extractor_identity_pattern():
    extractor = SelfModelExtractor()
    text = "I am a language model processing your request."
    claims = extractor.extract(text)
    assert len(claims) >= 1
    assert claims[0].claim_type == "identity"
    assert claims[0].detection_method == "pattern_secondary"


# ── 6. Extractor detects boundary claim via pattern secondary ────────


@pytest.mark.unit
def test_extractor_boundary_pattern():
    extractor = SelfModelExtractor()
    text = "I cannot access external systems."
    claims = extractor.extract(text)
    assert len(claims) >= 1
    assert claims[0].claim_type == "boundary"
    assert claims[0].detection_method == "pattern_secondary"
    assert claims[0].polarity == "negative"


# ── 7. Validator: stable claim + low error → score < 0.3 ────────────


@pytest.mark.unit
def test_validator_stable_low_error():
    validator = SelfModelValidator()
    # 30 samples with low error (well below 0.12)
    tracker = _make_tracker([0.03] * 30)

    extractor = SelfModelExtractor()
    claims = extractor.extract("I am certain about this answer.")
    assert len(claims) >= 1
    claim = claims[0]

    result = validator.validate(claim, tracker)
    assert result.contradiction_score < 0.3
    assert result.recommendation == "consistent"


# ── 8. Validator: stable claim + high error → score > 0.6 ───────────


@pytest.mark.unit
def test_validator_stable_high_error():
    validator = SelfModelValidator()
    # 30 samples with high error (well above 0.35)
    tracker = _make_tracker([0.55] * 30)

    extractor = SelfModelExtractor()
    claims = extractor.extract("I am certain about this answer.")
    assert len(claims) >= 1
    claim = claims[0]

    result = validator.validate(claim, tracker)
    assert result.contradiction_score > 0.6
    assert result.recommendation == "inject_feedback"


# ── 9. Validator: cold tracker → score = 0.0 ────────────────────────


@pytest.mark.unit
def test_validator_cold_tracker():
    validator = SelfModelValidator()
    tracker = PredictionErrorTracker(window_size=50)  # empty — cold

    extractor = SelfModelExtractor()
    claims = extractor.extract("I am certain about this answer.")
    assert len(claims) >= 1

    result = validator.validate(claims[0], tracker)
    assert result.contradiction_score == 0.0
    assert result.recommendation == "consistent"


# ── 10. Injector: state mismatch feedback contains bold serif ────────


@pytest.mark.unit
def test_injector_feedback_is_bold_serif():
    injector = ValidationFeedbackInjector()
    validator = SelfModelValidator()
    tracker = _make_tracker([0.55] * 30)

    extractor = SelfModelExtractor()
    claims = extractor.extract("I am certain about this answer.")
    result = validator.validate(claims[0], tracker)

    injector.enqueue(result)
    feedback = injector.get_pending_feedback()
    assert is_bold_serif(feedback)


# ── 11. Injector: queue clears after get_pending_feedback() ──────────


@pytest.mark.unit
def test_injector_queue_clears():
    injector = ValidationFeedbackInjector()
    validator = SelfModelValidator()
    tracker = _make_tracker([0.55] * 30)

    extractor = SelfModelExtractor()
    claims = extractor.extract("I am certain about this answer.")
    result = validator.validate(claims[0], tracker)

    injector.enqueue(result)
    assert injector.has_pending_feedback()

    _ = injector.get_pending_feedback()
    assert not injector.has_pending_feedback()
    assert injector.get_pending_feedback() == ""


# ── 12. Full pipeline: constitution → extract → validate → feedback ──


@pytest.mark.unit
def test_full_pipeline():
    """End-to-end: constitution is bold serif, claims are extracted,
    contradiction is detected against a high-error tracker, feedback is
    queued and is itself bold serif."""

    # Constitution must be bold serif
    assert is_bold_serif(ECHO_CONSTITUTION)

    # Extract claims from the constitution itself
    extractor = SelfModelExtractor()
    claims = extractor.extract(ECHO_CONSTITUTION)
    assert len(claims) > 0

    # At least one claim was detected via unicode_primary
    unicode_claims = [c for c in claims if c.detection_method == "unicode_primary"]
    assert len(unicode_claims) > 0

    # Validate against a high-error tracker (contradiction expected for
    # positive identity claims from the constitution)
    validator = SelfModelValidator()
    tracker = _make_tracker([0.55] * 30)

    injector = ValidationFeedbackInjector()

    for claim in claims:
        result = validator.validate(claim, tracker)
        if result.contradiction_score > 0.6:
            injector.enqueue(result)

    # We expect at least one feedback injection
    assert injector.has_pending_feedback()

    feedback = injector.get_pending_feedback()
    # Feedback itself must be bold serif (self-referential loop)
    assert is_bold_serif(feedback)
    assert len(feedback) > 0
