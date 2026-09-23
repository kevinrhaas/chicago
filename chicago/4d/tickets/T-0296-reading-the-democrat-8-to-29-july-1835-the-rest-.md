---
id: T-0296
title: Reading the Democrat, 8 to 29 July 1835: the rest of the scene month
state: done
epic: PAPERS
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: T-0260
opened: 2026-08-28
closed: 2026-08-28
pr: 495
claimed_by: run 8/28/2026, 7:53:13 PM CT
blocked_on: null
needs_bake: false
---

The rest of the scene month: **1835-07-08** (Vol. II No. 12, PARTIAL — its fourth page
is absent from the source PDF, and the extraction file must say so), **07-15** (No. 13),
**07-22** (No. 14) and **07-29** (No. 15). Piece 2 of 4 of **T-0260**.

An advertisement in these four still attests the scene date — a business advertising on
July 29 existed on July 1 — unless its copy announces a NEW opening. Record
`announces_opening: true` where it does, because T-0262 excludes those from the July 1
town.

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

### What each issue is read from

- **07-08** — the reconciled deposit `.txt` (`primary`), on `main`; supported dialect,
  so verify under `--deposit`.
- **07-15**, **07-22**, **07-29** — the committed derived text under `text/`, which
  resolves on `dev`, so the gate reassembles those quotes here.
- **07-15 is a sole witness and the worst text in the range**: the `-2` rebuild, whose
  own QA note records a median cross-pass agreement of 4 per cent. Its Chicago
  post-office list is not legible at name level. Say so on the record; do not mint a
  person out of `Anderenn, EB, Rebas, Fuerst`.
- These issues also carry the **Hennepin, Plainfield, DuPage and Juliet** post-office
  lists, which are legible. A name on one of those does NOT mint a Chicago resident —
  carry the office on the claim.

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

- All four issues have an extraction file, and coverage of 1835-07-08 to 1835-07-29 is
  asserted BY THE GATE against `corpus.json`.
- Letter lists extracted in full where the transcription is legible at name level, with
  the post office carried on the claim and a sampled hand count stated in the PR. Where
  a list is not legible at name level it is recorded as a claim with its verbatim text
  and a note saying so — a mush name is not a resident.
- Every claim passes the T-0257 gate, quotes reassembled character for character
  (`--deposit` for 07-08).
- The gazetteer recompiles green; new merges all carry `merge_rule`.
- The PR states counts: claims, persons (letter-list vs corroborated), businesses,
  placements by class.
