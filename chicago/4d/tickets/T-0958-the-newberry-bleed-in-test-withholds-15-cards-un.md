---
id: T-0958
title: The Newberry bleed-in test withholds 15 cards under a 15-character run and 43 under a unique-prefix run: one corpus, two rules, and only one is on dev
state: withdrawn
epic: PAPERS
requested_by: steward
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-07
closed: 2026-09-17
pr: null
claimed_by: null
blocked_on: folded into T-1291
needs_bake: false
closed_at: 2026-09-17T19:18:47.549Z
claimed_run: null
---

`#1003` and `#1002` both answer T-0769 — a Newberry card body that OPENS with the tail of
the card in the column to its left, so a locality is matched on ink that is not on the card.
#1003 merged; #1002 was parked under `hold` and is closed by T-0930 with its measurement
carried here.

**They are not the same test, and they do not find the same cards.**

| | on `dev` (#1003, T-0769) | on `#1002`'s branch |
|---|---|---|
| the rule | a byte-exact run of **15 characters** | a byte-exact run that is the **unique** prefix of no other body in the four volumes |
| candidates found | 15 | **47** |
| withheld (no locality of their own) | **15** | **43** |
| vol. 01 records carrying `bled_in_from` | **0** | **26** |
| the delta profile | not stated as a control | **every one at column delta +1**, none at any other delta |

**The branch's control is the part `dev` does not hold.** Delta is the crop geometry's own
prediction: a column can only bleed into the column on its right, so a real artefact must sit
at +1 and cannot sit at 0. Under the uniqueness rule the branch finds 47, all at +1, and 0 at
delta 0. Drop the uniqueness clause and it finds 113, **three of them at delta 0, where the
artefact is impossible** — so the channel that should be empty is populated exactly when the
rule is loosened. That is an argument for the rule, and it is the argument `dev`'s fifteen do
not make.

Length alone will not carry it, which is why: six byte-exact characters finds 113 candidates
and most are a common formula — `Chicago,` opens **519** bodies in this corpus, `Illinois`
285, `Cook Co.` 274.

**What `dev` holds that the branch does not.** `dev`'s README states the fifteen per volume
(10, 2, 3) and folds them into `cards = records − slivers − bled_in_bodies`, and it settles
`nbi_v02_0610`, the row T-0601 had recorded as a sliver. The branch reaches the same verdict
on that row by a different route. `dev` is also the tree the precision sample was
adjudicated against.

**Why it matters.** 15 and 43 are not a rounding difference — they are 28 cards whose only
locality is borrowed and which are either in the counts or out of them. `by_locality`, the
leads and the reading order all read off that set. The branch's vol. 01 alone marks 26 where
`dev` marks 0 in that volume.

**Acceptance**

1. The two rules are run against the same corpus on today's `dev` and the difference is
   itemised — the 28 cards one holds and the other does not, listed by id.
2. The delta control is run on `dev`'s rule as well. If `dev`'s fifteen also sit wholly at
   +1, the branch's uniqueness clause buys precision and not soundness, and the ticket says
   so; if `dev`'s rule admits a delta-0 card, that is a defect in force.
3. Whichever rule wins, the README's per-volume table, `coverage.json` and the `cards`
   arithmetic move with it in one commit.
4. A card is marked, never trimmed, either way — `MANIFEST.text_sha256` refuses an edited
   reading and that is not reopened here.
