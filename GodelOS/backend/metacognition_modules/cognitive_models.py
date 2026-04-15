"""Compatibility shim: re-exports everything from metacognition_modules.cognitive_models."""

import os, sys

# Ensure the root-level metacognition_modules is on sys.path
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _root not in sys.path:
    sys.path.insert(0, _root)

from metacognition_modules.cognitive_models import *
