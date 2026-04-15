#!/usr/bin/env python3
"""
Diagnostic script — exercises the full GroundingPredictionError stack
with synthetic data and prints six labeled analysis sections.

Usage:
    python scripts/diagnose_prediction_error.py
"""

import math
import random
import sys
import os
import time

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import MagicMock

from godelOS.symbol_grounding.symbol_grounding_associator import (
    GroundingLink,
    GroundingPredictionError,
    PrototypeModel,
    SymbolGroundingAssociator,
)
from godelOS.symbol_grounding.prediction_error_tracker import PredictionErrorTracker
from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface
from godelOS.core_kr.type_system.manager import TypeSystemManager

# ── helpers ────────────────────────────────────────────────────────────

NUM_SYMBOLS = 5
ACTIVATIONS_PER_SYMBOL = 25
LEARNING_PHASE = 15   # first N activations per symbol use consistent features
TEST_PHASE = ACTIVATIONS_PER_SYMBOL - LEARNING_PHASE  # remaining activations

# Prototype generation parameters
BRIGHTNESS_STEP = 0.2       # brightness increment per symbol
SHARPNESS_BASE = 0.1        # base sharpness for symbol 0
SHARPNESS_STEP = 0.15       # sharpness increment per symbol
LEARNING_JITTER = 0.02      # Gaussian σ during learning phase
SLIGHT_JITTER = 0.08        # Gaussian σ for slight test variations
NOVEL_DEVIATION_MIN = 0.3   # minimum shift for novel observations
NOVEL_DEVIATION_MAX = 0.6   # maximum shift for novel observations

random.seed(42)


def _jitter(base: float, scale: float = 0.05) -> float:
    return base + random.gauss(0, scale)


# ── build the stack ───────────────────────────────────────────────────

def build_stack():
    kr = MagicMock(spec=KnowledgeStoreInterface)
    kr.list_contexts.return_value = []
    ts = MagicMock(spec=TypeSystemManager)
    ts.get_type.return_value = MagicMock()
    sga = SymbolGroundingAssociator(kr_system_interface=kr, type_system=ts)
    tracker = PredictionErrorTracker(window_size=500)
    return sga, tracker


# ── synthetic scenario ────────────────────────────────────────────────

def run_scenario():
    sga, tracker = build_stack()

    # Define prototypes for each symbol (what the grounder should learn)
    prototypes = {
        f"sym_{i}": {
            "brightness": BRIGHTNESS_STEP * i,
            "sharpness": SHARPNESS_BASE + SHARPNESS_STEP * i,
        }
        for i in range(NUM_SYMBOLS)
    }

    # Track per-phase statistics
    identical_norms = []
    novel_norms = []
    per_symbol_first_10 = {s: [] for s in prototypes}
    per_symbol_last_10 = {s: [] for s in prototypes}

    t0 = time.time()

    for sym, proto in prototypes.items():
        for act in range(ACTIVATIONS_PER_SYMBOL):
            # Ensure monotonic timestamps
            ts_now = t0 + (list(prototypes).index(sym) * ACTIVATIONS_PER_SYMBOL + act) * 0.01

            if act < LEARNING_PHASE:
                # LEARNING PHASE: consistent features (small jitter)
                obs = {k: _jitter(v, LEARNING_JITTER) for k, v in proto.items()}
            else:
                # TEST PHASE: mix identical, slight, novel
                roll = random.random()
                if roll < 0.33:
                    # identical
                    obs = dict(proto)
                elif roll < 0.66:
                    # slight variation
                    obs = {k: _jitter(v, SLIGHT_JITTER) for k, v in proto.items()}
                else:
                    # novel (large deviation)
                    obs = {
                        k: v + random.uniform(NOVEL_DEVIATION_MIN, NOVEL_DEVIATION_MAX)
                        for k, v in proto.items()
                    }

            # Inject the prototype as a grounding link (simulate learning)
            sga.grounding_links[sym] = [
                GroundingLink(
                    symbol_ast_id=sym,
                    sub_symbolic_representation=proto,
                    modality="visual_features",
                    confidence=0.9,
                )
            ]

            result = sga.measure_prediction_error_at_activation(
                sym, obs, "visual_features"
            )
            if result is None:
                continue

            # Override timestamp for controlled time-series
            result = GroundingPredictionError(
                symbol_ast_id=result.symbol_ast_id,
                modality=result.modality,
                timestamp=ts_now,
                predicted_features=result.predicted_features,
                observed_features=result.observed_features,
                feature_errors=result.feature_errors,
                error_norm=result.error_norm,
            )
            tracker.record(result)

            # Classify for analysis
            if act < LEARNING_PHASE:
                per_symbol_first_10[sym].append(result.error_norm)
            else:
                per_symbol_last_10[sym].append(result.error_norm)
                if obs == proto:
                    identical_norms.append(result.error_norm)
                elif result.error_norm > 0.2:
                    novel_norms.append(result.error_norm)

    return tracker, per_symbol_first_10, per_symbol_last_10, identical_norms, novel_norms


