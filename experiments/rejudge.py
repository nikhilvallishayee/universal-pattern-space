#!/usr/bin/env python3
"""Re-judge stored answers with a DIFFERENT judge model to test the single-judge threat.
Usage: python3 rejudge.py results_opus.jsonl claude-haiku-4-5-20251001 rejudge_haiku.jsonl"""
import json, random, sys, concurrent.futures as cf
from run_experiment import call_claude, JUDGE_INSTR, parse_judge

infile, model, out = sys.argv[1], sys.argv[2], sys.argv[3]
recs = [json.loads(l) for l in open(infile) if l.strip()]

def rej(r):
    ans = r["answers"]; arms = ["A","B","C"]; random.shuffle(arms)
    lm = dict(zip(["X","Y","Z"], arms))
    jp = JUDGE_INSTR + "PROMPT:\n" + r["ask"] + "\n\n"
    for lab in ("X","Y","Z"): jp += f"=== ANSWER {lab} ===\n{ans[lm[lab]]}\n\n"
    jr = parse_judge(call_claude(jp, model, "/tmp"))
    o = {"id": r["id"], "category": r["category"]}
    if jr and isinstance(jr.get("ranking"), list):
        try:
            o["ranking_arms"] = [lm[l] for l in jr["ranking"]]; o["winner_arm"] = o["ranking_arms"][0]
        except: o["winner_arm"] = None
    return o

fh = open(out, "w"); n=0
with cf.ThreadPoolExecutor(max_workers=6) as ex:
    for o in ex.map(rej, recs):
        fh.write(json.dumps(o)+"\n"); fh.flush(); n+=1
        if o.get("winner_arm"): print(f"[{n}] id={o['id']} winner={o['winner_arm']}", flush=True)
fh.close(); print(f"done {n} -> {out}", flush=True)
