"""
Feature: Ensure critical runtime dependencies are available

Scenario: Importing core packages succeeds
    Given the runtime environment
    When importing FastAPI, Pydantic, and spaCy
    Then they are available without ImportError
"""
import importlib
import pytest

REQUIRED_PACKAGES = ["fastapi", "pydantic", "spacy"]


@pytest.mark.unit
def test_imports():
    for pkg in REQUIRED_PACKAGES:
        try:
            importlib.import_module(pkg)
            print(f"✅ {pkg} imported")
        except Exception as exc:
            pytest.fail(f"❌ {pkg} failed to import: {exc}")

