---
id: T-0260
title: Reading the Democrat, part three: January to August 1835
state: split
epic: PAPERS
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-27
closed: 2026-08-28
pr: null
claimed_by: null
blocked_on: T-0257
needs_bake: false
---
An extraction pass over the Chicago Democrat January through August 1835 — the Jan 21 issue, the March 25 Extra, and the weekly run May 20 through August 26 (~20 issues). T-0257's schema and compiler exist; this ticket
READS, extracting every claim of these kinds into per-issue extraction files:

- **persons** — every named individual: advertisers, officials, jurors, meeting
  attendees, marriage/death notices, arrivals, AND THE POST-OFFICE LETTER LISTS
  IN FULL (ruling 1: a listed name mints a resident candidate; mark
  `letter_list_only`). Tedious is not optional — the lists are the census proxy.
- **businesses** — proprietor(s), trade, goods, the address text VERBATIM plus
  the placement class and anchor, the ad's own copy date, and any dissolution/
  removal/succession notice (ruling 3's veto lives here).
- **buildings** — to-let notices, new-building notices, raisings, fires,
  materials, storeys, "the building lately occupied by…" chains.
- **street & infrastructure details** — bridges, the pier, ferries, wharfing,
  street work, ordinances, the estray pen, pumps, wells, crossings.
- **events / shipping / prices** where they carry town texture worth a card.

The Jan-Jul validation notes flag: May 20 is conservatively marked uncertain
throughout (rebuilt crops, no final human pass); June 17 page 25 carries a
physical obstruction; **July 8 is PARTIAL — its fourth page is absent from the
source PDF**, and the extraction file must say so. The July 22 through August 26
issues are `.docx`-only — read them via T-0256's derived text.

## OCR judgment, bounded

The transcriptions interleave column fragments in places (two ads shuffled
line-by-line). Unshuffle by sense; record the result in `normalized` and keep
`quote` verbatim with its brackets. Correct only recognition-class errors the
context supports (the workflow's own rule: never fill a gap because a phrase
sounds likely). A reading you are not sure of stays inside `[uncertain: …]` in
normalized too — the marker is the honesty, do not launder it out.

THIS RANGE IS THE SCENE'S OWN EVIDENCE — closest to 1835-07-01 and heaviest
weight in the register. The issues AFTER July 1 still attest the scene date:
a business advertising on August 5 existed on July 1 unless its ad announces a
NEW opening — record `announces_opening: true` where the copy says so, because
T-0262 excludes those from the scene-date town.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- Every issue in the range has an extraction file, and `corpus.json` coverage
  for the range is asserted in the gate, not eyeballed.
- Letter lists are extracted IN FULL: for one sampled issue, the extracted count
  is checked against a hand count of the printed list and stated in the PR.
- Every claim passes the T-0257 gate (quote + locator + reading present,
  locators resolve).
- The gazetteer recompiles green; new merges all carry `merge_rule`.
- The PR states counts: claims, persons (letter-list vs corroborated),
  businesses, placements by class.