# ── output sections ───────────────────────────────────────────────────

def print_histogram(dist):
    print("\n=== ERROR DISTRIBUTION HISTOGRAM ===")
    if dist["sample_count"] == 0:
        print("  (no data)")
        return
    edges = dist["bucket_edges"]
    counts = dist["bucket_counts"]
    max_count = max(counts) if counts else 1
    bar_width = 40
    for i, count in enumerate(counts):
        lo, hi = edges[i], edges[i + 1]
        bar_len = int(count / max_count * bar_width) if max_count else 0
        bar = "#" * bar_len
        print(f"  [{lo:6.4f}, {hi:6.4f}) | {bar:<{bar_width}} | {count}")
    print(f"\n  min={dist['min']:.4f}  max={dist['max']:.4f}  mean={dist['mean']:.4f}  n={dist['sample_count']}")


def print_per_symbol(tracker):
    print("\n=== PER-SYMBOL MEAN ERROR ===")
    for sym, mean in sorted(tracker.per_symbol_error().items()):
        print(f"  {sym} : {mean:.4f}")


def print_learning_signal(first_10, last_10):
    print("\n=== LEARNING SIGNAL ===")
    for sym in sorted(first_10):
        f = first_10[sym]
        l = last_10[sym]
        mean_f = sum(f) / len(f) if f else 0
        mean_l = sum(l) / len(l) if l else 0
        direction = "↓ decreased" if mean_l < mean_f else "↑ increased or equal"
        print(f"  {sym}:  first {len(f)} mean={mean_f:.4f}  last {len(l)} mean={mean_l:.4f}  → {direction}")
    overall_first = [v for vs in first_10.values() for v in vs]
    overall_last = [v for vs in last_10.values() for v in vs]
    mf = sum(overall_first) / len(overall_first) if overall_first else 0
    ml = sum(overall_last) / len(overall_last) if overall_last else 0
    print(f"\n  Overall: first-phase mean={mf:.4f}  test-phase mean={ml:.4f}")
    if ml < mf:
        print("  Conclusion: Error DECREASED from learning to test phase (learning works but test includes novel stimuli).")
    else:
        print("  Conclusion: Error INCREASED in test phase — novel observations drive up prediction error as expected.")


def print_surprise_signal(identical_norms, novel_norms):
    print("\n=== SURPRISE SIGNAL ===")
    mi = sum(identical_norms) / len(identical_norms) if identical_norms else 0
    mn = sum(novel_norms) / len(novel_norms) if novel_norms else 0
    print(f"  Identical observations (n={len(identical_norms)}):  mean error = {mi:.4f}")
    print(f"  Novel observations     (n={len(novel_norms)}):  mean error = {mn:.4f}")
    if mn > mi:
        print("  ✅ Novel observations produce higher prediction error — surprise signal is real.")
    else:
        print("  ⚠️  No clear surprise signal separation.")


