# Football Heritage — Decisions & Rationale

_Companion to COMPLETIONS_LOG.md. The log says what's built; this says **why**,
what was deliberately deferred, and what's still open. Reconstructed 2026-09-19._

## How this was built (authorship)
- **Code:** collaborative, guided. You wrote it via guess-and-check; correct
  answers were supplied and checked along the way. Credit as joint, not solo.
- **Trait & analogue descriptions:** co-written.
- **Cross-sport comparisons (teams, reasons, scores):** researched from multiple
  sources on your confirmation.
- **`similarity_score` values:** trait-informed research estimates, confirmed by
  you — derived from online research on how each franchise is perceived, mapped
  against the qualitative traits in the table. **Not an independent scoring
  system and not model output.** One basis (the traits); these scores are just
  an early manual expression of it, to be replaced by the ML weighting later.

## Settled decisions
- **Season 2024 is an arbitrary sample**, chosen to prove the backend end-to-end
  before scaling. Everything currently in the DB is scaffolding, not product.
- **Data architecture: three layers — raw → marts → curated.**
  Raw quantitative soccerdata and hand-curated qualitative content never share
  tables (different shapes, lifecycles, owners). Raw lands in a `staging` schema
  in the same Supabase Postgres; marts derive style metrics from it; the 5
  curated tables stay human-authored. This separation is also the resume-legible
  data-engineering story.
- **`understat_team_id` lives inline on `clubs`** — it's genuinely 1:1 today, so
  no bridge table until a second source exists.
- **`club_traits` is a true many-to-many** (a club has many traits; a trait spans
  many clubs). Verified by shared traits in the seed data.
- **Trait vocabulary is split into identity vs. playing-style families** — lets
  the future ML weight "identity match" and "style match" separately.
- **Empty honors is real data, not a gap** (Brighton). Don't treat missing
  honors as null-to-be-filled.

## Deliberate "not yets"
- `cross_sport_analogues.external_team` is free text, so the table is currently
  **1:M in structure** even though the concept is M:M. Promote `external_team`
  to its own table (with league/city/its own traits) only when it needs
  attributes of its own. Conscious choice, not an oversight.

## Open questions (decide before/while building forward)
1. **Where do ML match weights live?** `similarity_score` captures the final
   club↔team match but not the per-trait weights that would explain it. This is
   the one genuinely unresolved design fork.
2. **Fanbase methodology** — pick one consistent, reproducible platform set and
   re-derive all clubs (current stored value for City doesn't match the
   IG+YT+TikTok rule).
3. **"Permanent link" flavor** — one-shot script, idempotent refresh, or
   scheduled? Leaning idempotent-on-demand for the next step; automation later.

## Parked improvements — raise at the RIGHT time, not now
_These are sound ideas that are deliberately out of scope while building the
small-sample framework. The current goal is a correct framework on 3 clubs
before automating — not re-litigating these. Bring each up only when we touch
the relevant piece._
- **When we touch the fanbase column:** does `fanbase_size` mean *size* (one
  number) or *identity* (per-platform breakdown — TikTok-young-global vs
  Facebook-legacy)? The matcher may want both. (Also fixes the reconciliation
  issue.)
- **When we design the matching logic:** is "similarity" the right frame, or is
  it "affinity"? A fan may value the *arc* (underdog→dynasty), not the finished
  article — similarity to the Chiefs could hand them City when a mid-arc club
  fits better.
- **When we wire analytics into `club_traits`:** which traits become
  data-derived from Understat (possession-control, high-press-intensity,
  attacking-flair) vs. stay human-judgment-only (historic-giant,
  working-class-roots)? This is the seam between the curated and analytics layers.

## Naming note
Project is **Football Heritage** / **FBH Backend** in Supabase — memory had it
as "soccer-stats," which is just the local folder name.
