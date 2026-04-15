"""
Tests for the ChromaDB knowledge store, OntologyHotReloader, and
ChromaDB-backed KnowledgeStoreInterface.

Covers:
- Round-trip persistence (add → destroy client → reopen → verify)
- All KnowledgeStoreBackend operations via ChromaKnowledgeStore
- Semantic retrieval via Chroma vector search
- Structured retrieval via ``where`` metadata filters
- OntologyHotReloader fires on file change
- KnowledgeStoreInterface backend selection via constructor arg and env var
"""

import json
import os
import shutil
import tempfile
import time
import unittest

import pytest

from godelOS.core_kr.ast.nodes import (
    ApplicationNode,
    ConnectiveNode,
    ConstantNode,
    VariableNode,
)
from godelOS.core_kr.knowledge_store.hot_reloader import (
    OntologyHotReloader,
    _parse_jsonld_triples,
    _parse_ttl_triples,
)
from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface
from godelOS.core_kr.knowledge_store.chroma_store import ChromaKnowledgeStore
from godelOS.core_kr.type_system.manager import TypeSystemManager
from godelOS.core_kr.type_system.types import FunctionType
from godelOS.core_kr.unification_engine.engine import UnificationEngine


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_fixtures():
    """Return a dict of reusable AST fixtures."""
    tsm = TypeSystemManager()
    entity = tsm.get_type("Entity")
    boolean = tsm.get_type("Boolean")
    func_type = FunctionType([entity], boolean)

    socrates = ConstantNode("Socrates", entity)
    plato = ConstantNode("Plato", entity)
    human_pred = ConstantNode("Human", func_type)
    mortal_pred = ConstantNode("Mortal", func_type)

    var_x = VariableNode("?x", 1, entity)

    human_socrates = ApplicationNode(human_pred, [socrates], boolean)
    mortal_socrates = ApplicationNode(mortal_pred, [socrates], boolean)
    human_plato = ApplicationNode(human_pred, [plato], boolean)
    human_var_x = ApplicationNode(human_pred, [var_x], boolean)

    implies_hm = ConnectiveNode(
        "IMPLIES", [human_socrates, mortal_socrates], boolean
    )

    return {
        "tsm": tsm,
        "entity": entity,
        "boolean": boolean,
        "func_type": func_type,
        "socrates": socrates,
        "plato": plato,
        "human_pred": human_pred,
        "mortal_pred": mortal_pred,
        "var_x": var_x,
        "human_socrates": human_socrates,
        "mortal_socrates": mortal_socrates,
        "human_plato": human_plato,
        "human_var_x": human_var_x,
        "implies_hm": implies_hm,
    }


# ---------------------------------------------------------------------------
# ChromaKnowledgeStore tests
# ---------------------------------------------------------------------------


