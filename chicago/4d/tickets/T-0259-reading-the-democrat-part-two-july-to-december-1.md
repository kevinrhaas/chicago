---
id: T-0259
title: Reading the Democrat, part two: July to December 1834
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
claimed_by: run 8/28/2026, 10:44:41 AM CT
blocked_on: T-0257
needs_bake: false
---
An extraction pass over the Chicago Democrat July through December 1834 — Vol I No 31 (1834-07-02) through Vol II No 4 (1834-12-24), ~26 issues. T-0257's schema and compiler exist; this ticket
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

All have committed `.txt` transcriptions and the 1834 manifest + validation
notes cover them.

## OCR judgment, bounded

The transcriptions interleave column fragments in places (two ads shuffled
line-by-line). Unshuffle by sense; record the result in `normalized` and keep
`quote` verbatim with its brackets. Correct only recognition-class errors the
context supports (the workflow's own rule: never fill a gap because a phrase
sounds likely). A reading you are not sure of stays inside `[uncertain: …]` in
normalized too — the marker is the honesty, do not launder it out.

This is the year the town incorporates growth the papers narrate weekly —
watch for businesses MOVING (a second address for a known name is a move or a
branch, never a silent overwrite; both mentions stand with their dates).

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

## Split, 2026-08-28 — measured, not guessed

Claimed as one `M` run. The run read the first issue, 1834-07-02, before committing to
the whole range and found the shape of the work: six segmenter columns per page with two
of them alternating line by line through nearly every advertising column, so a single
advertisement survives as two cut halves in two different columns and has to be
reassembled from both. One issue carries on the order of forty claims across four dense
pages. Twenty-six issues of that is not one demonstration.

Split into six monthly pieces — T-0289 (July) through T-0294 (December) — which hold
this ticket's exact place in QUEUE.md. Months are the seam because the standing
advertisements and the post-office letter lists run in monthly cohorts: a run that reads
one month carries the context of every ad in it. The rulings, the OCR-judgment rule and
the acceptance clause are carried into each child verbatim.

The same measurement applies to T-0258 and T-0260, which were sized the same way and are
not this ticket's to re-size.
