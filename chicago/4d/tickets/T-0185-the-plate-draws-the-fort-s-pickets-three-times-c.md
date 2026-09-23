---
id: T-0185
title: The plate draws the fort's pickets three times coarser than the model builds them
state: done
epic: TOWN
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-24
closed: 2026-08-28
pr: 436
claimed_by: run 8/27/2026, 11:33:13 PM CT
blocked_on: null
needs_bake: true
---

The plate draws the fort's pickets three times coarser than the model builds them.

Found by T-0094, which measured `data/sources/assets/prefire_views_kevin_2026_08/p4_0.png` to
refute a different claim about the same wall and turned this up on the way. It is the one thing
about the pickets the plate DOES say, and nothing has acted on it.

Measured (`tools/measure_picket_plate.py`, no `--gate`): the curtain's column profile
autocorrelates at **+0.70 at a 10 px lag** on the east reach and **+0.60 at the same lag** on the
west, so the draughtsman drew separate posts at a 10 px rhythm; the curtain stands **43 px** tall
there. That is about **0.23 of the wall's height per post**. The model builds `picket_spacing_m`
0.30 on a `picket_height_m` of 3.7 — **0.081**, nearly three times finer.

**Neither number is evidence about 1816.** Both `picket_width_m` (0.24) and `picket_spacing_m`
(0.30) are `reconstructed` and their notes say so; the plate is tier 5 and admissible for materials
and form as `inferred` at best, and 0.23 of a 3.7 m wall is a 0.85 m post, which is not a picket
anybody split. So the question is NOT "adopt the plate's proportion". It is whether a rhythm this
fine is the right reconstruction when the only picture anyone has drawn a stockade three times
coarser, and whether the wall reads as posts or as a slab at the distances a visitor actually
stands.

**Acceptance**, stated before the work and not weakened to pass:

Either `picket_width_m` and `picket_spacing_m` move together, at the tier the reasoning earns,
with what bounds the new figures written in their notes and the liberty updated — or they are
kept, with the plate's disagreement recorded against them so the next run does not re-open it.
**Whichever way, the plate's own drawn resolution is measured**, because "the plate disagrees" is
only evidence once somebody has shown the plate COULD have agreed; and the reading is taken from
`p4_0`'s own stand and from the north wall, at both release viewports, with the picket count and
the triangle cost stated.

**Answered: they are kept.** The plate could not have drawn this wall — at its own scale of
11.59 px/m the model's rhythm is 2.78 px of post and **0.70 px of gap**, and the narrowest gap the
plate holds anywhere on that curtain is **2 px**, so its 10 px pitch is the floor of the medium
and not a reading of the fort (0.23 of a 3.7 m wall is an 0.86 m post, which is not a picket).
And the model resolves as separate posts at every stand a visitor can reach: 34 px at the north
gate on a desktop, 16 px on a phone, 4 px against an expected 4.49 px from the river stand. It
falls under the pixel grid at one place only — a phone at the river stand, 1.62 px beating into a
4 px moire — which is **T-0266** rather than a reason to coarsen the wall. 768 posts and 21,504
positions on the picket surface, unchanged: no vertex moved, so `needs_bake` cost nothing.

**Links:** T-0094 (the pass that found the disagreement) · L47 (the liberty that owns the gap
between the posts) · T-0266 (the phone moire) · `tools/measure_picket_plate.py` § 4 ·
`tools/measure_picket_reading.mjs` · docs/RESEARCH/fort_dearborn_image_accuracy.md.

Either `picket_width_m` and `picket_spacing_m` move together, at the tier the reasoning earns, with
what bounds the new figures written in their notes and the liberty updated — or they are kept, with
the plate's disagreement recorded against them so the next run does not re-open it. Whichever way,
a before/after from `p4_0`'s own stand and from the north wall, and the picket count and triangle
cost stated. Geometry — needs the nightly bake.
