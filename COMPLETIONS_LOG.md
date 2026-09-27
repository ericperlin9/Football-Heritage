# Soccer Project — Completions Log

A plain-language record of things I've finished, why they mattered, and the
actual actions/code each one required. Written so future-me (or a reviewer) can
understand not just *what* I did but *what the code was doing*.

Newest at the bottom.

---

## ✅ Fixed the TLS library error permanently

### Layman explanation
The soccer data library (`soccerdata`) pulls stats from a website called
Understat. Websites can tell when a *program* (not a person in a browser) is
requesting data, and they often block it. To get around that, soccerdata uses a
small specialized helper file — a "dylib" — that makes its request look like a
normal web browser so Understat lets it in.

That helper file is compiled code written in another language (Go), built for a
specific operating system and computer chip. My Mac is Intel ("darwin-amd64").
soccerdata tried to auto-download the helper but used the wrong filename, so it
failed every time. I downloaded the correct file by hand, and then — this step —
I made my script *automatically* tell Python where that file is, every time it
runs. Before this fix I had to type an `export` command in the terminal every
single session or the program would crash. Now it just works, in any terminal,
even if I move the project or put it on GitHub.

### What "dylib" means
- **dylib = dynamic library** = a bundle of pre-compiled code a program loads
  *while running*, instead of having it built in. (Windows calls these `.dll`,
  Linux `.so`.)
- Filename decoded: `tls-client` (what it does) + `darwin-amd64` (macOS + Intel
  chip) + `1.13.1` (version) + `.dylib` (file type).
- Big lesson: many Python libraries are really Python "wrappers" around compiled
  code in other languages (C/Go/Rust). Weird "can't load library" errors are
  often this — the compiled piece didn't download or doesn't match my system.
  Will see this again in machine learning (NumPy, PyTorch, scikit-learn all use
  compiled backends).

### The action / code required
Added two lines at the very TOP of the script, ABOVE `import soccerdata`
(it has to come first, because the library reads the setting when it loads):

```python
import os
os.environ["TLS_LIBRARY_PATH"] = os.path.join(os.path.dirname(__file__), "tls-client-darwin-amd64-1.13.1.dylib")
```

What each part does:
- `import os` — loads Python's operating-system toolkit (lets me set
  environment variables from inside code).
- `os.environ["TLS_LIBRARY_PATH"] = ...` — sets the environment variable the
  library looks for, but *from within Python* — so I no longer need the terminal
  `export`.
- `os.path.dirname(__file__)` — "the folder this script lives in." Using this
  instead of a hardcoded path means it still works if the project moves or is
  cloned to another machine.
- `os.path.join(folder, "tls-...dylib")` — glues the folder and filename into
  one full file path.

Requirement to remember: the `.dylib` file must sit in the SAME folder as the
script. Confirmed working — ran in a fresh terminal with no `export` and it
loaded the library and pulled data cleanly.


---

## ✅ Built the traits system (many-to-many) and the first matching query

### Layman explanation
This is the part that turns the database from "a list of facts about clubs" into
something that can actually *match* clubs to each other. I added the ability to
tag each club with descriptive traits ("underdog", "big-spender",
"possession-control", etc.). Because one club has many traits AND one trait
applies to many clubs, this is a "many-to-many" relationship — which needs a
special middle table to connect the two sides. Once clubs are tagged, I can ask
the database "which clubs share the most traits?" — and that shared-trait count
is the seed of the whole recommendation engine.

### Key concepts learned
- **Many-to-many relationship:** when both sides can have many of each other
  (clubs↔traits). Can't be done with a single foreign key — needs a THIRD table.
- **Junction table (a.k.a. linking/bridge table):** the middle table
  (`club_traits`) that holds one row per club-trait pairing. Same pattern shows
  up everywhere: users↔roles, students↔courses, products↔tags.
- **Composite primary key:** `club_traits`'s key is the PAIR (club_id, trait_id)
  together, not a separate id column. This also prevents tagging a club with the
  same trait twice.
- **Controlled-but-flexible vocabulary:** traits live in their own `traits`
  table (not a rigid CHECK list). Adding a new trait = insert one row, no schema
  change. And the foreign key stops typos/garbage values. Best of both worlds —
  this is also the shape ML wants categorical features in later.
- **Text needs single quotes in SQL:** unquoted `historic-giant` makes SQL read
  the hyphen as a MINUS sign (historic minus giant). Numbers stay unquoted.
- **The `<` trick for unique pairs:** when comparing rows in the same table to
  each other, `a.club_id < b.club_id` gives each pair exactly once. `!=` (unequal)
  would give every pair twice (both directions); `<` removes both self-matches
  AND mirror-image duplicates in one condition.

### The action / code required

**Two tables — the master list and the junction:**
```sql
CREATE TABLE traits (
  trait_id SERIAL PRIMARY KEY,
  trait_name varchar(50),
  description text
);

CREATE TABLE club_traits (
  club_id int REFERENCES clubs(club_id),
  trait_id int REFERENCES traits(trait_id),
  PRIMARY KEY (club_id, trait_id)     -- composite key: the PAIR is unique
);
```
- `SERIAL PRIMARY KEY` — auto-generating id for each trait.
- `REFERENCES other_table(col)` — makes a foreign key (the correct syntax; NOT
  the words "FOREIGN KEY" inline).
