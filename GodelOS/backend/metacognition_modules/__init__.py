"""Compatibility shim: re-exports from the root-level metacognition_modules package.

Several modules (e.g. backend.enhanced_cognitive_api) import from
``backend.metacognition_modules``.  The real code lives at
``<repo_root>/metacognition_modules/``.  This package ensures every
attribute / sub-module request is forwarded there.
"""

import importlib
import os
import sys

# Ensure the root-level metacognition_modules is importable
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _root not in sys.path:
    sys.path.insert(0, _root)

_real = importlib.import_module('metacognition_modules')

# Register sub-module aliases so that
# ``from backend.metacognition_modules.foo import Bar`` works.
_submodules = [
    'cognitive_models',
    'enhanced_metacognition_manager',
    'knowledge_gap_detector',
    'autonomous_knowledge_acquisition',
    'stream_coordinator',
    'enhanced_self_monitoring',
]

for _sub in _submodules:
    _fqn_alias = f'backend.metacognition_modules.{_sub}'
    if _fqn_alias not in sys.modules:
        try:
            _real_sub = importlib.import_module(f'metacognition_modules.{_sub}')
            sys.modules[_fqn_alias] = _real_sub
        except ImportError:
            pass


def __getattr__(name):
    """Proxy attribute access to the real metacognition_modules package."""
    return getattr(_real, name)


