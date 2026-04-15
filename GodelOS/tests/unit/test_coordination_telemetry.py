import asyncio
import json
import pytest
from fastapi import HTTPException

from backend import unified_server as us


@pytest.mark.unit
def test_coordination_recent_requires_manager(monkeypatch):
    monkeypatch.setattr(us, "cognitive_manager", None)
    with pytest.raises(HTTPException) as ei:
        asyncio.run(us.get_recent_coordination_decisions())
    exc = ei.value
    assert exc.status_code == 503
    assert isinstance(exc.detail, dict)
    assert exc.detail.get("code") == "cognitive_manager_unavailable"
    assert exc.detail.get("details", {}).get("service") == "coordination"


@pytest.mark.unit
def test_coordination_recent_returns_data(monkeypatch):
    class StubCM:
        def get_recent_coordination_decisions(self, limit=20):
            return [
                {"timestamp": 1000.0, "session_id": "s1", "decision": {"action": "proceed", "params": {}, "rationale": "ok"}},
                {"timestamp": 1001.0, "session_id": "s2", "decision": {"action": "augment_context", "params": {"suggested_sources": []}, "rationale": "low confidence"}},
            ]

    monkeypatch.setattr(us, "cognitive_manager", StubCM())

    res = asyncio.run(us.get_recent_coordination_decisions(limit=2))
    # JSONResponse -> bytes body
    payload = json.loads(res.body.decode())
    assert payload["count"] == 2
    assert len(payload["decisions"]) == 2
    assert payload["decisions"][0]["session_id"] == "s1"
    assert payload["decisions"][1]["decision"]["action"] == "augment_context"

