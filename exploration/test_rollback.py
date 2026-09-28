"""Does a failed load leave the previous load untouched?

Builds the real shots, corrupts one situation code so the CHECK constraint
rejects it mid-transaction, and confirms the table still holds the earlier
load (same row count, same loaded_at).
Run:  python exploration/test_rollback.py   (after one successful load)
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))  # so we can import the loader

from sqlalchemy import create_engine, text

from load_understat_shots import SEASON, build_shots
from staging_load import replace_season

STATE_SQL = text(
    "SELECT count(*), min(loaded_at) FROM staging.understat_shots WHERE season_id = :season_id"
)


def table_state():
    engine = create_engine(os.environ["DATABASE_URL"])
    with engine.connect() as conn:
        return tuple(conn.execute(STATE_SQL, {"season_id": int(SEASON)}).one())


shots = build_shots(SEASON)
shots.loc[shots.index[-1], "situation"] = "NotARealCode"  # last row, so the DELETE and most inserts run first

try:
    replace_season(shots, "understat_shots", int(SEASON))  # also runs load_dotenv(), so table_state() can connect
    print("UNEXPECTED: the bad load committed")
except Exception as error:
    # pandas wraps SQLAlchemy's error, which wraps psycopg2's; the innermost has Postgres' details
    db_error = getattr(error.__cause__, "orig", error)
    constraint = getattr(getattr(db_error, "diag", None), "constraint_name", None)
    print("Load failed as intended:", type(db_error).__name__, "on constraint", constraint)

before = table_state()
print(f"Table after the failed load: {before[0]} rows, loaded_at {before[1]}")
