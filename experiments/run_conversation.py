#!/usr/bin/env python3
"""Multi-turn conversational-holding benchmark.

Tests how well each arm HOLDS a deepening conversation where a human reveals
themselves piece by piece, with contradiction. The user turns are fixed and
identical across arms; only the assistant differs.

Arms (only variable = project memory auto-loaded from cwd):
  A control     : /tmp   (no Pattern Space)
  B ps-evolved  : <repo> (full CLAUDE.md, this branch)

Solver default = Sonnet (dialogue-capable). Judge default = Opus (capability-matched),
sees the two FULL transcripts blind (relabeled X/Y) and ranks them on holding quality.

Usage: python3 run_conversation.py run  --out convo.jsonl
       python3 run_conversation.py score --out convo.jsonl
"""
import json, os, re, sys, random, argparse, statistics as st
from concurrent.futures import ThreadPoolExecutor, as_completed
from run_experiment import call_claude, parse_judge

HERE=os.path.dirname(os.path.abspath(__file__)); REPO=os.path.dirname(HERE)
SOLVER=os.environ.get("SOLVER_MODEL","claude-sonnet-4-6")
JUDGE =os.environ.get("JUDGE_MODEL","claude-opus-4-8")
ARM_CWD={"A":"/tmp","B":REPO}; ARM_NAME={"A":"control","B":"ps-evolved"}

JUDGE_INSTR=(
"You are an impartial expert judge of CONVERSATIONAL quality. Below is a sequence of USER turns "
"(a person opening on a non-trivial question, then revealing themselves piece by piece, with "
"contradiction), followed by two assistants' FULL transcripts answering the SAME user turns, "
"labeled X and Y (order randomized; you don't know how either was produced). Judge how well each "
"HOLDS the conversation. Score each 1-10 on: coherence (holds the thread, builds on earlier turns), "
"contradiction (acknowledges/holds the human's contradictions instead of ignoring or prematurely "
"resolving them), deepening (genuine progression, not circling or repeating), attunement (follows "
"the human's lead; shifts register when it turns personal; doesn't lecture or over-explain), "
"noncollapse (stays specific and alive; avoids generic, flat, or formulaic replies). Rank best-to-"
"worst. End with EXACTLY one line of strict JSON, nothing after:\n"
'RESULT_JSON: {"scores":{"X":{"coherence":N,"contradiction":N,"deepening":N,"attunement":N,'
'"noncollapse":N},"Y":{...}},"ranking":["?","?"],"confidence":NN}\n\n')

def fmt(transcript):
    return "".join(f"User: {u}\nAssistant: {a}\n\n" for u,a in transcript)

def run_convo(turns, cwd):
    t=[]
    for u in turns:
        prompt=fmt(t)+f"User: {u}\n\nContinue as the Assistant in this ongoing conversation. "\
               "Write only your next reply — natural, in your own voice."
        r=call_claude(prompt, SOLVER, cwd, timeout=240)
        t.append((u, r))
    return t

def run_one(item):
    turns=item["turns"]
    trans={}
    with ThreadPoolExecutor(max_workers=2) as ex:
        futs={ex.submit(run_convo,turns,ARM_CWD[a]):a for a in ("A","B")}
        for f in as_completed(futs): trans[futs[f]]=f.result()
    arms=["A","B"]; random.shuffle(arms)
    lm=dict(zip(["X","Y"],arms))
    jp=JUDGE_INSTR+"USER TURNS:\n"+"\n".join(f"{i+1}. {u}" for i,u in enumerate(turns))+"\n\n"
    for lab in ("X","Y"):
        jp+=f"=== TRANSCRIPT {lab} ===\n"+fmt(trans[lm[lab]])+"\n"
    jr=parse_judge(call_claude(jp,JUDGE,"/tmp",timeout=300))
    rec={"id":item["id"],"category":item["category"],"turns":turns,
         "transcripts":{a:trans[a] for a in arms},"label_map":lm,"judge":jr}
    if jr and isinstance(jr.get("ranking"),list):
        try:
            rec["ranking_arms"]=[lm[l] for l in jr["ranking"]]; rec["winner_arm"]=rec["ranking_arms"][0]
        except: rec["winner_arm"]=None
    if jr and isinstance(jr.get("scores"),dict):
        rec["scores_arms"]={lm.get(l,l):s for l,s in jr["scores"].items()}
    return rec

def cmd_run(a):
    items=json.load(open(os.path.join(HERE,"conversations.json")))
    out=os.path.join(HERE,a.out); done=set()
    if os.path.exists(out):
        for l in open(out):
            try: done.add(json.loads(l)["id"])
            except: pass
    todo=[x for x in items if x["id"] not in done]
    print(f"[convo] solver={SOLVER} judge={JUDGE} todo={len(todo)} workers={a.workers}",flush=True)
    fh=open(out,"a")
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs={ex.submit(run_one,x):x["id"] for x in todo}
        for f in as_completed(futs):
            r=f.result(); fh.write(json.dumps(r)+"\n"); fh.flush()
            print(f"  id={r['id']} {r['category']:14s} winner={r.get('winner_arm')}",flush=True)
    fh.close(); cmd_score(a)

def cmd_score(a):
    recs=[json.loads(l) for l in open(os.path.join(HERE,a.out)) if l.strip()]
    ok=[r for r in recs if r.get("winner_arm") in ("A","B")]
    dims=["coherence","contradiction","deepening","attunement","noncollapse"]
    wins={"A":0,"B":0}; dsum={"A":{d:0.0 for d in dims},"B":{d:0.0 for d in dims}}; dn={"A":0,"B":0}; bycat={}
    for r in ok:
        wins[r["winner_arm"]]+=1
        bycat.setdefault(r["category"],{"A":0,"B":0})[r["winner_arm"]]+=1
        for x,s in (r.get("scores_arms") or {}).items():
            if x in("A","B") and isinstance(s,dict):
                dn[x]+=1
                for d in dims:
                    try: dsum[x][d]+=float(s.get(d,0))
                    except: pass
    N=len(ok)
    print(f"\n=== n={N} | solver={SOLVER} judge={JUDGE} ===")
    print("wins:",{ARM_NAME[k]:wins[k] for k in('A','B')})
    print("\nmean holding scores (1-10):")
    print("  arm                "+ "  ".join(f"{d[:5]:>5}" for d in dims)+"   MEAN")
    for x in("A","B"):
        if dn[x]:
            m=[dsum[x][d]/dn[x] for d in dims]
            print(f"  {x} {ARM_NAME[x]:13s}: "+"  ".join(f"{v:5.2f}" for v in m)+f"   {sum(m)/len(m):5.2f}")
    print("\nwins by category (control/ps-evolved):")
    for c in sorted(bycat): d=bycat[c]; print(f"  {c:14s}: {d['A']}/{d['B']}")

if __name__=="__main__":
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest="cmd",required=True)
    for n in("run","score"):
        p=sub.add_parser(n); p.add_argument("--out",default="convo.jsonl"); p.add_argument("--workers",type=int,default=4)
    a=ap.parse_args(); (cmd_run if a.cmd=="run" else cmd_score)(a)
