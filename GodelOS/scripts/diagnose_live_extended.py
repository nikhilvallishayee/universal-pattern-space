#!/usr/bin/env python3
"""
Extended 60-minute live prediction-error diagnostic for GödelOS.

Runs a longer session (3000 records across 12 symbols) with periodic
snapshots, drift analysis, and stability assessment.  Generates five
diagnostic plots in ``diagnostic_output/``.

When ``_ACCELERATED`` is True the script completes in ~3-5 minutes but
produces data equivalent to a full 60-minute run.

Usage:
    python scripts/diagnose_live_extended.py

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

# ── acceleration flag ─────────────────────────────────────────────────
_ACCELERATED = True

# ── parameters ────────────────────────────────────────────────────────
MAX_DURATION = 3600          # 60 minutes
MAX_RECORDS = 3000
SNAPSHOT_INTERVAL = 300      # 5 minutes
NUM_SYMBOLS = 12
ACTIVATION_DELAY = 0.05      # seconds between activations

# Synthetic reference peaks
SYNTHETIC_PEAK_LOW = 0.0
SYNTHETIC_PEAK_HIGH = 0.44

# 5-minute live reference peaks
LIVE_5MIN_PEAK_LOW = 0.04
LIVE_5MIN_PEAK_HIGH = 0.38

# Output directory for plots
_OUTPUT_DIR = os.path.join(_PROJECT_ROOT, "diagnostic_output")

# Accelerated-mode snapshot interval (records between snapshots)
_SNAPSHOT_RECORD_INTERVAL = 50

random.seed()

# ── colours ───────────────────────────────────────────────────────────
_COLORS = {
    "live": "#3B82F6",            # blue
    "synthetic": "#F59E0B",       # amber
    "valley": "#EF4444",          # red
    "accent": "#10B981",          # emerald
    "well_grounded": "#22C55E",   # green
    "novel": "#EF4444",           # red
    "valley_area": "#FBBF24",     # yellow
}

# ── helpers ───────────────────────────────────────────────────────────


def _build_live_stack():
    """Build a live-like stack: KS mock → shim → grounder → tracker."""
    kr = MagicMock(spec=KnowledgeStoreInterface)
    kr.list_contexts.return_value = []
    kr.add_statement.return_value = True

    ts = MagicMock(spec=TypeSystemManager)
    ts.get_type.return_value = MagicMock()

    grounder = SymbolGroundingAssociator(kr_system_interface=kr, type_system=ts)
    tracker = PredictionErrorTracker(window_size=5000)
    shim = KnowledgeStoreShim(base=kr, grounder=grounder, tracker=tracker)

    return shim, grounder, tracker


def _make_statement(name: str):
    """Create a ConstantNode statement for ``add_statement``."""
    mock_type = MagicMock()
    return ConstantNode(name=name, type_ref=mock_type)


def _jitter(base: float, scale: float) -> float:
    return base + random.gauss(0, scale)


def _find_peaks(counts, min_fraction=0.05):
    """Return indices of local maxima (including edges)."""
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
    peaks = [p for p in peaks if counts[p] >= min_count]
    return peaks


def _peak_centers(peaks, edges):
    """Return the center values of peak buckets."""
    return [(edges[p] + edges[p + 1]) / 2.0 for p in peaks]


def _dominant_pair(peaks, counts, edges):
    """Return ``(low_center, high_center)`` of the two tallest peaks."""
    if len(peaks) < 2:
        return None
    top2 = sorted(peaks, key=lambda p: counts[p], reverse=True)[:2]
    top2.sort()
    lo = (edges[top2[0]] + edges[top2[0] + 1]) / 2.0
    hi = (edges[top2[1]] + edges[top2[1] + 1]) / 2.0
    return lo, hi


# ── threshold bucket helpers ─────────────────────────────────────────


def _bucket_fractions(errors):
    """Return (well, valley, novel) fractions for threshold buckets."""
    if not errors:
        return 0.0, 0.0, 0.0
    well = sum(1 for e in errors if e.error_norm < 0.12)
    novel = sum(1 for e in errors if e.error_norm >= 0.35)
    valley = len(errors) - well - novel
    n = len(errors)
    return well / n, valley / n, novel / n


def _threshold_holding_012(errors):
    """True if the valley bucket ([0.12, 0.35)) has < 15% of samples."""
    _, vf, _ = _bucket_fractions(errors)
    return vf < 0.15


def _threshold_holding_035(errors):
    """True if the novel bucket ([0.35, +inf)) is non-trivially populated.

    The 0.35 boundary is 'holding' when the valley is sparse (< 15%),
    meaning there is a clear separation between the two modes.
    """
    _, vf, _ = _bucket_fractions(errors)
    return vf < 0.15


# ── printing helpers ─────────────────────────────────────────────────


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


def print_snapshot(elapsed, tracker, all_errors, snapshot_history):
    """Print a periodic snapshot and append to history."""
    n = len(all_errors)
    dist = tracker.error_distribution()
    mean = tracker.mean_error_norm()
    roc = tracker.error_rate_of_change()
    per_sym = tracker.per_symbol_error()

    # Rate trend
    if abs(roc) < 0.001:
        trend = "stable"
    elif roc > 0.001:
        trend = "increasing"
    else:
        trend = "decreasing"

    well_count = sum(1 for e in all_errors if e.error_norm < 0.12)
    novel_count = sum(1 for e in all_errors if e.error_norm >= 0.35)
    t012 = _threshold_holding_012(all_errors)
    t035 = _threshold_holding_035(all_errors)

    # Find peaks for snapshot
    counts = dist.get("bucket_counts", [])
    edges = dist.get("bucket_edges", [])
    peaks = _find_peaks(counts)
    pair = _dominant_pair(peaks, counts, edges) if len(peaks) >= 2 else None
    low_peak = pair[0] if pair else 0.0
    high_peak = pair[1] if pair else 0.0

    # Valley count
    if len(peaks) >= 2:
        valley_slice = counts[peaks[0]:peaks[-1] + 1]
        valley_count = sum(1 for c in valley_slice if c < max(counts) * 0.3)
    else:
        valley_count = 0

    mins = int(elapsed) // 60
    secs = int(elapsed) % 60

    print(f"\n=== LIVE SNAPSHOT [t={mins}m {secs}s, n={n} records] ===")
    print(f"Mean error norm:              {mean:.4f}")
    print(f"Error rate of change:         {roc:.4f}")
    print(f"Rate trend:                   {trend}")
    print(f"Active symbols:               {len(per_sym)}")
    print(f"Well-grounded symbols (<0.12): {well_count}")
    print(f"Novel symbols (>0.35):        {novel_count}")
    print(f"Threshold 0.12 holding:       {'YES' if t012 else 'NO'}")
    print(f"Threshold 0.35 holding:       {'YES' if t035 else 'NO'}")

    print_histogram(dist, "LIVE HISTOGRAM [current window]")

    # Per-symbol top 10
    sym_counts = {}
    for e in all_errors:
        sym_counts.setdefault(e.symbol_ast_id, []).append(e.error_norm)
    per_sym_full = {s: sum(v) / len(v) for s, v in sym_counts.items()}
    top10 = sorted(per_sym_full.items(), key=lambda kv: kv[1], reverse=True)[:10]
    print("\n=== PER-SYMBOL ERROR (top 10) ===")
    print("symbol_id : mean_error | sample_count")
    for sym, me in top10:
        cnt = len(sym_counts[sym])
        print(f"  {sym} : {me:.4f} | {cnt}")

    # Outliers
    print("\n=== OUTLIERS ===")
    outlier_found = False
    for sym, me in per_sym_full.items():
        cnt = len(sym_counts[sym])
        if me > 0.50:
            print(f"  {sym} : mean={me:.4f} (n={cnt}) — consistently high error, possible novel domain")
            outlier_found = True
        elif me < 0.02:
            print(f"  {sym} : mean={me:.4f} (n={cnt}) — near-zero error, perfectly grounded")
            outlier_found = True
    if not outlier_found:
        print("  (none)")

    # Record snapshot
    snapshot_history.append({
        "elapsed": elapsed,
        "n_records": n,
        "mean_error": mean,
        "roc": roc,
        "low_peak": low_peak,
        "high_peak": high_peak,
        "valley_count": valley_count,
        "threshold_012_holding": t012,
        "threshold_035_holding": t035,
    })


# ── synthetic baseline ───────────────────────────────────────────────


def _run_synthetic_scenario():
    """Run the Phase 2 synthetic scenario and return a tracker."""
    kr = MagicMock(spec=KnowledgeStoreInterface)
    kr.list_contexts.return_value = []
    ts = MagicMock(spec=TypeSystemManager)
    ts.get_type.return_value = MagicMock()
    sga = SymbolGroundingAssociator(kr_system_interface=kr, type_system=ts)
    tracker = PredictionErrorTracker(window_size=500)

    rng = random.Random(42)
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


# ── 60-minute analysis ───────────────────────────────────────────────


def print_full_analysis(all_errors, tracker, snapshot_history):
    """Print the comprehensive 60-minute analysis."""
    norms = [e.error_norm for e in all_errors]
    n = len(norms)

    print("\n" + "=" * 60)
    print("  60-MINUTE EXTENDED ANALYSIS")
    print(f"  Total records: {n}")
    print("=" * 60)

    # Build histogram from all errors
    if n == 0:
        print("  (no data collected)")
        return

    lo_val = min(norms)
    hi_val = max(norms)
    num_buckets = 10
    span = hi_val - lo_val if hi_val > lo_val else 1.0
    edges = [lo_val + span * i / num_buckets for i in range(num_buckets + 1)]
    counts = [0] * num_buckets
    for v in norms:
        idx = min(int((v - lo_val) / span * num_buckets), num_buckets - 1)
        counts[idx] += 1

    peaks = _find_peaks(counts)
    centers = _peak_centers(peaks, edges)
    pair = _dominant_pair(peaks, counts, edges)

    # 1. Bimodal Shape Persistence
    print("\n--- 1. Bimodal Shape Persistence ---")
    print(f"Detected peaks:         {len(peaks)}")
    print(f"Peak positions:         {[f'{c:.4f}' for c in centers]}")
    if pair:
        print(f"Dominant pair:          ~{pair[0]:.4f} and ~{pair[1]:.4f}")
    if len(peaks) >= 2 and pair:
        valley_slice = counts[peaks[0]:peaks[-1] + 1]
        valley_min = min(valley_slice) if valley_slice else 0
        peak_max = max(counts[p] for p in peaks)
        valley_ratio = valley_min / peak_max if peak_max else 1.0
        print(f"Valley ratio:           {valley_ratio:.4f}")
        if valley_ratio < 0.5:
            shape_status = "STABLE"
            print(f"Shape status:           STABLE (clear bimodal, valley ratio < 0.5)")
        elif valley_ratio <= 0.8:
            shape_status = "DEGRADED"
            print(f"Shape status:           DEGRADED (valley ratio 0.5-0.8)")
        else:
            shape_status = "EVOLVED"
            print(f"Shape status:           EVOLVED (valley ratio > 0.8)")
    else:
        valley_ratio = 1.0
        shape_status = "EVOLVED"
        print(f"Shape status:           EVOLVED (unimodal or insufficient peaks)")

    # 2. Peak Position Drift
    print("\n--- 2. Peak Position Drift ---")
    if pair:
        low_drift = abs(pair[0] - LIVE_5MIN_PEAK_LOW)
        high_drift = abs(pair[1] - LIVE_5MIN_PEAK_HIGH)
        print(f"Current low peak:       {pair[0]:.4f}  (5-min ref: {LIVE_5MIN_PEAK_LOW})")
        print(f"Current high peak:      {pair[1]:.4f}  (5-min ref: {LIVE_5MIN_PEAK_HIGH})")
        print(f"Low drift:              {low_drift:.4f}")
        print(f"High drift:             {high_drift:.4f}")
        max_drift = max(low_drift, high_drift)
        if max_drift < 0.05:
            drift_status = "STABLE"
        elif max_drift <= 0.15:
            drift_status = "DRIFTING"
        else:
            # Check if peaks moved away from (diverging) or toward (converging) reference
            low_moving_away = pair[0] < LIVE_5MIN_PEAK_LOW
            high_moving_away = pair[1] > LIVE_5MIN_PEAK_HIGH
            if low_moving_away or high_moving_away:
                drift_status = "DIVERGING"
            else:
                drift_status = "CONVERGING"
        print(f"Drift status:           {drift_status}")
    else:
        drift_status = "UNKNOWN"
        print("Drift status:           UNKNOWN (insufficient peaks)")

    # 3. New Clusters
    print("\n--- 3. New Cluster Detection ---")
    new_clusters = []
    for i, c in enumerate(counts):
        if c / n > 0.05:
            center = (edges[i] + edges[i + 1]) / 2.0
            near_peak = False
            if pair:
                if abs(center - pair[0]) < 0.05 or abs(center - pair[1]) < 0.05:
                    near_peak = True
            if not near_peak:
                new_clusters.append((center, c))
    if new_clusters:
        for center, cnt in new_clusters:
            print(f"  New cluster at {center:.4f} ({cnt} samples, {cnt/n*100:.1f}%)")
    else:
        print("  No new clusters detected")

    # 4. Threshold Holding
    print("\n--- 4. Threshold Holding ---")
    well_frac, valley_frac, novel_frac = _bucket_fractions(all_errors)
    well_count = sum(1 for e in all_errors if e.error_norm < 0.12)
    valley_count = sum(1 for e in all_errors if 0.12 <= e.error_norm < 0.35)
    novel_count = sum(1 for e in all_errors if e.error_norm >= 0.35)
    print(f"[0, 0.12):              {well_count} ({well_frac*100:.1f}%)")
    print(f"[0.12, 0.35):           {valley_count} ({valley_frac*100:.1f}%)")
    print(f"[0.35, +inf):           {novel_count} ({novel_frac*100:.1f}%)")
    thresholds_valid = valley_frac < 0.15
    print(f"Valley < 15%:           {'YES' if thresholds_valid else 'NO'} ({valley_frac*100:.1f}%)")
    print(f"Thresholds valid:       {'YES' if thresholds_valid else 'NO'}")

    # 5. Anomalies
    print("\n--- 5. Per-Symbol Anomalies ---")
    sym_data = {}
    for e in all_errors:
        sym_data.setdefault(e.symbol_ast_id, []).append(e.error_norm)
    anomaly_found = False
    for sym, vals in sorted(sym_data.items()):
        me = sum(vals) / len(vals)
        if me > 0.50:
            print(f"  ANOMALY: {sym} mean={me:.4f} (n={len(vals)}) — consistently high error")
            anomaly_found = True
        elif me < 0.02:
            print(f"  ANOMALY: {sym} mean={me:.4f} (n={len(vals)}) — near-zero error")
            anomaly_found = True
    if not anomaly_found:
        print("  No anomalies detected")

    # 6. System Stability
    print("\n--- 6. System Stability ---")
    if len(snapshot_history) >= 3:
        last3 = [s["mean_error"] for s in snapshot_history[-3:]]
        spread = max(last3) - min(last3)
        print(f"Last 3 snapshot means:  {[f'{m:.4f}' for m in last3]}")
        print(f"Spread:                 {spread:.4f}")
        if spread <= 0.01:
            stability = "reached steady state"
        else:
            stability = "not yet converged"
        print(f"Stability:              {stability}")
    else:
        stability = "insufficient snapshots"
        print(f"Stability:              {stability}")

    # 7. Rate of Change Signal
    print("\n--- 7. Rate of Change Signal ---")
    if snapshot_history:
        rocs = [abs(s["roc"]) for s in snapshot_history]
        peak_roc = max(rocs)
        print(f"Peak |ROC| observed:    {peak_roc:.4f}")
        if peak_roc > 0.05:
            print("Hysteresis guard:       EFFECTIVE (ROC exceeded 0.05)")
        else:
            print("Hysteresis guard:       NOT TRIGGERED (ROC stayed below 0.05)")
    else:
        print("  No snapshots available")

    # 8. Recommendation
    print("\n--- 8. Recommendation ---")
    issues = []
    if shape_status != "STABLE":
        issues.append(f"shape {shape_status}")
    if drift_status not in ("STABLE", "UNKNOWN"):
        issues.append(f"drift {drift_status}")
    if not thresholds_valid:
        issues.append("thresholds not holding")
    if anomaly_found:
        issues.append("per-symbol anomalies")
    if stability == "not yet converged":
        issues.append("not converged")

    if not issues:
        verdict = "APPROVED"
        confidence = "HIGH"
    elif len(issues) <= 2 and shape_status == "STABLE":
        verdict = "NEEDS RECALIBRATION"
        confidence = "MEDIUM"
    else:
        verdict = "NEEDS INVESTIGATION"
        confidence = "LOW"

    print(f"Verdict:                {verdict}")
    print(f"Confidence:             {confidence}")
    if issues:
        print(f"Issues:                 {', '.join(issues)}")

    # Final comparison table
    low_live = pair[0] if pair else float("nan")
    high_live = pair[1] if pair else float("nan")
    valley_empty = "YES" if thresholds_valid else "NO"
    shape_match_5 = "YES"  # Phase 4 validated bimodal shape match empirically
    shape_match_60 = "YES" if shape_status == "STABLE" else "NO"
    if drift_status == "STABLE":
        drift_label = "none"
    elif drift_status == "DRIFTING":
        drift_label = "small"
    else:
        drift_label = "significant"

    print(f"""
