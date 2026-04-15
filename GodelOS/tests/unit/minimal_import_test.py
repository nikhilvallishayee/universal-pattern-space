#!/usr/bin/env python3
"""
Minimal test to isolate import issues.
"""

import sys
import os
from pathlib import Path

# Add paths
project_root = Path(__file__).resolve().parents[2]
# Ensure the repository root is on sys.path for absolute imports
sys.path.insert(0, str(project_root))

print("🔍 Testing individual imports...")

try:
    print("1. Testing basic Python imports...")
    import asyncio
    import logging
    import time
    from typing import Dict, List, Optional, Any
    print("✅ Basic imports successful")
    
    print("2. Testing GödelOS core imports...")
    try:
        from godelOS.core_kr.type_system.manager import TypeSystemManager
        print("✅ TypeSystemManager imported")
    except Exception as e:
        print(f"⚠️  TypeSystemManager failed: {e}")
    
    try:
        from godelOS.core_kr.ast.nodes import ConstantNode
        print("✅ AST nodes imported")
    except Exception as e:
        print(f"⚠️  AST nodes failed: {e}")
    
    print("3. Testing backend imports...")
    try:
        from backend.models import ReasoningStep
        print("✅ Backend models imported")
    except Exception as e:
        print(f"⚠️  Backend models failed: {e}")
    
    print("4. Testing integration class definition...")
    # Import just the module without instantiating
    import backend.godelos_integration
    print("✅ Integration module imported")
    
    print("5. Testing class instantiation...")
    integration = backend.godelos_integration.GödelOSIntegration()
    print("✅ Integration class instantiated")
    
    print("✅ All tests passed!")
    
except Exception as e:
    print(f"❌ Import test failed: {e}")
    import traceback
    traceback.print_exc()