class TestChromaKnowledgeStore(unittest.TestCase):
    """Direct tests against the ChromaKnowledgeStore backend."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.fix = _make_fixtures()
        self.ue = UnificationEngine(self.fix["tsm"])
        self.store = ChromaKnowledgeStore(
            self.ue, persist_directory=self.tmpdir
        )
        # Create default context
        self.store.create_context("TRUTHS", None, "truths")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    # -- context CRUD ------------------------------------------------------

    def test_create_and_list_contexts(self):
        self.assertIn("TRUTHS", self.store.list_contexts())
        self.store.create_context("BELIEFS", None, "beliefs")
        self.assertIn("BELIEFS", self.store.list_contexts())

    def test_create_duplicate_context_raises(self):
        with self.assertRaises(ValueError):
            self.store.create_context("TRUTHS", None, "truths")

    def test_create_context_with_missing_parent_raises(self):
        with self.assertRaises(ValueError):
            self.store.create_context("CHILD", "NONEXISTENT", "child")

    def test_delete_context(self):
        self.store.create_context("TO_DELETE", None, "temp")
        self.assertIn("TO_DELETE", self.store.list_contexts())
        self.store.delete_context("TO_DELETE")
        self.assertNotIn("TO_DELETE", self.store.list_contexts())

    def test_delete_context_with_children_raises(self):
        self.store.create_context("PARENT", None, "parent")
        self.store.create_context("CHILD", "PARENT", "child")
        with self.assertRaises(ValueError):
            self.store.delete_context("PARENT")

    def test_delete_nonexistent_context_raises(self):
        with self.assertRaises(ValueError):
            self.store.delete_context("NOPE")

    def test_get_context_info(self):
        info = self.store.get_context_info("TRUTHS")
        self.assertIsNotNone(info)
        self.assertEqual(info["type"], "truths")
        self.assertIsNone(info["parent"])

    # -- statement CRUD ----------------------------------------------------

    def test_add_and_exists(self):
        result = self.store.add_statement(self.fix["human_socrates"], "TRUTHS")
        self.assertTrue(result)
        self.assertTrue(
            self.store.statement_exists(self.fix["human_socrates"], ["TRUTHS"])
        )

    def test_add_duplicate_returns_false(self):
        self.store.add_statement(self.fix["human_socrates"], "TRUTHS")
        result = self.store.add_statement(self.fix["human_socrates"], "TRUTHS")
        self.assertFalse(result)

    def test_add_to_nonexistent_context_raises(self):
        with self.assertRaises(ValueError):
            self.store.add_statement(self.fix["human_socrates"], "NOPE")

    def test_retract_statement(self):
        self.store.add_statement(self.fix["human_socrates"], "TRUTHS")
        self.assertTrue(
            self.store.retract_statement(self.fix["human_socrates"], "TRUTHS")
        )
        self.assertFalse(
            self.store.statement_exists(self.fix["human_socrates"], ["TRUTHS"])
        )

    def test_retract_nonexistent_returns_false(self):
        self.assertFalse(
            self.store.retract_statement(self.fix["human_plato"], "TRUTHS")
        )

    def test_retract_with_variable_pattern(self):
        self.store.add_statement(self.fix["human_socrates"], "TRUTHS")
        result = self.store.retract_statement(self.fix["human_var_x"], "TRUTHS")
        self.assertTrue(result)
        self.assertFalse(
            self.store.statement_exists(self.fix["human_socrates"], ["TRUTHS"])
        )

    # -- query pattern matching --------------------------------------------

    def test_query_exact(self):
        self.store.add_statement(self.fix["human_socrates"], "TRUTHS")
        results = self.store.query_statements_match_pattern(
            self.fix["human_socrates"], ["TRUTHS"]
        )
        self.assertEqual(len(results), 1)

    def test_query_variable_binding(self):
        self.store.add_statement(self.fix["human_socrates"], "TRUTHS")
        results = self.store.query_statements_match_pattern(
            self.fix["human_var_x"], ["TRUTHS"]
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][self.fix["var_x"]], self.fix["socrates"])

    def test_query_multiple_contexts(self):
        self.store.create_context("BELIEFS", None, "beliefs")
        self.store.add_statement(self.fix["human_socrates"], "TRUTHS")
        self.store.add_statement(self.fix["human_plato"], "BELIEFS")
        results = self.store.query_statements_match_pattern(
            self.fix["human_var_x"], ["TRUTHS", "BELIEFS"]
        )
        self.assertEqual(len(results), 2)

    def test_query_nonexistent_context_raises(self):
        with self.assertRaises(ValueError):
            self.store.query_statements_match_pattern(
                self.fix["human_socrates"], ["NOPE"]
            )

    def test_query_with_variables_to_bind(self):
        self.store.add_statement(self.fix["human_socrates"], "TRUTHS")
        results = self.store.query_statements_match_pattern(
            self.fix["human_var_x"],
            ["TRUTHS"],
            variables_to_bind=[self.fix["var_x"]],
        )
        self.assertEqual(len(results), 1)
        self.assertIn(self.fix["var_x"], results[0])

    # -- get_all_statements_in_context -------------------------------------

    def test_get_all_statements_in_context(self):
        self.store.add_statement(self.fix["human_socrates"], "TRUTHS")
        self.store.add_statement(self.fix["mortal_socrates"], "TRUTHS")
        stmts = self.store.get_all_statements_in_context("TRUTHS")
        self.assertEqual(len(stmts), 2)

    # -- round-trip persistence --------------------------------------------

    def test_round_trip_persistence(self):
        """Add data, destroy client, reopen from same dir, verify presence."""
        self.store.add_statement(self.fix["human_socrates"], "TRUTHS")
        self.store.add_statement(self.fix["mortal_socrates"], "TRUTHS")

        # Destroy the existing client to force a cold restart
        del self.store

        # Reopen from disk
        store2 = ChromaKnowledgeStore(self.ue, persist_directory=self.tmpdir)
        self.assertTrue(
            store2.statement_exists(self.fix["human_socrates"], ["TRUTHS"])
        )
        self.assertTrue(
            store2.statement_exists(self.fix["mortal_socrates"], ["TRUTHS"])
        )
        self.assertIn("TRUTHS", store2.list_contexts())

        results = store2.query_statements_match_pattern(
            self.fix["human_var_x"], ["TRUTHS"]
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][self.fix["var_x"]], self.fix["socrates"])

    def test_round_trip_connective(self):
        """Connective nodes survive serialisation round-trip."""
        self.store.add_statement(self.fix["implies_hm"], "TRUTHS")
        del self.store

        store2 = ChromaKnowledgeStore(self.ue, persist_directory=self.tmpdir)
        self.assertTrue(
            store2.statement_exists(self.fix["implies_hm"], ["TRUTHS"])
        )

    # -- semantic retrieval ------------------------------------------------

    def test_query_by_similarity(self):
        """Semantic vector search returns relevant results."""
        self.store.add_statement(self.fix["human_socrates"], "TRUTHS")
        self.store.add_statement(self.fix["mortal_socrates"], "TRUTHS")

        results = self.store.query_by_similarity(
            "who is human", "TRUTHS", n_results=2
        )
        self.assertTrue(len(results) > 0)
        # Each result should have expected keys
        for r in results:
            self.assertIn("id", r)
            self.assertIn("document", r)
            self.assertIn("metadata", r)
            self.assertIn("distance", r)
            self.assertIn("statement", r)

    def test_query_by_similarity_empty_context(self):
        """Semantic query on empty context returns empty list."""
        results = self.store.query_by_similarity(
            "anything", "TRUTHS", n_results=5
        )
        self.assertEqual(len(results), 0)

    # -- structured metadata retrieval -------------------------------------

    def test_query_by_metadata(self):
        """Structured metadata filter returns matching items."""
        self.store.add_statement(self.fix["human_socrates"], "TRUTHS")
        self.store.add_statement(self.fix["mortal_socrates"], "TRUTHS")

        results = self.store.query_by_metadata(
            "TRUTHS", {"predicate": "Human"}
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["metadata"]["predicate"], "Human")

    def test_query_by_metadata_subject(self):
        """Filter by subject metadata."""
        self.store.add_statement(self.fix["human_socrates"], "TRUTHS")
        self.store.add_statement(self.fix["human_plato"], "TRUTHS")

        results = self.store.query_by_metadata(
            "TRUTHS", {"subject": "Plato"}
        )
        self.assertEqual(len(results), 1)


# ---------------------------------------------------------------------------
# KnowledgeStoreInterface with ChromaDB backend
# ---------------------------------------------------------------------------


class TestKnowledgeStoreInterfaceChroma(unittest.TestCase):
    """Test KnowledgeStoreInterface configured to use the ChromaDB backend."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.fix = _make_fixtures()
        self.ks = KnowledgeStoreInterface(
            self.fix["tsm"], backend="chroma", db_path=self.tmpdir
        )

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_default_contexts_created(self):
        contexts = self.ks.list_contexts()
        self.assertIn("TRUTHS", contexts)
        self.assertIn("BELIEFS", contexts)
        self.assertIn("HYPOTHETICAL", contexts)

    def test_add_and_query(self):
        self.ks.add_statement(self.fix["human_socrates"])
        results = self.ks.query_statements_match_pattern(self.fix["human_var_x"])
        self.assertEqual(len(results), 1)

    def test_persistence_across_interface_recreations(self):
        """Knowledge survives interface tear-down/re-creation."""
        self.ks.add_statement(self.fix["human_socrates"])
        del self.ks
        ks2 = KnowledgeStoreInterface(
            self.fix["tsm"], backend="chroma", db_path=self.tmpdir
        )
        self.assertTrue(ks2.statement_exists(self.fix["human_socrates"]))

    def test_env_var_backend_selection(self):
        """KNOWLEDGE_STORE_BACKEND env-var selects the backend."""
        db2 = os.path.join(self.tmpdir, "env_test")
        old_backend = os.environ.get("KNOWLEDGE_STORE_BACKEND")
        old_path = os.environ.get("KNOWLEDGE_STORE_PATH")
        try:
            os.environ["KNOWLEDGE_STORE_BACKEND"] = "chroma"
            os.environ["KNOWLEDGE_STORE_PATH"] = db2
            ks = KnowledgeStoreInterface(self.fix["tsm"])
            ks.add_statement(self.fix["human_socrates"])
            self.assertTrue(ks.statement_exists(self.fix["human_socrates"]))
            # Persistence directory should exist
            self.assertTrue(os.path.exists(db2))
        finally:
            if old_backend is None:
                os.environ.pop("KNOWLEDGE_STORE_BACKEND", None)
            else:
                os.environ["KNOWLEDGE_STORE_BACKEND"] = old_backend
            if old_path is None:
                os.environ.pop("KNOWLEDGE_STORE_PATH", None)
            else:
                os.environ["KNOWLEDGE_STORE_PATH"] = old_path


