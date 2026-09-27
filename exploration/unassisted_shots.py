"""Why is assist_player_id null for ~2,500 shots? Should the column allow NULL?

Hypothesis: NULL means no pass led directly to the shot, so it should be
common for penalties, direct free kicks, rebounds and dribbles.
Run:  python exploration/unassisted_shots.py
"""
import glob
import json
from collections import Counter
from pathlib import Path

RAW_DIR = Path.home() / "soccerdata" / "data" / "Understat"

total, unassisted = Counter(), Counter()
by_last_action, goals = Counter(), Counter()
for path in glob.glob(str(RAW_DIR / "match_*.json")):
    match = json.load(open(path))
    for side in ("h", "a"):
        for shot in match["shots"][side]:
            no_assist = shot["player_assisted"] is None
            total[shot["situation"]] += 1
            goals[(shot["result"] == "Goal", no_assist)] += 1
            if no_assist:
                unassisted[shot["situation"]] += 1
                by_last_action[shot["lastAction"]] += 1

print("Unassisted shots:", sum(unassisted.values()), "of", sum(total.values()))
for situation in total:
    print(f"  {situation:15} {unassisted[situation]:5} / {total[situation]:5} unassisted")
print("\nLast action before an unassisted shot:", dict(by_last_action.most_common(8)))
print("Goals scored unassisted:", goals[(True, True)], "of", goals[(True, True)] + goals[(True, False)])
