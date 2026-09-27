"""What types and values does read_shot_events() actually return?

Evidence for choosing Postgres column types in staging.understat_shots.
Run:  python exploration/inspect_shot_types.py
"""
import os
os.environ["TLS_LIBRARY_PATH"] = os.path.join(os.path.dirname(__file__), "..", "tls-client-darwin-amd64-1.13.1.dylib")

import soccerdata as sd

understat = sd.Understat(leagues="ENG-Premier League", seasons="2024")
shots = understat.read_shot_events().reset_index()  # index holds league/season/game/team/player

print("Shape:", shots.shape)
print(shots.dtypes.to_string())

# xg: probability-like float -> double precision, not numeric
print("\nxg min/max:", shots["xg"].min(), shots["xg"].max(), "| sample:", repr(shots["xg"].iloc[0]))

# date: has a time of day but no time zone attached (Understat sends UTC)
print("date tz:", shots["date"].dt.tz)
print("most common kick-off times:", shots["date"].dt.strftime("%H:%M").value_counts().head(8).to_dict())

# Candidate primary key must be unique and never null
print("\nshot_id unique:", shots["shot_id"].is_unique, "| nulls:", shots["shot_id"].isna().sum())

print("\nColumns with nulls:", shots.isna().sum()[lambda n: n > 0].to_dict())

# minute and pitch location ranges
print("minute min/max:", shots["minute"].min(), shots["minute"].max())
for col in ("location_x", "location_y"):
    print(f"{col} min/max:", shots[col].min(), shots[col].max())
