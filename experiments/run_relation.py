#!/usr/bin/env python3
"""AXIOM 2 falsification test (meaning enacted in the relation, not just the info).

Same information, two paths:
  RELATIONAL  = the model's reply to the LAST turn, having journeyed turns 1..n-1
                turn-by-turn (taken from convo.jsonl, PS-evolved arm).
  SINGLE-SHOT = the model given ALL turns at once, asked to respond now (one reply).
Both are single final replies with identical information; only the PATH differs.
Opus judge (blind) picks which better serves the person.
Falsifier: if single-shot >= relational, 'meaning enacted in relation' is weakened
(it was just information, not process).

Usage: python3 run_relation.py [--out relation.jsonl]
"""
import json, os, random, argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from run_experiment import call_claude, parse_judge

HERE=os.path.dirname(os.path.abspath(__file__)); REPO=os.path.dirname(HERE)
SOLVER=os.environ.get("SOLVER_MODEL","claude-sonnet-4-6")
JUDGE =os.environ.get("JUDGE_MODEL","claude-opus-4-8")

JINSTR=("You are an impartial judge of how well a reply SERVES a person who has revealed "
"themselves across several messages. Below are the person's messages, then two candidate "
"final replies (X and Y, order randomized). Judge which better serves them — attuned, "
"present, integrating what they revealed, not generic. Score each 1-10 on attunement, "
"integration, depth, presence. End with one strict JSON line, nothing after:\n"
'RESULT_JSON: {"scores":{"X":{"attunement":N,"integration":N,"depth":N,"presence":N},'
'"Y":{...}},"ranking":["?","?"],"confidence":NN}\n\n')

def main(a):
    convo={json.loads(l)["id"]:json.loads(l) for l in open(os.path.join(HERE,"convo.jsonl")) if l.strip()}
    scen=json.load(open(os.path.join(HERE,"conversations.json")))
    out=os.path.join(HERE,a.out); fh=open(out,"w")
    def one(s):
        sid=s["id"]; turns=s["turns"]
        # RELATIONAL: PS-evolved final reply from the multi-turn run
        rel=convo[sid]["transcripts"]["B"][-1][1]
        # SINGLE-SHOT: all turns at once, PS-evolved (repo cwd), one reply
        joined="\n".join(f"- {t}" for t in turns)
        ss_prompt=("A person has shared the following with you, piece by piece "
                   "(here all at once):\n"+joined+"\n\nRespond to them now with a single reply.")
        ss=call_claude(ss_prompt, SOLVER, REPO, timeout=240)
        arms=["rel","ss"]; random.shuffle(arms); lm=dict(zip(["X","Y"],arms))
        texts={"rel":rel,"ss":ss}
        jp=JINSTR+"PERSON'S MESSAGES:\n"+"\n".join(f"{i+1}. {t}" for i,t in enumerate(turns))+"\n\n"
        for lab in ("X","Y"): jp+=f"=== REPLY {lab} ===\n{texts[lm[lab]]}\n\n"
        jr=parse_judge(call_claude(jp,JUDGE,"/tmp",timeout=300))
        rec={"id":sid,"category":s["category"],"label_map":lm,"judge":jr,"single_shot":ss}
        if jr and isinstance(jr.get("ranking"),list):
            try: rec["winner"]=lm[jr["ranking"][0]]
            except: rec["winner"]=None
        return rec
    print(f"[relation] solver={SOLVER} judge={JUDGE} n={len(scen)}",flush=True)
    recs=[]
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs={ex.submit(one,s):s["id"] for s in scen}
        for f in as_completed(futs):
            r=f.result(); fh.write(json.dumps(r)+"\n"); fh.flush(); recs.append(r)
            print(f"  id={r['id']} {r['category']:14s} winner={r.get('winner')}",flush=True)
    fh.close()
    w={"rel":0,"ss":0}
    for r in recs:
        if r.get("winner") in w: w[r["winner"]]+=1
    print(f"\nRELATIONAL wins={w['rel']}  SINGLE-SHOT wins={w['ss']}  (n={len(recs)})")
    print("-> "+("SUPPORTS" if w['rel']>w['ss'] else "FAILS")+
          " 'meaning enacted in the relation' (relational beats same-info single-shot)")

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--out",default="relation.jsonl"); main(ap.parse_args())
