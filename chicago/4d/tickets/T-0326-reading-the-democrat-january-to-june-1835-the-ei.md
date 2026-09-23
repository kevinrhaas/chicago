---
id: T-0326
title: Reading the Democrat, January to June 1835: the eight issues, now that their columns resolve
state: done
epic: PAPERS
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: T-0298
opened: 2026-08-28
closed: 2026-08-28
pr: 504
claimed_by: run 8/28/2026, 10:16:04 PM CT
blocked_on: null
needs_bake: false
---

The eight Democrats before the scene month: **1835-01-21** (Vol. II No. 5), the
**03-25 Extra**, **05-20**, **05-27**, **06-04**, **06-10**, **06-17** and **06-24**.
Piece 2 of 2 of **T-0298**, and piece 4 of 4 of **T-0260**.

**The resolver block is gone.** T-0325 taught `column_starts()` the two dialects these
issues speak, and all eight now resolve their columns — 118 markers that were invisible.
Cite them exactly as every other read in this epic does.

**The other block is gone too, and nobody had noticed.** T-0298 was `blocked_on: T-0275`
because all eight are deposit-held `.txt` with no derived alternate and the deposit was on
`main` only. The promotion back-merge has since carried `chicago/reference/` onto `dev`:
checked file by file on 2026-08-29, all 178 recorded paths and sha256s in `corpus.json`
resolve and match on this branch, `tools/newspaper_corpus.py --check` says `deposit
present`, and the gate reassembles all 713 committed quotes here. **So this pass needs no
`--deposit` and no materialised copy** — unlike T-0289, T-0290, T-0291, T-0292, T-0293,
T-0308, T-0309, T-0310, T-0311 and T-0313, every one of which had to. T-0275 itself is
still open and asks for exactly the back-merge that happened; read its row before doing
the work again.

**One page needs its reading stated.** Page 4 of the 03-25 Extra is Calhoun's own
subscription list — a single-column prospectus, resolved as that page's column 1 — and it
names people. Read it as the letter lists are read.

## What the parent asks for, and it is unchanged here

Every claim of these kinds, into `data/research/newspapers/extracted/<issue_id>.json`:

- **persons** — every named individual: advertisers, officials, jurors, meeting
  attendees, marriage/death notices, arrivals, AND THE POST-OFFICE LETTER LISTS IN
  FULL (ruling 1: a listed name mints a resident candidate; mark `letter_list_only`).
  Sweep for a list by READING the columns, not by searching them — T-0313 is why.
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

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- All eight issues have an extraction file, and coverage of the range is asserted BY
  THE GATE against `corpus.json`.
- Every claim passes the T-0257 gate, quotes reassembled character for character
  (`--deposit` against a materialised copy of the deposit).
- The gazetteer recompiles green; new merges all carry `merge_rule`.
- The PR states counts: claims, persons (letter-list vs corroborated), businesses,
  placements by class.
