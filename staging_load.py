"""Shared by every staging loader: replace one season of a table, all or nothing."""
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Table names can't be passed as query parameters, so they go into the SQL
# string; allow only known tables so nothing unexpected is ever pasted in.
STAGING_TABLES = {"understat_shots", "understat_schedule"}


def replace_season(frame, table, season_id):
    """Replace one season in staging.<table>: delete, insert, verify, commit.

    Returns (rows deleted, rows loaded). Any failure rolls the whole thing
    back, leaving the previous load untouched.
    """
    if table not in STAGING_TABLES:
        raise ValueError(f"Unknown staging table: {table}")
    if frame.empty:
        raise ValueError("Built 0 rows; refusing to replace the season with nothing")
    if set(frame["season_id"]) != {season_id}:
        raise ValueError(f"Built rows are not all season {season_id}")

    load_dotenv()
    engine = create_engine(os.environ["DATABASE_URL"])

    # engine.begin() = BEGIN now; COMMIT when the block ends normally;
    # ROLLBACK if anything inside raises (including a dropped connection).
    with engine.begin() as conn:
        deleted = conn.execute(
            text(f"DELETE FROM staging.{table} WHERE season_id = :season_id"),
            {"season_id": season_id},  # passed separately, never pasted into the SQL string
        ).rowcount

        frame.to_sql(
            table, conn, schema="staging",
            if_exists="append",  # the table already exists; never let pandas recreate it
            index=False,         # don't write pandas' row numbers as a column
            method="multi",      # many rows per INSERT statement: far fewer round trips
            chunksize=1000,
        )

        loaded = conn.execute(
            text(f"SELECT count(*) FROM staging.{table} WHERE season_id = :season_id"),
            {"season_id": season_id},
        ).scalar_one()
        if loaded != len(frame):  # raising here triggers the ROLLBACK
            raise ValueError(f"staging.{table} has {loaded} rows for season {season_id}, built {len(frame)}")

    return deleted, loaded
