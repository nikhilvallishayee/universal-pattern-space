"""Compatibility shim: backend.main → backend.unified_server.

Several test modules import from ``backend.main``.  After the server
consolidation the canonical module is ``backend.unified_server``.  This
shim replaces itself in ``sys.modules`` with the real module so that:

* ``from backend.main import app`` works
* ``patch('backend.main.godelos_integration', …)`` patches the actual
  global used by endpoint handlers.
"""

import sys
import importlib

# Import the canonical module.
import backend.unified_server as _unified  # noqa: E402

# Expose a ``create_app`` factory expected by legacy test_service_injection.
# The factory wires the provided services into the module-level globals that
# the lifespan and endpoint handlers reference.
# Stores original values of unified_server module attributes when create_app()
# performs service injection, allowing proper restoration on reset.
_ORIG = {}


def create_app(
    ws_manager=None,
    ingestion_service=None,
    knowledge_management=None,
    knowledge_pipeline=None,
):
    """Create (or reset) the FastAPI app with optional dependency overrides.

    When called with service arguments, returns a lightweight copy of the app
    whose lifespan only wires the injected services (instead of running the
    full ``initialize_core_services`` / ``initialize_optional_services`` which
    would overwrite the injected globals).

    When called with no arguments, restores original globals and returns the
    canonical ``app``.
    """
    import asyncio
    from contextlib import asynccontextmanager
    from fastapi import FastAPI

    has_overrides = any(
        arg is not None
        for arg in (ws_manager, ingestion_service, knowledge_management, knowledge_pipeline)
    )

    if not has_overrides:
        # Reset any previously saved originals
        for key, val in _ORIG.items():
            setattr(_unified, key, val)
        _ORIG.clear()
        return _unified.app

    # --- Service injection path ---

    if ws_manager is not None:
        _ORIG.setdefault("websocket_manager", _unified.websocket_manager)
        _unified.websocket_manager = ws_manager

    if ingestion_service is not None:
        _ORIG.setdefault("knowledge_ingestion_service", getattr(_unified, "knowledge_ingestion_service", None))
        _unified.knowledge_ingestion_service = ingestion_service
        ingestion_service.websocket_manager = ws_manager

    if knowledge_management is not None:
        _ORIG.setdefault("knowledge_management_service", getattr(_unified, "knowledge_management_service", None))
        _unified.knowledge_management_service = knowledge_management

    if knowledge_pipeline is not None:
        _ORIG.setdefault("knowledge_pipeline_service", getattr(_unified, "knowledge_pipeline_service", None))
        _unified.knowledge_pipeline_service = knowledge_pipeline
        knowledge_pipeline.websocket_manager = ws_manager

    # Build a thin lifespan that initialises only the injected services
    # (mirrors what the old ``backend/main.py`` did) without touching any of
    # the module-level globals that were just set above.
    @asynccontextmanager
    async def _test_lifespan(_app: FastAPI):
        # Startup: initialize the injected services
        if ingestion_service is not None:
            await ingestion_service.initialize(ws_manager)
        if knowledge_management is not None:
            await knowledge_management.initialize()
        if knowledge_pipeline is not None:
            await knowledge_pipeline.initialize(websocket_manager=ws_manager)

        yield  # --- application runs here ---

        # Shutdown: nothing to tear down for test doubles

    # Copy the real app's routes into a lightweight FastAPI instance whose
    # lifespan does not reinitialise the world.
    test_app = FastAPI(lifespan=_test_lifespan)
    test_app.router.routes = _unified.app.router.routes
    # Preserve exception handlers registered on the real app
    test_app.exception_handlers = dict(getattr(_unified.app, "exception_handlers", {}))

    return test_app


# Ensure legacy module-level attributes that old tests patch are present on
# the unified module before we swap.  These were globals in the original
# ``backend/main.py`` and tests do ``patch('backend.main.<attr>', ...)``.

_unified.create_app = create_app

# cognitive_transparency_api – imported lazily inside unified_server handlers;
# expose a module-level reference so that ``patch(...)`` can find it.
if not hasattr(_unified, "cognitive_transparency_api"):
    try:
        from backend.cognitive_transparency_integration import cognitive_transparency_api as _cta
        _unified.cognitive_transparency_api = _cta
    except Exception:
        _unified.cognitive_transparency_api = None

# get_llm_cognitive_driver – factory function from llm_cognitive_driver
if not hasattr(_unified, "get_llm_cognitive_driver"):
    try:
        from backend.llm_cognitive_driver import get_llm_cognitive_driver as _glcd
        _unified.get_llm_cognitive_driver = _glcd
    except Exception:
        _unified.get_llm_cognitive_driver = None

# Replace this module in sys.modules with the unified_server module.
sys.modules[__name__] = _unified