- `PRIMARY KEY (club_id, trait_id)` — composite key, written as its own line at
  the end, listing both columns.
- Also enabled RLS + public-read policies on both tables (consistency with
  clubs/honors; SQL Editor bypasses RLS so my editor work is unaffected).

**Populated 12 traits, then tagged the 3 clubs** (13 club-trait pairings) with
multi-row INSERTs (one VALUES, comma between rows, semicolon at end).

**The three-table join — turns stored id-pairs back into readable meaning:**
```sql
SELECT c.club_name, t.trait_name, t.description
FROM clubs c
JOIN club_traits ct ON c.club_id = ct.club_id
JOIN traits t ON ct.trait_id = t.trait_id
ORDER BY c.club_name, t.trait_name;
```
Walks clubs → club_traits → traits (two joins chained) to show each club with its
trait names spelled out.

**The first matching query — counts shared traits per club pair (the engine seed):**
```sql
SELECT c1.club_name AS club_1, c2.club_name AS club_2, COUNT(*) AS shared_traits
FROM club_traits a
JOIN club_traits b ON a.trait_id = b.trait_id AND a.club_id < b.club_id
JOIN clubs c1 ON a.club_id = c1.club_id
JOIN clubs c2 ON b.club_id = c2.club_id
GROUP BY c1.club_name, c2.club_name
ORDER BY shared_traits DESC;
```
More shared traits = more similar clubs. This is recommendation logic in embryo.

### Data note
Trait tags per club (from research on each club's identity/style):
- Man City: modern-power, big-spender, possession-control, working-class-roots, global-fanbase
- Liverpool: historic-giant, high-press-intensity, global-fanbase, attacking-flair
- Brighton: underdog, data-driven-recruitment, overachiever, attacking-flair
Shared traits (the matches): City–Liverpool share global-fanbase; Liverpool–Brighton share attacking-flair.

---

## ✅ Built the cross-sport analogues table (the signature feature)

### Layman explanation
This is the standout feature of the site: mapping each soccer club to teams in
OTHER sports (e.g. "Man City is the New York Yankees of soccer"). The key product
decision: instead of forcing ONE equivalent per club, each club gets MULTIPLE
possible analogues, each with a reason and a strength score — so an end user can
pick the analogue that matches what THEY value (money & dominance → Yankees;
recent-dynasty-that-bought-success → Chiefs; etc.). Cross-sport analogies are
genuinely contested (different credible sources pick different teams for Man City),
so giving the user a reasoned menu is both more honest and more engaging than
pretending there's one right answer.

### Key concepts / decisions
- **One-to-many pays off:** because analogues are their own table with many rows
  per club, the SAME external team (e.g. LA Dodgers) can be an analogue for TWO
  different clubs for different reasons — two rows, no conflict. An inline
  "the_equivalent" column could not have done this.
- **When NOT to over-normalize:** kept the external team INLINE in this table
  (name + sport in the same row) rather than giving external teams their own
  table. Reason: the "reason" text is specific to each pairing anyway, and teams
  aren't reused heavily enough to justify the extra table yet. Knowing when to
  stop normalizing is a real skill. (If external teams start getting reused with
  duplicated info, that's the signal to split them out later.)
- **score + reason earn their keep:** with multiple analogues per club, the score
  RANKS them (strongest fit first) and the reason explains the tradeoff — turning
  a lookup into a decision menu.
- **numeric(3,2):** the score type = up to 3 digits, 2 after the decimal (0.00–9.99),
  covers a 0–1 similarity score and is the format ML models prefer.
- **Everything is editable later:** UPDATE to change a reason/score, DELETE to
  remove, INSERT to add more. Don't let "is this the perfect analogy?" block
  progress — data is the easy thing to change.

### The action / code required

**The table:**
```sql
CREATE TABLE cross_sport_analogues (
  analogue_id SERIAL PRIMARY KEY,
  club_id int REFERENCES clubs(club_id),
  external_team varchar(100),
  sport varchar(50),
  reason text,
  similarity_score numeric(3,2)
);
-- plus RLS enable + public-read policy, for consistency with the other tables
```

**Populated 8 analogues** across the 3 clubs (multiple per club — the contested
menu): Man City → Yankees / Chiefs / Dodgers / Eagles; Liverpool → Red Sox /
Dodgers; Brighton → Athletics / Rays. Each with a reason + score.

**Ranked reveal query — each club's analogues, strongest first:**
```sql
SELECT c.club_name, a.external_team, a.sport, a.similarity_score, a.reason
FROM clubs c
JOIN cross_sport_analogues a ON c.club_id = a.club_id
ORDER BY c.club_name, a.similarity_score DESC;
```
`ORDER BY similarity_score DESC` is what ranks each club's menu best-fit-first.

### Where the backend stands now
Five linked tables: clubs, honors, traits, club_traits (junction),
cross_sport_analogues. Real data in all. Matching foundation working
(shared-trait counts + ranked cross-sport analogues). Next candidates: deepen
matching logic, add more clubs, or wire in the Understat computed style layer.