def print_rate_of_change(tracker):
    print("\n=== RATE OF CHANGE ===")
    roc = tracker.error_rate_of_change()
    print(f"  error_rate_of_change() = {roc:.6f}")
    if abs(roc) < 0.001:
        print("  Interpretation: Error rate is approximately stable over the window.")
    elif roc > 0:
        print("  Interpretation: Error is increasing over time (system encountering more novelty).")
    else:
        print("  Interpretation: Error is decreasing over time (system adapting).")


def print_phase_analysis(dist):
    print("\n=== PHASE ANALYSIS ===")
    counts = dist.get("bucket_counts", [])
    edges = dist.get("bucket_edges", [])
    n = dist.get("sample_count", 0)

    if n < 10:
        print("  Insufficient data for phase analysis.")
        print("  Recommended action: collect more data before deciding.")
        return

    # Check for bimodality: are there two distinct peaks separated by a valley?
    if len(counts) < 4:
        print("  Too few buckets to analyze shape.")
        print("  Recommended action: keep phase transition machinery (insufficient evidence to remove).")
        return

    # Find peaks (local maxima)
    peaks = []
    for i in range(1, len(counts) - 1):
        if counts[i] > counts[i - 1] and counts[i] > counts[i + 1]:
            peaks.append(i)
    # Also check edges
    if len(counts) >= 2:
        if counts[0] > counts[1]:
            peaks.insert(0, 0)
        if counts[-1] > counts[-2]:
            peaks.append(len(counts) - 1)

    # Check concentration: what fraction in top-3 buckets?
    sorted_counts = sorted(counts, reverse=True)
    top3_mass = sum(sorted_counts[:3]) / n if n else 0

    print(f"  Number of peaks detected: {len(peaks)}")
    print(f"  Peak bucket indices: {peaks}")
    print(f"  Top-3 bucket concentration: {top3_mass:.1%} of samples")

    if len(peaks) >= 2:
        # Check if peaks are separated by a meaningful valley
        valley_between = min(counts[peaks[0]:peaks[-1] + 1])
        peak_max = max(counts[p] for p in peaks)
        valley_ratio = valley_between / peak_max if peak_max else 1.0
        print(f"  Valley-to-peak ratio: {valley_ratio:.2f}")
        if valley_ratio < 0.5:
            print("  Shape: BIMODAL — distinct clusters of low-error and high-error activations.")
            print("  Recommended action: keep phase transition machinery — the error distribution")
            print("  shows natural phase separation that can drive meaningful phase transitions.")
        else:
            print("  Shape: BROAD but not clearly bimodal.")
            print("  Recommended action: keep phase transition machinery with caution —")
            print("  the separation is weak but present. Consider raising the hysteresis threshold.")
    elif top3_mass > 0.8:
        print("  Shape: CONCENTRATED — most errors cluster in a narrow range.")
        print("  Recommended action: delete phase transition machinery — the error distribution")
        print("  is too uniform to produce meaningful phase transitions. Use mean error + rate")
        print("  of change directly.")
    else:
        print("  Shape: SMOOTH / SPREAD — errors distributed across a wide range without clear clustering.")
        print("  Recommended action: keep phase transition machinery — the spread suggests")
        print("  genuine variation in prediction quality that phase detection can capture.")


# ── main ──────────────────────────────────────────────────────────────

def main():
    print("Running prediction error diagnostic with synthetic data...")
    print(f"  {NUM_SYMBOLS} symbols × {ACTIVATIONS_PER_SYMBOL} activations each")
    print(f"  Learning phase: {LEARNING_PHASE}  Test phase: {TEST_PHASE}")

    tracker, first_10, last_10, identical, novel = run_scenario()

    dist = tracker.error_distribution()

    print_histogram(dist)
    print_per_symbol(tracker)
    print_learning_signal(first_10, last_10)
    print_surprise_signal(identical, novel)
    print_rate_of_change(tracker)
    print_phase_analysis(dist)

    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
