"""What does read_player_season_stats() return, and does it match the raw JSON?

Evidence for designing staging.understat_player_season. Suspect: for players
who played for two clubs in one season, Understat's team_title is "A,B" and
soccerdata keeps only the first team, crediting whole-season stats to it.
Run:  python exploration/inspect_player_stats.py
"""
import os
os.environ["TLS_LIBRARY_PATH"] = os.path.join(os.path.dirname(__file__), "..", "tls-client-darwin-amd64-1.13.1.dylib")

import json
from collections import Counter
from pathlib import Path

import soccerdata as sd

RAW_FILE = Path.home() / "soccerdata" / "data" / "Understat" / "league_1_season_2024.json"

stats = sd.Understat(leagues="ENG-Premier League", seasons="2024").read_player_season_stats().reset_index()
print("Shape:", stats.shape)
print(stats.dtypes.to_string())
print("\nplayer_id unique:", stats["player_id"].is_unique,
      "| nulls:", stats.isna().sum()[lambda n: n > 0].to_dict())
print("position values:", stats["position"].value_counts().head(12).to_dict())

raw = json.load(open(RAW_FILE))["players"]  # soccerdata calls it playersData in code
print("\nRaw players:", len(raw), "| raw fields:", list(raw[0]))

multi = [p for p in raw if "," in p["team_title"]]
print(f"\nPlayers listed with more than one club: {len(multi)}")
for p in multi[:8]:
    print(f"  {p['player_name']:28} team_title={p['team_title']!r:45} games={p['games']} goals={p['goals']} xG={float(p['xG']):.2f}")
print("Their share of all season minutes:",
      round(sum(int(p["time"]) for p in multi) / sum(int(p["time"]) for p in raw), 3))

# Which club does soccerdata credit them to? Check against the shots table's team_id
shots = sd.Understat(leagues="ENG-Premier League", seasons="2024").read_shot_events().reset_index()
shot_teams = shots.groupby("player_id")["team"].agg(lambda t: dict(Counter(t)))
sd_team = stats.set_index("player_id")["team"]
print("\nShots by club for multi-club players vs soccerdata's single team:")
for p in multi[:8]:
    pid = int(p["id"])
    print(f"  {p['player_name']:28} soccerdata team={sd_team.get(pid)!s:25} shots by club={shot_teams.get(pid, {})}")
