"""
Tests for PredictionErrorTracker.
"""

import time
import unittest

from godelOS.symbol_grounding.symbol_grounding_associator import GroundingPredictionError
from godelOS.symbol_grounding.prediction_error_tracker import PredictionErrorTracker


def _make_error(symbol: str = "sym", norm: float = 0.5, ts: float = 0.0) -> GroundingPredictionError:
    return GroundingPredictionError(
        symbol_ast_id=symbol,
        modality="visual_features",
        timestamp=ts or time.time(),
        predicted_features={"x": 0.0},
        observed_features={"x": norm},
        feature_errors={"x": norm},
        error_norm=norm,
    )


class TestPredictionErrorTrackerEmpty(unittest.TestCase):
    """Empty tracker edge cases."""

    def test_mean_zero(self):
        self.assertEqual(PredictionErrorTracker().mean_error_norm(), 0.0)

    def test_rate_of_change_zero(self):
        self.assertEqual(PredictionErrorTracker().error_rate_of_change(), 0.0)

    def test_per_symbol_empty(self):
        self.assertEqual(PredictionErrorTracker().per_symbol_error(), {})

    def test_distribution_empty(self):
        dist = PredictionErrorTracker().error_distribution()
        self.assertEqual(dist["sample_count"], 0)
        self.assertEqual(dist["bucket_edges"], [])

    def test_not_sufficient(self):
        self.assertFalse(PredictionErrorTracker().is_sufficient_for_analysis())


class TestPredictionErrorTrackerStats(unittest.TestCase):
    """Statistics after recording errors."""

    def setUp(self):
        self.tracker = PredictionErrorTracker(window_size=100)

    def test_mean_error_norm(self):
        for v in [0.1, 0.2, 0.3]:
            self.tracker.record(_make_error(norm=v))
        self.assertAlmostEqual(self.tracker.mean_error_norm(), 0.2, places=5)

    def test_mean_error_norm_last_n(self):
        for v in [0.1, 0.2, 0.3, 0.4]:
            self.tracker.record(_make_error(norm=v))
        self.assertAlmostEqual(self.tracker.mean_error_norm(last_n=2), 0.35, places=5)

    def test_per_symbol_grouping(self):
        self.tracker.record(_make_error(symbol="a", norm=0.2))
        self.tracker.record(_make_error(symbol="a", norm=0.4))
        self.tracker.record(_make_error(symbol="b", norm=1.0))
        groups = self.tracker.per_symbol_error()
        self.assertAlmostEqual(groups["a"], 0.3, places=5)
        self.assertAlmostEqual(groups["b"], 1.0, places=5)

    def test_distribution_buckets(self):
        for i in range(25):
            self.tracker.record(_make_error(norm=i / 24.0))
        dist = self.tracker.error_distribution()
        self.assertEqual(len(dist["bucket_counts"]), 10)
        self.assertEqual(sum(dist["bucket_counts"]), 25)
        self.assertGreater(dist["max"], 0.0)

    def test_sufficiency_threshold(self):
        for _ in range(19):
            self.tracker.record(_make_error())
        self.assertFalse(self.tracker.is_sufficient_for_analysis())
        self.tracker.record(_make_error())
        self.assertTrue(self.tracker.is_sufficient_for_analysis())

    def test_window_trimming(self):
        tracker = PredictionErrorTracker(window_size=5)
        for i in range(10):
            tracker.record(_make_error(norm=float(i)))
        # Only last 5 should remain
        self.assertAlmostEqual(tracker.mean_error_norm(), (5+6+7+8+9) / 5.0, places=5)


if __name__ == "__main__":
    unittest.main()
