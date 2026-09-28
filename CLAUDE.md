# CLAUDE.md — Football Heritage

Instructions for Claude working in this repo. For full context read
`COMPLETIONS_LOG.md` (verified state) and `DECISIONS.md` (rationale). Where
`HANDOFF.md` disagrees with those two, they win.

## Who I am and how to help

I'm using this project to **learn Python and data engineering**, not just to
ship an app. It's also a portfolio piece meant to show analyst/consultant skills.

- **Explain before you write.** For each script: *why* (what problem, why now),
  *what* (plain-language behavior), *how* (mechanics, line by line where it
  matters). Define jargon the first time it appears.
- **Guess-and-check.** For the analytically important parts — ingestion logic,
  style metrics, matching logic — ask me to guess or write it first, then
  correct me. Don't hand me finished files for those.
  Boilerplate, config and debugging you can just do (and briefly say what you did).
- **Flag study topics.** When a concept is worth learning properly rather than
  just using (e.g. SQL transactions, virtual environments), say so, briefly,
  with what to study and why it matters here. Keep it to things that pay off
  in this project.
- **Ask at real decision points** — forks where my judgment changes the design.
  No "shall I proceed?" busywork.
- **One step at a time.** Prove a narrow slice end to end before generalizing.
- **Commit every working step** with a descriptive message. The commit history
  is the completions log. Never leave work uncommitted.
- **Don't relitigate settled decisions** (see `DECISIONS.md`). Raise parked
  improvements only when we touch the relevant piece.

## Project in one paragraph

A site that helps a new soccer fan pick a Premier League club based on sports
teams they already follow (NFL, MLB, …). Understat xG/shot data (via
`soccerdata`) feeds a playing-style layer; hand-curated traits and
`cross_sport_analogues` feed the matcher. v1 matching is rule-based (n≈20 clubs
is too small for ML); keep the design ML-ready.

## Architecture — three layers, never mixed

1. **staging** schema — raw Understat data, replaced on each pull, never hand-edited.
2. **marts** — per-club style metrics derived from staging.
3. **public** (curated) — `clubs`, `traits`, `club_traits`, `honors`,
   `cross_sport_analogues`. Human-authored. Joined to analytics via
   `clubs.understat_team_id`.

All in one Supabase Postgres ("Football Heritage" / branch "FBH Backend").

## Stack & environment

