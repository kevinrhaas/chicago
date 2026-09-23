---
id: T-0172
title: The other three anonymous parcels still deal a retyped roof pitch, and none of them bounds an eave band by what the archetype can carry
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-24
closed: 2026-08-28
pr: 444
claimed_by: run 8/28/2026, 3:36:01 AM CT
blocked_on: null
needs_bake: false
---

The other three anonymous parcels still deal a retyped roof pitch, and none of them bounds
an eave band by what the archetype can carry.

**Acceptance:** `tools/measure_family_deal.py` sweeps `generate_west_infill.py`,
`generate_inferred_infill.py` and `generate_inferred_households.py` as well as the block
generator, and is green on all four — or every deal it refuses is named with the reason it
stands. Whatever geometry moves re-derives and re-bakes in the same commit.

**Found by T-0142 (2026-08-24), which repaired the platted-block parcel and left the other
three alone deliberately** — the sweep it built is scoped to the families the block schedule
deals, and says so in as many words. What is left:

* `generate_west_infill.py` and `generate_inferred_infill.py` still carry the constants T-0144
  and T-0145 took out of the north parcel: a flat 35, 38, 33 or 44 deg per family shape. Every
  fault T-0142 measured on the block parcel is the same code in these two files.
  `generate_inferred_households.py` is the same shape again.
* NONE of the four parcels but the block one asks `family_bands.eave_limits`, so a family
  whose authored eave band runs past what its archetype will carry is still sampled uniformly
  across the whole of it. H2 is dealt by the north parcel through `frame_tavern`, whose flat
  14 m limit does not bite — but D6 and H1 reach `frame_dwelling` in the west and household
  parcels and the 1.5-storey floor of 3.051 m does.
* The sweep itself is one `import generate_block_infill as blk` away from being general: it
  needs the parcel's `form_for` and `finish_for`, which all four expose under the same names.

Roughly M: the sweep generalises cheaply, the bake is whatever moves.
