---
id: T-0572
title: The 134 Black Hawk War veterans who enrolled at Chicago in 1832, read from the Illinois State Archives index and crosswalked to the 1833-1835 town lists
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0556
opened: 2026-09-03
closed: 2026-09-03
pr: 711
claimed_by: run 9/3/2026, 12:17:53 PM CT
blocked_on: null
needs_bake: false
---

The 134 Black Hawk War veterans who enrolled at Chicago in 1832, read from the Illinois State Archives index and crosswalked to the 1833-1835 town lists.

Piece 2 of 6 of **T-0556 — genealogytrails.com Cook County: inventory every section of the site, grade what it holds for 1835 Chicago, and split the extraction of residents, households, businesses, structures and occupations into tickets**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**The source.** `text/blackhawkwar.txt` — 134 table rows, header excluded, each giving NAME, rank,
company, place of enrollment and regiment or brigade. The site transcribes the Illinois State
Archives database indexing volume 1 of Ellen M. Whitney, *The Black Hawk War 1831-1832*.

**Why it is worth a run.** Every one of these men enrolled AT CHICAGO in 1832, three years before
the scene: 134 men demonstrably standing in this town, with a rank and a company. Kercheval's is
the commonest company, and Gholson Kercheval signs the 1833 poll list this project already holds.

**A trap, stated before the work starts.** Names are printed in several forms and NOT all of them
carry a surname comma — `AS KE WITT` is a row. A reader who filters on the comma silently drops the
French and Potawatomi names, which are the ones this reconstruction is least able to lose.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)
- All 134 rows in `data/research/civic/records/` with rank, company, enrollment place and regiment
  preserved as read; the count is declared in `coverage.json` and a missing row fails.
- A crosswalk to the 1833-1835 poll and tax lists with every merge carrying its rule and every
  refusal named. Presence here is presence in 1832 and is NOT residence in 1835: say so on the
  record, and let no merge assert it.
- A source record naming Whitney's volume as the original and the State Archives index as the layer
  actually read.

**Links:** parent T-0556 · `data/research/civic/records/voter_lists_1833_1835.json` (the crosswalk
target) · T-0513 waits on this.


**Where it is.** Cached, in text, at `chicago/4d/data/research/genealogytrails/text/` — this
project's own committed copy, taken 2026-09-03. Do NOT re-fetch to read it; the cache is what a
later run has to be able to trust, and `tools/read_genealogytrails.py --fetch` is how it is
refreshed if it ever must be. `data/research/genealogytrails/inventory.json` is the grade and the
count this ticket was sized from, and `README.md` beside it says what the site is and is not.

**The shape.** T-0492 fixed it: a records file for a list, a claims file for prose, a closed kind
vocabulary, `reading: transcription_mediated` (nothing here is a scan read), a `coverage.json`
declaration for what was read, and a `crosswalk.json` whose refusals are written as carefully as
its merges — surname-only is always a refusal.

**The ladder.** The owner ratified it on 2026-09-03 and it binds this ticket: a source later than
1835 alone never makes an 1835 resident. It corroborates, it enriches, and above all it DATES.
Everything read here carries `describes_date`.
