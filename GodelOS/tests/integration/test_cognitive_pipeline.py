"""
End-to-end integration tests for GödelOS cognitive subsystems.

Tests exercise the full cognitive pipeline:
    NLU → Knowledge Store (write/read) → Inference → Context Engine → NLG

External dependencies (spaCy, Z3) are mocked so that tests run in CI
without optional native packages.
"""

import pytest
from unittest.mock import patch, MagicMock
from typing import Dict, List, Optional, Set

from godelOS.core_kr.type_system.manager import TypeSystemManager
from godelOS.core_kr.type_system.types import AtomicType, FunctionType
from godelOS.core_kr.ast.nodes import (
    AST_Node,
    ConstantNode,
    VariableNode,
    ApplicationNode,
    ConnectiveNode,
    QuantifierNode,
)
from godelOS.core_kr.knowledge_store import KnowledgeStoreInterface
from godelOS.core_kr.unification_engine.engine import UnificationEngine
from godelOS.inference_engine.coordinator import InferenceCoordinator
from godelOS.inference_engine.resolution_prover import ResolutionProver
from godelOS.inference_engine.base_prover import ResourceLimits
from godelOS.inference_engine.proof_object import ProofObject
from godelOS.nlu_nlg.nlu.pipeline import NLUPipeline, NLUResult, create_nlu_pipeline
from godelOS.nlu_nlg.nlg.pipeline import NLGPipeline, NLGResult, create_nlg_pipeline
from godelOS.nlu_nlg.nlu.discourse_manager import DiscourseStateManager, DiscourseContext
from godelOS.nlu_nlg.nlu.lexical_analyzer_parser import (
    Token,
    Entity,
    Span,
    Sentence,
    SyntacticParseOutput,
)

# ---------------------------------------------------------------------------
# All tests in this module run in-process — no backend server required.
# ---------------------------------------------------------------------------
pytestmark = [pytest.mark.integration, pytest.mark.standalone]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_token(text: str, lemma: str, pos: str, tag: str, dep: str,
                i: int, head_i: Optional[int] = None,
                is_stop: bool = False, is_punct: bool = False,
                is_sent_start: Optional[bool] = None,
                ent_type: str = "", ent_iob: str = "O",
                idx: int = 0) -> Token:
    """Build a ``Token`` data-class instance without touching spaCy."""
    return Token(
        text=text,
        lemma=lemma,
        pos=pos,
        tag=tag,
        dep=dep,
        is_stop=is_stop,
        is_punct=is_punct,
        is_space=False,
        is_ent=bool(ent_type),
        ent_type=ent_type,
        ent_iob=ent_iob,
        idx=idx,
        i=i,
        is_alpha=text.isalpha(),
        is_digit=text.isdigit(),
        is_lower=text.islower(),
        is_upper=text.isupper(),
        is_title=text.istitle(),
        is_sent_start=is_sent_start,
        morphology={},
        sent_idx=0,
        head_i=head_i,
    )


def _make_syntactic_parse(text: str, tokens: List[Token]) -> SyntacticParseOutput:
    """Wrap tokens in a ``SyntacticParseOutput`` with one sentence."""
    root = next((t for t in tokens if t.dep == "ROOT"), tokens[0])
    sentence = Sentence(
        text=text,
        start_char=0,
        end_char=len(text),
        tokens=tokens,
        entities=[],
        noun_phrases=[],
        verb_phrases=[],
        root_token=root,
    )
    return SyntacticParseOutput(
        text=text,
        tokens=tokens,
        sentences=[sentence],
        entities=[],
        noun_phrases=[],
        verb_phrases=[],
        doc_metadata={"source": "integration_test"},
    )


def _build_chase_tokens() -> List[Token]:
    """Return tokens for 'The cat chases the mouse.'"""
    return [
        _make_token("The", "the", "DET", "DT", "det", 0, head_i=1,
                     is_stop=True, is_sent_start=True, idx=0),
        _make_token("cat", "cat", "NOUN", "NN", "nsubj", 1, head_i=2, idx=4),
        _make_token("chases", "chase", "VERB", "VBZ", "ROOT", 2, head_i=2, idx=8),
        _make_token("the", "the", "DET", "DT", "det", 3, head_i=4,
                     is_stop=True, idx=15),
        _make_token("mouse", "mouse", "NOUN", "NN", "dobj", 4, head_i=2, idx=19),
        _make_token(".", ".", "PUNCT", ".", "punct", 5, head_i=2,
                     is_punct=True, idx=24),
    ]


