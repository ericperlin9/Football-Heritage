# Football Heritage — Session Handoff

**Purpose:** carry the context from the chat sessions of 2026-09-19/27 into Claude
Code. Read this alongside `COMPLETIONS_LOG.md` (verified state) and
`DECISIONS.md` (rationale + parked ideas). Where this file and those disagree,
those two win — they were verified against the live database.

---

## 1. How I want to work (read this first)

I am using this project to **learn Python and data engineering**, not just to
get a working app. That changes how you should help:

- **Explain before you write.** For each script: the *why* (what problem, why
  now), the *what* (plain-language behavior), and the *how* (mechanics, line by
  line where it matters).
- **Let me write code and check me.** The prior working pattern was: you give
  the right answer, I guess first, you correct. Keep that. Do not silently hand
  me finished files for the parts that matter analytically (ingestion logic,
  style metrics, matching logic). Boilerplate/config/debugging you can just do.
- **Ask for confirmation at real decision points** — forks where my judgment
  changes the design. Not "shall I proceed?" busywork.
- **Commit every working step** with a descriptive message. The commit history
  is now the completions log. (Context was lost once already because nothing was
  in version control — do not let work sit uncommitted.)
- **One step at a time.** Prove a narrow slice end to end before generalizing.

---

## 2. What this project is

A site that helps a **new soccer fan pick a Premier League club to support**,
based on characteristics of sports teams they already follow (NFL, MLB, etc.).

- `cross_sport_analogues` is the matching layer (club ↔ external team, with a
  reason and a score).
- Understat xG/shot data will feed a **playing-style** layer.
- Long term: historical legendary matches and club legends with YouTube links;
  eventually ML-driven matching.
- It is a **portfolio project** for GitHub/resume — meant to signal
  analyst/consultant skills ("turn data into decisions").

---

## 3. Where things actually stand

**Repo:** https://github.com/ericperlin9/Football-Heritage (local:
`~/Documents/soccer-stats`). Initial commit `78071ee`. `.gitignore` already
excludes `venv/`, `.venv/`, `__pycache__/`, `*.pyc`, `.env`, `.env.*`, `.DS_Store`.

**Supabase project:** "Football Heritage" / branch "FBH Backend" / `main`.

**Working:** Understat reads via `soccerdata`. The Cloudflare/TLS blocker is
solved with a shell export before running:

    export TLS_LIBRARY_PATH="$(pwd)/tls-client-darwin-amd64-1.13.1.dylib"

Confirmed loading successfully on 2026-09-09 and again 2026-09-19. An earlier
manual `ctypes` load was explored during debugging; only the env-var route is
confirmed working. **Unresolved:** whether a manual load is ever needed on a
cold start.

**Existing scripts are exploration only** — they read and print, nothing
persists: `check_methods.py`, `show_columns.py`, `explore_data.py`,
`understat_clubs.py`.

**Verified data contract** (season `"2024"` = 2024/25 campaign, cached as `2425`):
- `read_shot_events()` — 9,878 rows × 16 cols: `league_id, season_id, game_id,
  date, shot_id, team_id, player_id, assist_player_id, assist_player, xg,
  location_x, location_y, minute, body_part, situation, result`
- `read_schedule()` — incl. `home_team_id, away_team_id, home_team, away_team,
  home_goals, away_goals, home_xg, away_xg, is_result, has_data, url`
- `read_player_season_stats()` — incl. `position, matches, minutes, goals, xg,
  np_goals, np_xg, assists, xa, shots, key_passes, xg_chain, xg_buildup`

**All 20 PL `understat_team_id`s:** Arsenal 83 · Aston Villa 71 · Bournemouth 73 ·
Brentford 244 · Brighton 220 · Chelsea 80 · Crystal Palace 78 · Everton 72 ·
Fulham 228 · Ipswich 285 · Leicester 75 · Liverpool 87 · Manchester City 88 ·
Manchester United 89 · Newcastle United 86 · Nottingham Forest 249 ·
Southampton 74 · Tottenham 82 · West Ham 81 · Wolverhampton Wanderers 229

**Database (verified live 2026-09-19):** 5 tables in `public`, seeded with a
3-club sample — `clubs` (3), `traits` (12), `club_traits` (13), `honors` (8),
`cross_sport_analogues` (8). **No `staging` schema exists. No raw Understat data
is persisted anywhere yet.** Clean slate for ingestion.

Sample clubs are **Manchester City (club_id 1), Liverpool (2), Brighton (3)** —
note City, *not* Manchester United. `understat_team_id`s 88, 87, 220.

---

## 4. The immediate next step

**The "permanent link":** persist Understat data into Supabase instead of
reading-to-memory-and-printing.

Agreed shape:
- **Idempotent refresh** — re-runnable without duplicating. Not one-shot, not
  scheduled yet (scheduling comes after it works manually).
- **Start narrow:** raw shot events for season `"2024"` into a **new `staging`
  schema**, and nothing else. Prove the write path end to end, then widen to
  schedule and players.

**Open question I still owe an answer on:** how to connect to Supabase from
Python — SQLAlchemy + psycopg2, the `supabase` client, or walk me through the
options. **Ask me before writing the connection code.**

The Supabase connection string goes in a `.env` file (already gitignored).
Never commit it.

---

## 5. Architecture decision: three layers

Raw quantitative data and hand-curated qualitative content **never share
tables** — different shapes, lifecycles and owners; a data refresh must never
clobber hand-entered judgment.

