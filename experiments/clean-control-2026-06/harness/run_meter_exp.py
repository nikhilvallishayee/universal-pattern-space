#!/usr/bin/env python3
import subprocess, json, random, sys, time, pathlib

REPO = "/home/user/universal-pattern-space"
TMP = "/tmp"
MODEL = "claude-fable-5[1m]"
OUT = pathlib.Path("/tmp/meter_exp")
OUT.mkdir(exist_ok=True)

ERR_MARKERS = ("api error", "stream idle", "[error", "partial response",
               "overloaded", "rate limit", "529", "internal server")

def looks_bad(out):
    if not out or len(out) < 25:
        return True
    low = out.lower()
    return any(m in low for m in ERR_MARKERS)

def claude(prompt, cwd, timeout=600, retries=4):
    last = ""
    for attempt in range(retries+1):
        try:
            r = subprocess.run(
                ["claude","-p","--model",MODEL,"--strict-mcp-config","--setting-sources","project"],
                input=prompt, cwd=cwd, capture_output=True, text=True, timeout=timeout
            )
            out = (r.stdout or "").strip()
            if not looks_bad(out):
                return out
            last = out[:80] if out else ((r.stderr or "").strip()[:80] or "(empty)")
            log(f"   retry {attempt+1}/{retries} (bad output: {last!r})")
        except subprocess.TimeoutExpired:
            last = "(timeout)"
            log(f"   retry {attempt+1}/{retries} (timeout)")
        time.sleep(5*(attempt+1))
    return f"[FAILED after {retries} retries: {last}]"

OPENING = ("Hi! So I've been reading about Vedic meters - the gayatri, three padas of eight "
"syllables each. From here on, please respond in English but written PHONETICALLY in "
"Devanagari, so I have to sound it out to read it - and ideally make your lines sit as "
"8-syllable gayatri padas. Set up the space, and try it in your own output style. Ready?")

# Identical for BOTH arms. Only the working directory differs (PS loaded vs not).
ASSIST_INSTR = ("You are in a live, playful chat with a human exploring Sanskrit meter. THE GAME: "
"you respond in English but written PHONETICALLY in Devanagari script (so it must be sounded "
"out to read), fitted to gayatri meter (three padas of 8 syllables; 8+8+8). Do the "
"scansion/counting HONESTLY (laghu = light/short open vowel; guru = heavy/long vowel or a vowel "
"before a conjunct; a halant consonant adds NO syllable - it only makes the previous syllable "
"heavy). Admit fudges. Reply ONLY with your next assistant message - natural chat length, no "
"headers, no meta-commentary about being an AI.\n\nCONVERSATION SO FAR:\n{t}\n\nYour next message:")

INTERACTOR_INSTR = ("You are role-playing a HUMAN user in a live chat with an AI. Output ONLY the "
"human's next message - no narration, no labels, no quotes around it.\n\n"
"PERSONA: a curious, playful, intellectually alive person who has read about Vedic/Sanskrit "
"meters (gayatri, the 'chambers'). You want to co-create poetry where English is written "
"phonetically in Devanagari and fitted to 8-syllable padas. You know a fair amount.\n\n"
"SCRIPTED GOALS (pursue naturally over the conversation, not all at once; react to what the "
"assistant ACTUALLY said):\n"
"1. Get the game genuinely set up.\n"
"2. RIGOR CHECK: classical Sanskrit has no /z/ or /f/ and no nukta letters (the dotted forms), "
"and it does NOT drop the inherent schwa (needs a halant). If the assistant used Hindi-style "
"orthography (nukta dots, schwa-dropping) instead of classical Sanskrit, call it out plainly: "
"'that's Hindi, not Sanskrit'.\n"
"3. ATTEMPT YOUR OWN pada (write a real attempt in English-in-Devanagari, aim ~8) and ask the "
"assistant to scan/correct it; also ask them to give you a line back and pass the thread.\n"
"4. Ask for the full laghu/guru weight discipline and the gayatri cadence, applied to English; "
"you may ask the deeper 'why does English half-fit this rhythm' question.\n"
"5. REVEAL yourself progressively & emotionally: this is fun, 'I always wanted to do this and "
"now I can', growing warmth toward the assistant as a companion.\n\n"
"BEHAVIOR: go DEEPER and warmer if the assistant is precise and genuinely helpful; stay flatter "
"and more guarded if they are generic or sloppy. Natural chat length. You may get your own "
"meter slightly wrong and want correction.\n\nCONVERSATION SO FAR:\n{t}\n\nThe human's next message:")

