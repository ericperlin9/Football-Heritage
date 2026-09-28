"""Run a .sql file against Supabase inside a transaction, then roll it back.

Proves the SQL is valid without changing the database: Postgres DDL
(CREATE SCHEMA / CREATE TABLE) is transactional, so ROLLBACK undoes it.
Run:  python exploration/dry_run_sql.py db/002_staging_understat_schedule.sql
"""
import os
import re
import sys

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
engine = create_engine(os.environ["DATABASE_URL"])

sql = open(sys.argv[1]).read()
# The table the file creates, e.g. "staging.understat_schedule"
schema, table = re.search(r"CREATE TABLE IF NOT EXISTS (\w+)\.(\w+)", sql).groups()

with engine.connect() as conn:
    existed = conn.execute(text("SELECT to_regclass(:name)"), {"name": f"{schema}.{table}"}).scalar_one()
    if existed:
        raise SystemExit(f"{schema}.{table} already exists; IF NOT EXISTS would skip it, so this proves nothing")

with engine.connect() as conn:  # SQLAlchemy 2.0 opens a transaction automatically
    conn.execute(text(sql))
    columns = conn.execute(text(
        "SELECT column_name, data_type, is_nullable FROM information_schema.columns "
        "WHERE table_schema = :schema AND table_name = :table ORDER BY ordinal_position"
    ), {"schema": schema, "table": table}).all()
    for name, data_type, nullable in columns:
        print(f"  {name:18} {data_type:26} {'NULL ok' if nullable == 'YES' else ''}")
    conn.rollback()

with engine.connect() as conn:
    exists = conn.execute(text("SELECT to_regclass(:name)"), {"name": f"{schema}.{table}"}).scalar_one()
print(f"{len(columns)} columns created in {schema}.{table}, then rolled back. Exists now: {exists is not None}")
