-- staging.understat_schedule: raw Understat fixtures and results, one row per match.
--
-- Same rules as staging.understat_shots: data exactly as the source sent it,
-- replaced per season on every pull, never hand-edited.
-- Evidence: exploration/inspect_schedule.py, exploration/future_matches.py.

CREATE SCHEMA IF NOT EXISTS staging;

CREATE TABLE IF NOT EXISTS staging.understat_schedule (
    game_id            integer          PRIMARY KEY,   -- staging.understat_shots.game_id points here
    league_id          text             NOT NULL,
    season_id          integer          NOT NULL,      -- start year: 2024 = 2024/25; scopes each reload
    date               timestamptz      NOT NULL,      -- kick-off; Understat sends naive UTC
    home_team_id       integer          NOT NULL,      -- joins to public.clubs.understat_team_id
    away_team_id       integer          NOT NULL,
    home_team          text             NOT NULL,
    away_team          text             NOT NULL,
    home_team_code     text             NOT NULL,      -- e.g. 'MUN'
    away_team_code     text             NOT NULL,

    -- NULL = not played yet (is_result false). Never filled with predictions.
    home_goals         integer          CHECK (home_goals >= 0),
    away_goals         integer          CHECK (away_goals >= 0),
    home_xg            double precision CHECK (home_xg >= 0),
    away_xg            double precision CHECK (away_xg >= 0),
    is_result          boolean          NOT NULL,

    -- Understat's post-match result probabilities, computed from the match's
    -- xG (home side's view). Absent for unplayed matches, so NULL there.
    forecast_home_win  double precision CHECK (forecast_home_win BETWEEN 0 AND 1),
    forecast_draw      double precision CHECK (forecast_draw BETWEEN 0 AND 1),
    forecast_away_win  double precision CHECK (forecast_away_win BETWEEN 0 AND 1),

    loaded_at          timestamptz      NOT NULL DEFAULT now()
);