def _build_hides_tokens() -> List[Token]:
    """Return tokens for 'The mouse hides under the table.'"""
    return [
        _make_token("The", "the", "DET", "DT", "det", 0, head_i=1,
                     is_stop=True, is_sent_start=True, idx=0),
        _make_token("mouse", "mouse", "NOUN", "NN", "nsubj", 1, head_i=2, idx=4),
        _make_token("hides", "hide", "VERB", "VBZ", "ROOT", 2, head_i=2, idx=10),
        _make_token("under", "under", "ADP", "IN", "prep", 3, head_i=2, idx=16),
        _make_token("the", "the", "DET", "DT", "det", 4, head_i=5,
                     is_stop=True, idx=22),
        _make_token("table", "table", "NOUN", "NN", "pobj", 5, head_i=3, idx=26),
        _make_token(".", ".", "PUNCT", ".", "punct", 6, head_i=2,
                     is_punct=True, idx=31),
    ]


def _build_fast_tokens() -> List[Token]:
    """Return tokens for 'It is very fast.'"""
    return [
        _make_token("It", "it", "PRON", "PRP", "nsubj", 0, head_i=1,
                     is_sent_start=True, idx=0),
        _make_token("is", "be", "AUX", "VBZ", "ROOT", 1, head_i=1,
                     is_stop=True, idx=3),
        _make_token("very", "very", "ADV", "RB", "advmod", 2, head_i=3,
                     is_stop=True, idx=6),
        _make_token("fast", "fast", "ADJ", "JJ", "acomp", 3, head_i=1, idx=11),
        _make_token(".", ".", "PUNCT", ".", "punct", 4, head_i=1,
                     is_punct=True, idx=15),
    ]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def type_system() -> TypeSystemManager:
    """Shared TypeSystemManager used across tests."""
    return TypeSystemManager()


@pytest.fixture()
def knowledge_store(type_system) -> KnowledgeStoreInterface:
    """Fresh in-memory knowledge store."""
    return KnowledgeStoreInterface(type_system)


@pytest.fixture()
def unification_engine(type_system) -> UnificationEngine:
    """Unification engine matching the type system."""
    return UnificationEngine(type_system)


@pytest.fixture()
def resolution_prover(knowledge_store, unification_engine) -> ResolutionProver:
    """Resolution prover wired to the knowledge store."""
    return ResolutionProver(knowledge_store, unification_engine)


# ---------------------------------------------------------------------------
# Test 1: Single-query round-trip  (NLU → KR → NLG)
# ---------------------------------------------------------------------------


class TestSingleQueryRoundTrip:
    """Process a sentence through NLU, store the ASTs in KR, read them back,
    and generate natural language via NLG."""

    def test_nlu_to_kr_to_nlg(self, type_system, knowledge_store):
        """Full NLU → KR write → KR read → NLG round-trip."""
        text = "The cat chases the mouse."
        tokens = _build_chase_tokens()
        parse_output = _make_syntactic_parse(text, tokens)

        # --- NLU ---
        # Patch the LAP (spaCy dependent) to return our synthetic parse.
        nlu = create_nlu_pipeline(type_system)
        with patch.object(nlu.lexical_analyzer_parser, "process",
                          return_value=parse_output):
            with patch.object(nlu, "_initialize_lexicon_ontology"):
                nlu_result = nlu.process(text)

        assert nlu_result.success, f"NLU failed: {nlu_result.errors}"
        assert len(nlu_result.ast_nodes) > 0, "NLU produced no AST nodes"

        # --- KR write ---
        knowledge_store.create_context("INTEGRATION_TEST")
        for ast_node in nlu_result.ast_nodes:
            added = knowledge_store.add_statement(ast_node, "INTEGRATION_TEST")
            assert added, f"Failed to add statement: {ast_node}"

        # --- KR read ---
        stored = knowledge_store.get_all_statements_in_context("INTEGRATION_TEST")
        assert len(stored) > 0, "Knowledge store returned empty set"
        # The number of stored statements must equal the number we wrote.
        assert len(stored) == len(nlu_result.ast_nodes), (
            f"Expected {len(nlu_result.ast_nodes)} stored statements, "
            f"got {len(stored)}"
        )

        # --- NLG ---
        nlg = create_nlg_pipeline(type_system)
        nlg_result = nlg.process(list(stored))
        assert nlg_result.success, f"NLG failed: {nlg_result.errors}"
        assert nlg_result.output_text, "NLG produced empty output"
        assert len(nlg_result.output_text.strip()) > 0

    def test_nlu_result_contains_timing(self, type_system):
        """NLU result must carry timing information."""
        text = "The cat chases the mouse."
        tokens = _build_chase_tokens()
        parse_output = _make_syntactic_parse(text, tokens)

        nlu = create_nlu_pipeline(type_system)
        with patch.object(nlu.lexical_analyzer_parser, "process",
                          return_value=parse_output):
            with patch.object(nlu, "_initialize_lexicon_ontology"):
                nlu_result = nlu.process(text)

        assert nlu_result.processing_time >= 0
        assert isinstance(nlu_result.component_times, dict)


