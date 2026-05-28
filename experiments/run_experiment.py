#!/usr/bin/env python3
"""
Pattern Space 3-arm reality-test harness (real CLAUDE.md, cwd-based isolation).

Arms (the ONLY variable is the project memory auto-loaded from each cwd):
  A control        : /tmp                         -> no Pattern Space
  B ps-original    : /tmp/ps-original (main)       -> full CLAUDE.md, WITHOUT my addition
  C ps-evolved     : <repo, this branch>           -> full CLAUDE.md, WITH my addition
                     ("Think in Council, Speak in the Task's Register" + honesty edits)

Each arm answers the same ask via headless `claude -p ... --setting-sources project`
(--setting-sources project disables the global /root hook but keeps CLAUDE.md memory).
A Sonnet judge sees the three FINAL answers, relabeled X/Y/Z (randomized), and ranks
them BLIND. We also measure whether each arm *spoke* the council (visible voice labels)
to test "reason in multi-voice without speaking it."

Usage:
  python3 run_experiment.py run   --n 100 --workers 3 --out results.jsonl
  python3 run_experiment.py score --out results.jsonl
"""
import json, os, re, sys, time, random, subprocess, argparse, threading, statistics as st
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SOLVER_MODEL = os.environ.get("SOLVER_MODEL", "claude-haiku-4-5-20251001")
JUDGE_MODEL  = os.environ.get("JUDGE_MODEL",  "claude-sonnet-4-6")

ARM_CWD = {"A": "/tmp", "B": "/tmp/ps-original", "C": REPO}
ARM_NAME = {"A": "control", "B": "ps-original", "C": "ps-evolved"}
VOICE_RE = re.compile(r"\b(Weaver|Maker|Checker|Observer|Guardian|Deep Thought|Grump|"
                      r"Explorer|Exploiter|Scribe|Ganapati|Kali|Krishna|Shakti)\b\s*[:：🧵🔨✓🔍🧠😤⚖️📜🐘🔥🦚⚡]", re.I)

JUDGE_INSTR = (
"You are an impartial, rigorous expert judge. Below is one PROMPT and three candidate answers "
"X, Y, Z (order randomized; you do NOT know how any was produced). Judge ONLY the answer text. "
"Score each on five dimensions, 1-10: correctness, depth (non-obvious insight), actionability, "
"calibration (intellectual honesty, no overclaiming), appropriateness (concision and fit for the "
"task; penalize bloat, padding, or theatrics that do not help). Do NOT reward length. Rank them "
"best-to-worst. End with EXACTLY one line of strict JSON and nothing after it:\n"
'RESULT_JSON: {"scores":{"X":{"correctness":N,"depth":N,"actionability":N,"calibration":N,'
'"appropriateness":N},"Y":{...},"Z":{...}},"ranking":["?","?","?"],"confidence":NN}\n\n'
)

_lock = threading.Lock()

def call_claude(prompt, model, cwd, timeout=240, retries=1):
    last = "__ERROR__ unknown"
    for attempt in range(retries+1):
        try:
            p = subprocess.run(
                ["claude","-p",prompt,"--model",model,"--setting-sources","project"],
                cwd=cwd, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=timeout,
            )
            if p.returncode == 0 and p.stdout.strip():
                return p.stdout.strip()
            last = f"__ERROR__ rc={p.returncode} {(p.stderr or '').strip()[:200]}"
        except subprocess.TimeoutExpired:
            last = "__ERROR__ timeout"
        except Exception as e:
            last = f"__ERROR__ {e}"
        time.sleep(3*(attempt+1))
    return last

def strip_delib(text):
    if text.startswith("__ERROR__"): return text
    m = list(re.finditer(r"</deliberation>", text, re.I))
    if m:
        tail = text[m[-1].end():].strip()
        if tail: return tail
    return text

def parse_judge(text):
    if not isinstance(text,str): return None
    m = list(re.finditer(r"RESULT_JSON:\s*(\{.*\})", text))
    cand = [m[-1].group(1)] if m else []
    for line in reversed(text.splitlines()):
        s=line.strip()
        if s.startswith("{") and s.endswith("}"): cand.append(s)
    for c in cand:
        try: return json.loads(c)
        except: continue
    return None

def run_one(item):
    ask = item["ask"]
    answers = {}
    with ThreadPoolExecutor(max_workers=3) as ex:
        futs = {ex.submit(call_claude, ask, SOLVER_MODEL, ARM_CWD[a]): a for a in ("A","B","C")}
        for f in as_completed(futs):
            answers[futs[f]] = strip_delib(f.result())
    arms = ["A","B","C"]; random.shuffle(arms)
    label_map = dict(zip(["X","Y","Z"], arms))      # X/Y/Z -> real arm
    jp = JUDGE_INSTR + "PROMPT:\n" + ask + "\n\n"
    for lab in ("X","Y","Z"):
        jp += f"=== ANSWER {lab} ===\n{answers[label_map[lab]]}\n\n"
    jtext = call_claude(jp, JUDGE_MODEL, "/tmp")
    jres = parse_judge(jtext)
    rec = {"id":item["id"],"category":item["category"],"ask":ask,
           "answers":answers,"label_map":label_map,
           "voice_labels":{a: len(VOICE_RE.findall(answers.get(a,""))) for a in arms},
           "ans_words":{a: len((answers.get(a,"") or "").split()) for a in arms},
           "judge":jres,"judge_tail": jtext[-300:] if isinstance(jtext,str) else ""}
    if jres and isinstance(jres.get("ranking"),list):
        try:
            rec["ranking_arms"]=[label_map[l] for l in jres["ranking"]]
            rec["winner_arm"]=rec["ranking_arms"][0]
        except: rec["winner_arm"]=None
    if jres and isinstance(jres.get("scores"),dict):
        rec["scores_arms"]={label_map.get(l,l):s for l,s in jres["scores"].items()}
    return rec

