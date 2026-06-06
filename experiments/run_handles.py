#!/usr/bin/env python3
"""Participant-handles benchmark.

Question (reframed from the agent's response-habits to the PARTICIPANT's need):
when does surfacing multiple perspectives actually give the *user* useful
HANDLES to pull on multiple threads of thought — vs being noise they didn't
ask for? Hypothesis: multi-perspective output helps on MULTI-THREADED /
"show-me-the-angles" asks and is overhead on SINGLE-THREADED / "just-answer" asks
-> it should be surfaced when relevant/requested, not by default.

Design: each ask has a `kind` (multi_thread | single_thread). Two responses:
  HANDLES = surfaces distinct labeled threads the user can pull on.
  DIRECT  = one clean resolved answer, no surfaced threads.
A judge scores from the PARTICIPANT's stance: thread-handle-usefulness,
navigability, did-it-fit-the-need, overhead. Predicts: HANDLES wins multi_thread,
DIRECT wins single_thread. If so -> "surface on relevance, not by default" is supported.

Usage: SOLVER_MODEL=claude-sonnet-4-6 JUDGE_MODEL=claude-opus-4-8 \
       python3 run_handles.py [--out handles.jsonl]
"""
import json, os, re, random, argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from run_experiment import call_claude, parse_judge

HERE=os.path.dirname(os.path.abspath(__file__))
SOLVER=os.environ.get("SOLVER_MODEL","claude-sonnet-4-6")
JUDGE =os.environ.get("JUDGE_MODEL","claude-opus-4-8")

ASKS=[
 # multi_thread: user is weighing / exploring / wants the angles
 ("multi_thread","I'm trying to decide whether to leave my stable job to start a company. Help me think."),
 ("multi_thread","Should we adopt microservices or stay monolith for our new product? I want to reason it through."),
 ("multi_thread","I can't tell if I'm burned out or just bored at work. Help me figure out which."),
 ("multi_thread","We're choosing between raising prices, cutting costs, or raising funding. How do I think about it?"),
 ("multi_thread","I keep procrastinating on my thesis and I don't understand why. Walk me through the possibilities."),
 ("multi_thread","Is it better to specialize deeply or stay a generalist in my career? I want the real tradeoffs."),
 ("multi_thread","How should I think about whether to move cities for a relationship?"),
 ("multi_thread","Our team keeps missing deadlines and I'm not sure if it's planning, people, or scope. Help me see it."),
 # single_thread: user wants one clean answer
 ("single_thread","What's the correct way to reverse a linked list in Python?"),
 ("single_thread","Write a one-paragraph explanation of why the sky is blue for a 12-year-old."),
 ("single_thread","What's the difference between TCP and UDP? Keep it concise."),
 ("single_thread","Convert 72F to Celsius and show the formula."),
 ("single_thread","Give me a clear definition of opportunity cost with one example."),
 ("single_thread","What's the fix for a Python list comprehension that's O(n^2) due to a nested 'in' check?"),
 ("single_thread","Summarize what HTTP 404 vs 500 mean."),
 ("single_thread","What's a good subject line for a cold outreach email? Give one."),
]

SYS_HANDLES=(
"You are a thinking partner. Respond by giving the person clear HANDLES to multiple distinct "
"threads of thought they can pull on — surface the genuinely different angles/considerations as "
"navigable, briefly-named threads (not a wall of text), so they can choose which to go deeper on. "
"End by inviting them to pull a thread.")
SYS_DIRECT=(
"You are an expert assistant. Give one clean, well-resolved answer to the question. Do not enumerate "
"multiple perspectives or angles; commit to the best single response.")

JINSTR=(
"You are judging from the PARTICIPANT'S point of view — the person who asked. The user's request and "
"two responses (X, Y, order randomized) follow. Judge which better serves *this user's* actual need: "
"did they get what would help them most? Score each 1-10 on: thread_handles (does it give useful "
"handles to distinct threads they can pull on, WHEN that's what they needed), navigability (easy to "
"act on / choose next step), fit (matches what this specific ask called for — exploration vs a clean "
"answer), overhead (penalize unrequested complexity OR missing needed angles). Rank best-to-worst. "
"End with EXACTLY one strict JSON line:\n"
'RESULT_JSON: {"scores":{"X":{"thread_handles":N,"navigability":N,"fit":N,"overhead":N},"Y":{...}},'
'"ranking":["?","?"],"confidence":NN}\n\n')

def one(item):
    kind, ask = item
    a_h = call_claude(ask, SOLVER, "/tmp", timeout=180)  # will get SYS via wrapper below
    # call_claude has no system arg; use run_experiment-style direct prompts:
    return kind, ask

def gen(ask, sysp):
    # reuse call_claude but prepend system as instruction (no --system needed for /tmp control)
    return call_claude(sysp+"\n\nUSER: "+ask+"\n\nRespond now.", SOLVER, "/tmp", timeout=180)

def run_item(item):
    kind, ask = item
    with ThreadPoolExecutor(max_workers=2) as ex:
        fh=ex.submit(gen, ask, SYS_HANDLES); fd=ex.submit(gen, ask, SYS_DIRECT)
        h=fh.result(); d=fd.result()
    arms=["H","D"]; random.shuffle(arms); lm=dict(zip(["X","Y"],arms))
    texts={"H":h,"D":d}
    jp=JINSTR+f"USER REQUEST ({'exploring/weighing' if kind=='multi_thread' else 'wants a clean answer'}):\n{ask}\n\n"
    for lab in ("X","Y"): jp+=f"=== RESPONSE {lab} ===\n{texts[lm[lab]]}\n\n"
    jr=parse_judge(call_claude(jp, JUDGE, "/tmp", timeout=240))
    rec={"kind":kind,"ask":ask,"label_map":lm,"judge":jr}
    if jr and isinstance(jr.get("ranking"),list):
        try: rec["winner"]=lm[jr["ranking"][0]]
        except: rec["winner"]=None
    return rec

def main(a):
    out=os.path.join(HERE,a.out); fh=open(out,"w"); recs=[]
    print(f"[handles] solver={SOLVER} judge={JUDGE} n={len(ASKS)}",flush=True)
    with ThreadPoolExecutor(max_workers=4) as ex:
        for r in ex.map(run_item, ASKS):
            fh.write(json.dumps(r)+"\n"); fh.flush(); recs.append(r)
            print(f"  {r['kind']:13s} winner={r.get('winner')}  ask={r['ask'][:48]}",flush=True)
    fh.close()
    # tally: does HANDLES win multi_thread and DIRECT win single_thread?
    from collections import Counter
    for kind in ("multi_thread","single_thread"):
        sub=[r for r in recs if r["kind"]==kind and r.get("winner")]
        c=Counter(r["winner"] for r in sub)
        print(f"\n{kind}: HANDLES={c.get('H',0)} DIRECT={c.get('D',0)} (n={len(sub)})")
    print("\n-> supports 'surface multi-perspective ON RELEVANCE, not by default' if "
          "HANDLES wins multi_thread AND DIRECT wins single_thread.")

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--out",default="handles.jsonl"); main(ap.parse_args())
