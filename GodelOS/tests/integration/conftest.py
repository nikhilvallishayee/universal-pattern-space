"""
Local conftest for ``tests/integration/``.

The root conftest auto-tags every file under ``integration/`` with the
``requires_backend`` marker.  The cognitive-pipeline integration tests
exercise core subsystems **in-process** and never contact a running server,
so they carry the ``standalone`` marker that suppresses the backend check.
"""