1. **Raw/staging** — `staging.understat_shots`, `…_schedule`, `…_players`.
   Loaded from soccerdata, replaced on each pull, never hand-edited.
2. **Marts/analytical** — per-club playing-style metrics derived from staging
   (xG for/against, shot volume, open-play vs set-piece share, shot quality).
   This is the layer that carries the data-engineering story on the resume.
3. **Curated domain** — the existing 5 tables. Human-authored. Linked to
   analytics via `clubs.understat_team_id`.

Flow: soccerdata → staging → marts → informs curated traits → feeds the matcher.

Same Supabase Postgres, separate schema. Not a separate database.

---

## 6. Settled decisions (don't relitigate)

- **Season 2024 is an arbitrary sample**, chosen to prove the backend before
  scaling. Everything in the DB now is scaffolding, not product.
- **`understat_team_id` sits inline on `clubs`** — genuinely 1:1 today. Migrate
  to a `club_source_ids` bridge only when a second data source (FBref/Opta) is
  added.
- **`club_traits` is a true many-to-many.** Confirmed by shared traits in seed
  data (global-fanbase spans City + Liverpool; attacking-flair spans Liverpool +
  Brighton).
- **Trait vocabulary deliberately splits into two families:** club *identity*
  (historic-giant, modern-power, underdog, big-spender, data-driven-recruitment,
  global-fanbase, working-class-roots, overachiever) and *playing style*
  (possession-control, high-press-intensity, attacking-flair,
  defensive-resilience). This lets future ML weight identity and style
  separately.
- **Empty `honors` is real data, not a gap.** Brighton has no major trophies —
  that absence is part of their underdog/overachiever profile. Never treat it as
  null-to-be-filled.
- **`similarity_score` values are trait-informed research estimates**, derived
  from research on how each franchise is perceived, mapped against the trait
  vocabulary, and confirmed by me — *not* model output and not an independent
  scoring system. They're an early manual expression of the trait basis, to be
  replaced by ML weighting later.
- **`cross_sport_analogues.external_team` is free text, not an FK** — so the
  table is 1:M in structure though M:M in spirit. Conscious "not yet"; promote
  `external_team` to its own table only when external teams need attributes of
  their own.
- **`honors.competition_type` is a controlled vocabulary:** `european`,
  `domestic_league`, `domestic_cup`. Keep exact casing when scaling or you get
  silent duplicates.

---

## 7. Open questions (unresolved — raise when relevant)

1. **Where do ML match weights live?** A single `similarity_score` doesn't store
   per-trait weights, so a match can't be explained ("you match Brighton because
   you weight overachiever 0.8"). Options: a `weight` column on `club_traits`,
   or a separate scoring table. Genuinely undecided.
2. **Fanbase methodology is unconfirmed.** Stored value for Man City is
   109,500,000 but Instagram + TikTok + YouTube ≈ 97M. Pick one reproducible
   rule and re-derive all clubs before scaling to 20.
3. **Supabase connection approach** (see §4).
4. **Cold-start TLS** — is the manual `ctypes` load ever needed? (see §3)

---

## 8. Parked improvements — raise at the right moment, not now

Deliberately out of scope while the small-sample framework is built. Bring each
up only when we touch that piece:

- **When touching the fanbase column:** should `fanbase_size` be *size* (one
  number) or *identity* (per-platform breakdown — TikTok-young-global vs
  Facebook-legacy)? The matcher may want both.
- **When designing matching logic:** is "similarity" the right frame, or
  "affinity"? A fan may value the *arc* (underdog→dynasty), not the finished
  article — pure similarity to the Chiefs hands them Man City when a mid-arc
  club might fit better.
- **When wiring analytics into `club_traits`:** which traits become
  data-derived from Understat (possession-control, high-press-intensity,
  attacking-flair) vs. stay human-judgment-only (historic-giant,
  working-class-roots)? This is the seam between the curated and analytics
  layers.

---

## 9. Roadmap and a scoping recommendation

Remaining phases, roughly in order:
1. Staging ingestion (next)
2. Marts layer — style metrics from shots/xG
3. Scale 3 → 20 clubs (**the real bottleneck is qualitative curation, not code**)
4. `club_legends` + `legendary_matches` tables with YouTube links
5. Matching logic
6. Streamlit frontend
7. ML (see below)

**Recommendation already accepted in principle: cut ML from v1.** With 20 clubs
and ~12 traits there are ~20 rows of training data — not an ML-sized dataset;
any model would memorize, not learn, and an interviewer will spot that. Ship a
transparent **rule-based weighted match** (trait overlap × justifiable weights)
and keep the architecture ML-ready. "Rule-based v1 because n=20" is a strength
in an interview, not a weakness. Revisit ML if the project scales to multiple
leagues and hundreds of clubs.

---

## 10. Immediate to-dos

- [ ] Commit `COMPLETIONS_LOG.md`, `DECISIONS.md`, this file, and `CLAUDE.md`
      to the repo.
- [ ] Add a `requirements.txt` — nothing pins dependencies yet.
- [ ] Decide the Supabase connection approach.
- [ ] Build the staging ingestion script (idempotent, shots only, season 2024).
- [ ] Add a `db/` folder with the schema as version-controlled SQL — the schema
      currently exists only in Supabase, not in the repo.
- [ ] Consider a logging config so soccerdata's INFO noise stops requiring
      `2>/dev/null` (which currently also hides real errors).
