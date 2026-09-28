-- staging.understat_player_season: raw Understat season totals, one row per
-- player per season.
--
-- Same rules as the other staging tables: data exactly as the source sent
-- it, replaced per season on every pull, never hand-edited.
-- Evidence: exploration/inspect_player_stats.py.

CREATE SCHEMA IF NOT EXISTS staging;

CREATE TABLE IF NOT EXISTS staging.understat_player_season (
    season_id     integer          NOT NULL,   -- start year: 2024 = 2024/25; scopes each reload
    player_id     integer          NOT NULL,   -- same id every season; matches shots.player_id
    league_id     text             NOT NULL,
    player        text             NOT NULL,

    -- A player who played for two clubs in one season has ONE row of combined
    -- totals. Keep Understat's club list as sent ("Brighton,Ipswich") plus
    -- the matching team ids; splitting the totals per club happens later.
    team_title    text             NOT NULL,
    team_ids      integer[]        NOT NULL CHECK (cardinality(team_ids) >= 1),
    position      text             NOT NULL,   -- raw, e.g. 'D M S'

    matches       integer          NOT NULL CHECK (matches >= 0),
    minutes       integer          NOT NULL CHECK (minutes >= 0),
    goals         integer          NOT NULL CHECK (goals >= 0),
    np_goals      integer          NOT NULL CHECK (np_goals >= 0),     -- non-penalty
    assists       integer          NOT NULL CHECK (assists >= 0),
    shots         integer          NOT NULL CHECK (shots >= 0),
    key_passes    integer          NOT NULL CHECK (key_passes >= 0),
    yellow_cards  integer          NOT NULL CHECK (yellow_cards >= 0),
    red_cards     integer          NOT NULL CHECK (red_cards >= 0),
    xg            double precision NOT NULL CHECK (xg >= 0),
    np_xg         double precision NOT NULL CHECK (np_xg >= 0),
    xa            double precision NOT NULL CHECK (xa >= 0),
    xg_chain      double precision NOT NULL CHECK (xg_chain >= 0),
    xg_buildup    double precision NOT NULL CHECK (xg_buildup >= 0),

    loaded_at     timestamptz      NOT NULL DEFAULT now(),

    PRIMARY KEY (season_id, player_id)   -- composite: player_id repeats across seasons
);