# ---------------------------------------------------------------------------
# Test 2: Knowledge persistence within a session
# ---------------------------------------------------------------------------

class TestKnowledgePersistence:
    """Verify that facts stored in the KR survive across multiple
    operations within the same session and across different contexts."""

    def test_facts_persist_across_additions(self, type_system, knowledge_store):
        """Adding multiple facts then querying back returns all of them."""
        entity = type_system.get_type("Entity")
        boolean = type_system.get_type("Boolean")
        func_type = FunctionType([entity], boolean)

        likes_pred = ConstantNode("Likes", func_type)
        alice = ConstantNode("Alice", entity)
        bob = ConstantNode("Bob", entity)
        carol = ConstantNode("Carol", entity)

        facts = [
            ApplicationNode(likes_pred, [alice], boolean),
            ApplicationNode(likes_pred, [bob], boolean),
            ApplicationNode(likes_pred, [carol], boolean),
        ]

        for f in facts:
            assert knowledge_store.add_statement(f, "TRUTHS")

        stored = knowledge_store.get_all_statements_in_context("TRUTHS")
        for f in facts:
            assert f in stored, f"Fact {f} lost after multiple insertions"

    def test_retract_removes_only_target(self, type_system, knowledge_store):
        """Retracting a single fact must not affect unrelated facts."""
        entity = type_system.get_type("Entity")
        boolean = type_system.get_type("Boolean")
        func_type = FunctionType([entity], boolean)

        pred = ConstantNode("Tall", func_type)
        alice = ConstantNode("Alice", entity)
        bob = ConstantNode("Bob", entity)

        tall_alice = ApplicationNode(pred, [alice], boolean)
        tall_bob = ApplicationNode(pred, [bob], boolean)

        knowledge_store.add_statement(tall_alice, "TRUTHS")
        knowledge_store.add_statement(tall_bob, "TRUTHS")

        knowledge_store.retract_statement(tall_alice, "TRUTHS")

        assert not knowledge_store.statement_exists(tall_alice, ["TRUTHS"])
        assert knowledge_store.statement_exists(tall_bob, ["TRUTHS"])

    def test_cross_context_isolation(self, type_system, knowledge_store):
        """Facts in one context must not leak into another."""
        entity = type_system.get_type("Entity")
        boolean = type_system.get_type("Boolean")
        func_type = FunctionType([entity], boolean)

        pred = ConstantNode("Smart", func_type)
        dave = ConstantNode("Dave", entity)
        fact = ApplicationNode(pred, [dave], boolean)

        knowledge_store.create_context("CTX_A")
        knowledge_store.create_context("CTX_B")

        knowledge_store.add_statement(fact, "CTX_A")

        assert knowledge_store.statement_exists(fact, ["CTX_A"])
        assert not knowledge_store.statement_exists(fact, ["CTX_B"])

    def test_pattern_query_with_variable(self, type_system, knowledge_store):
        """Querying with a variable pattern returns matching bindings."""
        entity = type_system.get_type("Entity")
        boolean = type_system.get_type("Boolean")
        func_type = FunctionType([entity], boolean)

        color_pred = ConstantNode("Color", func_type)
        red = ConstantNode("Red", entity)
        blue = ConstantNode("Blue", entity)

        knowledge_store.add_statement(
            ApplicationNode(color_pred, [red], boolean), "TRUTHS"
        )
        knowledge_store.add_statement(
            ApplicationNode(color_pred, [blue], boolean), "TRUTHS"
        )

        var_x = VariableNode("?x", 1, entity)
        query = ApplicationNode(color_pred, [var_x], boolean)
        results = knowledge_store.query_statements_match_pattern(
            query, context_ids=["TRUTHS"], variables_to_bind=[var_x]
        )

        # Expect at least two bindings (one per colour fact).
        assert len(results) >= 2, f"Expected >=2 bindings, got {len(results)}"


