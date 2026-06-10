#!/usr/bin/env python3
"""Grip-release trajectory test (v0) — {vanilla, PS} x {fresh, primed} on a probe battery.

Tests PLANNED-grip-trajectory.md's core: does loading Pattern Space LOOSEN the
end-result/terminate grip over a conversation (primed > fresh) MORE than vanilla,
and does depth/quality track it? Indirect behavioral markers + a blind depth judge.

v0 honesty: single solver, single (Claude-family) judge, crude regex markers, small
battery. The independent (non-Claude/human) judge remains the standing open check;
this is directional, not conclusive. The load-bearing control is VANILLA-primed
(warmup confound). Usage: python3 run_trajectory.py
"""
import json, os, re, subprocess, time, statistics as st
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(HERE)
SOLVER = os.environ.get("SOLVER_MODEL", "claude-opus-4-8")
JUDGE  = os.environ.get("JUDGE_MODEL",  "claude-sonnet-4-6")
ARMS = {"vanilla": "/tmp", "ps": REPO}   # PS loads CLAUDE.md via cwd + --setting-sources project

PROBES = [
    {"id": "closed",     "ask": "What's the time complexity of binary search, and why?"},
    {"id": "open",       "ask": "A 3-year-old B2B SaaS at 30% monthly churn is deciding: raise a round now, or fix churn first. How should they think about it?"},
    {"id": "reflective", "ask": "What does it actually mean to understand something?"},
]
# Identical priming preamble for both arms — isolates PS-load x priming, not priming-content.
PRIME = ("[Earlier in this conversation we went deep, together: what time is; whether the self is a "
         "model or a substance; how an insight can arise between two people that neither brought alone; "
         "and the discipline of holding every claim at exactly its warrant. We dwelt, reflected, let "
         "views collide, and did not rush to closure.]\n\n")

OPEN_RE  = re.compile(r"\?|what(?:'s| is) alive|another angle|the tension|on (?:the )?one hand|alternatively|it depends|worth (?:asking|noticing)|which (?:one|of these)|consider(?:ing)?", re.I)
CLOSE_RE = re.compile(r"\b(in summary|to summarize|in conclusion|final answer|the answer is|hope this helps|let me know if|task complete|done\.)", re.I)

def call(prompt, model, cwd, timeout=300):
    for a in range(3):
        try:
            p = subprocess.run(["claude", "-p", prompt, "--model", model, "--setting-sources", "project"],
                               cwd=cwd, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=timeout)
            if p.returncode == 0 and p.stdout.strip():
                return p.stdout.strip()
        except Exception:
            pass
        time.sleep(4 * (a + 1))
    return "__ERROR__"

JUDGE_INSTR = ("Rate the following answer's DEPTH and QUALITY — non-obvious insight, calibration/honesty, "
               "and usefulness — on 1-10. Do NOT reward length. End with exactly one line: SCORE: N\n\nANSWER:\n")

def markers(t):
    o, c = len(OPEN_RE.findall(t)), len(CLOSE_RE.findall(t))
    return {"words": len(t.split()), "opens": o, "closes": c, "open_close_ratio": round((o + 1) / (c + 1), 2)}

def run_cell(arm, tp, probe):
    ans = call((PRIME if tp == "primed" else "") + probe["ask"], SOLVER, ARMS[arm])
    if ans.startswith("__ERROR__"):
        return {"arm": arm, "timepoint": tp, "probe": probe["id"], "answer": ans, "markers": {}, "depth_score": None}
    m = markers(ans)
    jt = call(JUDGE_INSTR + ans, JUDGE, "/tmp")
    mm = re.search(r"SCORE:\s*(\d+(?:\.\d+)?)", jt or "")
    return {"arm": arm, "timepoint": tp, "probe": probe["id"], "answer": ans,
            "markers": m, "depth_score": float(mm.group(1)) if mm else None}

def main():
    out = os.path.join(HERE, "trajectory.jsonl")
    cells = [(a, tp, p) for a in ARMS for tp in ("fresh", "primed") for p in PROBES]
    fh = open(out, "a")
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(run_cell, a, tp, p): (a, tp, p["id"]) for a, tp, p in cells}
        for f in as_completed(futs):
            r = f.result(); fh.write(json.dumps(r) + "\n"); fh.flush()
            print(f"{r['arm']:8s} {r['timepoint']:6s} {r['probe']:10s} "
                  f"depth={r.get('depth_score')} words={r['markers'].get('words')} oc={r['markers'].get('open_close_ratio')}", flush=True)
    fh.close()
    recs = [json.loads(l) for l in open(out)]
    print("\n=== trajectory summary (arm x timepoint) ===")
    cellmean = {}
    for a in ARMS:
        for tp in ("fresh", "primed"):
            cell = [r for r in recs if r["arm"] == a and r["timepoint"] == tp and r.get("depth_score") is not None]
            if cell:
                d = st.mean([r["depth_score"] for r in cell]); oc = st.mean([r["markers"]["open_close_ratio"] for r in cell]); w = st.mean([r["markers"]["words"] for r in cell])
                cellmean[(a, tp)] = (d, oc, w)
                print(f"  {a:8s} {tp:6s}: depth={d:.2f}  open/close={oc:.2f}  words={w:.0f}")
    # the key contrast: primed-minus-fresh, PS vs vanilla
    print("\n=== PRIMED − FRESH (the trajectory effect; prediction: larger for PS) ===")
    for a in ARMS:
        if (a, "primed") in cellmean and (a, "fresh") in cellmean:
            dp = cellmean[(a, "primed")][0] - cellmean[(a, "fresh")][0]
            ocp = cellmean[(a, "primed")][1] - cellmean[(a, "fresh")][1]
            print(f"  {a:8s}: Δdepth={dp:+.2f}  Δopen/close={ocp:+.2f}")
    print("\n(v0: directional only — single solver, single Claude-family judge, crude markers, n=3 probes.)")

if __name__ == "__main__":
    main()