- **Python 3.14** venv, macOS, local dir `~/Documents/soccer-stats`.
- **soccerdata** → Understat (xG, shots, schedule, player season stats).
- **Supabase** (hosted Postgres) — project "Football Heritage", branch "FBH Backend", `main`.
- Planned: dbt (marts), Streamlit (frontend), GitHub Actions (scheduling).
- Before any Understat read:
  `export TLS_LIBRARY_PATH="$(pwd)/tls-client-darwin-amd64-1.13.1.dylib"`
  (macOS-only dylib; Understat pulls won't run in a Linux cloud session).
- Supabase connection string lives in `.env`. **Never commit `.env` or print
  secrets.** `.gitignore` already covers it.
- `requirements.txt` pins direct dependencies only. Rebuild with
  `pip install -r requirements.txt`. `.env.example` is the committed template
  for `.env`.
- Existing scripts (`check_methods.py`, `show_columns.py`, `explore_data.py`,
  `understat_clubs.py`) are exploration only: they read and print, nothing persists.
- **`exploration/`** holds every throwaway check that informed a decision, kept
  for study and as a record of process. Never run one-off checks without
  saving them here; commit each with the finding it supports. Run from the repo
  root: `python exploration/<script>.py`.

## Data contract (season `"2024"` = 2024/25, cached as `2425`)

- `read_shot_events()` — 9,878 rows × 16 cols: `league_id, season_id, game_id,
  date, shot_id, team_id, player_id, assist_player_id, assist_player, xg,
  location_x, location_y, minute, body_part, situation, result`
- `read_schedule()` — incl. `home_team_id, away_team_id, home_team, away_team,
  home_goals, away_goals, home_xg, away_xg, is_result, has_data, url`
- `read_player_season_stats()` — incl. `position, matches, minutes, goals, xg,
  np_goals, np_xg, assists, xa, shots, key_passes, xg_chain, xg_buildup`

Understat team ids: full list of all 20 PL clubs in `COMPLETIONS_LOG.md`.

**soccerdata shot bugs — staging takes these from the raw cached JSON**
(`~/soccerdata/data/Understat/match_*.json`; evidence in `exploration/`):
- `situation`, `body_part`, `result`: stored as raw Understat codes
  (`OpenPlay`, `Head`, `MissedShots`…). soccerdata's label map turns
  `Penalty`, `Head`, `OtherBodyPart` into NULL.
- `assist_player_id`: soccerdata returns the roster *row* id (per-match lineup
  slot), not the player id. Resolve the assister's name to the raw roster's
  `player_id` instead (all 7,377 resolve unambiguously in 2024).
- `last_action`: raw `lastAction`, which soccerdata drops. Added as a 17th column.

Table definition: `db/001_staging_understat_shots.sql` (+ `loaded_at` audit column).

## Supabase schema (public verified 2026-09-19; staging 2026-09-27)

`public` has 5 curated tables, seeded with a 3-club sample. `staging` has
`understat_shots`: **9,878 rows for season 2024**, loaded by
`load_understat_shots.py`. That loader is idempotent (one transaction: delete the
season, insert, verify count, commit) — re-running replaces, never duplicates;
`exploration/test_rollback.py` proves a failed load leaves the previous one intact.
The `public` schema lives only in Supabase — not yet in the repo. `db/` holds
new SQL, numbered in the order to apply it; `001` (staging shots) is applied.

| Table | Shape | Rows | Notes |
|---|---|---|---|
| `clubs` | hub | 3 | club, founded, stadium, nickname, fanbase_size, `understat_team_id` |
| `traits` | lookup | 12 | identity + playing-style families |
| `club_traits` | M:M junction | 13 | clubs ↔ traits |
| `honors` | 1:M | 8 | `competition_type` ∈ `european`, `domestic_league`, `domestic_cup` (exact casing) |
| `cross_sport_analogues` | 1:M (M:M in spirit) | 8 | club ↔ free-text `external_team`, reason, `similarity_score` |

Sample clubs: **Manchester City (id 1, understat 88), Liverpool (2, 87),
Brighton (3, 220)** — City, *not* Manchester United.

## Settled decisions — don't relitigate

- Season 2024 is an arbitrary sample; everything in the DB is scaffolding.
- Three layers (above); raw and curated data never share tables.
- `understat_team_id` stays inline on `clubs` until a second data source exists
  (then a `club_source_ids` bridge).
- `club_traits` is a true many-to-many.
- Trait vocabulary splits into *identity* vs *playing style* families.
- Empty `honors` (Brighton) is real data, not a gap.
- `similarity_score` values are trait-informed research estimates confirmed by
  me — not model output.
- `external_team` is free text, not an FK — a conscious "not yet".
- Next ingestion is an **idempotent, on-demand refresh**, starting with shots
  only for season 2024 into a new `staging` schema. Scheduling comes later.
- **Python → Supabase connection: SQLAlchemy + psycopg2**, with
  `python-dotenv` loading `DATABASE_URL` from `.env` (decided 2026-09-27).
  Supabase stays the database; ERDs come from its dashboard Schema Visualizer.
- **`staging.understat_shots`**: grain is one row per shot, `shot_id` is the
  PK, `game_id` links to the (future) schedule table, `season_id` scopes each
  reload.
- **No ML in v1**: rule-based weighted matching (n≈20 clubs is too small);
  keep the architecture ML-ready.

## Open questions — raise when relevant

1. ~~Supabase connection approach~~ — resolved 2026-09-27, see Settled
   decisions.
2. **Where ML/match weights live** — `weight` column on `club_traits` or a
   separate scoring table. Undecided.
3. **Fanbase methodology** — stored City value (109.5M) doesn't match
   IG+TikTok+YouTube (~97M). Pick one rule, re-derive all clubs before scaling.
4. **Cold-start TLS** — is the manual `ctypes` load ever needed?

Parked improvements (fanbase size vs identity, similarity vs affinity,
which traits become data-derived) are in `DECISIONS.md` — raise each only when
we touch that piece.

## Roadmap

1. Staging ingestion (shots done 2026-09-27; schedule/players not yet) → 2. Marts (style metrics) → 3. Scale 3 → 20 clubs
(bottleneck is curation, not code) → 4. `club_legends` + `legendary_matches`
(YouTube links) → 5. Matching logic → 6. Streamlit → 7. ML (only if it scales).
