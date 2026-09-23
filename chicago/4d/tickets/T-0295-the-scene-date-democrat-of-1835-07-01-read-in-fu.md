---
id: T-0295
title: The scene-date Democrat of 1835-07-01, read in full
state: done
epic: PAPERS
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: T-0260
opened: 2026-08-28
closed: 2026-08-28
pr: 468
claimed_by: run 8/28/2026, 10:54:48 AM CT
blocked_on: null
needs_bake: false
---

**Chicago Democrat, Wednesday 1835-07-01, Vol. II No. 11** — the issue printed on the
scene date. Piece 1 of 4 of **T-0260 — Reading the Democrat, part three**.

T-0257 left three worked claims in `extracted/chicago_democrat_1835_07_01.json` — Peter
Cohen, J. S. C. Hogan, one letter-list name — as the fixture the schema was written
against. This ticket READS THE REST OF THE ISSUE.

Nothing in the epic outranks this issue. It is the only Democrat printed on the scene
date, so where it and another issue disagree about a storefront, this one wins, and
T-0262's July 1 register is built on it first.

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

### What it is read from

The **reconciled deposit `.txt`** (`artifact_role: primary`), which is on `main` and not
on `dev` (T-0275). It is markedly better than the `-2` rebuild that `dev` can open — the
letter list is legible at name level in the primary and is not in the alternate — and it
speaks the `===== ISSUE PAGE n / PDF PAGE m / COLUMN k OF 6 =====` dialect the compiler
already reads. So verify with `--check --deposit <materialised deposit>`, where every
quote is machine-reassembled, and expect the committed gate on `dev` to report those
claims unresolved-but-green until T-0275 lands.

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

- The Chicago post-office letter list of 1835-06-30 is extracted IN FULL: every name in
  it reaches the gazetteer as a person carrying `letter_list_only`, and the count is
  checked against a hand count of the printed list and stated in the PR.
- The issue's advertisements are claims, each with its placement class, its anchor and
  the paper's own offset text verbatim where it has one, and its `ad_copy_date`.
- The issue's town-bearing local matter is claimed: the reception of the Secretary of
  War, the ward and school-district meetings and their named delegates, the corner
  stone of the new Baptist meeting house, the land-office sale, the vessel list.
- Every claim passes the T-0257 gate, and every quote is reassembled character for
  character under `--deposit`. Say in the PR that it was run that way.
- Coverage of 1835-07-01 is asserted BY THE GATE against `corpus.json`, not eyeballed.
- The gazetteer recompiles green; new merges all carry `merge_rule`.
- The PR states counts: claims, persons (letter-list vs corroborated), businesses,
  placements by class.
