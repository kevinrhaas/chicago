---
id: T-0574
title: Fergus's 743 old-settler death notices from the 1843 directory: ages at death read as birth years and crosswalked to attested residents
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0556
opened: 2026-09-03
closed: 2026-09-03
pr: 718
claimed_by: run 9/3/2026, 1:20:58 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-03T19:04:47.161Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33789725815
---

Fergus's 743 old-settler death notices from the 1843 directory: ages at death read as birth years and crosswalked to attested residents.

Piece 4 of 6 of **T-0556 — genealogytrails.com Cook County: inventory every section of the site, grade what it holds for 1835 Chicago, and split the extraction of residents, households, businesses, structures and occupations into tickets**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**The source.** `text/earlysettlerobits.txt` — 743 entry-shaped lines. Fergus's list of the deaths
of Chicago's old settlers as printed in the 1843 directory (Fergus Printing Company reprint, 1896),
transcribed by K. Torp, 2007. Entries read like `Allen, Col. James, U. S. Army, died, Fort
Leavenworth, Kansas, August 23, 1846, aged 40` — name, often a trade or a title, place of death,
date, and an age.

**Why it is worth a run.** An age at death is a birth year, and the resident layer is shorter of
birth years than of names. Lt. James Allen, in that very entry, is the first name on the 1833
Chicago tax list.

**A trap, stated before the work starts.** The list's own header says it names "some of Chicago's
Old Settlers, prior to 1843, **and other well-known citizens who arrived after 1843**". So presence
in this list does NOT establish arrival before 1843, let alone residence in 1835, and no merge may
use it that way.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)
- All 743 entries read, with the age preserved AS PRINTED (`a. 89½`, `aged 82-2-15`) beside any
  derived birth year, and the derivation marked `inferred` with its arithmetic stated.
- A crosswalk to attested 1833-1835 residents, merges with rules, refusals named; the header's
  admission is quoted on the crosswalk itself so the next reader cannot miss it.
- `describes_date` reflects the DEATH date, not the settlement date, and the distinction is written
  down.

**Links:** parent T-0556 · T-0554 (the Calumet Club receptions and the Fergus reception lists — the
same genre, a different list; read them beside each other and say how they disagree) · T-0513 waits
on this.


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
