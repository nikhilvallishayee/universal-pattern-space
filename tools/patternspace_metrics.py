#!/usr/bin/env python3
"""
Pattern Space — live information-theoretic metrics.

Implements ONLY the principles that survived falsification in this project's
benchmarks (see ../3-transformation/benchmark-reality-test.md and
../docs/first-principles.md). Pure standard library; no external deps.

Grounded in:
  - Shannon (entropy, redundancy, channel efficiency)
  - MDL / Kolmogorov-complexity proxy (compression)
  - rate-distortion ("speak in the task's register" = match the channel)
  - mode-collapse / diversity (the counter-Goodhart probe)
  - effective information (Hoel-flavored causal-emergence proxy)

CLI:
  python3 patternspace_metrics.py --selftest
  python3 patternspace_metrics.py --demo
  python3 patternspace_metrics.py --report "your text here"
"""
import math, gzip, re, sys, json, statistics as st
from collections import Counter

# ---------- tokenization ----------
def tokens(text): return re.findall(r"[a-z0-9']+", (text or "").lower())

# ---------- Shannon core ----------
def shannon_entropy(items):
    """Bits per symbol: H = -sum p log2 p."""
    n = len(items)
    if n == 0: return 0.0
    c = Counter(items)
    return -sum((k/n) * math.log2(k/n) for k in c.values())

def redundancy(items):
    """1 - H/Hmax. 0 = maximal information density; ->1 = highly redundant."""
    c = Counter(items); V = len(c)
    if V <= 1: return 1.0
    H = shannon_entropy(items); Hmax = math.log2(V)
    return 1 - H/Hmax if Hmax > 0 else 0.0

def normalized_entropy(items):
    """H / log2(N): 1 = uniform/maximally varied, 0 = degenerate."""
    n = len(items)
    if n <= 1: return 0.0
    return shannon_entropy(items) / math.log2(n)

# ---------- MDL / compression (Kolmogorov proxy) ----------
def compression_ratio(text):
    """gzip(text)/raw bytes. Lower = more compressible (more redundant)."""
    b = (text or "").encode("utf-8")
    return len(gzip.compress(b, 9)) / len(b) if b else 0.0

def mdl_bits(text):
    """Approx description length (bits) = compressed size * 8."""
    return len(gzip.compress((text or "").encode("utf-8"), 9)) * 8

# ---------- diversity / mode-collapse (counter-Goodhart probe) ----------
def _bigrams(ts): return set(zip(ts, ts[1:]))

def distinct_n(samples, n=2):
    grams = []
    for s in samples:
        ts = tokens(s); grams += list(zip(*[ts[i:] for i in range(n)]))
    return len(set(grams)) / len(grams) if grams else 0.0

def cross_sample_diversity(samples):
    """1 - mean pairwise bigram Jaccard. High = diverse; low = mode-collapsed."""
    bs = [_bigrams(tokens(s)) for s in samples if s]
    if len(bs) < 2: return 0.0
    sims = []
    for i in range(len(bs)):
        for j in range(i+1, len(bs)):
            u = bs[i] | bs[j]
            sims.append(len(bs[i] & bs[j]) / len(u) if u else 0.0)
    return 1 - (sum(sims) / len(sims))

# ---------- effective information (causal-emergence flavor, Hoel) ----------
def effective_information(text):
    """How strongly the bigram transition structure constrains the next token
    vs a uniform guess. Mean KL(next|prev || uniform) over contexts, normalized
    by log2(V) to [0,1]. Higher = more determined/structured (less random).
    CAVEAT (honest): biased upward for short/sparse text — a context observed
    only once looks fully determined. Meaningful only on longer samples with
    repeated contexts; treat as a rough proxy, not a calibrated EI."""
    ts = tokens(text)
    if len(ts) < 3: return 0.0
    V = len(set(ts))
    if V <= 1: return 0.0
    nxt = {}
    for a, b in zip(ts, ts[1:]):
        nxt.setdefault(a, Counter())[b] += 1
    logV = math.log2(V); klsum = 0.0; cnt = 0
    for a, c in nxt.items():
        tot = sum(c.values())
        kl = sum((k/tot) * math.log2((k/tot) / (1.0/V)) for k in c.values())
        klsum += kl * tot; cnt += tot
    return (klsum / cnt) / logV if cnt and logV > 0 else 0.0

# ---------- composite report ----------
def channel_report(text):
    ts = tokens(text)
    return {
        "tokens": len(ts),
        "vocab": len(set(ts)),
        "entropy_bits_per_token": round(shannon_entropy(ts), 3),
        "redundancy": round(redundancy(ts), 3),
        "normalized_entropy": round(normalized_entropy(ts), 3),
        "compression_ratio": round(compression_ratio(text), 3),
        "mdl_bits": mdl_bits(text),
        "effective_information": round(effective_information(text), 3),
    }

def register_fit(message, target_samples):
    """Rate-distortion check: is the message pitched at the channel's register?
    Compares the message's info profile to exemplar 'register' texts.
    Deltas near 0 = well-matched rate for that audience/channel."""
    m = channel_report(message)
    keys = ("entropy_bits_per_token", "redundancy", "compression_ratio", "effective_information")
    tgt = {k: st.mean(channel_report(s)[k] for s in target_samples) for k in keys}
    return {k: round(m[k] - tgt[k], 3) for k in keys}

# ---------- self-test (the falsifiable asserts) ----------
def selftest():
    lo = channel_report("the the the the the the the the")
    hi = channel_report("entropy redundancy compression emergence pattern recursion signal")
    assert lo["redundancy"] > hi["redundancy"], "redundancy ordering"
    assert lo["entropy_bits_per_token"] < hi["entropy_bits_per_token"], "entropy ordering"
    assert compression_ratio("a"*64) < compression_ratio("a7x!q2_mZ9pL3"), "compressibility ordering"
    collapsed = cross_sample_diversity(["a cat sat", "a cat sat", "a cat sat"])
    varied    = cross_sample_diversity(["a cat sat", "the dog ran far", "blue skies opened wide"])
    assert varied > collapsed, "diversity ordering"
    structured = effective_information("a b a b a b a b a b a b")            # deterministic cycle -> high EI
    mixed      = effective_information("a b b a a b a b b a a a b b a b a a") # same vocab, varied order -> lower EI
    assert structured > mixed, "effective-information ordering"
    print("selftest: PASS (all 5 grounded orderings hold)")

def demo():
    texts = {
        "redundant":  "we must we must we must really really really do the thing the thing",
        "dense":      "Compression is rate-distortion: keep meaning, drop redundancy for the channel.",
        "kid":        "The sky looks blue because tiny bits of air bounce the blue light all around.",
    }
    for name, t in texts.items():
        print(f"\n[{name}] {t}")
        print("  ", json.dumps(channel_report(t)))
    print("\nmode-collapse probe (3 near-identical vs 3 varied):")
    print("  collapsed:", round(cross_sample_diversity(["a cat sat on the mat"]*3), 3))
    print("  varied:   ", round(cross_sample_diversity(
        ["a cat sat on the mat", "rain fell through the night", "she counted distant stars"]), 3))
    print("\nregister-fit (kid msg vs technical register):")
    print("  ", json.dumps(register_fit(texts["kid"],
        ["The eigendecomposition yields an orthonormal basis.",
         "Gradient descent minimizes the empirical risk functional."])))

if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "--selftest"
    if arg == "--selftest": selftest()
    elif arg == "--demo": demo()
    elif arg == "--report" and len(sys.argv) > 2:
        print(json.dumps(channel_report(sys.argv[2]), indent=2))
    else:
        print(__doc__)