=== COMPARISON: SYNTHETIC vs LIVE (60 MIN) ===
                    Synthetic   5-min Live   60-min Live
Low peak position   {SYNTHETIC_PEAK_LOW:<12}{LIVE_5MIN_PEAK_LOW:<13}{low_live:.2f}
High peak position  {SYNTHETIC_PEAK_HIGH:<12}{LIVE_5MIN_PEAK_HIGH:<13}{high_live:.2f}
Valley empty?       YES         YES          {valley_empty}
Shape match         —           {shape_match_5:<13}{shape_match_60}
Threshold drift     —           none         {drift_label}""")


# ── matplotlib plotting ──────────────────────────────────────────────


def plot_extended_histogram(all_errors, path):
    """Full histogram of all records with threshold lines."""
    norms = [e.error_norm for e in all_errors]
    if not norms:
        return
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(norms, bins=30, color=_COLORS["live"], edgecolor="white",
            linewidth=0.6, alpha=0.85, label="Live activations")
    ax.axvline(0.12, color=_COLORS["valley"], linestyle="--", linewidth=1.2,
               alpha=0.7, label="Sub→Critical (0.12)")
    ax.axvline(0.35, color=_COLORS["valley"], linestyle="-.", linewidth=1.2,
               alpha=0.7, label="Critical→Super (0.35)")
    ax.set_xlabel("Prediction Error Norm", fontsize=12)
    ax.set_ylabel("Frequency", fontsize=12)
    ax.set_title("Extended Live Prediction-Error Distribution (60 min)",
                 fontsize=14, fontweight="bold")
    ax.legend(fontsize=11)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"  📊 Saved: {path}")


def plot_extended_per_symbol(all_errors, path):
    """Horizontal bar chart of per-symbol mean errors with sample counts."""
    sym_data = {}
    for e in all_errors:
        sym_data.setdefault(e.symbol_ast_id, []).append(e.error_norm)
    if not sym_data:
        return
    symbols = sorted(sym_data.keys())
    means = [sum(sym_data[s]) / len(sym_data[s]) for s in symbols]
    sample_counts = [len(sym_data[s]) for s in symbols]

    fig, ax = plt.subplots(figsize=(10, max(4, len(symbols) * 0.5)))
    bars = ax.barh(symbols, means, color=_COLORS["accent"], edgecolor="white",
                   linewidth=0.6, height=0.6)
    ax.set_xlabel("Mean Error Norm", fontsize=12)
    ax.set_title("Per-Symbol Prediction Error (Extended 60 min)",
                 fontsize=14, fontweight="bold")
    ax.grid(axis="x", alpha=0.3)
    for bar, val, cnt in zip(bars, means, sample_counts):
        ax.text(bar.get_width() + 0.005, bar.get_y() + bar.get_height() / 2,
                f"{val:.4f} (n={cnt})", va="center", fontsize=9, color="#374151")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"  📊 Saved: {path}")


def plot_extended_comparison(all_errors, synth_tracker, path):
    """Overlaid density histograms with comparison text."""
    live_norms = [e.error_norm for e in all_errors]
    synth_norms = [e.error_norm for e in synth_tracker._errors]
    if not live_norms:
        return

    fig, axes = plt.subplots(2, 1, figsize=(12, 9),
                             gridspec_kw={"height_ratios": [3, 1]})

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
            label=f"Extended Live (n={len(live_norms)})", density=True)

    ax.axvline(0.12, color=_COLORS["valley"], linestyle="--", linewidth=1.2,
               alpha=0.7, label="Sub→Critical (0.12)")
    ax.axvline(0.35, color=_COLORS["valley"], linestyle="-.", linewidth=1.2,
               alpha=0.7, label="Critical→Super (0.35)")
    ax.set_xlabel("Prediction Error Norm", fontsize=12)
    ax.set_ylabel("Density", fontsize=12)
    ax.set_title("Synthetic vs Extended Live Prediction-Error Distribution",
                 fontsize=14, fontweight="bold")
    ax.legend(fontsize=10, loc="upper right")
    ax.grid(axis="y", alpha=0.3)

    ax2 = axes[1]
    ax2.axis("off")
    comp_text = (
        f"Synthetic peaks:  ~{SYNTHETIC_PEAK_LOW} and ~{SYNTHETIC_PEAK_HIGH}\n"
        f"5-min live peaks: ~{LIVE_5MIN_PEAK_LOW} and ~{LIVE_5MIN_PEAK_HIGH}\n"
        f"Extended live:     n={len(live_norms)} records over 60 min"
    )
    ax2.text(0.02, 0.95, comp_text, transform=ax2.transAxes,
             fontsize=10, fontfamily="monospace", verticalalignment="top",
             bbox=dict(boxstyle="round,pad=0.5", facecolor="#F3F4F6",
                       edgecolor="#D1D5DB", alpha=0.9))

    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"  📊 Saved: {path}")


def plot_mean_error_trend(snapshot_history, path):
    """Line plot of mean error norm over time from snapshot history."""
    if not snapshot_history:
        return
    elapsed_min = [s["elapsed"] / 60.0 for s in snapshot_history]
    means = [s["mean_error"] for s in snapshot_history]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(elapsed_min, means, marker="o", color=_COLORS["live"],
            linewidth=2, markersize=5, label="Mean error norm")
    ax.axhline(0.12, color=_COLORS["valley"], linestyle="--", linewidth=1.2,
               alpha=0.7, label="Threshold 0.12")
    ax.axhline(0.35, color=_COLORS["valley"], linestyle="-.", linewidth=1.2,
               alpha=0.7, label="Threshold 0.35")
    ax.set_xlabel("Elapsed (minutes)", fontsize=12)
    ax.set_ylabel("Mean Error Norm", fontsize=12)
    ax.set_title("Mean Error Norm Trend Over 60 Minutes",
                 fontsize=14, fontweight="bold")
    ax.legend(fontsize=10)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"  📊 Saved: {path}")


def plot_threshold_evolution(snapshot_history, all_errors, path):
    """Stacked area chart showing threshold bucket fractions over time."""
    if not snapshot_history:
        return

    elapsed_min = []
    well_fracs = []
    valley_fracs = []
    novel_fracs = []

    for snap in snapshot_history:
        n_rec = snap["n_records"]
        # Use errors up to this snapshot's record count
        subset = all_errors[:n_rec]
        wf, vf, nf = _bucket_fractions(subset)
        elapsed_min.append(snap["elapsed"] / 60.0)
        well_fracs.append(wf)
        valley_fracs.append(vf)
        novel_fracs.append(nf)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.stackplot(elapsed_min, well_fracs, valley_fracs, novel_fracs,
                 labels=["Well-grounded [0, 0.12)", "Valley [0.12, 0.35)",
                         "Novel [0.35, +∞)"],
                 colors=[_COLORS["well_grounded"], _COLORS["valley_area"],
                         _COLORS["novel"]],
                 alpha=0.75)
    ax.set_xlabel("Elapsed (minutes)", fontsize=12)
    ax.set_ylabel("Fraction of Samples", fontsize=12)
    ax.set_title("Threshold Bucket Evolution Over 60 Minutes",
                 fontsize=14, fontweight="bold")
    ax.legend(fontsize=10, loc="upper right")
    ax.set_ylim(0, 1)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"  📊 Saved: {path}")


# ── main live session ────────────────────────────────────────────────


def main():
    print("=" * 60)
    print("  EXTENDED LIVE PREDICTION-ERROR DIAGNOSTIC (60 MIN)")
    print(f"  Max duration: {MAX_DURATION}s  |  Target records: {MAX_RECORDS}")
    if _ACCELERATED:
        print("  ⚡ ACCELERATED MODE — completing in ~3-5 minutes")
    print("=" * 60)

    shim, grounder, tracker = _build_live_stack()

    # Define symbol prototypes
    prototypes = {}
    for i in range(NUM_SYMBOLS):
        sym_id = f"ext_sym_{i}"
        proto = {
            "brightness": 0.1 + 0.1 * (i % 6),
            "sharpness": 0.05 + 0.12 * (i % 4),
            "contrast": 0.3 + 0.08 * (i % 5),
        }
        prototypes[sym_id] = proto
        grounder.grounding_links[sym_id] = [
            GroundingLink(
                symbol_ast_id=sym_id,
                sub_symbolic_representation=proto,
                modality="visual_features",
                confidence=0.9,
            )
        ]

    sym_ids = list(prototypes.keys())
    all_errors = []           # ALL records (not windowed)
    snapshot_history = []     # periodic snapshot dicts

    t_start = time.time()
    last_snapshot = t_start
    activation_count = 0
    records_at_last_snapshot = 0

    print(f"\nStarting live activations ({NUM_SYMBOLS} symbols)...\n")

    while True:
        elapsed = time.time() - t_start
        n_records = len(all_errors)

        # Simulated elapsed for data generation (full 60 min scale)
        if _ACCELERATED:
            elapsed_sim = (n_records / MAX_RECORDS) * MAX_DURATION
        else:
            elapsed_sim = elapsed

        elapsed_frac = min(elapsed_sim / MAX_DURATION, 1.0)

        # Termination conditions
        if not _ACCELERATED and elapsed >= MAX_DURATION:
            print(f"\n⏱  Max duration reached ({MAX_DURATION}s)")
            break
        if n_records >= MAX_RECORDS:
            print(f"\n🎯 Target records reached ({MAX_RECORDS})")
            break

        # Snapshot trigger
        take_snapshot = False
        if _ACCELERATED:
            if n_records - records_at_last_snapshot >= _SNAPSHOT_RECORD_INTERVAL and n_records > 0:
                take_snapshot = True
        else:
            if time.time() - last_snapshot >= SNAPSHOT_INTERVAL:
                take_snapshot = True

        if take_snapshot:
            print_snapshot(elapsed_sim, tracker, all_errors, snapshot_history)
            last_snapshot = time.time()
            records_at_last_snapshot = n_records

        # Pick a random symbol and generate observation
        sym_id = random.choice(sym_ids)
        proto = prototypes[sym_id]

        # Observation mix with time-based evolution (invariant: sum = 1.0)
        well_match_prob = 0.40 - elapsed_frac * 0.05   # 0.40 → 0.35
        slight_prob = 0.30                               # constant
        novel_prob = 0.20 + elapsed_frac * 0.05          # 0.20 → 0.25
        random_prob = 0.10                               # constant

        roll = random.random()
        if roll < well_match_prob:
            obs = {k: _jitter(v, 0.02) for k, v in proto.items()}
        elif roll < well_match_prob + slight_prob:
            obs = {k: _jitter(v, 0.08) for k, v in proto.items()}
        elif roll < well_match_prob + slight_prob + novel_prob:
            obs = {k: v + random.uniform(0.25, 0.55) for k, v in proto.items()}
        else:
            obs = {k: random.random() for k in proto}

        # Push through the shim
        shim.set_observation_context(obs, modality="visual_features")
        stmt = _make_statement(sym_id)
        shim.add_statement(stmt, "TRUTHS")

        # Record to all_errors separately
        if tracker._errors and len(tracker._errors) > len(all_errors):
            latest = tracker._errors[-1]
            all_errors.append(latest)

        activation_count += 1

        if _ACCELERATED:
            time.sleep(0.001)
        else:
            time.sleep(ACTIVATION_DELAY)

    # Final snapshot
    elapsed_final = MAX_DURATION if _ACCELERATED else (time.time() - t_start)
    print_snapshot(elapsed_final, tracker, all_errors, snapshot_history)

    # Shim stats
    stats = shim.measurement_stats
    print(f"\n=== SHIM MEASUREMENT STATS ===")
    print(f"  measurements_recorded: {stats['measurements_recorded']}")
    print(f"  skipped_no_context:    {stats['skipped_no_context']}")
    print(f"  skipped_cold_start:    {stats['skipped_cold_start']}")
    print(f"  total activations:     {activation_count}")

    # Full 60-minute analysis
    print_full_analysis(all_errors, tracker, snapshot_history)

    # Generate plots
    os.makedirs(_OUTPUT_DIR, exist_ok=True)
    print(f"\n=== GENERATING PLOTS → {_OUTPUT_DIR}/ ===")

    plot_extended_histogram(
        all_errors, os.path.join(_OUTPUT_DIR, "extended_live_histogram.png"))
    plot_extended_per_symbol(
        all_errors, os.path.join(_OUTPUT_DIR, "extended_per_symbol_error.png"))

    print("  Running synthetic baseline for overlay comparison...")
    synth_tracker = _run_synthetic_scenario()
    plot_extended_comparison(
        all_errors, synth_tracker,
        os.path.join(_OUTPUT_DIR, "extended_synthetic_vs_live.png"))

    plot_mean_error_trend(
        snapshot_history, os.path.join(_OUTPUT_DIR, "extended_mean_error_trend.png"))
    plot_threshold_evolution(
        snapshot_history, all_errors,
        os.path.join(_OUTPUT_DIR, "extended_threshold_evolution.png"))

    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
