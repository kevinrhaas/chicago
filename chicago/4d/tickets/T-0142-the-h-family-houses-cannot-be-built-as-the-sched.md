---
id: T-0142
title: The H-family houses cannot be built as the schedule deals them: the crosswalk's eave and roof bands fall outside what frame_dwelling and the band gate allow
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-22
closed: 2026-08-24
pr: 352
claimed_by: run 8/23/2026, 11:03:40 PM CT
blocked_on: null
needs_bake: false
---

The H-family houses cannot be built as the schedule deals them: the crosswalk's eave and roof bands fall outside what frame_dwelling and the band gate allow.

**Acceptance:** every H-family record the block recipes can be dealt either builds under both
gates, or the family's crosswalk band is corrected with its reasoning stated — and the nine H
records already standing re-derive and re-bake in the same commit as the change.

**Found by T-0105 (2026-08-22), running the gates rather than around them.** The schedule dealt
`blk_randolph_dearborn` an H1 and an H2 in its second deal and neither could be built:

* **H2, the merchant or professional house.** At the size the crosswalk's own band deals it at
  this sequence the family asks for a two-storey wall of **6.234 m**, and
  `generators/archetypes/frame_dwelling_params.py` refuses anything over **6.2 m** — because the
  one attested ceiling height in this dataset is the Green Tree's seven and a half feet and a
  house was not built taller than the hotel. The eave band the crosswalk authors for H2 is
  18-21 ft, so roughly the top half of it cannot be built at all.
* **H1, the larger one-and-a-half-storey house.** `tools/generate_block_infill.py` deals every
  1.5-storey D/H family a flat **44.0 deg** roof pitch, which is inside D6's cited 9:12-12:12 and
  **outside H1's cited 8:12-11:12** (33.7-42.5 deg). `tools/measure_band_claims.py --gate` refuses
  it by name: *44.0 deg (= 11.59:12) vs 33.7-42.5 deg — +1.5 deg outside*.

**Three families are dealt a pitch their own crosswalk entry forbids**, measured across the
whole table: H1 (44.0 against 33.7-42.5), H2 and H3 (38.0 against 26.6-36.9). Nine anonymous
records of those families already stand — five H1, three H2, one H3 — so whichever way the
conflict is settled, the fix moves committed geometry and needs their bake in the same commit.
That is why T-0105 did not settle it in passing: it is a repair to the crosswalk or to the
generator, not a slot to re-order until the sampler deals a shorter house.
