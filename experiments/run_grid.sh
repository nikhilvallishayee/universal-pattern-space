#!/bin/bash
# v2.2 grid driver — hands-off, rate-limit-tolerant (rounds + scrub-on-resume).
# Main grid: vanilla vs PS-edition, full model×edition matrix (fair value rubric, neutral control).
# Concise test: PS-normal vs PS-normal+concise (does PS value survive without the verbosity tax?).
cd /home/user/universal-pattern-space/experiments || exit 1
export INTERACTOR_MODEL=claude-sonnet-4-6 JUDGE_MODEL=claude-opus-4-8 TURNS=5
H=claude-haiku-4-5-20251001; S=claude-sonnet-4-6; O=claude-opus-4-8
# model | arm_a(control) | arm_b(treatment) | out | workers
CELLS=(
"$H|vanilla|micro|int_haiku_micro.jsonl|2"
"$H|vanilla|mini|int_haiku_mini.jsonl|2"
"$H|vanilla|normal|int_haiku_normal.jsonl|2"
"$S|vanilla|mini|int_sonnet_mini.jsonl|2"
"$S|vanilla|normal|int_sonnet_normal.jsonl|2"
"$O|vanilla|micro|int_opus_micro.jsonl|2"
"$O|vanilla|mini|int_opus_mini.jsonl|2"
"$O|vanilla|normal|int_opus_normal.jsonl|2"
"$O|normal|normal+concise|conc_opus.jsonl|2"
"$S|normal|normal+concise|conc_sonnet.jsonl|2"
)
clean_count(){ python3 -c "import json;from run_interaction import _is_good;print(sum(_is_good(json.loads(l)) for l in open('$1')))" 2>/dev/null || echo 0; }
python3 run_interaction.py setup
for round in $(seq 1 14); do
  echo "=== ROUND $round ($(date +%H:%M:%S)) ==="
  pids=()
  for c in "${CELLS[@]}"; do
    IFS='|' read -r m a b out w <<< "$c"
    n=$(clean_count "$out")
    if [ "${n:-0}" -ge 43 ]; then echo "  $out complete ($n)"; continue; fi
    echo "  launching $out (have $n)"
    python3 run_interaction.py run --model "$m" --arm-a "$a" --arm-b "$b" --workers "$w" --out "$out" > "/tmp/grid_${out%.jsonl}.log" 2>&1 &
    pids+=($!)
  done
  [ ${#pids[@]} -eq 0 ] && { echo "ALL CELLS COMPLETE"; break; }
  wait "${pids[@]}"
done
echo "=== GRID FINISHED ($(date +%H:%M:%S)) ==="
for c in "${CELLS[@]}"; do IFS='|' read -r m a b out w <<< "$c"; echo "$out: $(clean_count "$out")/43"; done
