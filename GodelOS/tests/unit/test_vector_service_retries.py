import time
import pytest
import sys
import types

# Provide a fake vector_database before importing vector_service to avoid faiss dep
fake_vdb = types.ModuleType('backend.core.vector_database')
class _StubPVD:  # PersistentVectorDatabase stub (not used in tests)
    pass
fake_vdb.PersistentVectorDatabase = _StubPVD
fake_vdb.EmbeddingModel = object
sys.modules['backend.core.vector_database'] = fake_vdb

from backend.core import vector_service as vs


@pytest.mark.unit
def test_add_items_retries_and_telemetry(monkeypatch):
    events = []
    vs.set_telemetry_notifier(lambda e: events.append(e))

    class FakeProdDB:
        def __init__(self):
            self.calls = 0
        def add_items(self, items, **kwargs):
            self.calls += 1
            if self.calls < 3:
                raise RuntimeError("transient failure")
            return {"success": True}

    svc = vs.VectorDatabaseService.__new__(vs.VectorDatabaseService)
    svc.storage_dir = "/tmp"
    svc.enable_migration = False
    svc.legacy_fallback = False
    svc.production_db = FakeProdDB()
    svc.use_production = True
    svc.legacy_store = None

    ok = svc.add_items([("id1", "text")])
    assert ok is True
    # Two failures should emit two recoverable events
    assert len(events) >= 2
    assert all(e.get("type") == "recoverable_error" and e.get("service") == "vector_db" for e in events[:2])


@pytest.mark.unit
def test_search_retries_and_returns_legacy_format(monkeypatch):
    class FakeProdDB:
        def __init__(self):
            self.calls = 0
        def search(self, query_text, k=5, **kwargs):
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("transient search error")
            return [{"id": "a", "similarity_score": 0.9}, {"id": "b", "score": 0.8}]

    svc = vs.VectorDatabaseService.__new__(vs.VectorDatabaseService)
    svc.storage_dir = "/tmp"
    svc.enable_migration = False
    svc.legacy_fallback = False
    svc.production_db = FakeProdDB()
    svc.use_production = True
    svc.legacy_store = None

    results = svc.search("hello", k=2)
    assert results == [("a", 0.9), ("b", 0.8)]


@pytest.mark.unit
def test_add_items_raises_when_no_fallback(monkeypatch):
    class AlwaysFailDB:
        def add_items(self, items, **kwargs):
            raise RuntimeError("persistent failure")

    svc = vs.VectorDatabaseService.__new__(vs.VectorDatabaseService)
    svc.storage_dir = "/tmp"
    svc.enable_migration = False
    svc.legacy_fallback = False
    svc.production_db = AlwaysFailDB()
    svc.use_production = True
    svc.legacy_store = None

    with pytest.raises(RuntimeError):
        svc.add_items([("id1", "text")])
