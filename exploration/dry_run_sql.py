"""Run a .sql file against Supabase inside a transaction, then roll it back.

Proves the SQL is valid without changing the database: Postgres DDL
(CREATE SCHEMA / CREATE TABLE) is transactional, so ROLLBACK undoes it.
Run:  python exploration/dry_run_sql.py db/001_staging_understat_shots.sql
"""
import os
import sys

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
engine = create_engine(os.environ["DATABASE_URL"])

sql = open(sys.argv[1]).read()
with engine.connect() as conn:  # SQLAlchemy 2.0 opens a transaction automatically
    conn.execute(text(sql))
    columns = conn.execute(text(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_schema = 'staging' AND table_name = 'understat_shots' "
        "ORDER BY ordinal_position"
    )).all()
    for name, data_type in columns:
        print(f"  {name:18} {data_type}")
    conn.rollback()

with engine.connect() as conn:
    exists = conn.execute(text("SELECT to_regclass('staging.understat_shots')")).scalar_one()
print(f"{len(columns)} columns created, then rolled back. Table exists now: {exists is not None}")
