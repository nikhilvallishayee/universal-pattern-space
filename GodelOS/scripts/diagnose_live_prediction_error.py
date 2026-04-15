#!/usr/bin/env python3
"""
Live prediction-error diagnostic — starts a minimal GödelOS session,
feeds real symbol activations through ``KnowledgeStoreShim``, and
prints periodic histograms with a final synthetic-vs-live comparison.

Matplotlib plots are saved alongside the text output for visual review.

Usage:
    python scripts/diagnose_live_prediction_error.py

Requirements:
    - Project root on ``sys.path``
    - All godelOS core_kr and symbol_grounding packages importable
    - matplotlib (``pip install matplotlib``)
    - No running backend required (self-contained)
"""

import math
import random
import sys
import os
import time

# Ensure project root is on the path
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _PROJECT_ROOT)

# Matplotlib — headless backend for CI / server environments
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

from unittest.mock import MagicMock

from godelOS.symbol_grounding.symbol_grounding_associator import (
    GroundingLink,
    GroundingPredictionError,
    SymbolGroundingAssociator,
)
from godelOS.symbol_grounding.prediction_error_tracker import PredictionErrorTracker
from godelOS.symbol_grounding.knowledge_store_shim import KnowledgeStoreShim
from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface
from godelOS.core_kr.type_system.manager import TypeSystemManager
from godelOS.core_kr.ast.nodes import ConstantNode

# ── parameters ────────────────────────────────────────────────────────

MAX_DURATION = 300        # 5 minutes
MAX_RECORDS = 200
SNAPSHOT_INTERVAL = 30    # seconds
NUM_SYMBOLS = 8
ACTIVATION_DELAY = 0.05   # seconds between activations (simulated real-time)

# Synthetic reference peaks from diagnose_prediction_error.py
SYNTHETIC_PEAK_LOW = 0.0
SYNTHETIC_PEAK_HIGH = 0.44

# Output directory for plots
_OUTPUT_DIR = os.path.join(_PROJECT_ROOT, "diagnostic_output")

random.seed()

# ── helpers ────────────────────────────────────────────────────────────


def _build_live_stack():
    """Build a live-like stack: KS mock → shim → grounder → tracker."""
    kr = MagicMock(spec=KnowledgeStoreInterface)
    kr.list_contexts.return_value = []
    # add_statement returns True (success)
    kr.add_statement.return_value = True

    ts = MagicMock(spec=TypeSystemManager)
    ts.get_type.return_value = MagicMock()

    grounder = SymbolGroundingAssociator(kr_system_interface=kr, type_system=ts)
    tracker = PredictionErrorTracker(window_size=500)
    shim = KnowledgeStoreShim(base=kr, grounder=grounder, tracker=tracker)

    return shim, grounder, tracker


def _make_statement(name: str):
    """Create a ConstantNode statement for ``add_statement``."""
    mock_type = MagicMock()
    return ConstantNode(name=name, type_ref=mock_type)


def _jitter(base: float, scale: float) -> float:
    return base + random.gauss(0, scale)


# ── printing ──────────────────────────────────────────────────────────


def print_histogram(dist, title="LIVE HISTOGRAM"):
    print(f"\n=== {title} ===")
    if dist["sample_count"] == 0:
        print("  (no data)")
        return
    edges = dist["bucket_edges"]
    counts = dist["bucket_counts"]
    max_count = max(counts) if counts else 1
    bar_width = 32
    for i, count in enumerate(counts):
        lo, hi = edges[i], edges[i + 1]
        bar_len = int(count / max_count * bar_width) if max_count else 0
        bar = "#" * bar_len
        print(f"  [{lo:6.4f}, {hi:6.4f}) | {bar:<{bar_width}} | {count}")


