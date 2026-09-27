-- staging.understat_shots: raw Understat shot events, one row per shot.
--
-- Staging holds data exactly as the source sent it; it is replaced on every
-- pull (delete the season, re-insert it) and never hand-edited.
-- Evidence for each choice below lives in exploration/.

CREATE SCHEMA IF NOT EXISTS staging;

CREATE TABLE IF NOT EXISTS staging.understat_shots (
    shot_id           integer          PRIMARY KEY,   -- Understat shot id
    league_id         text             NOT NULL,      -- Understat league id ('1' = Premier League)
    season_id         integer          NOT NULL,      -- start year: 2024 = 2024/25; scopes each reload
    game_id           integer          NOT NULL,      -- joins to the future schedule table
    date              timestamptz      NOT NULL,      -- kick-off; Understat sends naive UTC
    team_id           integer          NOT NULL,      -- joins to public.clubs.understat_team_id
    player_id         integer          NOT NULL,      -- shooter
    assist_player_id  integer,                        -- NULL = unassisted (all penalties, direct free kicks)
    assist_player     text,
    xg                double precision NOT NULL CHECK (xg BETWEEN 0 AND 1),
    location_x        double precision NOT NULL CHECK (location_x BETWEEN 0 AND 1),
    location_y        double precision NOT NULL CHECK (location_y BETWEEN 0 AND 1),
    minute            integer          NOT NULL CHECK (minute >= 0),

    -- Raw Understat codes, not soccerdata's labels (its mapping drops
    -- Penalty, Head and OtherBodyPart to NULL). NOT NULL + CHECK makes a
    -- load fail loudly if a mapping gap ever lets a NULL or new code through.
    body_part         text             NOT NULL CHECK (body_part IN
                          ('RightFoot', 'LeftFoot', 'Head', 'OtherBodyPart')),
    situation         text             NOT NULL CHECK (situation IN
                          ('OpenPlay', 'FromCorner', 'SetPiece', 'DirectFreekick', 'Penalty')),
    result            text             NOT NULL CHECK (result IN
                          ('Goal', 'OwnGoal', 'SavedShot', 'BlockedShot', 'MissedShots', 'ShotOnPost')),
    last_action       text             NOT NULL,      -- 31+ values; the string 'None' is kept as sent

    loaded_at         timestamptz      NOT NULL DEFAULT now()  -- when this row was loaded
);
