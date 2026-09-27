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

## Environment

- Runs locally on macOS (`~/Documents/soccer-stats`), Python 3.14 venv.
- Before any Understat read:
  `export TLS_LIBRARY_PATH="$(pwd)/tls-client-darwin-amd64-1.13.1.dylib"`
  (the dylib is macOS-only; Understat pulls won't run in a Linux cloud session).
- Supabase connection string lives in `.env`. **Never commit `.env` or print
  secrets.** `.gitignore` already covers it.
- Season `"2024"` = 2024/25 campaign (cached as `2425`); it's a sample, not product.

## Conventions

- `honors.competition_type` vocabulary: `european`, `domestic_league`,
  `domestic_cup` — exact casing.
- Empty honors (Brighton) is real data, not missing data.
- Schema changes should be version-controlled SQL under `db/`.
