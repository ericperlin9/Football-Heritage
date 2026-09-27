"""Is soccerdata's assist_player_id really a player id?

Suspicion: its range (666,171-730,277) doesn't overlap player_id (65-13,582).
Understat only sends the assister's *name* ("player_assisted"), so soccerdata
looks the name up in the match roster -- but reads the roster row's "id"
(one lineup slot in one match) instead of its "player_id" (the person).
Run:  python exploration/assist_player_ids.py
"""
import glob
import json
from collections import Counter
from pathlib import Path

RAW_DIR = Path.home() / "soccerdata" / "data" / "Understat"

outcome = Counter()
for path in glob.glob(str(RAW_DIR / "match_*.json")):
    match = json.load(open(path))
    rosters = [row for side in ("h", "a") for row in match["rosters"][side].values()]
    name_counts = Counter(row["player"] for row in rosters)
    roster_by_name = {row["player"]: row for row in rosters}
    for side in ("h", "a"):
        for shot in match["shots"][side]:
            name = shot["player_assisted"]
            if name is None:
                outcome["unassisted"] += 1
            elif name not in roster_by_name:
                outcome["name not in roster"] += 1
            elif name_counts[name] > 1:
                outcome["ambiguous name (two players, same name)"] += 1
            else:
                row = roster_by_name[name]
                outcome["resolved"] += 1
                outcome["roster id == player_id"] += row["id"] == row["player_id"]

print(dict(outcome))
example = next(iter(match["rosters"]["h"].values()))
print("Example roster row -> id:", example["id"], "| player_id:", example["player_id"], "|", example["player"])
