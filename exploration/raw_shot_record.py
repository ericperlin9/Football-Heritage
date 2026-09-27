"""Print one shot exactly as Understat sent it (the JSON soccerdata caches).

Shows every raw field name, including ones soccerdata drops (lastAction).
Run:  python exploration/raw_shot_record.py   (after read_shot_events() has cached the season)
"""
import glob
import json
from pathlib import Path

RAW_DIR = Path.home() / "soccerdata" / "data" / "Understat"

first_match = sorted(glob.glob(str(RAW_DIR / "match_*.json")))[0]
match = json.load(open(first_match))
print("Top-level keys:", list(match))

# Note every value arrives as a string, even numbers: "minute": "19"
print(json.dumps(match["shots"]["h"][0], indent=1))
