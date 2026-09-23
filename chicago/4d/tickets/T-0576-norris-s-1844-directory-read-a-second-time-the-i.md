---
id: T-0576
title: Norris's 1844 directory read a second time: the independent Genealogy Trails transcription checked entry by entry against T-0566's 2,073, and every disagreement preserved
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0556
opened: 2026-09-03
closed: 2026-09-03
pr: 716
claimed_by: run 9/3/2026, 1:22:02 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-03T18:46:14.521Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33789742187
---

Norris's 1844 directory read a second time: the independent Genealogy Trails transcription checked entry by entry against T-0566's 2,073, and every disagreement preserved.

Piece 6 of 6 of **T-0556 — genealogytrails.com Cook County: inventory every section of the site, grade what it holds for 1835 Chicago, and split the extraction of residents, households, businesses, structures and occupations into tickets**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**The source, twice.** `text/1844directory.txt` and `text/1844dir2.txt` — Norris's *Chicago
Directory* for 1844 transcribed complete by Kim Torp, 1,972 entry-shaped lines over the two pages
plus the addenda. `data/research/directories/` already holds **2,073 entries** of the same book,
read by T-0566 (PR #704, 2026-09-03) off the Internet Archive scan `generaldirectory19norr`.

**Why a second reading is a run and not a waste.** These are two independent transcriptions of one
printed book, by different hands, from different copies. The repo already has the idiom and the
reason for it: `data/research/census_1840/second_readings/` exists because a reading nobody checked
is a reading nobody can weigh. Every place the two disagree is a name that was read twice — and the
disagreements are where the surnames this reconstruction gets wrong actually live, because the
entries most likely to differ are the ones hardest to read.

**What it must NOT become.** A re-import. Nothing here overwrites T-0566's entries: this ticket
produces a COMPARISON and preserves both readings, exactly as the census second readings do. Where
the two differ and neither is obviously right, both stand and the disagreement is the record.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)
- Every one of T-0566's 2,073 entries matched against the Genealogy Trails transcription, by a
  deterministic tool committed with the ticket, and the match rate stated as a number.
- Every disagreement preserved with BOTH readings verbatim and neither silently preferred; entries
  present in one transcription and absent from the other listed in both directions.
- The comparison declared in `coverage.json` so a later reader knows the check has been made and
  when; a note on any place where the addenda were handled differently by the two.
- No entry in `data/research/directories/` is deleted or rewritten by this ticket.

**Links:** parent T-0556 · T-0566 (the first reading) · `data/research/census_1840/second_readings/`
(the idiom) · T-0513 waits on this.


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
