"""Load one season of Understat player totals into staging.understat_player_season.

soccerdata's read_player_season_stats() is used for the stat columns, but its
single team/team_id is replaced: for players who played for two clubs it keeps
the alphabetically first one (see exploration/inspect_player_stats.py). Instead
we keep Understat's raw club list (team_title) and all matching team_ids.

The load replaces the whole season in one transaction, so it is safe to
re-run: a failure at any point leaves the previous load untouched.

Run:  python load_understat_player_season.py
"""
import os
os.environ["TLS_LIBRARY_PATH"] = os.path.join(os.path.dirname(__file__), "tls-client-darwin-amd64-1.13.1.dylib")

import json
from pathlib import Path

import pandas as pd
import soccerdata as sd

from staging_load import replace_season

SEASON = "2024"
RAW_DIR = Path.home() / "soccerdata" / "data" / "Understat"

# Column order of staging.understat_player_season (loaded_at is filled by the database)
TABLE_COLUMNS = [
    "season_id", "player_id", "league_id", "player", "team_title", "team_ids", "position",
    "matches", "minutes", "goals", "np_goals", "assists", "shots", "key_passes",
    "yellow_cards", "red_cards", "xg", "np_xg", "xa", "xg_chain", "xg_buildup",
]


def read_raw_teams(league_id, season_id):
    """Lookup: one row per player with the raw club list and its team ids."""
    raw = json.load(open(RAW_DIR / f"league_{league_id}_season_{season_id}.json"))
    team_ids = {team["title"]: int(team["id"]) for team in raw["teams"].values()}

    rows = [
        {
            "player_id": int(player["id"]),  # JSON sends ids as text
            "team_title": player["team_title"],
            # "Brighton,Ipswich" -> [220, 9]; an unknown name raises KeyError (fail loudly)
            "team_ids": [team_ids[name] for name in player["team_title"].split(",")],
        }
        for player in raw["players"]
    ]
    return pd.DataFrame(rows)


def build_player_season(season):
    """soccerdata's player totals with the raw club list instead of one club."""
    understat = sd.Understat(leagues="ENG-Premier League", seasons=season)
    stats = understat.read_player_season_stats().reset_index()  # also caches the raw league file

    teams = read_raw_teams(stats["league_id"].iloc[0], season)
    merged = stats.drop(columns=["team", "team_id"]).merge(
        teams,
        on="player_id",
        how="outer",              # every player must be on both sides
        validate="one_to_one",
        indicator=True,
    )
    unmatched = (merged["_merge"] != "both").sum()
    if unmatched:
        raise ValueError(f"{unmatched} players matched on only one side")

    return merged[TABLE_COLUMNS]


if __name__ == "__main__":
    players = build_player_season(SEASON)
    multi_club = (players["team_ids"].str.len() > 1).sum()
    print(f"Built {len(players)} players for season {SEASON} ({multi_club} with more than one club)")

    deleted, loaded = replace_season(players, "understat_player_season", int(SEASON))
    print(f"Committed: replaced {deleted} old rows with {loaded} new rows")
