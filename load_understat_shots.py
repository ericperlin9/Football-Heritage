"""Load one season of Understat shots into staging.understat_shots.

Most columns come from soccerdata's read_shot_events(). Four are rebuilt from
the raw match JSON soccerdata caches, because soccerdata gets them wrong
(evidence in exploration/): situation, body_part, result keep Understat's raw
codes; assist_player_id becomes a real player id; last_action is added.

The load replaces the whole season in one transaction, so it is safe to
re-run: a failure at any point leaves the previous load untouched.

Run:  python load_understat_shots.py
"""
import os
os.environ["TLS_LIBRARY_PATH"] = os.path.join(os.path.dirname(__file__), "tls-client-darwin-amd64-1.13.1.dylib")

import json
from pathlib import Path

import pandas as pd
import soccerdata as sd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

SEASON = "2024"
RAW_DIR = Path.home() / "soccerdata" / "data" / "Understat"

# Column order of staging.understat_shots (loaded_at is filled by the database)
TABLE_COLUMNS = [
    "shot_id", "league_id", "season_id", "game_id", "date", "team_id", "player_id",
    "assist_player_id", "assist_player", "xg", "location_x", "location_y", "minute",
    "body_part", "situation", "result", "last_action",
]
# soccerdata columns we replace with raw JSON values (last_action is added, not replaced)
REPLACED_COLUMNS = ["assist_player_id", "body_part", "situation", "result"]


def read_raw_shots(game_ids):
    """Build the lookup: one row per shot_id with the columns soccerdata gets wrong."""
    rows = []
    for game_id in game_ids:
        match = json.load(open(RAW_DIR / f"match_{game_id}.json"))

        # This match's lineups: player name -> real player id
        lineup = [row for side in ("h", "a") for row in match["rosters"][side].values()]
        player_ids = {row["player"]: int(row["player_id"]) for row in lineup}
        if len(player_ids) != len(lineup):
            raise ValueError(f"Game {game_id}: two players share a name; assists would be ambiguous")

        for side in ("h", "a"):  # home and away shots are stored separately
            for shot in match["shots"][side]:
                assister = shot["player_assisted"]
                rows.append({
                    "shot_id": int(shot["id"]),  # JSON sends "584630" as text
                    # None = unassisted; an unknown name raises KeyError (fail loudly)
                    "assist_player_id": player_ids[assister] if assister is not None else None,
                    "body_part": shot["shotType"],
                    "situation": shot["situation"],
                    "result": shot["result"],
                    "last_action": shot["lastAction"],
                })

    raw = pd.DataFrame(rows)
    raw["assist_player_id"] = raw["assist_player_id"].astype("Int64")  # integer that allows NULL
    return raw


def build_shots(season):
    """soccerdata's shots with the broken columns replaced by raw values."""
    understat = sd.Understat(leagues="ENG-Premier League", seasons=season)
    shots = understat.read_shot_events().reset_index()  # also caches every match file

    # Only this season's matches, so other seasons' cached files are ignored
    raw = read_raw_shots(shots["game_id"].unique())

    merged = shots.drop(columns=REPLACED_COLUMNS).merge(
        raw,
        on="shot_id",
        how="outer",              # keep unmatched rows from either side so we can count them
        validate="one_to_one",    # error if any shot_id appears twice on either side
        indicator=True,           # adds _merge: "both", "left_only" or "right_only"
    )
    unmatched = (merged["_merge"] != "both").sum()
    if unmatched:
        raise ValueError(f"{unmatched} shots matched on only one side")

    merged["date"] = merged["date"].dt.tz_localize("UTC")  # Understat's times are UTC
    return merged[TABLE_COLUMNS]


def load_shots(shots, season_id):
    """Replace one season in staging.understat_shots: delete, insert, verify, commit."""
    if shots.empty:
        raise ValueError("Built 0 shots; refusing to replace the season with nothing")
    if set(shots["season_id"]) != {season_id}:
        raise ValueError(f"Built shots are not all season {season_id}")

    load_dotenv()
    engine = create_engine(os.environ["DATABASE_URL"])

    # engine.begin() = BEGIN now; COMMIT when the block ends normally;
    # ROLLBACK if anything inside raises (including a dropped connection).
    with engine.begin() as conn:
        deleted = conn.execute(
            text("DELETE FROM staging.understat_shots WHERE season_id = :season_id"),
            {"season_id": season_id},  # passed separately, never pasted into the SQL string
        ).rowcount

        shots.to_sql(
            "understat_shots", conn, schema="staging",
            if_exists="append",  # the table already exists; never let pandas recreate it
            index=False,         # don't write pandas' row numbers as a column
            method="multi",      # many rows per INSERT statement: far fewer round trips
            chunksize=1000,
        )

        loaded = conn.execute(
            text("SELECT count(*) FROM staging.understat_shots WHERE season_id = :season_id"),
            {"season_id": season_id},
        ).scalar_one()
        if loaded != len(shots):  # raising here triggers the ROLLBACK
            raise ValueError(f"Table has {loaded} rows for season {season_id}, built {len(shots)}")

    return deleted, loaded


if __name__ == "__main__":
    shots = build_shots(SEASON)
    print(f"Built {len(shots)} shots for season {SEASON}, all matched to raw JSON")

    deleted, loaded = load_shots(shots, int(SEASON))
    print(f"Committed: replaced {deleted} old rows with {loaded} new rows")
