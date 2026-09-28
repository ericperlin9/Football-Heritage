"""What does read_schedule() return, and does it match the raw league JSON?

Evidence for designing staging.understat_schedule. Unlike shots, soccerdata's
schedule code has no label mapping, but it does rename teams and derive
has_data, so compare against the raw file anyway.
Run:  python exploration/inspect_schedule.py
"""
import os
os.environ["TLS_LIBRARY_PATH"] = os.path.join(os.path.dirname(__file__), "..", "tls-client-darwin-amd64-1.13.1.dylib")

import json
from pathlib import Path

import soccerdata as sd

RAW_FILE = Path.home() / "soccerdata" / "data" / "Understat" / "league_1_season_2024.json"

understat = sd.Understat(leagues="ENG-Premier League", seasons="2024")
schedule = understat.read_schedule().reset_index()

print("Shape:", schedule.shape)
print(schedule.dtypes.to_string())
print("\ngame_id unique:", schedule["game_id"].is_unique, "| nulls per column:",
      schedule.isna().sum()[lambda n: n > 0].to_dict())
print("is_result:", schedule["is_result"].value_counts().to_dict(),
      "| has_data:", schedule["has_data"].value_counts().to_dict())
print("Matches per team (home + away):",
      sorted(set((schedule["home_team_id"].value_counts() + schedule["away_team_id"].value_counts()).tolist())))

# Raw: one record per match, with every field Understat sends
raw = json.load(open(RAW_FILE))
print("\nRaw top-level keys:", list(raw))
matches = raw["dates"]  # soccerdata calls it datesData in code; the cached file says dates
print("Raw matches:", len(matches))
print(json.dumps(matches[0], indent=1))

# Did the team renaming change anything? Compare raw titles with soccerdata's names
raw_names = {m["h"]["title"] for m in matches} | {m["a"]["title"] for m in matches}
sd_names = set(schedule["home_team"]) | set(schedule["away_team"])
print("\nRenamed by soccerdata (raw only):", sorted(raw_names - sd_names))
print("Renamed to (soccerdata only):", sorted(sd_names - raw_names))

# Do the raw goals/xG agree with soccerdata's?
by_id = {int(m["id"]): m for m in matches}
mismatches = sum(
    int(by_id[row.game_id]["goals"]["h"]) != row.home_goals
    or abs(float(by_id[row.game_id]["xG"]["h"]) - row.home_xg) > 1e-9
    for row in schedule.itertuples()
)
print("Rows where home goals/xG differ from raw:", mismatches)