def print_snapshot(elapsed: float, tracker: PredictionErrorTracker):
    n = len(tracker._errors)
    dist = tracker.error_distribution()
    mean = tracker.mean_error_norm()
    roc = tracker.error_rate_of_change()
    sufficient = tracker.is_sufficient_for_analysis()

    # Determine threshold source
    if sufficient:
        threshold_src = "empirical_bimodal_phase2"
    else:
        threshold_src = "heuristic_fallback (insufficient data)"

    print(f"\n=== LIVE SNAPSHOT [t={int(elapsed)}s, n={n} records] ===")
    print(f"Mean error norm:     {mean:.4f}")
    print(f"Rate of change:      {roc:.4f}")
    print(f"Is grounded:         {sufficient}")
    print(f"Threshold source:    {threshold_src}")

    print_histogram(dist)

    # Per-symbol top 5
    per_sym = tracker.per_symbol_error()
    top5 = sorted(per_sym.items(), key=lambda kv: kv[1], reverse=True)[:5]
    print("\n=== PER-SYMBOL ERROR (top 5) ===")
    print("symbol_id : mean_error_norm")
    for sym, me in top5:
        print(f"  {sym} : {me:.4f}")


def _find_peaks(counts, min_fraction=0.05):
    """Return indices of local maxima (including edges).

    Parameters
    ----------
    counts : list[int]
        Bucket counts from the histogram.
    min_fraction : float
        Minimum fraction of total samples (default 0.05 = 5%) a bucket
        must contain to be considered a significant peak.  Prevents tiny
        tail noise from inflating the peak list.
    """
    peaks = []
    if not counts:
        return peaks
    total = sum(counts)
    min_count = total * min_fraction
    n = len(counts)
    if n >= 2 and counts[0] > counts[1]:
        peaks.append(0)
    for i in range(1, n - 1):
        if counts[i] > counts[i - 1] and counts[i] > counts[i + 1]:
            peaks.append(i)
    if n >= 2 and counts[-1] > counts[-2]:
        peaks.append(n - 1)
    # Filter out insignificant peaks
    peaks = [p for p in peaks if counts[p] >= min_count]
    return peaks


def _peak_centers(peaks, edges):
    """Return the center values of peak buckets."""
    return [(edges[p] + edges[p + 1]) / 2.0 for p in peaks]


def _dominant_pair(peaks, counts, edges):
    """Return ``(low_center, high_center)`` of the two tallest peaks.

    Parameters
    ----------
    peaks : list[int]
        Indices of significant peaks in the histogram.
    counts : list[int]
        Bucket counts for each histogram bin.
    edges : list[float]
        Bucket edge values (len = len(counts) + 1).

    Returns
    -------
    tuple[float, float] | None
        Center values of the two most-populated peaks, ordered low→high.
        ``None`` when fewer than two peaks are provided.
    """
    if len(peaks) < 2:
        return None
    # Sort peaks by count (descending), pick top-2, then order by position
    top2 = sorted(peaks, key=lambda p: counts[p], reverse=True)[:2]
    top2.sort()  # low position first
    lo = (edges[top2[0]] + edges[top2[0] + 1]) / 2.0
    hi = (edges[top2[1]] + edges[top2[1] + 1]) / 2.0
    return lo, hi


