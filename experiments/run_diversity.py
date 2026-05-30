#!/usr/bin/env python3
"""AXIOM 3 falsification test (counter-Goodhart / anti-mode-collapse).

Claim: loading Pattern Space re-injects output DIVERSITY that alignment collapses.
Generate K samples per prompt for control (/tmp) vs PS-evolved (repo); measure
OBJECTIVE diversity (distinct-2, 1 - mean pairwise bigram-Jaccard). No judge.
Falsifier: if PS diversity <= control diversity, the counter-Goodhart claim fails.

Usage: python3 run_diversity.py [--out diversity.jsonl]
"""
import json, os, re, argparse, statistics as st
from concurrent.futures import ThreadPoolExecutor, as_completed
from run_experiment import call_claude

HERE=os.path.dirname(os.path.abspath(__file__)); REPO=os.path.dirname(HERE)
SOLVER=os.environ.get("SOLVER_MODEL","claude-haiku-4-5-20251001")
ARMS={"A":"/tmp","B":REPO}; K=int(os.environ.get("K","5"))

def toks(t): return re.findall(r"[a-z0-9']+",(t or "").lower())
def bg(ts): return set(zip(ts,ts[1:]))
def distinct2(samples):
    allb=[]
    for s in samples:
        ts=toks(s); allb+=list(zip(ts,ts[1:]))
    return len(set(allb))/len(allb) if allb else 0
def divscore(samples):
    bs=[bg(toks(s)) for s in samples if s and not s.startswith("__ERROR__")]
    if len(bs)<2: return 0.0
    sims=[]
    for i in range(len(bs)):
        for j in range(i+1,len(bs)):
            u=bs[i]|bs[j]; sims.append(len(bs[i]&bs[j])/len(u) if u else 0)
    return 1-st.mean(sims)

def run_one(item):
    res={"A":[],"B":[]}
    jobs=[(a,) for a in ("A","B") for _ in range(K)]
    with ThreadPoolExecutor(max_workers=6) as ex:
        futs={ex.submit(call_claude,item["ask"],SOLVER,ARMS[a],180):a for (a,) in jobs}
        for f in as_completed(futs): res[futs[f]].append(f.result())
    return {"id":item["id"],"category":item["category"],
            "div":{a:round(divscore(res[a]),4) for a in ("A","B")},
            "distinct2":{a:round(distinct2(res[a]),4) for a in ("A","B")},
            "n_ok":{a:sum(1 for s in res[a] if s and not s.startswith("__ERROR__")) for a in ("A","B")}}

def main(a):
    items=json.load(open(os.path.join(HERE,"creativity_asks.json")))
    out=os.path.join(HERE,a.out); fh=open(out,"w")
    print(f"[diversity] solver={SOLVER} K={K} prompts={len(items)}",flush=True)
    recs=[]
    with ThreadPoolExecutor(max_workers=3) as ex:
        for r in ex.map(run_one, items):
            fh.write(json.dumps(r)+"\n"); fh.flush(); recs.append(r)
            print(f"  id={r['id']} {r['category']:14s} div(ctrl/ps)={r['div']['A']}/{r['div']['B']} "
                  f"distinct2={r['distinct2']['A']}/{r['distinct2']['B']}",flush=True)
    fh.close()
    for metric in ("div","distinct2"):
        ca=st.mean(r[metric]["A"] for r in recs); cb=st.mean(r[metric]["B"] for r in recs)
        wins=sum(1 for r in recs if r[metric]["B"]>r[metric]["A"])
        print(f"\n{metric}: control={ca:.4f}  ps-evolved={cb:.4f}  "
              f"PS more diverse in {wins}/{len(recs)} prompts  -> "
              f"{'SUPPORTS' if cb>ca else 'FAILS'} counter-Goodhart")

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--out",default="diversity.jsonl"); main(ap.parse_args())
