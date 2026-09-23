---
id: T-0313
title: Reading the Democrat, April 1834: Vol. I Nos. 18-22
state: done
epic: PAPERS
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0258
opened: 2026-08-28
closed: 2026-08-28
pr: 484
claimed_by: run 8/28/2026, 5:36:15 PM CT
blocked_on: null
needs_bake: false
---

An extraction pass over the *Chicago Democrat* of April 1834 — Vol. I Nos. 18-22, 5 issues —
through the T-0257 schema, writing one `data/research/newspapers/extracted/<issue_id>.json`
per issue. Piece 6 of 8 of **T-0258 — Reading the Democrat, part one: November 1833 to
June 1834**, which was measured at seven runs and split on 2026-08-28. The parent keeps the
full ask; read it, because every kind of claim it enumerates and all three of the owner's
rulings apply here unchanged.

**The issues:**

- `chicago_democrat_1834_04_01` — 1834-04-01
- `chicago_democrat_1834_04_08` — 1834-04-08
- `chicago_democrat_1834_04_16` — 1834-04-16
- `chicago_democrat_1834_04_23` — 1834-04-23
- `chicago_democrat_1834_04_30` — 1834-04-30

**Transcription dialect:** ruled. 550,304 characters, 23,597 lines.

The biggest piece in the range by every measure — five issues, 550k characters, 23,597 lines, 160 column markers — and TWO letter lists (1834-04-23 and 1834-04-30). If any piece here turns out to be two runs it is this one; measure before claiming, and split at the letter lists rather than shipping half a list.

## What the parent asks for, and it is not weakened here

- **persons** — every named individual, AND THE POST-OFFICE LETTER LISTS IN FULL (ruling 1:
  a listed name mints a resident candidate; mark `letter_list_only`).
- **businesses** — proprietors, trade, goods, the address text VERBATIM plus the placement
  class and anchor, the ad's own copy date, and any dissolution/removal/succession notice.
- **buildings** — to-let notices, new-building notices, raisings, fires, materials, storeys,
  "the building lately occupied by…" chains.
- **street & infrastructure** — bridges, the pier, ferries, wharfing, street work,
  ordinances, the estray pen, pumps, wells, crossings.
- **events / shipping / prices** where they carry town texture worth a card.

This range is a year and a half before the scene date, in the town's fastest-changing
period, so WINDOWS MATTER: a business last seen here and not corroborated in 1835 stands
under ruling 3 with a survival liberty, and the window this pass records is what that
liberty cites.

## How to run the gate on `dev`

The deposit is on `main` (T-0275), so materialise a read-only copy of
`chicago/reference/newspapers/Transcriptions` and machine-check every quote before opening
the PR:

    python3 tools/compile_gazetteer.py --check --deposit <that copy>

`check.sh` on `dev` then counts these claims unresolved and reports them, which is green.

## The measurement this piece was sized on

Counted on 2026-08-28 over the deposit itself, per issue, across the whole of the parent's
thirty-issue range:

| piece | issues | characters | lines | column markers | letter lists |
|---|---|---|---|---|---|
| T-0308 November 1833 | 1 | 133,650 | 3,419 | 25 | 0 |
| T-0309 December 1833 | 5 | 653,071 | 16,659 | 120 | 0 |
| T-0310 January 1834 | 4 | 488,263 | 6,006 | 96 | 1 |
| T-0311 February 1834 | 4 | 465,667 | 15,040 | 96 | 1 |
| T-0312 March 1834 | 3 | 354,692 | 11,556 | 72 | 0 |
| T-0313 April 1834 | 5 | 550,304 | 23,597 | 160 | 2 |
| T-0314 May 1834 | 4 | 455,877 | 18,442 | 128 | 0 |
| T-0315 June 1834 | 4 | 454,800 | 16,859 | 96 | 0 |
| **parent total** | **30** | **3,556,324** | **111,578** | **793** | **4** |

The seam is the month, and the reason is the one T-0300 asked for in place of a feeling:
**T-0289 read five issues of July 1834 in one run and produced 129 claims, 298 people and
five extraction files.** Thirty issues at that rate is six to seven runs, and no month in
this range holds more than five issues. Standing advertisements and letter lists also run in
monthly cohorts, so a month is the unit where a run's second issue is cheaper than its first
— which is why T-0259 was cut this way and why cutting T-0258 differently would cost more.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- Every issue listed above has an extraction file, and `coverage.json` declares
  1834-04-01 to 1834-04-30 so the gate asserts the range rather than counting files.
- Any letter list in the range is extracted IN FULL, and the extracted count is checked
  against a hand count of the printed list and stated in the PR.
- Every claim passes the T-0257 gate — quote verbatim, `normalized` beside it, locator
  resolving to a real page and column, quotes reassembled character for character.
- The gazetteer recompiles green and any new merge carries a `merge_rule`.
- The PR states counts: claims, persons (letter-list vs corroborated), businesses,
  placements by class.
