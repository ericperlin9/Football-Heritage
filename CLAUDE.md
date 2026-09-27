# CLAUDE.md — Football Heritage

Context for Claude Code sessions. Keep this file current: when a decision is
made or a question is answered, update the relevant section here.

## How to work with me (read first)

I'm using this project to **learn Python and data engineering**. Optimize for my
understanding, not for speed:

- **Explain the why, what, and how** of every change — why this approach, what
  the code does, how each part works. Name the general concept (e.g. "this is a
  junction table", "this is an environment variable") so I can recognize it
  elsewhere.
- Prefer small, readable steps over clever one-liners. Show SQL/Python I can run
  myself and understand line by line.
- When there are real tradeoffs, briefly say what the alternatives were and why
  we didn't pick them.
- After finishing something meaningful, offer to add an entry to
  `COMPLETIONS_LOG.md` in its existing format (Layman explanation → Key
  concepts → The action / code required).

## What the project is

**Football Heritage** matches soccer clubs to each other and to teams in
*other* sports, based on identity and playing style. Two signature features:

1. **Club-to-club matching.** Clubs are tagged with descriptive traits
   (underdog, big-spender, possession-control, …). Clubs that share more traits
   are more similar. This is the first version of a recommendation engine.
2. **Cross-sport analogues** (e.g. "Man City is the Yankees of soccer"). Each
   club gets a **menu of several analogues**, each with a reason and a
   similarity score, instead of one "correct" answer.

Planned: a computed **style layer** built from Understat match data (shots,
xG, schedule, player stats) to supplement the hand-assigned traits with numbers.

Currently seeded with 3 Premier League clubs: Manchester City, Liverpool, Brighton.

## Stack

| Layer | Tool | Notes |
|---|---|---|
| Database | **Supabase** (hosted Postgres) | Schema is built by hand in the Supabase SQL Editor. It is **not yet in this repo** (see Open questions). |
| Data source | **Understat** via the `soccerdata` Python library (1.9.1) | League `"ENG-Premier League"`, season `"2024"` (the 2024/25 season). |
| Language | Python 3.14, in a local `venv/` | `pandas` 3, `numpy` 2. `psycopg2-binary` and `SQLAlchemy` are installed but not used yet. They're for writing data from Python into Supabase. |
| Scraping helper | `tls-client-darwin-amd64-1.13.1.dylib` | See "TLS library" below. |

Activate the environment with `source venv/bin/activate`, then run a script
with `python explore_data.py`.

### TLS library (important gotcha)

Understat blocks requests that don't look like a browser. soccerdata gets
around this with a compiled Go helper, the `.dylib` in the repo root. It's built
for **macOS on Intel (darwin-amd64)**. soccerdata's auto-download of this file
is broken, so it was downloaded by hand. Every script must set the path
**before** `import soccerdata`:

```python
import os
os.environ["TLS_LIBRARY_PATH"] = os.path.join(os.path.dirname(__file__), "tls-client-darwin-amd64-1.13.1.dylib")
import soccerdata as sd
```

The script must sit in the same folder as the `.dylib`. On an Apple Silicon
(arm64) Mac or on Linux you'd need a different build of this file.

## Repo layout

- `explore_data.py`: prints the columns of Understat shots, schedule, and
  player-season stats. Includes the TLS fix.
- `understat_clubs.py`: lists each team name with its Understat `team_id`
  (these ids will eventually connect Understat data to our `clubs` table).
  Includes the TLS fix.
- `check_methods.py`, `show_columns.py`: early exploration scripts. **They're
  missing the TLS fix**, so they'll likely fail unless `TLS_LIBRARY_PATH` is
  exported in the shell. `show_columns.py` duplicates `explore_data.py`.
- `COMPLETIONS_LOG.md`: plain-language record of finished work and the code
  it took. Newest entries at the bottom.
- `.gitignore`: ignores `venv/`, bytecode, `.env*` (secrets), and `.DS_Store`.

## Supabase schema (current)

Five tables. **Row Level Security (RLS) is enabled on all of them with a
public-read policy.** Anyone with the public API key can read but not write.
The SQL Editor bypasses RLS, so edits made there aren't affected.

```
clubs ──< honors
  │
  ├──< club_traits >── traits          (many-to-many via junction table)
  │
  └──< cross_sport_analogues           (one-to-many: several analogues per club)
```

**`clubs`**: one row per club. PK `club_id`. Also has `club_name`. The full
column list isn't recorded anywhere yet, so check it in Supabase.

**`honors`**: trophies/titles per club, with an FK to `clubs`. The column list
isn't recorded yet either.

**`traits`**: the master list of trait vocabulary (12 rows).
```sql
CREATE TABLE traits (
  trait_id SERIAL PRIMARY KEY,
  trait_name varchar(50),
  description text
);
```

**`club_traits`**: junction table (13 rows).
```sql
CREATE TABLE club_traits (
  club_id int REFERENCES clubs(club_id),
  trait_id int REFERENCES traits(trait_id),
  PRIMARY KEY (club_id, trait_id)   -- composite key; also blocks duplicate tags
);
```

**`cross_sport_analogues`** (8 rows).
```sql
CREATE TABLE cross_sport_analogues (
  analogue_id SERIAL PRIMARY KEY,
  club_id int REFERENCES clubs(club_id),
  external_team varchar(100),
  sport varchar(50),
  reason text,
  similarity_score numeric(3,2)     -- 0.00–9.99; used as a 0–1 score
);
```

### Seed data snapshot
- Man City: modern-power, big-spender, possession-control, working-class-roots, global-fanbase.
  Analogues: Yankees, Chiefs, Dodgers, Eagles.
- Liverpool: historic-giant, high-press-intensity, global-fanbase, attacking-flair.
  Analogues: Red Sox, Dodgers.
- Brighton: underdog, data-driven-recruitment, overachiever, attacking-flair.
  Analogues: Athletics, Rays.

### Key queries
Shared-trait count per club pair (the core of the matching engine):
```sql
SELECT c1.club_name AS club_1, c2.club_name AS club_2, COUNT(*) AS shared_traits
FROM club_traits a
JOIN club_traits b ON a.trait_id = b.trait_id AND a.club_id < b.club_id
JOIN clubs c1 ON a.club_id = c1.club_id
JOIN clubs c2 ON b.club_id = c2.club_id
GROUP BY c1.club_name, c2.club_name
ORDER BY shared_traits DESC;
```
`a.club_id < b.club_id` returns each pair exactly once. It drops both
self-matches and mirror-image duplicates.

Ranked analogues per club:
```sql
SELECT c.club_name, a.external_team, a.sport, a.similarity_score, a.reason
FROM clubs c
JOIN cross_sport_analogues a ON c.club_id = a.club_id
ORDER BY c.club_name, a.similarity_score DESC;
```

## Decisions made (and why)

These come from `COMPLETIONS_LOG.md`. A separate `DECISIONS.md` was supposed to
exist but was never found (see Open questions).

1. **Traits live in their own table, not a CHECK constraint or free text.**
   Adding a trait means inserting one row, with no schema change. The FK blocks
   typos. It's also the shape ML models want for categorical features.
2. **Club↔trait is many-to-many through the `club_traits` junction table,**
   with a composite PK `(club_id, trait_id)` instead of a surrogate id.
3. **Multiple analogues per club, ranked by score and explained by reason.**
   Cross-sport comparisons are genuinely contested, so we offer a reasoned
   menu instead of pretending there's one right answer. The same external team
   can serve several clubs for different reasons (the Dodgers do for City and
   Liverpool).
4. **External teams are kept inline in `cross_sport_analogues`,** so there's
   no `external_teams` table yet. This is deliberate under-normalization,
   because each reason is specific to its pairing and teams aren't reused
   much. *Split them into their own table if external-team info starts
   getting duplicated.*
5. **`similarity_score` is `numeric(3,2)`,** an exact decimal. That's enough
   for a 0–1 score, and it's ML-friendly.
6. **RLS + public-read on every table**, for consistency and as a safe default
   for a public-facing site.
7. **The TLS dylib path is set from inside Python with `__file__`, not a
   shell `export`,** so scripts work in any terminal and after cloning.
8. **Data is easy to change,** so don't let "is this the perfect analogy?"
   block progress. Use UPDATE/DELETE/INSERT later.

## Open questions / TODO

- **`DECISIONS.md` is missing.** It isn't in the repo or anywhere on this Mac
  (as of 2026-09-27). If it exists elsewhere, add it to the repo and merge it
  into the section above.
- **The schema and seed data aren't in version control.** The initial commit
  message mentions "schema, seed data," but only the Python scripts were
  committed. Consider exporting the DDL + INSERTs to `sql/` files (or using
  Supabase CLI migrations) so the database can be rebuilt from the repo.
- **The `clubs` and `honors` column definitions are unrecorded.** Capture
  them here once they're pulled from Supabase.
- **There's no `requirements.txt`,** even though `.gitignore` assumes one.
  Generate it with `pip freeze > requirements.txt`.
- **The Understat → Supabase pipeline isn't built yet.** Open parts: which
  Understat fields become the "computed style layer," how Understat
  `team_id` maps to `clubs.club_id`, and where the Supabase connection string
  lives (it goes in `.env`, which is git-ignored, and never gets committed).
- **Fix or delete the two early scripts.** Add the TLS fix to
  `check_methods.py` and `show_columns.py`, or remove them.
- **The dylib is Intel-only.** Decide how to handle other machines (a
  per-platform file, or documented setup steps).
- **Next directions from the log:** deepen the matching logic (e.g. weighted
  traits), add more clubs, and wire in the Understat style layer.
