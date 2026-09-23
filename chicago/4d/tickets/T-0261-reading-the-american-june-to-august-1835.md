---
id: T-0261
title: Reading the American: June to August 1835
state: done
epic: PAPERS
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-27
closed: 2026-08-28
pr: 472
claimed_by: null
blocked_on: T-0257
needs_bake: false
---
An extraction pass over the Chicago American complete — 1835-06-08 (Vol I No 1) through 1835-08-29, thirteen issues. T-0257's schema and compiler exist; this ticket
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

All thirteen are `.docx`-only — T-0256's derived text is the reading copy. A
SECOND paper in the same eleven weeks is cross-examination: the same business
advertising in both papers is the strongest documentation this corpus can give,
and a person in one paper's list and the other's news is a corroboration
ruling 1 makes optional but the gazetteer still records.

## OCR judgment, bounded

The transcriptions interleave column fragments in places (two ads shuffled
line-by-line). Unshuffle by sense; record the result in `normalized` and keep
`quote` verbatim with its brackets. Correct only recognition-class errors the
context supports (the workflow's own rule: never fill a gap because a phrase
sounds likely). A reading you are not sure of stays inside `[uncertain: …]` in
normalized too — the marker is the honesty, do not launder it out.

The American's own establishment is itself a scene-date fact: a second
newspaper office operating in the town from June 8, with premises the paper
self-reports — extract its imprint line every issue like any other business.

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