# ---------------------------------------------------------------------------
# OntologyHotReloader
# ---------------------------------------------------------------------------


class TestOntologyHotReloader(unittest.TestCase):
    """Test the file-system watcher + delta application logic."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.added: list = []
        self.removed: list = []

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _on_add(self, s, p, o):
        self.added.append((s, p, o))

    def _on_remove(self, s, p, o):
        self.removed.append((s, p, o))

    def test_initial_snapshot_empty_dir(self):
        reloader = OntologyHotReloader(
            self.tmpdir, self._on_add, self._on_remove
        )
        self.assertEqual(reloader._snapshot, {})

    def test_reload_picks_up_new_file(self):
        reloader = OntologyHotReloader(
            self.tmpdir, self._on_add, self._on_remove
        )
        # Write a JSON-LD file
        path = os.path.join(self.tmpdir, "test.json-ld")
        data = [{"@id": "ex:Cat", "ex:sound": "meow"}]
        with open(path, "w") as fh:
            json.dump(data, fh)

        reloader.reload()
        self.assertEqual(len(self.added), 1)
        self.assertEqual(self.added[0], ("ex:Cat", "ex:sound", "meow"))

    def test_reload_detects_removal(self):
        # Seed a file first
        path = os.path.join(self.tmpdir, "animals.json-ld")
        data = [{"@id": "ex:Dog", "ex:sound": "woof"}]
        with open(path, "w") as fh:
            json.dump(data, fh)

        reloader = OntologyHotReloader(
            self.tmpdir, self._on_add, self._on_remove
        )
        self.assertEqual(len(self.added), 0)

        os.remove(path)
        reloader.reload()
        self.assertEqual(len(self.removed), 1)
        self.assertEqual(self.removed[0], ("ex:Dog", "ex:sound", "woof"))

    def test_reload_detects_modification(self):
        path = os.path.join(self.tmpdir, "mod.json-ld")
        data = [{"@id": "ex:A", "ex:val": "1"}]
        with open(path, "w") as fh:
            json.dump(data, fh)

        reloader = OntologyHotReloader(
            self.tmpdir, self._on_add, self._on_remove
        )

        data2 = [{"@id": "ex:A", "ex:val": "2"}]
        with open(path, "w") as fh:
            json.dump(data2, fh)

        reloader.reload()
        self.assertIn(("ex:A", "ex:val", "1"), self.removed)
        self.assertIn(("ex:A", "ex:val", "2"), self.added)

    def test_ttl_file_parsing(self):
        reloader = OntologyHotReloader(
            self.tmpdir, self._on_add, self._on_remove
        )
        path = os.path.join(self.tmpdir, "onto.ttl")
        with open(path, "w") as fh:
            fh.write("# comment\n")
            fh.write("<ex:Cat> <rdf:type> <ex:Animal> .\n")
            fh.write("<ex:Dog> <rdf:type> <ex:Animal> .\n")

        reloader.reload()
        self.assertEqual(len(self.added), 2)

    def test_hot_reload_via_observer(self):
        """The watchdog observer detects a new file within 5 seconds."""
        reloader = OntologyHotReloader(
            self.tmpdir, self._on_add, self._on_remove, debounce_seconds=0.1
        )
        reloader.start()
        try:
            path = os.path.join(self.tmpdir, "live.json-ld")
            data = [{"@id": "ex:Live", "ex:status": "active"}]
            with open(path, "w") as fh:
                json.dump(data, fh)

            deadline = time.monotonic() + 5.0
            while not self.added and time.monotonic() < deadline:
                time.sleep(0.2)

            self.assertTrue(
                len(self.added) > 0,
                "Hot-reload did not fire within 5 seconds",
            )
        finally:
            reloader.stop()


# ---------------------------------------------------------------------------
# Parsers unit tests
# ---------------------------------------------------------------------------


class TestParsers(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_parse_jsonld_graph(self):
        path = os.path.join(self.tmpdir, "g.json-ld")
        data = {"@graph": [{"@id": "ex:A", "ex:p": "v"}]}
        with open(path, "w") as fh:
            json.dump(data, fh)
        triples = _parse_jsonld_triples(path)
        self.assertEqual(triples, {("ex:A", "ex:p", "v")})

    def test_parse_jsonld_list(self):
        path = os.path.join(self.tmpdir, "l.json-ld")
        data = [{"@id": "ex:B", "ex:q": [{"@value": "42"}]}]
        with open(path, "w") as fh:
            json.dump(data, fh)
        triples = _parse_jsonld_triples(path)
        self.assertEqual(triples, {("ex:B", "ex:q", "42")})

    def test_parse_ttl_simple(self):
        path = os.path.join(self.tmpdir, "t.ttl")
        with open(path, "w") as fh:
            fh.write("<ex:S> <ex:P> <ex:O> .\n")
        triples = _parse_ttl_triples(path)
        self.assertEqual(triples, {("ex:S", "ex:P", "ex:O")})

    def test_parse_ttl_skips_prefix(self):
        path = os.path.join(self.tmpdir, "p.ttl")
        with open(path, "w") as fh:
            fh.write("@prefix ex: <http://example.org/> .\n")
            fh.write("<ex:S> <ex:P> <ex:O> .\n")
        triples = _parse_ttl_triples(path)
        self.assertEqual(triples, {("ex:S", "ex:P", "ex:O")})

    def test_parse_invalid_file_returns_empty(self):
        path = os.path.join(self.tmpdir, "bad.json-ld")
        with open(path, "w") as fh:
            fh.write("NOT JSON")
        triples = _parse_jsonld_triples(path)
        self.assertEqual(triples, set())


if __name__ == "__main__":
    unittest.main()
