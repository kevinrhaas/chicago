---
id: T-0298
title: Reading the Democrat, January to June 1835: the eight issues only the deposit can open
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
claimed_by: run 8/28/2026, 7:53:55 PM CT
blocked_on: T-0275
needs_bake: false
---

The eight Democrats before the scene month: **1835-01-21** (Vol. II No. 5), the
**03-25 Extra**, **05-20**, **05-27**, **06-04**, **06-10**, **06-17** and **06-24**.
Piece 4 of 4 of **T-0260**.

**This piece is blocked twice, and both blocks are measured, not suspected.**

1. **The text is not on `dev`.** All eight are deposit-held `.txt` with no derived
   alternate, so `chicago/reference/newspapers/` has to be on this branch before a
   single one can be opened. That is **T-0275**, itself waiting on the owner confirming
   sixty Finder-duplicate files on `main` are junk.
2. **Three marker dialects, and `tools/compile_gazetteer.py` speaks one of them.**
   Checked file by file on 2026-08-28:

   | issues | markers |
   |---|---|
   | 01-21, 03-25 Extra, 05-20 | `[Source PDF page 9; newspaper page 1; column 1]` |
   | 05-27, 06-04, 06-10 | bare `=====` rules carrying no page or column at all |
   | 06-17, 06-24 | `===== ISSUE PAGE 1 / PDF PAGE 25 / COLUMN 1 OF 6 =====` — the one the compiler reads |

   `column_span()` returns None for the first two groups, so every claim citing those
   six issues fails the gate with "the transcription carries no ISSUE PAGE / COLUMN
   marker". The three with bare rules may be a transcription defect rather than a
   resolver gap, and that is the question to answer before reading.

Do the resolver work first, in its own change, and read afterwards.

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

- `chicago/reference/newspapers/` is on the branch (T-0275 merged) and
  `tools/compile_gazetteer.py --check` resolves all eight texts.
- `column_starts()` reads the bracket dialect, its self-test covers it, and the three
  issues with bare rules either resolve or are recorded as uncitable with the reason.
- All eight issues have an extraction file, and coverage of the range is asserted BY
  THE GATE against `corpus.json`.
- Every claim passes the T-0257 gate, quotes reassembled character for character.
- The gazetteer recompiles green; new merges all carry `merge_rule`.
- The PR states counts: claims, persons (letter-list vs corroborated), businesses,
  placements by class.
