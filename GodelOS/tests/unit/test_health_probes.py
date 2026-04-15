import pytest
import types
import asyncio

from backend import unified_server as us


@pytest.mark.unit
def test_health_probes_are_present_and_timestamped(monkeypatch):
    # Patch vector DB getter to avoid creating real DB
    class StubVDB:
        def health_check(self):
            return {"status": "healthy", "timestamp": 123.0}

    monkeypatch.setattr(us, "VECTOR_DATABASE_AVAILABLE", True)
    monkeypatch.setattr(us, "get_vector_database", lambda: StubVDB())

    # Patch knowledge pipeline service
    class StubPipeline:
        def get_statistics(self):
            return {"status": "healthy", "initialized": True}

    monkeypatch.setattr(us, "KNOWLEDGE_SERVICES_AVAILABLE", True)
    monkeypatch.setattr(us, "knowledge_pipeline_service", StubPipeline())

    # Patch ingestion service
    class StubQueue:
        def qsize(self):
            return 0

    class StubIngestion:
        processing_task = object()
        import_queue = StubQueue()

    monkeypatch.setattr(us, "knowledge_ingestion_service", StubIngestion())

    # Patch cognitive manager
    class StubCM:
        active_sessions = {}

    monkeypatch.setattr(us, "cognitive_manager", StubCM())
    monkeypatch.setattr(us, "ENHANCED_APIS_AVAILABLE", True)

    resp = asyncio.run(us.health_check())
    assert resp["status"] == "healthy"
    probes = resp["probes"]
    # Check expected keys
    for key in [
        "vector_database",
        "knowledge_pipeline",
        "knowledge_ingestion",
        "cognitive_manager",
        "enhanced_apis",
    ]:
        assert key in probes
        assert isinstance(probes[key], dict)
        # Each probe should have a timestamp (added by endpoint)
        assert "timestamp" in probes[key]
