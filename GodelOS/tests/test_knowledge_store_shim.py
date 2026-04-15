"""
Tests for ``KnowledgeStoreShim`` — the transparent wrapper that feeds
``PredictionErrorTracker`` with real symbol activation data.
"""

import logging
from unittest.mock import MagicMock, patch

import pytest

from godelOS.core_kr.ast.nodes import ApplicationNode, ConstantNode
from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface
from godelOS.core_kr.type_system.manager import TypeSystemManager
from godelOS.symbol_grounding.knowledge_store_shim import KnowledgeStoreShim
from godelOS.symbol_grounding.prediction_error_tracker import PredictionErrorTracker
from godelOS.symbol_grounding.symbol_grounding_associator import (
    GroundingLink,
    GroundingPredictionError,
    SymbolGroundingAssociator,
)


# ── helpers ────────────────────────────────────────────────────────────

def _make_stack():
    """Return (shim, base_ks, grounder, tracker) wired together."""
    kr = MagicMock(spec=KnowledgeStoreInterface)
    kr.list_contexts.return_value = []
    ts = MagicMock(spec=TypeSystemManager)
    ts.get_type.return_value = MagicMock()
    grounder = SymbolGroundingAssociator(kr_system_interface=kr, type_system=ts)
    tracker = PredictionErrorTracker(window_size=100)
    shim = KnowledgeStoreShim(base=kr, grounder=grounder, tracker=tracker)
    return shim, kr, grounder, tracker


def _make_constant_statement(name: str = "Red"):
    """Create a simple ConstantNode statement for testing."""
    mock_type = MagicMock()
    return ConstantNode(name=name, type_ref=mock_type)


def _make_application_statement(predicate_name: str = "HasColor"):
    """Create a simple ApplicationNode statement for testing."""
    mock_type = MagicMock()
    operator = ConstantNode(name=predicate_name, type_ref=mock_type)
    arg = ConstantNode(name="obj_1", type_ref=mock_type)
    return ApplicationNode(operator=operator, arguments=[arg], type_ref=mock_type)


# ── Test 1: Delegation ────────────────────────────────────────────────

def test_delegates_non_intercepted_methods():
    """Calling any method other than add_statement reaches the base KS."""
    shim, base_ks, _, _ = _make_stack()

    # Arbitrary method that KnowledgeStoreInterface has
    base_ks.retract_statement.return_value = True
    result = shim.retract_statement("pattern", "TRUTHS")
    base_ks.retract_statement.assert_called_once_with("pattern", "TRUTHS")
    assert result is True

    # Another arbitrary method
    base_ks.query_statements_match_pattern.return_value = [{"x": "y"}]
    result = shim.query_statements_match_pattern("pat", ["TRUTHS"])
    base_ks.query_statements_match_pattern.assert_called_once_with("pat", ["TRUTHS"])
    assert result == [{"x": "y"}]


# ── Test 2: Cold start (no observation context) ──────────────────────

def test_cold_start_no_context():
    """add_statement with no observation context produces no tracker records."""
    shim, base_ks, _, tracker = _make_stack()
    base_ks.add_statement.return_value = True
    stmt = _make_constant_statement("Red")

    result = shim.add_statement(stmt, "TRUTHS")

    assert result is True
    assert len(tracker._errors) == 0
    assert shim.measurement_stats["skipped_no_context"] == 1


# ── Test 3: No grounding link (cold start for symbol) ────────────────

def test_no_grounding_link():
    """Observation context set but symbol has no learned grounding."""
    shim, base_ks, _, tracker = _make_stack()
    base_ks.add_statement.return_value = True
    stmt = _make_constant_statement("UnknownSymbol")

    shim.set_observation_context({"brightness": 0.5}, modality="visual_features")
    result = shim.add_statement(stmt, "TRUTHS")

    assert result is True
    assert len(tracker._errors) == 0
    assert shim.measurement_stats["skipped_cold_start"] == 1


# ── Test 4: After learning, activation produces tracker record ────────

def test_learned_grounding_produces_record():
    """After learning groundings, add_statement with context records an error."""
    shim, base_ks, grounder, tracker = _make_stack()
    base_ks.add_statement.return_value = True

    sym_id = "Red"

    # Inject a grounding link (learned prototype)
    link = GroundingLink(
        symbol_ast_id=sym_id,
        sub_symbolic_representation={"brightness": 0.8, "sharpness": 0.3},
        modality="visual_features",
        confidence=0.9,
    )
    grounder.grounding_links[sym_id] = [link]

    # Set observation context with novel features
    shim.set_observation_context(
        {"brightness": 0.4, "sharpness": 0.7}, modality="visual_features"
    )

    stmt = _make_constant_statement(sym_id)
    result = shim.add_statement(stmt, "TRUTHS")

    assert result is True
    assert len(tracker._errors) == 1
    assert tracker.mean_error_norm() > 0
    assert shim.measurement_stats["measurements_recorded"] == 1


# ── Test 5: Measurement failure never breaks insertion ────────────────

def test_measurement_failure_does_not_break_insertion():
    """Even if the grounder raises, add_statement still succeeds."""
    shim, base_ks, grounder, tracker = _make_stack()
    base_ks.add_statement.return_value = True

    # Monkey-patch grounder to raise
    grounder.measure_prediction_error_at_activation = MagicMock(
        side_effect=RuntimeError("boom")
    )

    shim.set_observation_context({"brightness": 0.5})
    stmt = _make_constant_statement("Red")

    # Must not raise
    result = shim.add_statement(stmt, "TRUTHS")
    assert result is True
    assert len(tracker._errors) == 0


# ── Test 6: measurement_stats tracks correctly ────────────────────────

def test_measurement_stats_tracking():
    """Mixed sequence of insertions tracks all stat categories correctly."""
    shim, base_ks, grounder, tracker = _make_stack()
    base_ks.add_statement.return_value = True

    sym_id = "Blue"
    link = GroundingLink(
        symbol_ast_id=sym_id,
        sub_symbolic_representation={"brightness": 0.2, "sharpness": 0.5},
        modality="visual_features",
        confidence=0.9,
    )
    grounder.grounding_links[sym_id] = [link]

    # 1) No context → skipped_no_context
    shim.add_statement(_make_constant_statement(sym_id), "TRUTHS")

    # 2) Context + known symbol → measurement_recorded
    shim.set_observation_context({"brightness": 0.6, "sharpness": 0.1})
    shim.add_statement(_make_constant_statement(sym_id), "TRUTHS")

    # 3) Context + unknown symbol → skipped_cold_start
    shim.add_statement(_make_constant_statement("UnknownSym"), "TRUTHS")

    # 4) Context + ApplicationNode with known predicate
    link2 = GroundingLink(
        symbol_ast_id="HasColor",
        sub_symbolic_representation={"brightness": 0.5, "sharpness": 0.3},
        modality="visual_features",
        confidence=0.9,
    )
    grounder.grounding_links["HasColor"] = [link2]
    shim.add_statement(_make_application_statement("HasColor"), "TRUTHS")

    # 5) Clear context then add → skipped_no_context
    shim.clear_observation_context()
    shim.add_statement(_make_constant_statement(sym_id), "TRUTHS")

    stats = shim.measurement_stats
    assert stats["skipped_no_context"] == 2      # steps 1 and 5
    assert stats["skipped_cold_start"] == 1       # step 3
    assert stats["measurements_recorded"] == 2    # steps 2 and 4
    assert len(tracker._errors) == 2