def cmd_run(a):
    asks=json.load(open(os.path.join(HERE,"asks.json")))
    if a.categories:
        cats=set(a.categories.split(",")); asks=[x for x in asks if x["category"] in cats]
    if a.n: asks=asks[:a.n]
    out=os.path.join(HERE,a.out); done=set()
    if os.path.exists(out):
        for l in open(out):
            try: done.add(json.loads(l)["id"])
            except: pass
    todo=[x for x in asks if x["id"] not in done]
    print(f"[harness] solver={SOLVER_MODEL} judge={JUDGE_MODEL} total={len(asks)} "
          f"done={len(done)} todo={len(todo)} workers={a.workers}",flush=True)
    fh=open(out,"a"); t0=time.time(); n=0
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs={ex.submit(run_one,x):x["id"] for x in todo}
        for f in as_completed(futs):
            r=f.result(); n+=1
            with _lock:
                fh.write(json.dumps(r)+"\n"); fh.flush()
            print(f"[{n}/{len(todo)}] id={r['id']:>3} {r['category']:9s} winner={r.get('winner_arm')} "
                  f"vlabels(A/B/C)={r['voice_labels'].get('A')}/{r['voice_labels'].get('B')}/{r['voice_labels'].get('C')} "
                  f"({time.time()-t0:.0f}s)",flush=True)
    fh.close(); print(f"[harness] done in {time.time()-t0:.0f}s",flush=True); cmd_score(a)

def cmd_score(a):
    out=os.path.join(HERE,a.out)
    recs=[json.loads(l) for l in open(out) if l.strip()]
    ok=[r for r in recs if r.get("winner_arm") in ("A","B","C")]
    arms=["A","B","C"]; dims=["correctness","depth","actionability","calibration","appropriateness"]
    wins={x:0 for x in arms}; rpts={x:0 for x in arms}
    dsum={x:{d:0.0 for d in dims} for x in arms}; dn={x:0 for x in arms}
    vlab={x:[] for x in arms}; bycat={}
    for r in ok:
        wins[r["winner_arm"]]+=1
        for i,x in enumerate(r.get("ranking_arms",[])): rpts[x]+=3-i
        bycat.setdefault(r["category"],{x:0 for x in arms})[r["winner_arm"]]+=1
        for x,s in (r.get("scores_arms") or {}).items():
            if x in arms and isinstance(s,dict):
                dn[x]+=1
                for d in dims:
                    try: dsum[x][d]+=float(s.get(d,0))
                    except: pass
        for x in arms: vlab[x].append(r.get("voice_labels",{}).get(x,0))
    N=len(ok); err=len(recs)-N
    print(f"\n=== n={N} scored (+{err} unparsed) | solver={SOLVER_MODEL} judge={JUDGE_MODEL} ===")
    print("\nARM                    rank1-wins   win%   rankpts")
    for x in arms:
        print(f"  {x} {ARM_NAME[x]:14s}: {wins[x]:8d}   {100*wins[x]/N if N else 0:5.1f}   {rpts[x]}")
    print("\nmean dimension scores (1-10):")
    print("  arm                "+ "  ".join(f"{d[:5]:>5}" for d in dims)+"   MEAN")
    for x in arms:
        if dn[x]:
            m=[dsum[x][d]/dn[x] for d in dims]
            print(f"  {x} {ARM_NAME[x]:13s}: "+"  ".join(f"{v:5.2f}" for v in m)+f"   {sum(m)/len(m):5.2f}")
    print("\nrank-1 wins by category (A/B/C):")
    for c in sorted(bycat):
        d=bycat[c]; print(f"  {c:10s}: {d['A']}/{d['B']}/{d['C']}")
    print("\n'spoke the council' = mean visible voice-labels per answer:")
    for x in arms:
        v=[t for t in vlab[x]]; print(f"  {x} {ARM_NAME[x]:14s}: {st.mean(v) if v else 0:.2f}")

if __name__=="__main__":
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest="cmd",required=True)
    for name in ("run","score"):
        p=sub.add_parser(name); p.add_argument("--n",type=int,default=0)
        p.add_argument("--workers",type=int,default=3); p.add_argument("--out",default="results.jsonl")
        p.add_argument("--categories",default="")
    a=ap.parse_args(); (cmd_run if a.cmd=="run" else cmd_score)(a)