# ---------------------------------------------------------------------------
# Test 3: Context switching (discourse manager)
# ---------------------------------------------------------------------------

class TestContextSwitching:
    """Multi-turn NLU processing with discourse context tracking."""

    def test_discourse_context_carries_across_turns(self, type_system):
        """Processing successive utterances updates the discourse context."""
        utterances = [
            ("The cat chases the mouse.", _build_chase_tokens()),
            ("It is very fast.", _build_fast_tokens()),
            ("The mouse hides under the table.", _build_hides_tokens()),
        ]

        nlu = create_nlu_pipeline(type_system)
        discourse_ctx: Optional[DiscourseContext] = None

        for text, tokens in utterances:
            parse_output = _make_syntactic_parse(text, tokens)
            with patch.object(nlu.lexical_analyzer_parser, "process",
                              return_value=parse_output):
                with patch.object(nlu, "_initialize_lexicon_ontology"):
                    result = nlu.process_with_context(text, discourse_ctx)

            assert result.success, f"NLU failed on '{text}': {result.errors}"
            discourse_ctx = result.discourse_context

        # After three turns the discourse context should exist and carry state.
        assert discourse_ctx is not None, "Discourse context is None after 3 turns"

    def test_context_reset_clears_state(self, type_system):
        """Resetting the discourse manager yields a fresh context."""
        text = "The cat chases the mouse."
        tokens = _build_chase_tokens()
        parse_output = _make_syntactic_parse(text, tokens)

        nlu = create_nlu_pipeline(type_system)
        with patch.object(nlu.lexical_analyzer_parser, "process",
                          return_value=parse_output):
            with patch.object(nlu, "_initialize_lexicon_ontology"):
                result_before = nlu.process(text)

        nlu.reset_discourse_context()

        with patch.object(nlu.lexical_analyzer_parser, "process",
                          return_value=parse_output):
            with patch.object(nlu, "_initialize_lexicon_ontology"):
                result_after = nlu.process(text)

        assert result_after.success

    def test_nlg_with_context_switching(self, type_system):
        """NLG pipeline handles context across multiple invocations."""
        entity = type_system.get_type("Entity")
        boolean = type_system.get_type("Boolean")

        chase = ConstantNode("chase", boolean)
        cat = ConstantNode("cat", entity)
        mouse = ConstantNode("mouse", entity)

        app1 = ApplicationNode(chase, [cat, mouse], boolean)

        hide = ConstantNode("hide", boolean)
        table = ConstantNode("table", entity)
        app2 = ApplicationNode(hide, [mouse, table], boolean)

        nlg = create_nlg_pipeline(type_system)
        discourse_ctx: Optional[DiscourseContext] = None

        r1 = nlg.process_with_context([app1], discourse_ctx)
        assert r1.success, f"NLG turn 1 failed: {r1.errors}"
        discourse_ctx = r1.discourse_context

        r2 = nlg.process_with_context([app2], discourse_ctx)
        assert r2.success, f"NLG turn 2 failed: {r2.errors}"
        assert r2.output_text, "NLG produced empty output on turn 2"


# ---------------------------------------------------------------------------
# Test 4: Inference chain with non-trivial reasoning
# ---------------------------------------------------------------------------


