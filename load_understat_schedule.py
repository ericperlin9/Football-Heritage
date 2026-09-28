"""Load one season of Understat fixtures/results into staging.understat_schedule.

soccerdata's read_schedule() matches the raw JSON exactly (see
exploration/inspect_schedule.py), so it's used as-is, minus its derived
url/has_data columns. The only raw-JSON step is adding Understat's post-match
forecast, which soccerdata drops.

The load replaces the whole season in one transaction, so it is safe to
re-run: a failure at any point leaves the previous load untouched.

Run:  python load_understat_schedule.py
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

# Column order of staging.understat_schedule (loaded_at is filled by the database)
TABLE_COLUMNS = [
    "game_id", "league_id", "season_id", "date",
    "home_team_id", "away_team_id", "home_team", "away_team", "home_team_code", "away_team_code",
    "home_goals", "away_goals", "home_xg", "away_xg", "is_result",
    "forecast_home_win", "forecast_draw", "forecast_away_win",
]


def read_raw_forecasts(league_id, season_id):
    """Lookup: one row per played match with Understat's forecast (home side's view)."""
    raw_file = RAW_DIR / f"league_{league_id}_season_{season_id}.json"
    matches = json.load(open(raw_file))["dates"]
    rows = [
        {
            "game_id": int(match["id"]),  # JSON sends ids as text
            "forecast_home_win": float(match["forecast"]["w"]),
            "forecast_draw": float(match["forecast"]["d"]),
            "forecast_away_win": float(match["forecast"]["l"]),  # a home loss is an away win
        }
        for match in matches
        if "forecast" in match  # unplayed matches have no forecast
    ]
    return pd.DataFrame(rows, columns=["game_id", "forecast_home_win", "forecast_draw", "forecast_away_win"])


def build_schedule(season):
    """soccerdata's schedule plus Understat's forecast."""
    understat = sd.Understat(leagues="ENG-Premier League", seasons=season)
    schedule = understat.read_schedule().reset_index()  # also caches the raw league file

    league_id = schedule["league_id"].iloc[0]
    forecasts = read_raw_forecasts(league_id, season)

    merged = schedule.merge(
        forecasts,
        on="game_id",
        how="left",               # keep unplayed matches; their forecast stays NULL
        validate="one_to_one",
        indicator=True,
    )
    if (merged["_merge"] == "both").sum() != len(forecasts):
        raise ValueError("Some raw forecasts didn't match a scheduled game_id")
    # Every played match must have a forecast, and no unplayed one should
    has_forecast = merged["_merge"] == "both"
    if (has_forecast != merged["is_result"]).any():
        raise ValueError("Forecast presence doesn't line up with is_result")

    merged["date"] = merged["date"].dt.tz_localize("UTC")  # Understat's times are UTC
    return merged[TABLE_COLUMNS]


if __name__ == "__main__":
    schedule = build_schedule(SEASON)
    played = int(schedule["is_result"].sum())
    print(f"Built {len(schedule)} matches for season {SEASON} ({played} played, all with forecasts)")

    deleted, loaded = replace_season(schedule, "understat_schedule", int(SEASON))
    print(f"Committed: replaced {deleted} old rows with {loaded} new rows")
