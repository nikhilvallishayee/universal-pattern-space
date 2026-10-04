#!/bin/bash
# Hands-off driver: generate (resumable rounds) -> judge (3 judges) -> effort pairs -> analyze.
cd "$(dirname "$0")"
for round in 1 2 3 4 5 6; do
  echo "=== generate round $round $(date -u +%H:%M:%S)"
  python3 run_ladder.py generate --workers ${WORKERS:-20}
  left=$(python3 -c "
import json
done=set()
for l in open('answers.jsonl'):
    r=json.loads(l)
    if 'text' in r: done.add((r['arm'],r['effort'],r['qid']))
print(480-len(done))")
  echo "remaining=$left"; [ "$left" = "0" ] && break; sleep 120
done
echo "GENERATION_DONE $(date -u +%H:%M:%S)"
for round in 1 2 3; do echo "=== judge round $round"; python3 run_ladder.py judge --workers 8; done
echo "JUDGING_DONE $(date -u +%H:%M:%S)"
for round in 1 2; do echo "=== effort pairs round $round"; python3 run_ladder.py judge-effort --workers 12; done
echo "PAIRS_DONE $(date -u +%H:%M:%S)"
python3 analyze.py > analysis_stdout.txt 2>&1
echo "ALL_DONE $(date -u +%H:%M:%S)"
