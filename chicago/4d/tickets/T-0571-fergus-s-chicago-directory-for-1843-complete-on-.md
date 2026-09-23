---
id: T-0571
title: Fergus's Chicago directory for 1843, complete on Genealogy Trails: 2,427 entries of name, trade and street, read into the directories domain and date-flagged as later evidence
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0556
opened: 2026-09-03
closed: 2026-09-03
pr: 714
claimed_by: run 9/3/2026, 12:53:28 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-03T18:08:11.313Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33783236430
---

Fergus's Chicago directory for 1843, complete on Genealogy Trails: 2,427 entries of name, trade and street, read into the directories domain and date-flagged as later evidence.

Piece 1 of 6 of **T-0556 — genealogytrails.com Cook County: inventory every section of the site, grade what it holds for 1835 Chicago, and split the extraction of residents, households, businesses, structures and occupations into tickets**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**The source.** `text/1843directory_1.txt` (businesses), `_2` (residents A-G), `_3` (H-O), `_4`
(P-Z) — the four pages of Robert Fergus's *Directory of the City of Chicago, Illinois for 1843*,
transcribed complete. 2,427 entry-shaped lines counted: 84 + 916 + 726 + 701. Most entries carry a
name, a trade and a street.

**Why it is worth a run.** It is the earliest complete Chicago directory available to this project,
and the only one of the three on this site that nobody owns. Eight years after the scene, so no
entry is an 1835 fact — but a man who signs the 1834 poll list and appears in 1843 as a cooper on
Kinzie Street has a trade and a street the reconstruction can use, and the resident layer is short
of exactly that. T-0566 has just done the same job for Norris's 1844: follow its file shapes rather
than inventing new ones, and the two directories become a series instead of two dialects.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)
- Every one of the four pages read into `data/research/directories/`, entry by entry, with the text
  verbatim and the normalisation beside it; the count matches the count declared in
  `coverage.json`, and a hole in a declared page fails the gate.
- A crosswalk that names every merge to an attested 1833-1835 person WITH ITS RULE, and refuses the
  rest by name. Surname-only is a refusal.
- `describes_date: "1843"` on everything. No resident record changes state in this ticket.
- A source record for Fergus 1843 that cites the printed directory and says this project has seen
  the Genealogy Trails republication, not the original.

**Links:** parent T-0556 · T-0566 (Norris 1844, done — the pattern to follow) · T-0506 (the 1839) ·
`data/sources/fergus_chicago_directory_1843.json`, which the repo carries and has never extracted ·
T-0513 waits on this.


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
