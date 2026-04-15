"""
Prediction Error Tracker — pure time-series analysis of grounding prediction errors.

No imports from ``backend/``.  No consciousness concepts.
This module provides rolling statistics and histogram analysis over a stream
of ``GroundingPredictionError`` records.
"""

import math
from collections import defaultdict
from typing import Any, Dict, List, Optional

from godelOS.symbol_grounding.symbol_grounding_associator import GroundingPredictionError


class PredictionErrorTracker:
    """Rolling statistics over a window of ``GroundingPredictionError`` records."""

    def __init__(self, window_size: int = 50) -> None:
        self._window_size = window_size
        self._errors: List[GroundingPredictionError] = []

    # ── recording ──────────────────────────────────────────────────────

    def record(self, error: GroundingPredictionError) -> None:
        """Append *error* and trim to window size."""
        self._errors.append(error)
        if len(self._errors) > self._window_size:
            self._errors = self._errors[-self._window_size:]

    # ── aggregate statistics ──────────────────────────────────────────

    def mean_error_norm(self, last_n: Optional[int] = None) -> float:
        """Mean ``error_norm`` over the most-recent *last_n* records (or all)."""
        if not self._errors:
            return 0.0
        subset = self._errors[-last_n:] if last_n else self._errors
        return sum(e.error_norm for e in subset) / len(subset)

    def error_rate_of_change(self) -> float:
        """Approximate d(mean_error)/dt via first-half vs second-half mean."""
        n = len(self._errors)
        if n < 2:
            return 0.0
        mid = n // 2
        first_half = self._errors[:mid]
        second_half = self._errors[mid:]
        mean_first = sum(e.error_norm for e in first_half) / len(first_half)
        mean_second = sum(e.error_norm for e in second_half) / len(second_half)
        dt = second_half[-1].timestamp - first_half[0].timestamp
        if dt == 0.0:
            return 0.0
        return (mean_second - mean_first) / dt

    def per_symbol_error(self) -> Dict[str, float]:
        """Mean ``error_norm`` grouped by ``symbol_ast_id``."""
        groups: Dict[str, List[float]] = defaultdict(list)
        for e in self._errors:
            groups[e.symbol_ast_id].append(e.error_norm)
        return {sym: sum(v) / len(v) for sym, v in groups.items()}

    # ── histogram / distribution ──────────────────────────────────────

    _NUM_BUCKETS = 10

    def error_distribution(self) -> Dict[str, Any]:
        """
        10-bucket histogram of ``error_norm`` values.

        Returns a dict with keys:
          bucket_edges, bucket_counts, min, max, mean, sample_count
        """
        norms = [e.error_norm for e in self._errors]
        n = len(norms)
        if n == 0:
            return {
                "bucket_edges": [],
                "bucket_counts": [],
                "min": 0.0,
                "max": 0.0,
                "mean": 0.0,
                "sample_count": 0,
            }

        lo, hi = min(norms), max(norms)
        mean_val = sum(norms) / n

        # Avoid zero-width bins
        if lo == hi:
            hi = lo + 1e-9

        width = (hi - lo) / self._NUM_BUCKETS
        edges = [lo + i * width for i in range(self._NUM_BUCKETS + 1)]
        counts = [0] * self._NUM_BUCKETS
        for v in norms:
            idx = min(int((v - lo) / width), self._NUM_BUCKETS - 1)
            counts[idx] += 1

        return {
            "bucket_edges": edges,
            "bucket_counts": counts,
            "min": lo,
            "max": hi,
            "mean": mean_val,
            "sample_count": n,
        }

    # ── sufficiency check ─────────────────────────────────────────────

    def is_sufficient_for_analysis(self, min_samples: int = 20) -> bool:
        """True when at least *min_samples* records have been collected."""
        return len(self._errors) >= min_samples
