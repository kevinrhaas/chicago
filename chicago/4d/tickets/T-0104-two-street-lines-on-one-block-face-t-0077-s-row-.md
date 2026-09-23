---
id: T-0104
title: Two street lines on one block face: T-0077's row stands 0.80 m off and the block generator's floor is 1.50 m
state: done
epic: TOWN
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-19
closed: 2026-08-24
pr: 359
claimed_by: run 8/24/2026, 6:25:13 AM CT
blocked_on: null
needs_bake: false
---

One block face carries two street lines, and they are 0.70 m apart.

Found by T-0079 while standing a party-line run on the Lake face of `blk_lake_clark`. Two
generators put rows on that one face and they disagree about where the street wall is:
`tools/generate_inferred_infill.py` (T-0077) stands its four units 0.80 m off the face line, and
`tools/generate_block_infill.py` cannot go closer than `LOT_MARGIN_M` = 1.50 m, which is the plat
module's own lot margin and is asserted by `check_frontage`. So the same face has a row at 0.80 m
and a row at 1.50 m.

**It does not read as a step today** and that is luck rather than design: the two runs are 10.58 m
apart along the face (T-0079's run ends at 18.36 m, `inf_bakery_lake` begins at 28.93 m), so no
wall meets another wall at the wrong offset. A later parcel that closes that gap would produce a
visible 0.70 m jog in a street wall the whole project describes as one line.

**The question is which number is right**, and it is not obviously 1.50: the margin is a rule about
standing clear of a LOT line, and a party-line row deliberately crosses its own side lot lines
already. The three routes are (a) move T-0077's row out to 1.50 m, which moves four committed
records; (b) let a frontage run stand closer than the lot margin on the STREET line specifically,
with the exemption stated as narrowly as L141's party-wall one; (c) leave both and record that a
face may carry two lines, which is the option this ticket exists to avoid choosing by default.

**Acceptance:** one street line per block face, asserted — `check_frontage` (or a gate beside it)
refuses two setbacks on one face across generators, and whichever of the three routes is taken is
recorded with the records it moved. A run that only documents the divergence has not closed this.

**Links:** T-0079 · T-0077 · L141 · L144 ·
`data/reconstruction/1835_platted_block_parcels.json` § `blk_lake_clark.frontage.setback_step_known`.
