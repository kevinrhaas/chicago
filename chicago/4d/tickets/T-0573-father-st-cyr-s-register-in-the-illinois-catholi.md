---
id: T-0573
title: Father St. Cyr's register in the Illinois Catholic Historical Review: 87 marriages of 1834-1839 with their witnesses named, and the nine deaths of 1834-1836
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0556
opened: 2026-09-03
closed: 2026-09-03
pr: 719
claimed_by: run 9/3/2026, 1:23:14 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-03T18:59:21.472Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33789717786
---

Father St. Cyr's register in the Illinois Catholic Historical Review: 87 marriages of 1834-1839 with their witnesses named, and the nine deaths of 1834-1836.

Piece 3 of 6 of **T-0556 — genealogytrails.com Cook County: inventory every section of the site, grade what it holds for 1835 Chicago, and split the extraction of residents, households, businesses, structures and occupations into tickets**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**The source.** Two pages, both printing Father J. M. I. St. Cyr's register out of the *Illinois
Catholic Historical Review*, vol. 4 (July 1921 - April 1922):
`text/marriages_catholic.txt` — 87 dated marriages, ALL of them 1834-1839 (1834:4, **1835:6**,
1836:8, 1837:36, 1838:21, 1839:12), each with date, groom, bride, the witnesses BY NAME and the
priest; and `text/church_catholicdeaths.txt` — nine deaths and burials, June 1834 to July 1836.

**Why it is worth a run.** Six marriages fall in the scene year and each names its witnesses: those
are people standing in Chicago on a named day of 1835, which is the strongest kind of presence
evidence this project can get short of a census. The death page carries the death of Thomas Owen,
agent of the Indians, at Chicago on 15 October 1835.

**Two traps, stated before the work starts.** (1) The register is not all Chicago — a footnote says
three couples of May 1834 were married at Bear Creek, Sangamon County, and a reader who takes the
whole page as a Chicago roll plants three households in the wrong town. The footnotes travel with
the entries and must be read with them. (2) `Mark Bourassa` marries in March 1835 and `Leon
Bourrassa` buries an infant son in July 1835; they are not joined here and may not be joined
without a stated rule.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)
- All 87 marriages and all nine deaths in `data/research/church/records/`, with witnesses as their
  own named entities and the footnotes carried onto the entries they qualify.
- The Bear Creek three flagged as NOT Chicago on the record itself, not in a note somewhere else.
- The 1835 entries crosswalked to attested residents, each merge with a rule, each refusal named.
- `gt_001` and `gt_002` in `data/research/genealogytrails/claims/` are the two findings this
  assessment already filed; supersede them properly rather than duplicating them.

**Links:** parent T-0556 · T-0503 (St Mary's BAPTISMAL register, from images — a different record
of the same parish) · `data/sources/catholic_chicago_st_cyr_1833.json` · T-0513 waits on this.


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
