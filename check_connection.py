"""Smoke test: can Python reach Supabase and read the curated tables?

Run:  python check_connection.py
Expected output:  Connected. clubs has 3 rows (expected 3).
"""
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Copy the KEY=value lines from .env into os.environ (the process's environment
# variables). It searches this script's folder, then each parent folder.
load_dotenv()

database_url = os.environ.get("DATABASE_URL")
if not database_url:
    raise SystemExit("DATABASE_URL is not set. Copy .env.example to .env and fill it in.")

# An engine is a reusable factory for connections. Creating it doesn't connect
# yet; the first real connection happens at engine.connect().
engine = create_engine(database_url)

# "with" closes the connection automatically, even if the query fails.
with engine.connect() as conn:
    # text() marks a plain SQL string for SQLAlchemy to run as-is.
    # scalar_one() returns the single value from a one-row, one-column result.
    club_count = conn.execute(text("SELECT count(*) FROM clubs")).scalar_one()

print(f"Connected. clubs has {club_count} rows (expected 3).")
