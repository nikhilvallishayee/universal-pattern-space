"""
Test fixture utilities for GödelOS

This module provides utilities for loading test fixtures in a consistent way.
"""

import json
from pathlib import Path
from typing import Any, Dict

FIXTURES_DIR = Path(__file__).parent / "fixtures"

def load_fixture(fixture_name: str, subfolder: str = None) -> Any:
    """Load a test fixture from JSON file"""
    if subfolder:
        fixture_path = FIXTURES_DIR / subfolder / f"{fixture_name}.json"
    else:
        fixture_path = FIXTURES_DIR / f"{fixture_name}.json"
    
    if not fixture_path.exists():
        raise FileNotFoundError(f"Fixture not found: {fixture_path}")
    
    with open(fixture_path) as f:
        return json.load(f)

def load_cognitive_state(state_name: str = "default") -> Dict:
    """Load a cognitive state fixture"""
    return load_fixture(state_name, "cognitive_states")

def load_api_response(endpoint: str) -> Dict:
    """Load an API response fixture"""
    return load_fixture(endpoint, "api_responses")

def load_sample_data(data_type: str) -> Any:
    """Load sample data fixture"""
    return load_fixture(data_type, "sample_data")
