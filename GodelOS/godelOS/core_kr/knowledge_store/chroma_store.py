"""
ChromaDB-backed Knowledge Store implementation.

This module implements the KnowledgeStoreBackend interface using ChromaDB
for persistent storage of both structured metadata and vector embeddings.
Knowledge items added in one server session survive restarts.

Each logical context (TRUTHS, BELIEFS, HYPOTHETICAL, etc.) maps to a
separate Chroma collection, enabling context-scoped retrieval.
"""

import hashlib
import logging
import os
import pickle
import time
from typing import Any, Dict, List, Optional, Set

import chromadb

from godelOS.core_kr.ast.nodes import (
    AST_Node,
    ApplicationNode,
    ConstantNode,
    VariableNode,
)
from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreBackend
from godelOS.core_kr.unification_engine.engine import UnificationEngine

logger = logging.getLogger(__name__)


class ChromaKnowledgeStore(KnowledgeStoreBackend):
    """
    ChromaDB-backed implementation of the knowledge store backend.

    Uses a ``PersistentClient`` so data survives process restarts.
    Each context becomes a separate Chroma collection.  AST statements
    are stored as pickled blobs in the document field for exact
    round-trip fidelity, while extracted subject/predicate/object
    strings are stored as metadata for structured ``where`` queries.
    ChromaDB also creates vector embeddings of the document text,
    enabling semantic similarity retrieval.

    Parameters
    ----------
    unification_engine : UnificationEngine
        Used for pattern matching and variable binding.
    persist_directory : str
        Filesystem path where ChromaDB stores its data.
    """

    def __init__(
        self,
        unification_engine: UnificationEngine,
        persist_directory: str = "./data/chroma",
    ) -> None:
        self.unification_engine = unification_engine
        self.persist_directory = os.path.abspath(persist_directory)

        # Ensure directory exists
        os.makedirs(self.persist_directory, exist_ok=True)

        self._client = chromadb.PersistentClient(path=self.persist_directory)

        # In-memory context metadata registry (rebuilt from Chroma on init)
        self._context_meta: Dict[str, Dict[str, Any]] = {}
        self._rebuild_context_meta()

        logger.info(
            "ChromaKnowledgeStore initialised at %s", self.persist_directory
        )

    # ------------------------------------------------------------------
    # Initialisation helpers
    # ------------------------------------------------------------------

    def _rebuild_context_meta(self) -> None:
        """Populate ``_context_meta`` from existing Chroma collections."""
        for col_info in self._client.list_collections():
            name = col_info if isinstance(col_info, str) else col_info.name
            col = self._client.get_collection(name)
            # Read context metadata we stash in a sentinel document
            meta = self._read_context_sentinel(col)
            self._context_meta[name] = meta

    def _read_context_sentinel(self, col) -> Dict[str, Any]:
        """Read the ``__context_meta__`` sentinel document from a collection."""
        try:
            result = col.get(ids=["__context_meta__"])
            if result and result["metadatas"] and result["metadatas"][0]:
                return result["metadatas"][0]
        except Exception:
            pass
        return {"parent": None, "type": "generic"}

    def _write_context_sentinel(self, col, meta: Dict[str, Any]) -> None:
        """Write / update the sentinel document that carries context metadata."""
        try:
            col.upsert(
                ids=["__context_meta__"],
                documents=["__context_meta__"],
                metadatas=[{k: v if v is not None else "" for k, v in meta.items()}],
            )
        except Exception:
            logger.exception("Failed to write context sentinel for %s", col.name)

    # ------------------------------------------------------------------
    # Serialisation helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _statement_id(statement: AST_Node, context_id: str) -> str:
        """Deterministic ID for a statement in a context."""
        blob = pickle.dumps(statement)
        return hashlib.sha256(blob).hexdigest()

    @staticmethod
    def _serialize_statement(statement: AST_Node) -> str:
        """Pickle → hex-encoded string (Chroma documents are text)."""
        return pickle.dumps(statement).hex()

    @staticmethod
    def _deserialize_statement(hex_str: str) -> AST_Node:
        """Hex string -> unpickled AST node."""
        return pickle.loads(bytes.fromhex(hex_str))  # noqa: S301 - trusted internal data

    @staticmethod
    def _extract_metadata(statement: AST_Node) -> Dict[str, str]:
        """Extract subject / predicate / object strings for Chroma metadata."""
        meta: Dict[str, str] = {"node_type": type(statement).__name__}
        if isinstance(statement, ApplicationNode):
            if isinstance(statement.operator, ConstantNode):
                meta["predicate"] = statement.operator.name
            if statement.arguments:
                first = statement.arguments[0]
                if isinstance(first, ConstantNode):
                    meta["subject"] = first.name
                if len(statement.arguments) > 1:
                    second = statement.arguments[1]
                    if isinstance(second, ConstantNode):
                        meta["object"] = second.name
        return meta

    @staticmethod
    def _statement_text(statement: AST_Node) -> str:
        """Human-readable text for Chroma embedding generation."""
        return str(statement)

    # ------------------------------------------------------------------
    # Collection access
    # ------------------------------------------------------------------

    def _get_collection(self, context_id: str):
        """Return the Chroma collection for *context_id*."""
        return self._client.get_collection(context_id)

    # ------------------------------------------------------------------
    # KnowledgeStoreBackend implementation
    # ------------------------------------------------------------------

    def add_statement(
        self,
        statement_ast: AST_Node,
        context_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        if context_id not in self._context_meta:
            raise ValueError(f"Context {context_id} does not exist")

        if metadata:
            statement_ast = statement_ast.with_updated_metadata(metadata)

        # Duplicate check
        if self.statement_exists(statement_ast, [context_id]):
            return False

        doc_id = self._statement_id(statement_ast, context_id)
        doc_text = self._statement_text(statement_ast)
        chroma_meta = self._extract_metadata(statement_ast)
        chroma_meta["_blob"] = self._serialize_statement(statement_ast)
        chroma_meta["timestamp"] = time.strftime(
            "%Y-%m-%dT%H:%M:%SZ", time.gmtime()
        )
        if metadata:
            confidence = metadata.get("confidence")
            if confidence is not None:
                chroma_meta["confidence"] = float(confidence)
            provenance = metadata.get("source") or metadata.get("provenance")
            if provenance is not None:
                chroma_meta["provenance"] = str(provenance)

        col = self._get_collection(context_id)
        col.add(ids=[doc_id], documents=[doc_text], metadatas=[chroma_meta])
        return True

    def retract_statement(
        self, statement_pattern_ast: AST_Node, context_id: str
    ) -> bool:
        if context_id not in self._context_meta:
            raise ValueError(f"Context {context_id} does not exist")

        col = self._get_collection(context_id)
        ids_to_delete: list[str] = []

        for doc_id, stmt in self._iter_statements(col):
            bindings, _ = self.unification_engine.unify(
                statement_pattern_ast, stmt
            )
            if bindings is not None:
                ids_to_delete.append(doc_id)

        if not ids_to_delete:
            return False

        col.delete(ids=ids_to_delete)
        return True

    def query_statements_match_pattern(
        self,
        query_pattern_ast: AST_Node,
        context_ids: List[str],
        variables_to_bind: Optional[List[VariableNode]] = None,
    ) -> List[Dict[VariableNode, AST_Node]]:
        results: list[Dict[VariableNode, AST_Node]] = []
        for context_id in context_ids:
            if context_id not in self._context_meta:
                raise ValueError(f"Context {context_id} does not exist")

            col = self._get_collection(context_id)
            for _, stmt in self._iter_statements(col):
                bindings, _ = self.unification_engine.unify(
                    query_pattern_ast, stmt
                )
                if bindings is not None:
                    if variables_to_bind:
                        filtered: Dict[VariableNode, AST_Node] = {}
                        for var in variables_to_bind:
                            if var.var_id in bindings:
                                filtered[var] = bindings[var.var_id]
                        results.append(filtered)
                    else:
                        query_vars: Dict[int, VariableNode] = {}
                        self._collect_variables(query_pattern_ast, query_vars)
                        var_bindings: Dict[VariableNode, AST_Node] = {}
                        for var_id, ast_node in bindings.items():
                            if var_id in query_vars:
                                var_bindings[query_vars[var_id]] = ast_node
                            else:
                                var_type = (
                                    self.unification_engine.type_system.get_type(
                                        "Entity"
                                    )
                                    or ast_node.type
                                )
                                var = VariableNode(
                                    f"?var{var_id}", var_id, var_type
                                )
                                var_bindings[var] = ast_node
                        results.append(var_bindings)
        return results

    def statement_exists(
        self, statement_ast: AST_Node, context_ids: List[str]
    ) -> bool:
        for context_id in context_ids:
            if context_id not in self._context_meta:
                raise ValueError(f"Context {context_id} does not exist")

            col = self._get_collection(context_id)
            for _, stmt in self._iter_statements(col):
                bindings, _ = self.unification_engine.unify(statement_ast, stmt)
                if bindings is not None:
                    return True
        return False

    def create_context(
        self,
        context_id: str,
        parent_context_id: Optional[str],
        context_type: str,
    ) -> None:
        if context_id in self._context_meta:
            raise ValueError(f"Context {context_id} already exists")
        if parent_context_id and parent_context_id not in self._context_meta:
            raise ValueError(
                f"Parent context {parent_context_id} does not exist"
            )

        meta = {"parent": parent_context_id or "", "type": context_type}
        col = self._client.get_or_create_collection(context_id)
        self._write_context_sentinel(col, meta)
        self._context_meta[context_id] = meta

    def delete_context(self, context_id: str) -> None:
        if context_id not in self._context_meta:
            raise ValueError(f"Context {context_id} does not exist")

        # Check for child contexts
        for cid, cmeta in self._context_meta.items():
            if cmeta.get("parent") == context_id:
                raise ValueError(
                    f"Cannot delete context {context_id} because it has child contexts"
                )

        self._client.delete_collection(context_id)
        del self._context_meta[context_id]

    def list_contexts(self) -> List[str]:
        return list(self._context_meta.keys())

    def get_context_info(self, context_id: str) -> Optional[Dict[str, Any]]:
        info = self._context_meta.get(context_id)
        if info is None:
            return None
        parent = info.get("parent")
        if parent == "":
            parent = None
        return {"parent": parent, "type": info.get("type", "generic")}

    def get_all_statements_in_context(self, context_id: str) -> Set[AST_Node]:
        """Return every statement stored in *context_id*."""
        if context_id not in self._context_meta:
            raise ValueError(f"Context {context_id} does not exist")
        col = self._get_collection(context_id)
        return {stmt for _, stmt in self._iter_statements(col)}

    # ------------------------------------------------------------------
    # Semantic retrieval (new capability for ChromaDB)
    # ------------------------------------------------------------------

    def query_by_similarity(
        self,
        query_text: str,
        context_id: str,
        n_results: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Semantic similarity search within a context.

        Parameters
        ----------
        query_text : str
            Natural-language query.
        context_id : str
            Which context collection to search.
        n_results : int
            Maximum number of results to return.

        Returns
        -------
        list of dicts
            Each dict has keys ``id``, ``document``, ``metadata``,
            ``distance``, and ``statement`` (the deserialized AST node).
        """
        if context_id not in self._context_meta:
            raise ValueError(f"Context {context_id} does not exist")
        col = self._get_collection(context_id)

        # Early return if collection is empty (minus sentinel doc)
        actual_count = max(col.count() - 1, 0)
        if actual_count == 0:
            return []

        n = min(n_results, actual_count)

        results = col.query(
            query_texts=[query_text],
            n_results=n,
            where={"_blob": {"$ne": ""}},  # exclude sentinel (no _blob field)
        )

        output: list[Dict[str, Any]] = []
        if results and results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                if doc_id == "__context_meta__":
                    continue
                meta = results["metadatas"][0][i] if results["metadatas"] else {}
                doc = results["documents"][0][i] if results["documents"] else ""
                dist = results["distances"][0][i] if results["distances"] else None
                stmt = None
                blob = meta.get("_blob")
                if blob:
                    try:
                        stmt = self._deserialize_statement(blob)
                    except Exception:
                        pass
                output.append(
                    {
                        "id": doc_id,
                        "document": doc,
                        "metadata": {k: v for k, v in meta.items() if k != "_blob"},
                        "distance": dist,
                        "statement": stmt,
                    }
                )
        return output

    def query_by_metadata(
        self,
        context_id: str,
        filters: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Structured metadata query within a context.

        Parameters
        ----------
        context_id : str
            Which context collection to search.
        filters : dict
            ChromaDB ``where`` filter dict, e.g. ``{"predicate": "Human"}``.

        Returns
        -------
        list of dicts
            Each dict has ``id``, ``document``, ``metadata``, and
            ``statement``.
        """
        if context_id not in self._context_meta:
            raise ValueError(f"Context {context_id} does not exist")
        col = self._get_collection(context_id)
        results = col.get(where=filters)

        output: list[Dict[str, Any]] = []
        if results and results["ids"]:
            for i, doc_id in enumerate(results["ids"]):
                if doc_id == "__context_meta__":
                    continue
                meta = results["metadatas"][i] if results["metadatas"] else {}
                doc = results["documents"][i] if results["documents"] else ""
                stmt = None
                blob = meta.get("_blob")
                if blob:
                    try:
                        stmt = self._deserialize_statement(blob)
                    except Exception:
                        pass
                output.append(
                    {
                        "id": doc_id,
                        "document": doc,
                        "metadata": {k: v for k, v in meta.items() if k != "_blob"},
                        "statement": stmt,
                    }
                )
        return output

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _iter_statements(self, col):
        """Yield ``(doc_id, AST_Node)`` for every real statement in *col*."""
        result = col.get()
        if not result or not result["ids"]:
            return
        for i, doc_id in enumerate(result["ids"]):
            if doc_id == "__context_meta__":
                continue
            meta = result["metadatas"][i] if result["metadatas"] else {}
            blob = meta.get("_blob")
            if blob:
                try:
                    yield doc_id, self._deserialize_statement(blob)
                except Exception:
                    logger.warning("Could not deserialise statement %s", doc_id)

    @staticmethod
    def _collect_variables(
        node: AST_Node, var_map: Dict[int, VariableNode]
    ) -> None:
        from godelOS.core_kr.ast.nodes import ConnectiveNode

        if isinstance(node, VariableNode):
            var_map[node.var_id] = node
        elif isinstance(node, ApplicationNode):
            ChromaKnowledgeStore._collect_variables(node.operator, var_map)
            for arg in node.arguments:
                ChromaKnowledgeStore._collect_variables(arg, var_map)
        elif isinstance(node, ConnectiveNode):
            for operand in node.operands:
                ChromaKnowledgeStore._collect_variables(operand, var_map)
