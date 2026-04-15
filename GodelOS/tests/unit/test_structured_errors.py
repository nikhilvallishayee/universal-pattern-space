import asyncio
import pytest
from fastapi import HTTPException

from backend import unified_server as us


@pytest.mark.unit
def test_consciousness_state_structured_error_when_unavailable(monkeypatch):
    # Force unavailability
    monkeypatch.setattr(us, "cognitive_manager", None)
    with pytest.raises(HTTPException) as ei:
        asyncio.run(us.get_consciousness_state())
    exc = ei.value
    assert exc.status_code == 503
    assert isinstance(exc.detail, dict)
    assert exc.detail.get("code") == "cognitive_manager_unavailable"
    assert exc.detail.get("details", {}).get("service") == "consciousness"


@pytest.mark.unit
def test_phenomenal_generate_structured_error_when_unavailable(monkeypatch):
    monkeypatch.setattr(us, "cognitive_manager", None)
    with pytest.raises(HTTPException) as ei:
        asyncio.run(us.generate_phenomenal_experience({"experience_type": "cognitive"}))
    exc = ei.value
    assert exc.status_code == 503
    assert isinstance(exc.detail, dict)
    assert exc.detail.get("code") == "cognitive_manager_unavailable"
    assert exc.detail.get("details", {}).get("service") == "phenomenal"


@pytest.mark.unit
def test_kg_summary_structured_error_when_unavailable(monkeypatch):
    monkeypatch.setattr(us, "cognitive_manager", None)
    with pytest.raises(HTTPException) as ei:
        asyncio.run(us.get_knowledge_graph_summary())
    exc = ei.value
    assert exc.status_code == 503
    assert isinstance(exc.detail, dict)
    assert exc.detail.get("code") == "cognitive_manager_unavailable"
    assert exc.detail.get("details", {}).get("service") == "knowledge_graph"

