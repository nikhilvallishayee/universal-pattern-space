"""conftest.py for tests/api/

Prevents the root conftest from triggering heavy ``backend.*`` imports
that are not needed for the isolated external API tests.
"""
