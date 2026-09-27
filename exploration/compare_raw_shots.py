import os
os.environ["TLS_LIBRARY_PATH"] = os.path.join(os.path.dirname(__file__), "..", "tls-client-darwin-amd64-1.13.1.dylib")

import glob
import json
from collections import Counter
from pathlib import Path

import soccerdata as sd

# soccerdata downloads Understat's raw JSON and caches one file per match here,
# then reshapes it into a DataFrame. This script compares the two views.
RAW_DIR = Path.home() / "soccerdata" / "data" / "Understat"

understat = sd.Understat(leagues="ENG-Premier League", seasons="2024")
shots = understat.read_shot_events()  # also ensures every match file is cached

raw = Counter()
for path in glob.glob(str(RAW_DIR / "match_*.json")):
    match = json.load(open(path))
    for side in ("h", "a"):  # home and away shots are stored separately
        for shot in match["shots"][side]:
            raw[("situation", shot["situation"])] += 1
            raw[("body_part", shot["shotType"])] += 1
            raw[("last_action", shot["lastAction"])] += 1

for column in ("situation", "body_part"):
    print(f"\n{column} — soccerdata:", shots[column].value_counts(dropna=False).to_dict())
    print(f"{column} — raw:       ", {k[1]: n for k, n in raw.items() if k[0] == column})

print("\nlast_action — raw only (soccerdata drops it):",
      {k[1]: n for k, n in raw.most_common() if k[0] == "last_action"})
