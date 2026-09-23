---
id: T-0292
title: Reading the Democrat, October 1834: Vol I Nos 44-48
state: done
epic: PAPERS
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: T-0259
opened: 2026-08-28
closed: 2026-08-28
pr: 476
claimed_by: run 8/28/2026, 12:49:13 PM CT
blocked_on: null
needs_bake: false
---

An extraction pass over the Chicago Democrat for October 1834 — 5 issues: 1834-10-01 (Vol I No 44), 1834-10-08 (No 45), 1834-10-15 (No 46), 1834-10-22 (No 47), 1834-10-29 (No 48).
T-0257's schema, compiler and gate exist; this ticket READS, extracting every claim of
these kinds into per-issue extraction files under
`data/research/newspapers/extracted/`:

- **persons** — every named individual: advertisers, officials, jurors, meeting
  attendees, marriage/death notices, arrivals, AND THE POST-OFFICE LETTER LISTS IN FULL
  (ruling 1: a listed name mints a resident candidate; mark `letter_list_only`). For
  this month, the post-office list of letters remaining at Chicago on 1 October 1834; a survey found list matter in Nos 45, 46, 47 and 48, and which issues carry the whole list is for the reading to settle.
- **businesses** — proprietor(s), trade, goods, the address text VERBATIM plus the
  placement class and anchor, the ad's own copy date, and any dissolution / removal /
  succession notice (ruling 3's veto lives here).
- **buildings** — to-let notices, new-building notices, raisings, fires, materials,
  storeys, "the building lately occupied by…" chains.
- **street & infrastructure details** — bridges, the pier, ferries, wharfing, street
  work, ordinances, the estray pen, pumps, wells, crossings.
- **events / shipping / prices** where they carry town texture worth a card.

Piece 4 of 6 of **T-0259 — Reading the Democrat, part two: July to December 1834**.
The parent keeps the full ask, the owner's three rulings and its links; this ticket owns
one month of it.

## Why the parent was split, measured rather than guessed

T-0259 was sized `M` — one run. A run that claimed it on 2026-08-28 read the first
issue, 1834-07-02, and measured the shape of the work before committing to it: this
batch is segmented into six physical columns per page and the segmenter alternates two
of them line by line through nearly every advertising column, so **each advertisement
survives as two cut halves in two different segmenter columns** (page 3 column 5 and
column 6 of 1834-07-02 are one such pair). A single issue carries on the order of forty
claims and four dense pages of it have to be read to find them. Twenty-six issues of
that is not one demonstration; it is six. The months are the split because the standing
advertisements, and the letter lists, run in monthly cohorts — a run that reads one
month carries the context of every ad in it.

## OCR judgment, bounded — the parent's rule, unchanged

Unshuffle interleaved columns by sense; record the result in `normalized` and keep
`quote` verbatim with its brackets. Correct only recognition-class errors the context
supports. Never fill a gap because a phrase sounds likely: `[…]` marks absence, `[word]`
marks a supply. A reading you are not sure of stays inside `[uncertain: …]` in
`normalized` too — the marker is the honesty, do not launder it out. A business seen at
a second address is a move or a branch, never a silent overwrite; both mentions stand
with their dates.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- Every issue in October 1834 has an extraction file, and that coverage is asserted in the
  gate rather than eyeballed.
- Where the month carries a letter list, it is extracted IN FULL, and for one sampled
  issue the extracted count is checked against a hand count of the printed list and
  stated in the PR.
- Every claim passes the T-0257 gate: quote reassembled from the transcription
  character for character, locator inside its own page and column, `reading` present.
- The gazetteer recompiles green; any new merge carries a `merge_rule`.
- The PR states counts: claims, persons (letter-list-only vs corroborated), businesses,
  placements by class.

The deposit is on `main` and not on `dev` (T-0275), so the quote check runs here with
`tools/compile_gazetteer.py --check --deposit <path>` against a read-only copy of the
deposit; on `dev` those claims are counted and reported unresolved, which is green.
