# Football Heritage — Completions Log

_Reconstructed 2026-09-19 from project files, terminal output, and Supabase
screenshots after the original working chat was lost. Every state below was
verified against a real artifact (the zip, the run log, or the live tables),
not recalled from the lost conversation._

Project: **Football Heritage** (Supabase) · backend branch **FBH Backend** · `main` / production
Local dir: `~/Documents/soccer-stats` · Python 3.14 venv (machine also has anaconda3 3.9, python.org 3.13)

---

## Goal

A site that helps a new soccer fan pick a Premier League club to support, based
on characteristics of sports teams they already follow (NFL, MLB, etc.). The
`cross_sport_analogues` table is the matching layer. Long-term: ML-driven
matching, plus historical legendary matches and club legends with YouTube links.

---

## Done & verified

### Environment / ingestion plumbing
- [x] venv on Python 3.14; `soccerdata` installed and working.
- [x] **Understat/Cloudflare TLS problem solved.** The working mechanism is a
      shell export before running:
      `export TLS_LIBRARY_PATH="$(pwd)/tls-client-darwin-amd64-1.13.1.dylib"`
      soccerdata's automatic loader then finds and loads it.
      Confirmed loading successfully on 2026-09-09 and again 2026-09-19.
      (A manual `ctypes` load was explored during debugging; the run logs only
      show the env-var route succeeding — CONFIRM whether the manual step is
      still needed on a cold start.)

### Data contract (season "2024" = 2024/25 campaign, cached as `2425`)
Confirmed column lists from soccerdata:
- **Shots** `read_shot_events()` — 9,878 rows × 16 cols:
  `league_id, season_id, game_id, date, shot_id, team_id, player_id,
  assist_player_id, assist_player, xg, location_x, location_y, minute,
  body_part, situation, result`
- **Schedule** `read_schedule()` — incl.
  `home_team_id, away_team_id, home_team, away_team, home_goals, away_goals,
  home_xg, away_xg, is_result, has_data, url`
- **Players** `read_player_season_stats()` — incl.
  `position, matches, minutes, goals, xg, np_goals, np_xg, assists, xa, shots,
  key_passes, xg_chain, xg_buildup`

### Team → understat_team_id (all 20 PL clubs, recovered in full)
Arsenal 83 · Aston Villa 71 · Bournemouth 73 · Brentford 244 · Brighton 220 ·
Chelsea 80 · Crystal Palace 78 · Everton 72 · Fulham 228 · Ipswich 285 ·
Leicester 75 · Liverpool 87 · Manchester City 88 · Manchester United 89 ·
Newcastle United 86 · Nottingham Forest 249 · Southampton 74 · Tottenham 82 ·
West Ham 81 · Wolverhampton Wanderers 229

### Backend schema — 5 tables, structure complete
`clubs` (hub) · `traits` · `club_traits` (M:M junction) · `honors` (1:M) ·
`cross_sport_analogues` (1:M today; M:M in spirit).
(Note: earlier in reconstruction this was miscounted as 6 — it is **5**.)

### Seed data — three-club sample, fully entered
**Sample = Manchester City, Liverpool, Brighton** (NOT Man United — every field
and every analogue confirms City: Etihad, "The Citizens", founded 1880,
understat 88, and analogue reasons about heavy spending / modern dynasty).

`clubs` (3):
| id | club | founded | stadium | nickname | fanbase | understat |
|----|------|---------|---------|----------|---------|-----------|
| 1 | Manchester City | 1880 | Etihad Stadium | The Citizens | 109,500,000 | 88 |
| 2 | Liverpool | 1892 | Anfield | The Reds | 104,600,000 | 87 |
| 3 | Brighton & Hove Albion | 1901 | Falmer Stadium | The Seagulls | 7,600,000 | 220 |

`traits` (12): historic-giant, modern-power, underdog, big-spender,
data-driven-recruitment, possession-control, high-press-intensity,
attacking-flair, defensive-resilience, global-fanbase, working-class-roots,
overachiever. (Two families: club *identity* + *playing style*.)

`club_traits` (13 mappings):
- City → modern-power, big-spender, possession-control, global-fanbase, working-class-roots
- Liverpool → historic-giant, high-press-intensity, attacking-flair, global-fanbase
- Brighton → underdog, data-driven-recruitment, attacking-flair, overachiever

`cross_sport_analogues` (8, scores 0.70–0.92):
- City → Yankees 0.90, Chiefs 0.85, Dodgers 0.80, Eagles 0.75
- Liverpool → Red Sox 0.88, Dodgers 0.70
- Brighton → Athletics 0.92, Rays 0.85
- (MLB + NFL only so far; no NBA/NHL. Dodgers appears for two clubs — the M:M in action.)

`honors` (8) — all factually correct:
- City → Champions League 2023, Premier League 2023, FA Cup 2023, EFL Cup 2021
- Liverpool → Champions League 2019, Premier League 2025, FA Cup 2022, EFL Cup 2024
- Brighton → **none (correct — Brighton has no major trophies; empty set is real signal)**
- `competition_type` controlled vocab: `european`, `domestic_league`, `domestic_cup`

### Version control (initialized 2026-09-19)
- **`.gitignore` authored before the first commit**, establishing secret-hygiene
  from the outset. Excluded paths and the rationale:
  - `venv/`, `.venv/` — the Python **virtual environment**: machine-specific and
    large, reproducible from a future `requirements.txt`, so it's never tracked.
  - `__pycache__/`, `*.pyc` — **compiled Python bytecode**, regenerated on run.
  - `.env`, `.env.*` — **environment/secrets files**. The Supabase **connection
    string** (which embeds the database password) will live here; this rule
    guarantees it is never committed or pushed to a remote.
  - `.DS_Store` — macOS Finder metadata.
- [x] `git init` → stage (`git add`) → **initial commit** `78071ee`
      ("Initial commit: Football Heritage backend…"), 6 files tracked.
- [x] **GitHub remote published** — `origin` →
      https://github.com/ericperlin9/Football-Heritage , `main` tracking
      `origin/main`. Authenticated over HTTPS with a Personal Access Token (PAT),
      not a password (GitHub no longer accepts password auth for Git).
- From here forward, **the commit history is the completions log** — commit each
  working step with a descriptive message.

---

## In progress / next action
- [ ] **The "permanent link":** persist soccerdata reads to Supabase instead of
      reading-to-memory-and-printing. This is the resume point.

## Not built yet (planned)
- [ ] `staging` schema for raw Understat data (shots/schedule/players)
- [ ] marts layer: per-club playing-style metrics derived from raw shots
- [ ] dbt, Streamlit dashboard, GitHub Actions scheduling
- [ ] legends + legendary_matches tables (YouTube links)
- [ ] ML matching layer

## Open items flagged
1. **Fanbase methodology unconfirmed** — "IG + YouTube + TikTok" doesn't
   reconcile: City's IG 57.1M + TikTok 31.7M + YouTube 8.5M ≈ 97M vs stored
   109.5M. Re-derive one consistent rule before scaling to 20 clubs.
2. **ML weight storage** — a single `similarity_score` doesn't hold per-trait
   weights; decide where explainable weights live (weight column on
   `club_traits`, or a separate scoring table). Unresolved.
3. `cross_sport_analogues.external_team` is free-text, not an FK — conscious
   "not yet"; promote to its own table if external teams ever need attributes.
4. `understat_team_id` inline 1:1 now; migrate to a `club_source_ids` bridge
   when a second data source (FBref/Opta/etc.) is added.
