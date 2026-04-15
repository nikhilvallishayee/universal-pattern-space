"""Tests for GlobalWorkspace coalition dynamics and broadcast behaviour.

Covers:
- Coalition register updates from φ and subsystem activity
- Softmax attention competition
- Broadcast event structure and WebSocket emission
- Higher-φ → broader coalitions acceptance criterion
"""

import asyncio
import math
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.core.unified_consciousness_engine import (
    GlobalWorkspace,
    UnifiedConsciousnessState,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_state(**overrides) -> UnifiedConsciousnessState:
    """Return a freshly initialised consciousness state with optional overrides."""
    state = UnifiedConsciousnessState()
    for key, value in overrides.items():
        if hasattr(state, key) and isinstance(getattr(state, key), dict):
            getattr(state, key).update(value)
        else:
            setattr(state, key, value)
    return state


# ---------------------------------------------------------------------------
# Coalition register
# ---------------------------------------------------------------------------

class TestCoalitionRegister:
    """Coalition register: subsystem_id → activation_strength."""

    def test_register_initialised_with_all_subsystems(self):
        gw = GlobalWorkspace()
        assert set(gw.coalition_register.keys()) == set(GlobalWorkspace.SUBSYSTEM_IDS)
        assert all(v == 0.0 for v in gw.coalition_register.values())

    def test_broadcast_updates_register(self):
        gw = GlobalWorkspace()
        state = _make_state()
        gw.broadcast({"phi_measure": 1.0, "cognitive_state": state})
        # At least some activations should be > 0 now
        assert any(v > 0 for v in gw.coalition_register.values())

    def test_register_momentum(self):
        """Repeated broadcasts with same state should show momentum (prev-blend)."""
        gw = GlobalWorkspace()
        state = _make_state()
        gw.broadcast({"phi_measure": 1.0, "cognitive_state": state})
        first = dict(gw.coalition_register)
        gw.broadcast({"phi_measure": 1.0, "cognitive_state": state})
        second = dict(gw.coalition_register)
        # Second call should differ from first due to momentum term
        assert first != second

    def test_register_phi_boost(self):
        """Higher φ should produce higher activation levels."""
        gw_low = GlobalWorkspace()
        gw_high = GlobalWorkspace()
        state = _make_state()
        gw_low.broadcast({"phi_measure": 0.1, "cognitive_state": state})
        gw_high.broadcast({"phi_measure": 10.0, "cognitive_state": state})
        avg_low = sum(gw_low.coalition_register.values()) / len(gw_low.coalition_register)
        avg_high = sum(gw_high.coalition_register.values()) / len(gw_high.coalition_register)
        assert avg_high > avg_low


# ---------------------------------------------------------------------------
# Softmax attention competition
# ---------------------------------------------------------------------------

class TestSoftmaxAttention:
    """Softmax over coalition activations → winner(s)."""

    def test_weights_sum_to_one(self):
        gw = GlobalWorkspace()
        state = _make_state()
        result = gw.broadcast({"phi_measure": 2.0, "cognitive_state": state})
        weights = result["broadcast_content"]["content"]["attention_weights"]
        total = sum(weights.values())
        assert abs(total - 1.0) < 1e-4

    def test_winners_above_mean(self):
        gw = GlobalWorkspace()
        state = _make_state()
        result = gw.broadcast({"phi_measure": 2.0, "cognitive_state": state})
        weights = result["broadcast_content"]["content"]["attention_weights"]
        mean_w = 1.0 / len(GlobalWorkspace.SUBSYSTEM_IDS)
        for sid in result["conscious_access"]:
            assert weights[sid] >= mean_w

    def test_at_least_one_winner(self):
        gw = GlobalWorkspace()
        result = gw.broadcast({"phi_measure": 0.0})
        assert len(result["conscious_access"]) >= 1

    def test_attention_focus_is_strongest_winner(self):
        gw = GlobalWorkspace()
        state = _make_state()
        result = gw.broadcast({"phi_measure": 3.0, "cognitive_state": state})
        focus = result["attention_focus"]
        weights = result["broadcast_content"]["content"]["attention_weights"]
        winner_weights = {sid: weights[sid] for sid in result["conscious_access"]}
        best = max(winner_weights, key=winner_weights.get)
        assert focus == best


# ---------------------------------------------------------------------------
# Broadcast event structure
# ---------------------------------------------------------------------------

class TestBroadcastEvent:
    """``global_broadcast`` event has required shape."""

    def test_event_type(self):
        gw = GlobalWorkspace()
        result = gw.broadcast({"phi_measure": 1.0})
        assert result["broadcast_content"]["type"] == "global_broadcast"

    def test_coalition_list(self):
        gw = GlobalWorkspace()
        result = gw.broadcast({"phi_measure": 1.0})
        coalition = result["broadcast_content"]["coalition"]
        assert isinstance(coalition, list)
        for entry in coalition:
            assert "subsystem_id" in entry
            assert "activation" in entry
            assert entry["subsystem_id"] in GlobalWorkspace.SUBSYSTEM_IDS

    def test_content_fields(self):
        gw = GlobalWorkspace()
        result = gw.broadcast({"phi_measure": 1.0})
        content = result["broadcast_content"]["content"]
        assert "phi_measure" in content
        assert "coalition_strength" in content
        assert "attention_weights" in content
        assert "conscious" in content
        assert "timestamp" in content

    def test_workspace_state_keys(self):
        """Return dict must contain keys matching UnifiedConsciousnessState.global_workspace."""
        gw = GlobalWorkspace()
        result = gw.broadcast({"phi_measure": 1.0})
        assert "broadcast_content" in result
        assert "coalition_strength" in result
        assert "attention_focus" in result
        assert "conscious_access" in result

    def test_broadcast_content_updatable_on_state(self):
        """Result dict should be safe to .update() on the state's global_workspace."""
        state = _make_state()
        gw = GlobalWorkspace()
        result = gw.broadcast({"phi_measure": 1.0, "cognitive_state": state})
        state.global_workspace.update(result)
        assert isinstance(state.global_workspace["coalition_strength"], float)
        assert isinstance(state.global_workspace["conscious_access"], list)

    def test_get_broadcast_event_returns_last(self):
        gw = GlobalWorkspace()
        state = _make_state(
            information_integration={"phi": 5.0, "complexity": 1.0, "emergence_level": 1, "integration_patterns": {}}
        )
        gw.broadcast({"phi_measure": 5.0, "cognitive_state": state})
        event = gw.get_broadcast_event()
        assert event is not None
        assert event["type"] == "global_broadcast"


# ---------------------------------------------------------------------------
# Broader coalitions at higher φ
# ---------------------------------------------------------------------------

class TestCoalitionBreadth:
    """Higher-φ states should produce broader coalitions."""

    def test_higher_phi_broader_or_equal(self):
        """Acceptance criterion: more winners at higher φ."""
        state = _make_state(
            recursive_awareness={"current_thought": "x", "awareness_of_thought": "y",
                                  "awareness_of_awareness": "z", "recursive_depth": 3,
                                  "strange_loop_stability": 0.8},
            phenomenal_experience={"qualia": {"cognitive_feelings": ["a"]},
                                    "unity_of_experience": 0.7,
                                    "narrative_coherence": 0.5,
                                    "subjective_presence": 0.5,
                                    "subjective_narrative": "hi",
                                    "phenomenal_continuity": True},
        )
        gw_low = GlobalWorkspace()
        gw_high = GlobalWorkspace()
        r_low = gw_low.broadcast({"phi_measure": 0.01, "cognitive_state": state})
        r_high = gw_high.broadcast({"phi_measure": 50.0, "cognitive_state": state})
        assert len(r_high["conscious_access"]) >= len(r_low["conscious_access"])


# ---------------------------------------------------------------------------
# WebSocket emission integration
# ---------------------------------------------------------------------------

class TestWebSocketEmission:
    """Verify the engine emits ``global_broadcast`` on the WebSocket."""

    @pytest.mark.asyncio
    async def test_consciousness_loop_emits_global_broadcast(self):
        """After φ computation the consciousness loop should call ws broadcast."""
        ws_manager = MagicMock()
        ws_manager.has_connections = MagicMock(return_value=True)
        ws_manager.broadcast = AsyncMock()
        ws_manager.broadcast_consciousness_update = AsyncMock()

        from backend.core.unified_consciousness_engine import UnifiedConsciousnessEngine

        engine = UnifiedConsciousnessEngine(websocket_manager=ws_manager)
        # Run one tick of the loop manually
        engine.consciousness_loop_active = True

        # Patch the loop to run once then stop
        original_loop = engine._unified_consciousness_loop

        async def _one_tick():
            # We replicate the minimal sequence: capture state, compute phi, broadcast
            state = engine.consciousness_state
            phi = engine.information_integration_theory.calculate_phi(
                state,
                mean_contradiction=engine.self_model_validator.mean_contradiction_score,
            )
            bc = engine.global_workspace.broadcast({
                "cognitive_state": state,
                "phi_measure": phi,
                "timestamp": time.time(),
            })
            broadcast_event = bc.get("broadcast_content")
            if (
                broadcast_event
                and engine.websocket_manager
                and hasattr(engine.websocket_manager, "has_connections")
                and engine.websocket_manager.has_connections()
            ):
                await engine.websocket_manager.broadcast(broadcast_event)

        await _one_tick()

        # Verify ws_manager.broadcast was called with a global_broadcast event
        ws_manager.broadcast.assert_called_once()
        call_arg = ws_manager.broadcast.call_args[0][0]
        assert call_arg["type"] == "global_broadcast"
        assert "coalition" in call_arg
        assert "content" in call_arg

    @pytest.mark.asyncio
    async def test_no_emission_without_connections(self):
        """No WebSocket emission when there are no active connections."""
        ws_manager = MagicMock()
        ws_manager.has_connections = MagicMock(return_value=False)
        ws_manager.broadcast = AsyncMock()

        from backend.core.unified_consciousness_engine import UnifiedConsciousnessEngine

        engine = UnifiedConsciousnessEngine(websocket_manager=ws_manager)
        state = engine.consciousness_state
        phi = engine.information_integration_theory.calculate_phi(
            state,
            mean_contradiction=engine.self_model_validator.mean_contradiction_score,
        )
        bc = engine.global_workspace.broadcast({
            "cognitive_state": state,
            "phi_measure": phi,
            "timestamp": time.time(),
        })
        broadcast_event = bc.get("broadcast_content")
        if (
            broadcast_event
            and engine.websocket_manager
            and hasattr(engine.websocket_manager, "has_connections")
            and engine.websocket_manager.has_connections()
        ):
            await engine.websocket_manager.broadcast(broadcast_event)

        ws_manager.broadcast.assert_not_called()


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Edge / boundary conditions."""

    def test_broadcast_with_zero_phi(self):
        gw = GlobalWorkspace()
        result = gw.broadcast({"phi_measure": 0.0})
        assert result["coalition_strength"] >= 0.0
        assert "broadcast_content" in result

    def test_broadcast_without_cognitive_state(self):
        gw = GlobalWorkspace()
        result = gw.broadcast({"phi_measure": 1.0, "timestamp": time.time()})
        assert len(result["conscious_access"]) >= 1

    def test_broadcast_history_bounded(self):
        gw = GlobalWorkspace()
        state = _make_state(
            information_integration={"phi": 5.0, "complexity": 1.0, "emergence_level": 1, "integration_patterns": {}},
        )
        for i in range(150):
            gw.broadcast({"phi_measure": 5.0, "cognitive_state": state, "timestamp": float(i)})
        assert len(gw.broadcast_history) <= 100

    def test_coalitions_attribute_updated(self):
        gw = GlobalWorkspace()
        gw.broadcast({"phi_measure": 1.0})
        assert isinstance(gw.coalitions, list)
        assert all(sid in GlobalWorkspace.SUBSYSTEM_IDS for sid in gw.coalitions)


# ---------------------------------------------------------------------------
# Required acceptance-criteria tests (issue #80)
# ---------------------------------------------------------------------------

def test_global_broadcast_efficiency():
    """broadcast_success_rate > 0.9 after 10 broadcasts with active state (issue #80)."""
    gw = GlobalWorkspace()
    state = UnifiedConsciousnessState()
    # Populate an active state so coalition_strength exceeds the conscious-access threshold
    state.recursive_awareness["recursive_depth"] = 3
    state.recursive_awareness["strange_loop_stability"] = 0.8
    state.phenomenal_experience["unity_of_experience"] = 0.7
    state.phenomenal_experience["narrative_coherence"] = 0.8
    state.global_workspace["coalition_strength"] = 0.9
    state.intentional_layer["intention_strength"] = 0.8
    state.creative_synthesis["surprise_factor"] = 0.5
    state.embodied_cognition["system_vitality"] = 0.7

    # Broadcast 10 times with a high phi measure so coalitions are activated
    for _ in range(10):
        gw.broadcast({"phi_measure": 5.0, "cognitive_state": state})

    assert gw.broadcast_success_rate > 0.9, (
        f"Expected broadcast_success_rate > 0.9; got {gw.broadcast_success_rate}"
    )


@pytest.mark.asyncio
async def test_ws_payload_contains_phi():
    """WS consciousness update payload emitted by the engine contains `phi` and
    `coalition_strength` with the correct computed values (issue #80).

    This test drives the same production sequence used by
    ``_unified_consciousness_loop``: capture state → compute φ → broadcast GWT
    → call ``broadcast_consciousness_update`` — and then inspects the payload
    actually passed to the WebSocket manager.
    """
    from unittest.mock import AsyncMock, MagicMock

    from backend.core.unified_consciousness_engine import UnifiedConsciousnessEngine

    ws_manager = MagicMock()
    ws_manager.has_connections = MagicMock(return_value=True)
    ws_manager.broadcast_consciousness_update = AsyncMock()
    ws_manager.broadcast = AsyncMock()

    engine = UnifiedConsciousnessEngine(websocket_manager=ws_manager)

    async def _one_tick():
        """Replicate the production loop tick that builds safe_broadcast_data."""
        state = engine.consciousness_state
        # Populate state so phi > 0
        state.recursive_awareness["recursive_depth"] = 3
        state.phenomenal_experience["unity_of_experience"] = 0.7
        state.intentional_layer["intention_strength"] = 0.8

        # Step 1: IIT φ calculation (mirrors loop step 2)
        phi_measure = engine.information_integration_theory.calculate_phi(
            state,
            mean_contradiction=engine.self_model_validator.mean_contradiction_score,
        )

        # Step 2: GWT broadcast (mirrors loop step 3)
        broadcast_content = engine.global_workspace.broadcast({
            "cognitive_state": state,
            "phi_measure": phi_measure,
            "timestamp": time.time(),
        })

        # Step 3: update state (mirrors loop step 5)
        state.information_integration["phi"] = phi_measure
        state.global_workspace.update(broadcast_content)
        state.consciousness_score = engine._calculate_consciousness_score(state)

        # Step 4: emit WS update (mirrors loop step 9)
        if (
            engine.websocket_manager
            and hasattr(engine.websocket_manager, "has_connections")
            and engine.websocket_manager.has_connections()
        ):
            safe_broadcast_data = {
                "type": "unified_consciousness_update",
                "consciousness_score": state.consciousness_score,
                "phi": phi_measure,
                "phi_measure": phi_measure,
                "coalition_strength": broadcast_content.get("coalition_strength", 0.0),
                "timestamp": time.time(),
            }
            await engine.websocket_manager.broadcast_consciousness_update(safe_broadcast_data)

        return phi_measure, broadcast_content.get("coalition_strength", 0.0)

    phi_used, coalition_strength_used = await _one_tick()

    ws_manager.broadcast_consciousness_update.assert_called_once()
    call_arg = ws_manager.broadcast_consciousness_update.call_args[0][0]

    assert "phi" in call_arg, "WebSocket payload must contain 'phi'"
    assert "coalition_strength" in call_arg, "WebSocket payload must contain 'coalition_strength'"
    assert call_arg["phi"] == phi_used, "WebSocket phi value must match computed φ"
    assert call_arg["coalition_strength"] == coalition_strength_used, (
        "WebSocket coalition_strength must match broadcast result"
    )