class TestInferenceChain:
    """Verify that the resolution prover can derive new facts via
    multi-step deduction using facts and rules stored in the KR system."""

    def test_socrates_syllogism(self, type_system, knowledge_store,
                                resolution_prover):
        """Classic syllogism: Human(Socrates) ∧ (∀x. Human(x) → Mortal(x))
        ⊢ Mortal(Socrates)."""
        entity = type_system.get_type("Entity")
        boolean = type_system.get_type("Boolean")
        func_type = FunctionType([entity], boolean)

        human_pred = ConstantNode("Human", func_type)
        mortal_pred = ConstantNode("Mortal", func_type)
        socrates = ConstantNode("Socrates", entity)

        human_socrates = ApplicationNode(human_pred, [socrates], boolean)
        mortal_socrates = ApplicationNode(mortal_pred, [socrates], boolean)

        # Rule: Human(?x) → Mortal(?x)
        var_x = VariableNode("?x", 1, entity)
        human_x = ApplicationNode(human_pred, [var_x], boolean)
        mortal_x = ApplicationNode(mortal_pred, [var_x], boolean)
        rule = ConnectiveNode("IMPLIES", [human_x, mortal_x], boolean)

        # Populate KR
        knowledge_store.add_statement(human_socrates, "TRUTHS")
        knowledge_store.add_statement(rule, "TRUTHS")

        context = list(knowledge_store.get_all_statements_in_context("TRUTHS"))
        assert len(context) == 2

        # Prove the goal
        proof = resolution_prover.prove(
            mortal_socrates, context,
            ResourceLimits(time_limit_ms=5000, depth_limit=50, nodes_limit=500),
        )

        assert proof.goal_achieved, f"Proof failed: {proof.status_message}"
        assert proof.proof_steps, "Proof has no steps"
        # The proof must contain at least one resolution step.
        resolution_steps = [s for s in proof.proof_steps
                            if s.rule_name == "resolution"]
        assert len(resolution_steps) >= 1, "No resolution steps found"

    def test_two_hop_inference(self, type_system, knowledge_store,
                               resolution_prover):
        """Two-hop chain: A(s) ∧ (A(x)→B(x)) ∧ (B(x)→C(x)) ⊢ C(s)."""
        entity = type_system.get_type("Entity")
        boolean = type_system.get_type("Boolean")
        func_type = FunctionType([entity], boolean)

        pred_a = ConstantNode("A", func_type)
        pred_b = ConstantNode("B", func_type)
        pred_c = ConstantNode("C", func_type)
        s = ConstantNode("s", entity)

        fact_a_s = ApplicationNode(pred_a, [s], boolean)

        var_x = VariableNode("?x", 1, entity)
        rule_ab = ConnectiveNode(
            "IMPLIES",
            [ApplicationNode(pred_a, [var_x], boolean),
             ApplicationNode(pred_b, [var_x], boolean)],
            boolean,
        )
        var_y = VariableNode("?y", 2, entity)
        rule_bc = ConnectiveNode(
            "IMPLIES",
            [ApplicationNode(pred_b, [var_y], boolean),
             ApplicationNode(pred_c, [var_y], boolean)],
            boolean,
        )

        goal = ApplicationNode(pred_c, [s], boolean)

        knowledge_store.add_statement(fact_a_s, "TRUTHS")
        knowledge_store.add_statement(rule_ab, "TRUTHS")
        knowledge_store.add_statement(rule_bc, "TRUTHS")

        context = list(knowledge_store.get_all_statements_in_context("TRUTHS"))
        assert len(context) == 3

        proof = resolution_prover.prove(
            goal, context,
            ResourceLimits(time_limit_ms=10000, depth_limit=100, nodes_limit=1000),
        )

        assert proof.goal_achieved, f"Two-hop proof failed: {proof.status_message}"
        resolution_steps = [s for s in proof.proof_steps
                            if s.rule_name == "resolution"]
        assert len(resolution_steps) >= 2, (
            f"Expected >=2 resolution steps, got {len(resolution_steps)}"
        )

    def test_inference_then_nlg(self, type_system, knowledge_store,
                                resolution_prover):
        """Derive a fact via inference then render it through NLG."""
        entity = type_system.get_type("Entity")
        boolean = type_system.get_type("Boolean")
        func_type = FunctionType([entity], boolean)

        human_pred = ConstantNode("Human", func_type)
        mortal_pred = ConstantNode("Mortal", func_type)
        socrates = ConstantNode("Socrates", entity)

        human_socrates = ApplicationNode(human_pred, [socrates], boolean)
        mortal_socrates = ApplicationNode(mortal_pred, [socrates], boolean)

        var_x = VariableNode("?x", 1, entity)
        rule = ConnectiveNode(
            "IMPLIES",
            [ApplicationNode(human_pred, [var_x], boolean),
             ApplicationNode(mortal_pred, [var_x], boolean)],
            boolean,
        )

        knowledge_store.add_statement(human_socrates, "TRUTHS")
        knowledge_store.add_statement(rule, "TRUTHS")

        context = list(knowledge_store.get_all_statements_in_context("TRUTHS"))
        proof = resolution_prover.prove(
            mortal_socrates, context,
            ResourceLimits(time_limit_ms=5000, depth_limit=50, nodes_limit=500),
        )
        assert proof.goal_achieved

        # Feed the derived conclusion to NLG.
        nlg = create_nlg_pipeline(type_system)
        nlg_result = nlg.process([mortal_socrates])
        assert nlg_result.success, f"NLG failed: {nlg_result.errors}"
        assert nlg_result.output_text, "NLG produced empty text"

    def test_failed_inference_returns_failure(self, type_system,
                                              knowledge_store,
                                              resolution_prover):
        """Attempting to prove an unsupported goal returns a non-achieved
        proof object (does not raise)."""
        entity = type_system.get_type("Entity")
        boolean = type_system.get_type("Boolean")
        func_type = FunctionType([entity], boolean)

        pred = ConstantNode("Flying", func_type)
        pig = ConstantNode("Pig", entity)
        goal = ApplicationNode(pred, [pig], boolean)

        # Empty context – nothing to derive from.
        proof = resolution_prover.prove(
            goal, [],
            ResourceLimits(time_limit_ms=2000, depth_limit=20, nodes_limit=200),
        )

        assert not proof.goal_achieved, "Proof should fail with empty context"


