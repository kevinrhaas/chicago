---
id: T-0258
title: Reading the Democrat, part one: November 1833 to June 1834
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
An extraction pass over the Chicago Democrat's first thirty issues — 1833-11-26 (Vol I No 1) through 1834-06-25 (No 30). T-0257's schema and compiler exist; this ticket
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

All thirty have committed `.txt` transcriptions. The repo already holds a
scan-verified record of the FIRST issue (`chicago_democrat_1833_11_26.json`)
whose `what_it_supplies` names ~24 findings — Carpenter, C. & I. Harmon,
W. Kimball, Cohen at the EAST end of South Water, Goss & Cobb at Lake and
Canal, Ingersoll's tavern, the November 1833 village ordinances, exactly two
plank bridges. Extract that issue THROUGH the schema like every other, but
where the scan-verified record disagrees with the transcription, THE SCAN RECORD
WINS and the claim says so (ruling 2's upgrade path, run backwards).

## OCR judgment, bounded

The transcriptions interleave column fragments in places (two ads shuffled
line-by-line). Unshuffle by sense; record the result in `normalized` and keep
`quote` verbatim with its brackets. Correct only recognition-class errors the
context supports (the workflow's own rule: never fill a gap because a phrase
sounds likely). A reading you are not sure of stays inside `[uncertain: …]` in
normalized too — the marker is the honesty, do not launder it out.

This range is nineteen-plus months before the scene date — the town's
fastest-changing period. Windows matter more here than anywhere: an 1833 ad
with no 1835 corroboration will be built under ruling 3 WITH a survival
liberty, so the window this pass records is what that liberty will cite.

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
