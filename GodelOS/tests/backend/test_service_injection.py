import sys
import types
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from fastapi import APIRouter


class DummyService:
    def __init__(self):
        self.websocket_manager = None
        self.initialized = False

    async def initialize(self, *args, **kwargs):
        print("🤖 DummyService initialized")
        self.initialized = True

    async def shutdown(self):
        print("👋 DummyService shutdown")


class DummyPipeline(DummyService):
    async def initialize(self, websocket_manager=None):
        print("🤖 DummyPipeline initialized")
        self.websocket_manager = websocket_manager
        self.initialized = True


class _WebSocketManagerStub:
    def __init__(self):
        self.active_connections = []
    def has_connections(self):
        return False
    async def broadcast(self, msg):
        pass
    async def connect(self, websocket):
        pass


class _GödelOSIntegrationStub:
    async def initialize(self):
        pass
    async def shutdown(self):
        pass
    async def get_cognitive_state(self):
        return {}


def _install_stubs():
    """Install lightweight stubs for heavy backend modules."""
    stubs = {}

    ki = types.ModuleType("backend.knowledge_ingestion")
    ki.knowledge_ingestion_service = DummyService()
    stubs["backend.knowledge_ingestion"] = ki

    km = types.ModuleType("backend.knowledge_management")
    km.knowledge_management_service = DummyService()
    stubs["backend.knowledge_management"] = km

    kp = types.ModuleType("backend.knowledge_pipeline_service")
    kp.knowledge_pipeline_service = DummyPipeline()
    stubs["backend.knowledge_pipeline_service"] = kp

    ct = types.ModuleType("backend.cognitive_transparency_integration")
    class _CT:
        router = APIRouter()
        async def initialize(self, *a, **kw): pass
        async def shutdown(self, *a, **kw): pass
    ct.cognitive_transparency_api = _CT()
    stubs["backend.cognitive_transparency_integration"] = ct

    eca = types.ModuleType("backend.enhanced_cognitive_api")
    eca.router = APIRouter()
    async def _init_eca(*a, **kw): pass
    eca.initialize_enhanced_cognitive = _init_eca
    stubs["backend.enhanced_cognitive_api"] = eca

    cm = types.ModuleType("backend.config_manager")
    cm.get_config = lambda *a, **kw: {}
    cm.is_feature_enabled = lambda *a, **kw: False
    stubs["backend.config_manager"] = cm

    wm = types.ModuleType("backend.websocket_manager")
    wm.WebSocketManager = _WebSocketManagerStub
    stubs["backend.websocket_manager"] = wm

    gi = types.ModuleType("backend.godelos_integration")
    gi.GödelOSIntegration = _GödelOSIntegrationStub
    stubs["backend.godelos_integration"] = gi

    lcd = types.ModuleType("backend.llm_cognitive_driver")
    async def _get_lcd(*a, **kw): return None
    lcd.get_llm_cognitive_driver = _get_lcd
    stubs["backend.llm_cognitive_driver"] = lcd

    # Save originals and inject stubs
    originals = {}
    for name, stub in stubs.items():
        if name in sys.modules:
            originals[name] = sys.modules[name]
        sys.modules[name] = stub

    return originals


def _restore_modules(originals):
    """Restore real modules (or remove stubs) from sys.modules."""
    stub_names = [
        "backend.knowledge_ingestion",
        "backend.knowledge_management",
        "backend.knowledge_pipeline_service",
        "backend.cognitive_transparency_integration",
        "backend.enhanced_cognitive_api",
        "backend.config_manager",
        "backend.websocket_manager",
        "backend.godelos_integration",
        "backend.llm_cognitive_driver",
    ]
    for name in stub_names:
        if name in originals:
            sys.modules[name] = originals[name]
        else:
            sys.modules.pop(name, None)


def test_service_injection_allows_mocks():
    originals = _install_stubs()
    try:
        # Force-reload backend.main so it picks up stubs
        sys.modules.pop("backend.main", None)
        from backend.main import create_app

        print("Given 🧪 mock services and a fake WebSocket manager")
        ws_mock = _WebSocketManagerStub()
        ingestion = DummyService()
        management = DummyService()
        pipeline = DummyPipeline()

        with patch('backend.main.GödelOSIntegration') as MockIntegration, \
             patch('backend.main.cognitive_transparency_api.initialize', new=AsyncMock()), \
             patch('backend.main.cognitive_transparency_api.shutdown', new=AsyncMock()), \
             patch('backend.main.get_llm_cognitive_driver', new=AsyncMock(return_value=None)):
            MockIntegration.return_value.initialize = AsyncMock()
            MockIntegration.return_value.shutdown = AsyncMock()
            MockIntegration.return_value.get_cognitive_state = AsyncMock(return_value={})

            app = create_app(
                ws_manager=ws_mock,
                ingestion_service=ingestion,
                knowledge_management=management,
                knowledge_pipeline=pipeline,
            )

            print("When 🚀 the app starts")
            with TestClient(app):
                pass

        create_app()  # Reset overrides for other tests

        print("Then ✅ the mocks are wired without side effects")
        assert ingestion.websocket_manager is ws_mock
        assert pipeline.websocket_manager is ws_mock
        assert ingestion.initialized
        assert management.initialized
        assert pipeline.initialized
    finally:
        _restore_modules(originals)