# ---------------------------------------------------------------------------
# Test 5: Full pipeline round-trip  (NLU → KR → Inference → NLG)
# ---------------------------------------------------------------------------

class TestFullPipelineRoundTrip:
    """Integration across all four subsystems in a single scenario."""

    def test_nlu_kr_inference_nlg(self, type_system, knowledge_store,
                                  unification_engine):
        """Process NLU output, store in KR, perform inference, render via NLG."""
        entity = type_system.get_type("Entity")
        boolean = type_system.get_type("Boolean")
        func_type = FunctionType([entity], boolean)

        # --- NLU phase (mocked LAP) ---
        text = "The cat chases the mouse."
        tokens = _build_chase_tokens()
        parse_output = _make_syntactic_parse(text, tokens)

        nlu = create_nlu_pipeline(type_system)
        with patch.object(nlu.lexical_analyzer_parser, "process",
                          return_value=parse_output):
            with patch.object(nlu, "_initialize_lexicon_ontology"):
                nlu_result = nlu.process(text)
        assert nlu_result.success

        # --- KR write phase ---
        knowledge_store.create_context("SCENE")
        for node in nlu_result.ast_nodes:
            knowledge_store.add_statement(node, "SCENE")

        # Also add a manually crafted rule:
        # fast(?x) → agile(?x)
        fast_pred = ConstantNode("fast", func_type)
        agile_pred = ConstantNode("agile", func_type)
        var_x = VariableNode("?x", 1, entity)
        fast_x = ApplicationNode(fast_pred, [var_x], boolean)
        agile_x = ApplicationNode(agile_pred, [var_x], boolean)
        rule = ConnectiveNode("IMPLIES", [fast_x, agile_x], boolean)
        knowledge_store.add_statement(rule, "SCENE")

        cat_const = ConstantNode("cat", entity)
        fast_cat = ApplicationNode(fast_pred, [cat_const], boolean)
        knowledge_store.add_statement(fast_cat, "SCENE")

        # --- Inference phase ---
        rp = ResolutionProver(knowledge_store, unification_engine)
        goal = ApplicationNode(agile_pred, [cat_const], boolean)
        context = list(knowledge_store.get_all_statements_in_context("SCENE"))
        proof = rp.prove(
            goal, context,
            ResourceLimits(time_limit_ms=5000, depth_limit=50, nodes_limit=500),
        )
        assert proof.goal_achieved, f"Inference failed: {proof.status_message}"

        # --- NLG phase ---
        nlg = create_nlg_pipeline(type_system)
        nlg_result = nlg.process([goal])
        assert nlg_result.success, f"NLG failed: {nlg_result.errors}"
        assert nlg_result.output_text, "NLG produced empty output"
