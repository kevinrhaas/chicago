---
id: T-0297
title: Reading the Democrat, August 1835: the four issues after the scene date
state: split
epic: PAPERS
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: T-0260
opened: 2026-08-28
closed: 2026-08-28
pr: null
claimed_by: run 8/28/2026, 7:51:49 PM CT
blocked_on: null
needs_bake: false
---

The four Democrats after the scene date: **1835-08-05** (Vol. II No. 16), **08-12**
(No. 17), **08-19** (No. 18) and **08-26** (No. 19) — the paper's last month in the
corpus. Piece 3 of 4 of **T-0260**.

All four are `.docx`-only primaries whose derived text is committed under `text/`, so
this is the one piece of the parent where **every** quote is machine-verified on `dev`
with no deposit at all. `corpus.json` records the August Democrat tail as single-pass
OCR — weight a reading by the batch it came from.

## What the parent asks for, and it is unchanged here

Every claim of these kinds, into `data/research/newspapers/extracted/<issue_id>.json`:

- **persons** — every named individual: advertisers, officials, jurors, meeting
  attendees, marriage/death notices, arrivals, AND THE POST-OFFICE LETTER LISTS IN
  FULL (ruling 1: a listed name mints a resident candidate; mark `letter_list_only`).
- **businesses** — proprietor(s), trade, goods, the address text VERBATIM plus the
  placement class and anchor, the ad's own copy date, and any dissolution / removal /
  succession notice (ruling 3's veto lives here).
- **buildings** — to-let notices, new-building notices, raisings, fires, materials,
  storeys, "the building lately occupied by…" chains.
- **street & infrastructure details** — bridges, the pier, ferries, wharfing, street
  work, ordinances, the estray pen, pumps, wells, crossings.
- **events / shipping / prices** where they carry town texture worth a card.

## OCR judgment, bounded

The transcriptions interleave column fragments — two physical columns woven line by
line is the NORMAL case here, not an exception. Unshuffle by sense; record the result
in `normalized` and keep `quote` verbatim with its brackets, which is machine-checked.
Correct only recognition-class errors the context supports. A reading you are not sure
of stays inside `[uncertain: …]` in normalized too.


The owner's three rulings, 2026-08-28, govern every ticket in this epic and are not
restated in full here — `tools/compile_gazetteer.py`'s header carries them, and each
one lives in a field rather than in prose: `letter_list_only` on a person, a required
`reading` flag on every claim, and a computed `built_at_scene_date` /
`survival_liberty_required` on a business.

## Why the parent was split into four, measured on 2026-08-28

The parent's range is **seventeen** issues, and they are not one kind of work:

| | issues | readable on `dev` | marker dialect |
|---|---|---|---|
| January–June 1835 | 8 | **no** — deposit-held, and the deposit is on `main` (T-0275) | two dialects the compiler cannot resolve |
| July 1835 | 5 | yes | both spoken dialects |
| August 1835 | 4 | yes | the heading dialect |

And the scene-date issue of 1835-07-01 is its own piece because of what is IN it: a
Chicago post-office letter list of some six hundred names — the census proxy ruling 1
turns on — woven line by line through the advertising columns. Reading that list is a
run on its own, and it is the single most heavily weighted issue in the epic, so it
does not belong in a batch where it would be hurried.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- All four issues have an extraction file, and coverage of 1835-08-01 to 1835-08-31 is
  asserted BY THE GATE against `corpus.json`.
- Because all four texts resolve on `dev`, every quote in this piece is reassembled by
  the gate — no claim in it may be left unresolved.
- Letter lists extracted in full where legible at name level, the post office carried,
  and a sampled hand count stated in the PR.
- An August advertisement that announces a NEW opening carries `announces_opening:
  true`, so T-0262 can keep it out of the July 1 town.
- The gazetteer recompiles green; new merges all carry `merge_rule`.
- The PR states counts: claims, persons (letter-list vs corroborated), businesses,
  placements by class.