def print_comparison(tracker: PredictionErrorTracker):
    """Print synthetic vs live comparison with threshold recommendation.

    Returns the comparison text block so it can be embedded in plots.
    """
    dist = tracker.error_distribution()
    counts = dist.get("bucket_counts", [])
    edges = dist.get("bucket_edges", [])
    n = dist.get("sample_count", 0)

    lines = []

    def _p(line=""):
        print(line)
        lines.append(line)

    _p("\n=== SYNTHETIC vs LIVE COMPARISON ===")
    _p(f"Synthetic bimodal peaks:  ~{SYNTHETIC_PEAK_LOW} and ~{SYNTHETIC_PEAK_HIGH}")

    if n < 10:
        _p("Live bimodal peaks:       INSUFFICIENT DATA")
        _p("Shape match:              INSUFFICIENT DATA")
        _p("Recommendation:           collect more data before deciding")
        return "\n".join(lines)

    peaks = _find_peaks(counts)
    centers = _peak_centers(peaks, edges)
    _p(f"Live detected peaks:      {[f'{c:.4f}' for c in centers]}")

    # Determine shape match
    if len(peaks) >= 2:
        # Check valley depth between the outermost significant peaks
        valley = min(counts[peaks[0]:peaks[-1] + 1])
        peak_max = max(counts[p] for p in peaks)
        valley_ratio = valley / peak_max if peak_max else 1.0

        if valley_ratio < 0.5:
            # True bimodal — compare the two dominant peaks against synthetic
            pair = _dominant_pair(peaks, counts, edges)
            low_peak, high_peak = pair
            _p(f"Live dominant peaks:       ~{low_peak:.4f} and ~{high_peak:.4f}")
            low_match = abs(low_peak - SYNTHETIC_PEAK_LOW) < 0.15
            high_match = abs(high_peak - SYNTHETIC_PEAK_HIGH) < 0.15
            if low_match and high_match:
                _p("Shape match:              YES")
                _p("Recommendation:           thresholds valid")
            else:
                _p("Shape match:              NO (peak positions differ)")
                # Valley detection for recalibration
                valley_idx = counts[peaks[0]:peaks[-1] + 1].index(valley) + peaks[0]
                valley_center = (edges[valley_idx] + edges[valley_idx + 1]) / 2.0
                new_sub = valley_center
                new_super = high_peak
                _p(f"Recommendation:           thresholds need recalibration")
                _p(f"  Suggested sub→critical threshold:  {new_sub:.4f}")
                _p(f"  Suggested critical→super threshold: {new_super:.4f}")
        else:
            _p("Shape match:              NO (no clear valley)")
            _p("Recommendation:           thresholds need recalibration")
            # Use quartile-based fallback
            norms = sorted(e.error_norm for e in tracker._errors)
            q1 = norms[len(norms) // 4]
            q3 = norms[3 * len(norms) // 4]
            _p(f"  Suggested sub→critical threshold:  {q1:.4f}")
            _p(f"  Suggested critical→super threshold: {q3:.4f}")
    else:
        _p("Shape match:              NO (unimodal)")
        _p("Recommendation:           thresholds need recalibration")
        norms = sorted(e.error_norm for e in tracker._errors)
        q1 = norms[len(norms) // 4] if norms else 0.0
        q3 = norms[3 * len(norms) // 4] if norms else 0.0
        _p(f"  Suggested sub→critical threshold:  {q1:.4f}")
        _p(f"  Suggested critical→super threshold: {q3:.4f}")

    return "\n".join(lines)


# ── synthetic baseline (reused from diagnose_prediction_error.py) ─────

def _run_synthetic_scenario():
    """Run the Phase 2 synthetic scenario and return a tracker."""
    kr = MagicMock(spec=KnowledgeStoreInterface)
    kr.list_contexts.return_value = []
    ts = MagicMock(spec=TypeSystemManager)
    ts.get_type.return_value = MagicMock()
    sga = SymbolGroundingAssociator(kr_system_interface=kr, type_system=ts)
    tracker = PredictionErrorTracker(window_size=500)

    rng = random.Random(42)  # deterministic
    num_sym, act_per_sym, learn_phase = 5, 25, 15
    prototypes = {
        f"sym_{i}": {"brightness": 0.2 * i, "sharpness": 0.1 + 0.15 * i}
        for i in range(num_sym)
    }
    t0 = time.time()
    for sym, proto in prototypes.items():
        for act in range(act_per_sym):
            ts_now = t0 + (list(prototypes).index(sym) * act_per_sym + act) * 0.01
            if act < learn_phase:
                obs = {k: v + rng.gauss(0, 0.02) for k, v in proto.items()}
            else:
                roll = rng.random()
                if roll < 0.33:
                    obs = dict(proto)
                elif roll < 0.66:
                    obs = {k: v + rng.gauss(0, 0.08) for k, v in proto.items()}
                else:
                    obs = {k: v + rng.uniform(0.3, 0.6) for k, v in proto.items()}
            sga.grounding_links[sym] = [
                GroundingLink(symbol_ast_id=sym, sub_symbolic_representation=proto,
                              modality="visual_features", confidence=0.9)
            ]
            result = sga.measure_prediction_error_at_activation(sym, obs, "visual_features")
            if result is None:
                continue
            result = GroundingPredictionError(
                symbol_ast_id=result.symbol_ast_id, modality=result.modality,
                timestamp=ts_now, predicted_features=result.predicted_features,
                observed_features=result.observed_features,
                feature_errors=result.feature_errors, error_norm=result.error_norm,
            )
            tracker.record(result)
    return tracker


# ── matplotlib plotting ───────────────────────────────────────────────

_COLORS = {
    "live": "#3B82F6",       # blue
    "synthetic": "#F59E0B",  # amber
    "valley": "#EF4444",     # red
    "accent": "#10B981",     # emerald
}


def plot_live_histogram(tracker: PredictionErrorTracker, path: str):
    """Render the live error-norm histogram as a standalone PNG."""
    norms = [e.error_norm for e in tracker._errors]
    if not norms:
        return

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(norms, bins=30, color=_COLORS["live"], edgecolor="white",
            linewidth=0.6, alpha=0.85, label="Live activations")
    ax.set_xlabel("Prediction Error Norm", fontsize=12)
    ax.set_ylabel("Frequency", fontsize=12)
    ax.set_title("Live Prediction-Error Distribution (KnowledgeStoreShim)",
                 fontsize=14, fontweight="bold")
    ax.legend(fontsize=11)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"  📊 Saved: {path}")


def plot_per_symbol(tracker: PredictionErrorTracker, path: str):
    """Render per-symbol mean error as a horizontal bar chart."""
    per_sym = tracker.per_symbol_error()
    if not per_sym:
        return

    symbols = sorted(per_sym.keys())
    means = [per_sym[s] for s in symbols]

    fig, ax = plt.subplots(figsize=(10, max(4, len(symbols) * 0.5)))
    bars = ax.barh(symbols, means, color=_COLORS["accent"], edgecolor="white",
                   linewidth=0.6, height=0.6)
    ax.set_xlabel("Mean Error Norm", fontsize=12)
    ax.set_title("Per-Symbol Prediction Error", fontsize=14, fontweight="bold")
    ax.grid(axis="x", alpha=0.3)
    # Value labels
    for bar, val in zip(bars, means):
        ax.text(bar.get_width() + 0.005, bar.get_y() + bar.get_height() / 2,
                f"{val:.4f}", va="center", fontsize=9, color="#374151")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"  📊 Saved: {path}")


def plot_comparison(live_tracker: PredictionErrorTracker,
                    synth_tracker: PredictionErrorTracker,
                    comparison_text: str, path: str):
    """Render overlaid synthetic vs live histograms with comparison metadata."""
    live_norms = [e.error_norm for e in live_tracker._errors]
    synth_norms = [e.error_norm for e in synth_tracker._errors]
    if not live_norms:
        return

    fig, axes = plt.subplots(2, 1, figsize=(12, 9),
                             gridspec_kw={"height_ratios": [3, 1]})

    # ── Top panel: overlaid histograms ──
    ax = axes[0]
    lo = min(min(live_norms), min(synth_norms)) if synth_norms else min(live_norms)
    hi = max(max(live_norms), max(synth_norms)) if synth_norms else max(live_norms)
    bins = 30
    bin_edges = [lo + (hi - lo) * i / bins for i in range(bins + 1)]

    ax.hist(synth_norms, bins=bin_edges, color=_COLORS["synthetic"],
            edgecolor="white", linewidth=0.5, alpha=0.55,
            label=f"Synthetic (n={len(synth_norms)})", density=True)
    ax.hist(live_norms, bins=bin_edges, color=_COLORS["live"],
            edgecolor="white", linewidth=0.5, alpha=0.65,
            label=f"Live (n={len(live_norms)})", density=True)

    # Phase threshold reference lines
    ax.axvline(0.12, color=_COLORS["valley"], linestyle="--", linewidth=1.2,
               alpha=0.7, label="Sub→Critical (0.12)")
    ax.axvline(0.35, color=_COLORS["valley"], linestyle="-.", linewidth=1.2,
               alpha=0.7, label="Critical→Super (0.35)")

    ax.set_xlabel("Prediction Error Norm", fontsize=12)
    ax.set_ylabel("Density", fontsize=12)
    ax.set_title("Synthetic vs Live Prediction-Error Distribution",
                 fontsize=14, fontweight="bold")
    ax.legend(fontsize=10, loc="upper right")
    ax.grid(axis="y", alpha=0.3)

    # ── Bottom panel: comparison text ──
    ax2 = axes[1]
    ax2.axis("off")
    ax2.text(0.02, 0.95, comparison_text, transform=ax2.transAxes,
             fontsize=10, fontfamily="monospace", verticalalignment="top",
             bbox=dict(boxstyle="round,pad=0.5", facecolor="#F3F4F6",
                       edgecolor="#D1D5DB", alpha=0.9))

    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"  📊 Saved: {path}")


# ── main live session ─────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  LIVE PREDICTION-ERROR DIAGNOSTIC")
    print(f"  Max duration: {MAX_DURATION}s  |  Target records: {MAX_RECORDS}")
    print("=" * 60)

    shim, grounder, tracker = _build_live_stack()

    # Define symbol prototypes (what the grounder has "learned")
    prototypes = {}
    for i in range(NUM_SYMBOLS):
        sym_id = f"live_sym_{i}"
        proto = {
            "brightness": 0.1 + 0.1 * i,
            "sharpness": 0.05 + 0.12 * i,
            "contrast": 0.3 + 0.08 * i,
        }
        prototypes[sym_id] = proto
        # Inject learned grounding link
        grounder.grounding_links[sym_id] = [
            GroundingLink(
                symbol_ast_id=sym_id,
                sub_symbolic_representation=proto,
                modality="visual_features",
                confidence=0.9,
            )
        ]

    sym_ids = list(prototypes.keys())
    t_start = time.time()
    last_snapshot = t_start
    activation_count = 0

    print(f"\nStarting live activations ({NUM_SYMBOLS} symbols)...\n")

    while True:
        elapsed = time.time() - t_start
        n_records = len(tracker._errors)

        # Termination conditions
        if elapsed >= MAX_DURATION:
            print(f"\n⏱  Max duration reached ({MAX_DURATION}s)")
            break
        if n_records >= MAX_RECORDS:
            print(f"\n🎯 Target records reached ({MAX_RECORDS})")
            break

        # Snapshot every SNAPSHOT_INTERVAL seconds
        if time.time() - last_snapshot >= SNAPSHOT_INTERVAL:
            print_snapshot(elapsed, tracker)
            last_snapshot = time.time()

        # Pick a random symbol and generate an observation
        sym_id = random.choice(sym_ids)
        proto = prototypes[sym_id]

        # Mix of observation types (mimicking real sensor variability):
        roll = random.random()
        if roll < 0.40:
            # Well-matched observation (low error)
            obs = {k: _jitter(v, 0.02) for k, v in proto.items()}
        elif roll < 0.70:
            # Slight variation
            obs = {k: _jitter(v, 0.08) for k, v in proto.items()}
        elif roll < 0.90:
            # Novel / surprising observation (high error)
            obs = {
                k: v + random.uniform(0.25, 0.55)
                for k, v in proto.items()
            }
        else:
            # Completely random features
            obs = {k: random.random() for k in proto}

        # Set observation context and push through the shim
        shim.set_observation_context(obs, modality="visual_features")
        stmt = _make_statement(sym_id)
        shim.add_statement(stmt, "TRUTHS")

        activation_count += 1
        time.sleep(ACTIVATION_DELAY)

    # ── final output ──────────────────────────────────────────────────

    elapsed = time.time() - t_start
    print_snapshot(elapsed, tracker)
    comparison_text = print_comparison(tracker)

    stats = shim.measurement_stats
    print(f"\n=== SHIM MEASUREMENT STATS ===")
    print(f"  measurements_recorded: {stats['measurements_recorded']}")
    print(f"  skipped_no_context:    {stats['skipped_no_context']}")
    print(f"  skipped_cold_start:    {stats['skipped_cold_start']}")
    print(f"  total activations:     {activation_count}")

    # ── Matplotlib plots ──────────────────────────────────────────────

    os.makedirs(_OUTPUT_DIR, exist_ok=True)
    print(f"\n=== GENERATING PLOTS → {_OUTPUT_DIR}/ ===")

    plot_live_histogram(
        tracker, os.path.join(_OUTPUT_DIR, "live_histogram.png"))
    plot_per_symbol(
        tracker, os.path.join(_OUTPUT_DIR, "per_symbol_error.png"))

    # Run synthetic baseline and render overlay comparison
    print("  Running synthetic baseline for overlay comparison...")
    synth_tracker = _run_synthetic_scenario()
    plot_comparison(
        tracker, synth_tracker, comparison_text,
        os.path.join(_OUTPUT_DIR, "synthetic_vs_live.png"))

    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
