---
id: T-0057
title: Ordinance 9's other half: timber, stone and brick stacked on the lots that were building
state: done
epic: TOWN
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-18
closed: 2026-08-23
pr: 325
claimed_by: run 8/23/2026, 6:05:00 AM CT
blocked_on: null
needs_bake: false
---

Ordinance 9's other half: timber, stone and brick stacked on the lots that were building.

Opened by T-0040, which shipped the *boxes and barrels* half of Ordinance 9 and refused the
rest in writing.

The village ordinance of 7 November 1833 (`data/sources/chicago_democrat_1833_11_26.json`,
tier 1) names **timber, stone, brick, boxes and barrels** stacked in the streets. T-0040 drew
the merchant's stock — casks and cases on the footway at the taverns and the stores, on the rule
in `tools/generate_yard_goods.py` — and deliberately left the other three out, because they are
a different claim: **timber, stone and brick are building material on a lot that is going up**,
not a trader's goods on his own frontage, and `data/yard/town_trade_goods.json` has no way to
say which lot was building in the week of 1 July 1835.

That is the question this ticket has to answer before it can place anything: **what does this
dataset know about which buildings were under construction on the scene date?** The Tremont's
successor, the hotel recorded `hotel_under_construction`, and the block programme's own dates
are the places to look; `documented_range.from` on a record whose year is 1835 is the nearest
thing to a start date the dataset carries, and for the 262 anonymous infill records it is a
programme date and not a construction date (L126 says so), which is exactly the trap.

**Acceptance:** stacked timber, stone or brick stands on the lot of at least one building this
dataset can say was going up on the scene date, chosen by a rule with its clauses stated and
re-derived by `tools/check.sh` like the goods are, graded `reconstructed` with its own
`docs/LIBERTIES.md` entry, and visible in the walkthrough at both release viewports. If the
honest answer turns out to be that no record supports a construction date, the ticket closes
by SAYING so with the census behind it — the negative finding is the deliverable then, and
`block --owner` is not the exit, because a missing number is not the owner's call.

Links: `docs/ROADMAP.md` K5 (c) · `docs/LIBERTIES.md` L131 · T-0040 (the half that shipped).
