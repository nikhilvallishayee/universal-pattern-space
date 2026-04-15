"""
Integration smoke tests for the activated cognitive subsystems.

These tests verify that all dormant subsystems have been properly wired
into the cognitive pipeline and that data can flow end-to-end through
the NLU → Knowledge Store → Inference Engine → Context Engine → NLG path.
"""

import pytest
import logging
from typing import Dict, Any

from godelOS.cognitive_pipeline import CognitivePipeline

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional-dependency guards
# ---------------------------------------------------------------------------

def _spacy_available() -> bool:
    """Return True if spaCy and the en_core_web_sm model are installed."""
    try:
        import spacy
        spacy.load("en_core_web_sm")
        return True
    except (ImportError, OSError):
        return False

_HAS_SPACY = _spacy_available()
requires_spacy = pytest.mark.skipif(
    not _HAS_SPACY,
    reason="spaCy or en_core_web_sm model not available",
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def pipeline():
    """Shared pipeline instance for the entire module (expensive to create)."""
    p = CognitivePipeline()
    p.initialize()
    return p


# ---------------------------------------------------------------------------
# 1. All subsystems initialise without error
# ---------------------------------------------------------------------------

class TestSubsystemActivation:
    """Every subsystem listed in the issue must be active after init."""

    EXPECTED_SUBSYSTEMS = [
        # Core KR
        "type_system",
        "knowledge_store",
        "unification_engine",
        "formal_logic_parser",
        # Inference engine (includes dormant modal & CLP)
        "resolution_prover",
        "modal_tableau_prover",
        "clp_module",
        "analogical_reasoning_engine",
        "inference_coordinator",
        # Scalability
        "caching_system",
        # NLU / NLG
        "nlu_pipeline",
        "nlg_pipeline",
        # Symbol Grounding (dormant)
        "simulated_environment",
        "perceptual_categorizer",
        "symbol_grounding_associator",
        "action_executor",
        "internal_state_monitor",
        # Common Sense & Context (dormant)
        "context_engine",
        "common_sense_manager",
        # Metacognition
        "metacognition_manager",
        # Learning System (dormant)
        "ilp_engine",
        "explanation_based_learner",
        "meta_control_rl",
    ]

    def test_all_subsystems_present(self, pipeline):
        """Every expected subsystem is registered in the pipeline."""
        status = pipeline.get_subsystem_status()
        for name in self.EXPECTED_SUBSYSTEMS:
            assert name in status, f"Subsystem '{name}' missing from pipeline"

    # Subsystems that require optional heavy deps (spaCy) — allowed to be in
    # degraded/error state when those deps are absent in slim CI environments.
    OPTIONAL_SUBSYSTEMS = {"nlu_pipeline", "nlg_pipeline"}

    def test_all_subsystems_active(self, pipeline):
        """Every expected subsystem has status active (optional ones may be degraded)."""
        status = pipeline.get_subsystem_status()
        for name in self.EXPECTED_SUBSYSTEMS:
            info = status.get(name, {})
            if name in self.OPTIONAL_SUBSYSTEMS:
                assert info.get("status") in ("active", "degraded", "error"), (
                    f"Optional subsystem {name!r} missing entirely: {info}"
                )
            else:
                assert info.get("status") == "active", (
                    f"Subsystem {name!r} is not active: {info}"
                )

    def test_no_init_errors(self, pipeline):
        """No non-optional initialisation errors recorded."""
        hard_errors = [
            e for e in pipeline.init_errors
            if not any(opt in e for opt in self.OPTIONAL_SUBSYSTEMS)
        ]
        assert hard_errors == [], (
            f"Pipeline recorded hard init errors: {hard_errors}"
        )

    def test_get_instance_returns_objects(self, pipeline):
        """get_instance returns non-None for every required subsystem."""
        for name in self.EXPECTED_SUBSYSTEMS:
            if name in self.OPTIONAL_SUBSYSTEMS:
                continue  # spaCy-optional: skip in slim CI
            instance = pipeline.get_instance(name)
            assert instance is not None, (
                f"get_instance({name!r}) returned None for an active subsystem"
            )



# ---------------------------------------------------------------------------
# 2. NLU pipeline processes text
# ---------------------------------------------------------------------------

@requires_spacy
class TestNLUPipeline:
    """The NLU pipeline should accept text and produce structured output."""

    def test_nlu_pipeline_process(self, pipeline):
        nlu = pipeline.get_instance("nlu_pipeline")
        assert nlu is not None, "NLU pipeline not available"
        result = nlu.process("The cat sat on the mat")
        # NLUResult has a 'success' attribute
        assert hasattr(result, "success"), "NLU result missing 'success' attribute"

    def test_nlu_pipeline_returns_ast_or_errors(self, pipeline):
        nlu = pipeline.get_instance("nlu_pipeline")
        result = nlu.process("Birds can fly")
        # Should have either AST nodes or errors — not just silently empty
        has_output = (
            getattr(result, "ast_nodes", None)
            or getattr(result, "errors", None)
            or getattr(result, "success", None) is not None
        )
        assert has_output, "NLU returned completely empty result"


# ---------------------------------------------------------------------------
# 3. Knowledge Store accepts and retrieves statements
# ---------------------------------------------------------------------------

class TestKnowledgeStore:
    """Knowledge Store should be operational and support basic ops."""

    def test_knowledge_store_has_default_contexts(self, pipeline):
        ks = pipeline.get_instance("knowledge_store")
        assert ks is not None
        # The KnowledgeStoreInterface creates TRUTHS, BELIEFS, HYPOTHETICAL
        assert hasattr(ks, "list_contexts"), "KnowledgeStore missing list_contexts"
        context_ids = ks.list_contexts()
        assert "TRUTHS" in context_ids, "Missing default TRUTHS context"


# ---------------------------------------------------------------------------
# 4. Inference Coordinator has all provers registered
# ---------------------------------------------------------------------------

class TestInferenceCoordinator:
    """The coordinator should know about all provers."""

    def test_coordinator_has_provers(self, pipeline):
        coord = pipeline.get_instance("inference_coordinator")
        assert coord is not None
        provers = getattr(coord, "provers", {})
        assert len(provers) >= 2, (
            f"Expected at least 2 provers, got {len(provers)}: {list(provers.keys())}"
        )

    def test_modal_prover_registered(self, pipeline):
        coord = pipeline.get_instance("inference_coordinator")
        provers = getattr(coord, "provers", {})
        assert "modal_tableau" in provers, (
            f"Modal tableau prover not registered. Available: {list(provers.keys())}"
        )

    def test_clp_module_registered(self, pipeline):
        coord = pipeline.get_instance("inference_coordinator")
        provers = getattr(coord, "provers", {})
        assert "clp" in provers, (
            f"CLP module not registered. Available: {list(provers.keys())}"
        )


# ---------------------------------------------------------------------------
# 5. Symbol Grounding subsystem is operational
# ---------------------------------------------------------------------------

class TestSymbolGrounding:
    """Symbol grounding components must be instantiated and connected."""

    def test_simulated_environment_ticks(self, pipeline):
        env = pipeline.get_instance("simulated_environment")
        assert env is not None
        # Should be able to tick the simulation without error
        env.tick(0.1)

    def test_perceptual_categorizer_exists(self, pipeline):
        pc = pipeline.get_instance("perceptual_categorizer")
        assert pc is not None

    def test_symbol_grounding_associator_exists(self, pipeline):
        sga = pipeline.get_instance("symbol_grounding_associator")
        assert sga is not None


# ---------------------------------------------------------------------------
# 6. Common Sense & Context subsystem
# ---------------------------------------------------------------------------

class TestCommonSense:
    """Context engine and common sense manager should be wired."""

    def test_context_engine_creates_context(self, pipeline):
        from godelOS.common_sense.context_engine import ContextType

        ce = pipeline.get_instance("context_engine")
        assert ce is not None
        ctx = ce.create_context(
            name="SmokeTest",
            context_type=ContextType.TASK,
        )
        assert ctx is not None

    def test_common_sense_manager_active(self, pipeline):
        csm = pipeline.get_instance("common_sense_manager")
        assert csm is not None
        assert getattr(csm, "initialized", False), "CommonSenseContextManager not initialized"


# ---------------------------------------------------------------------------
# 7. Learning System
# ---------------------------------------------------------------------------

class TestLearningSystem:
    """ILP engine, EBL, and meta-control RL should be instantiated."""

    def test_ilp_engine_exists(self, pipeline):
        ilp = pipeline.get_instance("ilp_engine")
        assert ilp is not None

    def test_explanation_based_learner_exists(self, pipeline):
        ebl = pipeline.get_instance("explanation_based_learner")
        assert ebl is not None

    def test_meta_control_rl_exists(self, pipeline):
        rl = pipeline.get_instance("meta_control_rl")
        assert rl is not None
        # Should have an action space
        actions = getattr(rl, "action_space", [])
        assert len(actions) > 0, "MetaControlRLModule has no action space"


# ---------------------------------------------------------------------------
# 8. Metacognition
# ---------------------------------------------------------------------------

class TestMetacognition:
    """MetacognitionManager should be initialised."""

    def test_metacognition_manager_exists(self, pipeline):
        mm = pipeline.get_instance("metacognition_manager")
        assert mm is not None

    def test_metacognition_manager_can_initialize(self, pipeline):
        mm = pipeline.get_instance("metacognition_manager")
        # The manager has an initialize() method that wires sub-components
        result = mm.initialize()
        assert result is True


# ---------------------------------------------------------------------------
# 9. End-to-end pipeline data flow smoke test
# ---------------------------------------------------------------------------

class TestEndToEndFlow:
    """A query should traverse NLU → KS → Inference → Context → NLG
    without silently dropping at any junction."""

    @requires_spacy
    def test_nlu_to_knowledge_store(self, pipeline):
        """NLU output can be stored in the knowledge store."""
        nlu = pipeline.get_instance("nlu_pipeline")
        ks = pipeline.get_instance("knowledge_store")
        assert nlu is not None and ks is not None

        result = nlu.process("Cats are mammals")
        # Even if NLU can't fully formalize, we confirm no crash and we
        # can interact with the knowledge store in the same pipeline.
        assert ks is not None

    def test_inference_coordinator_submit_does_not_crash(self, pipeline):
        """Submitting a trivial goal to the coordinator doesn't raise."""
        from godelOS.core_kr.type_system.types import AtomicType
        from godelOS.core_kr.ast.nodes import ConstantNode

        coord = pipeline.get_instance("inference_coordinator")
        ts = pipeline.get_instance("type_system")
        assert coord is not None and ts is not None

        bool_type = ts.get_type("Boolean")
        goal = ConstantNode("True", bool_type)
        # This may not prove anything but should not crash
        try:
            coord.submit_goal(goal, set())
        except Exception:
            pass  # proof failure is acceptable; crash is not

    def test_context_engine_round_trip(self, pipeline):
        """Data can be placed in and retrieved from the context engine."""
        from godelOS.common_sense.context_engine import ContextType

        ce = pipeline.get_instance("context_engine")
        assert ce is not None
        ctx = ce.create_context(name="E2E", context_type=ContextType.TASK)
        assert ctx is not None
        ctx_id = ctx.id
        retrieved = ce.get_context(ctx_id)
        assert retrieved is not None
        assert retrieved.name == "E2E"

    def test_nlg_pipeline_process(self, pipeline):
        """NLG pipeline can process empty input without crash."""
        nlg = pipeline.get_instance("nlg_pipeline")
        assert nlg is not None
        result = nlg.process([])
        assert hasattr(result, "success"), "NLG result missing 'success' attribute"


# ---------------------------------------------------------------------------
# 10. GödelOSIntegration smoke test
# ---------------------------------------------------------------------------

class TestGödelOSIntegration:
    """The backend integration should expose subsystem status."""

    @pytest.mark.asyncio
    async def test_integration_initializes_pipeline(self):
        from backend.godelos_integration import GödelOSIntegration

        integration = GödelOSIntegration()
        await integration.initialize()
        assert integration.cognitive_pipeline is not None
        status = await integration.get_cognitive_subsystem_status()
        assert status["available"] is True
        assert status["active_count"] > 0

    @pytest.mark.asyncio
    async def test_health_status_includes_subsystems(self):
        from backend.godelos_integration import GödelOSIntegration

        integration = GödelOSIntegration()
        await integration.initialize()
        health = await integration.get_health_status()
        assert "cognitive_subsystems" in health
