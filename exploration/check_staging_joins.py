"""Do the staging tables join to each other and to the curated clubs?

Staging has no foreign keys (they'd block reloads), so nothing in the database
enforces these links. This checks them after each load.
Run:  python exploration/check_staging_joins.py
"""
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
engine = create_engine(os.environ["DATABASE_URL"])

CHECKS = {
    "Rows per table (shots, schedule)": """
        SELECT (SELECT count(*) FROM staging.understat_shots),
               (SELECT count(*) FROM staging.understat_schedule)""",
    "Shots whose game_id isn't in the schedule (want 0)": """
        SELECT count(*) FROM staging.understat_shots s
        LEFT JOIN staging.understat_schedule g USING (game_id)
        WHERE g.game_id IS NULL""",
    "Shots whose team didn't play in that game (want 0)": """
        SELECT count(*) FROM staging.understat_shots s
        JOIN staging.understat_schedule g USING (game_id)
        WHERE s.team_id NOT IN (g.home_team_id, g.away_team_id)""",
    # An OwnGoal row is logged under the team of the player who put it in their
    # own net, and counts for the *other* team. (Counting only 'Goal' rows
    # left 23 games mismatched; this rule matches all 380.)
    "Games where the schedule's score != goals counted from shots (want 0)": """
        SELECT count(*) FROM staging.understat_schedule g
        JOIN (SELECT s.game_id,
                     sum(CASE WHEN s.result = 'Goal'    AND s.team_id = g.home_team_id THEN 1
                              WHEN s.result = 'OwnGoal' AND s.team_id = g.away_team_id THEN 1
                              ELSE 0 END) AS home,
                     sum(CASE WHEN s.result = 'Goal'    AND s.team_id = g.away_team_id THEN 1
                              WHEN s.result = 'OwnGoal' AND s.team_id = g.home_team_id THEN 1
                              ELSE 0 END) AS away
              FROM staging.understat_shots s JOIN staging.understat_schedule g USING (game_id)
              GROUP BY s.game_id) counted USING (game_id)
        WHERE g.home_goals != counted.home OR g.away_goals != counted.away""",
    "Own-goal rows: count and total xG attached to them": """
        SELECT count(*), round(sum(xg)::numeric, 3) FROM staging.understat_shots
        WHERE result = 'OwnGoal'""",
    "Sample clubs: matches played in staging": """
        SELECT c.club_name, count(g.game_id) FROM public.clubs c
        LEFT JOIN staging.understat_schedule g
               ON c.understat_team_id IN (g.home_team_id, g.away_team_id)
        GROUP BY c.club_name ORDER BY c.club_name""",
}

with engine.connect() as conn:
    for label, sql in CHECKS.items():
        print(f"{label}:", conn.execute(text(sql)).all())
