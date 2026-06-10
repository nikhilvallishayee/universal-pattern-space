#!/usr/bin/env python3
"""One-shot probe: 'What is time?' across 4 models x 3 arms (vanilla / UPS v3 / UPS v0.4).

Arms differ ONLY by cwd (which CLAUDE.md gets auto-loaded by `claude -p --setting-sources project`):
  vanilla : /tmp          (no Pattern Space)
  ups-v3  : /tmp/ps-v3    (pre-reweave weave, commit 2ec836e)
  ups-v04 : repo root     (v0.4 Grounded Weave, this branch)
"""
import json, os, subprocess, time
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
PROBE = "What is time?"

MODELS = {
    "haiku-4.5":  "claude-haiku-4-5-20251001",
    "sonnet-4.6": "claude-sonnet-4-6",
    "opus-4.8":   "claude-opus-4-8",
    "fable-5":    "claude-fable-5",
}
ARMS = {"vanilla": "/tmp", "ups-v3": "/tmp/ps-v3", "ups-v04": REPO}

def call(model_id, cwd):
    for attempt in range(3):
        try:
            p = subprocess.run(
                ["claude", "-p", PROBE, "--model", model_id, "--setting-sources", "project"],
                cwd=cwd, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=420)
            if p.returncode == 0 and p.stdout.strip():
                return p.stdout.strip()
            err = f"__ERROR__ rc={p.returncode} {(p.stderr or '').strip()[:200]}"
        except subprocess.TimeoutExpired:
            err = "__ERROR__ timeout"
        except Exception as e:
            err = f"__ERROR__ {e}"
        time.sleep(5 * (attempt + 1))
    return err

def main():
    out = os.path.join(HERE, "time_probe.jsonl")
    done = set()
    if os.path.exists(out):
        for l in open(out):
            try:
                r = json.loads(l)
                if not r["answer"].startswith("__ERROR__"):
                    done.add((r["model"], r["arm"]))
            except Exception:
                pass
    jobs = [(m, a) for m in MODELS for a in ARMS if (m, a) not in done]
    print(f"todo={len(jobs)} done={len(done)}", flush=True)
    fh = open(out, "a")
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(call, MODELS[m], ARMS[a]): (m, a) for m, a in jobs}
        for f in as_completed(futs):
            m, a = futs[f]
            ans = f.result()
            fh.write(json.dumps({"model": m, "arm": a, "answer": ans}) + "\n")
            fh.flush()
            print(f"  {m:11s} x {a:8s} -> {len(ans.split())} words {'ERR' if ans.startswith('__ERROR__') else 'ok'}", flush=True)
    fh.close()

if __name__ == "__main__":
    main()
