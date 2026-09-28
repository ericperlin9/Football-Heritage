"""What does Understat send for matches that haven't been played yet?

Season 2024 is complete, so it can't answer this. Uses the current season,
which has future fixtures. Decides whether goals/xG/forecast allow NULL.
Run:  python exploration/future_matches.py
"""
import os
os.environ["TLS_LIBRARY_PATH"] = os.path.join(os.path.dirname(__file__), "..", "tls-client-darwin-amd64-1.13.1.dylib")

import json
from pathlib import Path

import soccerdata as sd

SEASON = "2026"  # 2026/27, in progress
RAW_FILE = Path.home() / "soccerdata" / "data" / "Understat" / f"league_1_season_{SEASON}.json"

schedule = sd.Understat(leagues="ENG-Premier League", seasons=SEASON).read_schedule().reset_index()
print("is_result:", schedule["is_result"].value_counts().to_dict(),
      "| has_data:", schedule["has_data"].value_counts().to_dict())

future = schedule[~schedule["is_result"]]
print("\nsoccerdata, first unplayed match:")
print(future.iloc[0][["game_id", "date", "home_team", "away_team", "home_goals", "home_xg", "has_data"]].to_string())

matches = json.load(open(RAW_FILE))["dates"]
raw_future = [m for m in matches if not m["isResult"]]
print("\nRaw, first unplayed match:")
print(json.dumps(raw_future[0], indent=1))
print("Unplayed matches with a forecast:", sum("forecast" in m for m in raw_future), "of", len(raw_future))
print("Played matches with a forecast:", sum("forecast" in m for m in matches if m["isResult"]),
      "of", sum(m["isResult"] for m in matches))
