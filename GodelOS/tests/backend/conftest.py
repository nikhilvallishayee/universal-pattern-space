"""conftest.py for tests/backend/

``test_service_injection.py`` replaces several ``backend.*`` entries in
``sys.modules`` at **import time** (module scope) so that the heavy real
modules are not loaded during its single test.  This happens during
collection, before any fixtures run.

We fix the pollution in two places:

1. ``pytest_collection_modifyitems`` — runs after *all* items are collected,
   so we flush the stubs and let normal imports work again.
2. An autouse fixture that does the same after every test in this package.
"""
import importlib
import sys
import types
import pytest

# Modules that test_service_injection.py replaces with stubs at module scope.
_GUARDED_MODULES = [
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


def _is_stub(mod):
    """Return True if *mod* looks like one of the test_service_injection stubs."""
    if mod is None:
        return False
    # Stubs are bare ``types.ModuleType`` instances with no ``__file__``
    return (
        isinstance(mod, types.ModuleType)
        and getattr(mod, "__file__", None) is None
        and getattr(mod, "__path__", None) is None
    )


def _flush_stubs():
    """Remove any stub modules injected by test_service_injection.py."""
    for name in _GUARDED_MODULES:
        mod = sys.modules.get(name)
        if _is_stub(mod):
            del sys.modules[name]


# ---- hooks ----

def pytest_collection_modifyitems(session, config, items):
    """Flush stubs after collection so later packages import the real code."""
    _flush_stubs()


@pytest.fixture(autouse=True)
def _restore_sys_modules():
    """Flush stubs after each test in this package."""
    yield
    _flush_stubs()
