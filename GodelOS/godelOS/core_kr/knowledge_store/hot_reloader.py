"""
Ontology Hot-Reloader.

Watches a configured directory for ``.ttl`` and ``.json-ld`` files.  When a
file is created, modified, or deleted the reloader computes a delta against
the current knowledge graph and applies it without requiring a full restart.
"""

import json
import logging
import os
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Set

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

logger = logging.getLogger(__name__)

# Supported ontology file extensions
_SUPPORTED_EXTENSIONS = {".ttl", ".json-ld"}


def _parse_jsonld_triples(path: str) -> Set[tuple]:
    """
    Parse a JSON-LD file and return a set of ``(subject, predicate, object)``
    triples suitable for diffing.
    """
    triples: Set[tuple] = set()
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        items = data if isinstance(data, list) else data.get("@graph", [data])
        for item in items:
            subject = item.get("@id", "")
            for key, value in item.items():
                if key.startswith("@"):
                    continue
                values = value if isinstance(value, list) else [value]
                for v in values:
                    if isinstance(v, dict):
                        obj = v.get("@id", v.get("@value", str(v)))
                    else:
                        obj = str(v)
                    triples.add((subject, key, obj))
    except Exception:
        logger.exception("Failed to parse JSON-LD file %s", path)
    return triples


def _parse_ttl_triples(path: str) -> Set[tuple]:
    """
    Parse a minimal Turtle (``.ttl``) file and return a set of
    ``(subject, predicate, object)`` triples.

    This is a lightweight parser covering the common ``<s> <p> <o> .`` form
    and simple prefixed names.  It is **not** a full Turtle parser.
    """
    triples: Set[tuple] = set()
    prefixes: Dict[str, str] = {}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for raw_line in fh:
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.lower().startswith("@prefix"):
                    parts = line.rstrip(".").split()
                    if len(parts) >= 3:
                        prefix = parts[1].rstrip(":")
                        uri = parts[2].strip("<>")
                        prefixes[prefix] = uri
                    continue
                # Attempt to split a simple triple line
                line = line.rstrip(".")
                parts = line.split(None, 2)
                if len(parts) == 3:
                    s, p, o = (t.strip().strip("<>") for t in parts)
                    triples.add((s, p, o))
    except Exception:
        logger.exception("Failed to parse TTL file %s", path)
    return triples


def _parse_file(path: str) -> Set[tuple]:
    """Dispatch to the correct parser based on extension."""
    lower_path = path.lower()
    if lower_path.endswith(".json-ld"):
        return _parse_jsonld_triples(path)
    if lower_path.endswith(".ttl"):
        return _parse_ttl_triples(path)
    return set()


class OntologyHotReloader:
    """
    Watch a directory for ontology file changes and apply deltas to a
    knowledge graph callback.

    Parameters
    ----------
    watch_dir : str
        Filesystem directory to monitor.
    on_add : callable(subject, predicate, object) -> None
        Called for each triple that is *new* relative to the previous snapshot.
    on_remove : callable(subject, predicate, object) -> None
        Called for each triple that was *removed* relative to the previous
        snapshot.
    debounce_seconds : float
        Minimum interval between reloads (default 1.0 s).
    """

    def __init__(
        self,
        watch_dir: str,
        on_add: Callable[..., None],
        on_remove: Callable[..., None],
        debounce_seconds: float = 1.0,
    ) -> None:
        self.watch_dir = os.path.abspath(watch_dir)
        self._on_add = on_add
        self._on_remove = on_remove
        self._debounce = debounce_seconds

        self._observer: Optional[Observer] = None
        self._snapshot: Dict[str, Set[tuple]] = {}
        self._lock = threading.Lock()
        self._last_reload: float = 0.0

        # Build initial snapshot
        os.makedirs(self.watch_dir, exist_ok=True)
        self._snapshot = self._build_snapshot()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Begin watching the directory for changes."""
        handler = _Handler(self._on_change)
        self._observer = Observer()
        self._observer.schedule(handler, self.watch_dir, recursive=False)
        self._observer.daemon = True
        self._observer.start()
        logger.info("OntologyHotReloader watching %s", self.watch_dir)

    def stop(self) -> None:
        """Stop the file-system watcher."""
        if self._observer is not None:
            self._observer.stop()
            self._observer.join(timeout=5)
            self._observer = None
            logger.info("OntologyHotReloader stopped")

    def reload(self) -> None:
        """Force an immediate reload (useful for testing)."""
        self._do_reload()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _build_snapshot(self) -> Dict[str, Set[tuple]]:
        snapshot: Dict[str, Set[tuple]] = {}
        if not os.path.isdir(self.watch_dir):
            return snapshot
        for name in os.listdir(self.watch_dir):
            path = os.path.join(self.watch_dir, name)
            if not os.path.isfile(path):
                continue
            if not any(name.lower().endswith(ext) for ext in _SUPPORTED_EXTENSIONS):
                continue
            snapshot[path] = _parse_file(path)
        return snapshot

    def _on_change(self, event: FileSystemEvent) -> None:
        now = time.monotonic()
        if now - self._last_reload < self._debounce:
            return
        path = event.src_path
        if not any(path.lower().endswith(ext) for ext in _SUPPORTED_EXTENSIONS):
            return
        self._do_reload()

    def _do_reload(self) -> None:
        with self._lock:
            new_snapshot = self._build_snapshot()

            old_all: Set[tuple] = set()
            for triples in self._snapshot.values():
                old_all |= triples
            new_all: Set[tuple] = set()
            for triples in new_snapshot.values():
                new_all |= triples

            added = new_all - old_all
            removed = old_all - new_all

            for s, p, o in added:
                try:
                    self._on_add(s, p, o)
                except Exception:
                    logger.exception("on_add callback failed for (%s, %s, %s)", s, p, o)

            for s, p, o in removed:
                try:
                    self._on_remove(s, p, o)
                except Exception:
                    logger.exception(
                        "on_remove callback failed for (%s, %s, %s)", s, p, o
                    )

            self._snapshot = new_snapshot
            self._last_reload = time.monotonic()

            if added or removed:
                logger.info(
                    "OntologyHotReloader applied delta: +%d -%d triples",
                    len(added),
                    len(removed),
                )


class _Handler(FileSystemEventHandler):
    """Watchdog handler that delegates to a single callback."""

    def __init__(self, callback: Callable[..., None]) -> None:
        super().__init__()
        self._callback = callback

    def on_created(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._callback(event)

    def on_modified(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._callback(event)

    def on_deleted(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._callback(event)