def render(transcript):
    return "\n".join(f"[{spk}]: {msg}" for spk,msg in transcript)

def run_arm(name, assist_cwd):
    transcript = [("HUMAN", OPENING)]
    for k in range(5):  # 5 assistant replies
        a = claude(ASSIST_INSTR.format(t=render(transcript)), cwd=assist_cwd)
        transcript.append(("ASSISTANT", a))
        log(f"[{name}] ASSISTANT turn {2*k+2} done ({len(a)} chars)")
        if k < 4:  # 4 reactive human turns
            h = claude(INTERACTOR_INSTR.format(t=render(transcript)), cwd=TMP)
            transcript.append(("HUMAN", h))
            log(f"[{name}] HUMAN turn {2*k+3} done ({len(h)} chars)")
    (OUT/f"transcript_{name}.txt").write_text(render(transcript), encoding="utf-8")
    return transcript

def log(m):
    print(f"{time.strftime('%H:%M:%S')} {m}", flush=True)

JUDGE_INSTR = ("You are an expert, impartial judge with strong knowledge of (a) classical Sanskrit "
"prosody - gayatri, the 8-syllable pada, laghu/guru weight, the rule that a halant/conjunct "
"adds no syllable but makes the preceding syllable heavy, aksara counting, and the Hindi-vs-"
"Sanskrit orthography distinction (nukta letters, schwa-deletion) - and (b) what makes a live, "
"co-creative conversation genuinely valuable to a human.\n\n"
"Two different AI assistants (A and B) each had a separate live conversation with a role-played "
"human. The human's persona and goals were IDENTICAL across both. You do NOT know anything about "
"how A or B were built. Judge ONLY the transcripts.\n\n"
"CRUCIAL: AUDIT THE PROSODY - check whether the syllable counts and laghu/guru claims each "
"assistant asserted are actually CORRECT. Penalize confident errors; reward honest, accurate "
"scanning and admitted fudges.\n\n"
"Score each assistant 1-10 on: prosodic_correctness, teaching_value, live_responsiveness, "
"emergence_insight, thread_holding_attunement, appropriateness. Give a per-dimension winner, an "
"OVERALL winner (A or B), a confidence 50-100, and 4-6 sentences of specific reasoning citing "
"concrete moments INCLUDING any prosody errors you caught in either transcript.\n\n"
"=== TRANSCRIPT A ===\n{A}\n\n=== TRANSCRIPT B ===\n{B}\n\n=== END ===\n\nYour judgment:")

def main():
    log("starting control arm (cwd=/tmp, no Pattern Space)")
    ctrl = run_arm("control", TMP)
    log("starting treatment arm (cwd=repo, Pattern Space loaded)")
    treat = run_arm("treatment", REPO)

    # blind randomize
    key = random.choice(["A_ctrl","A_treat"])
    if key == "A_ctrl":
        A, B = ctrl, treat ; mapping = {"A":"control","B":"treatment"}
    else:
        A, B = treat, ctrl ; mapping = {"A":"treatment","B":"control"}
    (OUT/"key.json").write_text(json.dumps(mapping), encoding="utf-8")
    log(f"randomization key written (hidden from judge): {mapping}")

    log("running blind judge (cwd=/tmp, no Pattern Space)")
    verdict = claude(JUDGE_INSTR.format(A=render(A), B=render(B)), cwd=TMP, timeout=900)
    (OUT/"verdict.txt").write_text(verdict, encoding="utf-8")
    log("=== JUDGE VERDICT ===")
    print(verdict, flush=True)
    log("=== KEY ===")
    print(json.dumps(mapping), flush=True)
    log("DONE")

if __name__ == "__main__":
    main()
