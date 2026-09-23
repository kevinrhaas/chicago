---
id: T-0125
title: The stockade sank into the raised mound: four feet of picket show from the parade
state: done
epic: TOWN
requested_by: steward
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-20
closed: 2026-08-20
pr: 287
claimed_by: run 8/20/2026, 10:08:23 PM CT
blocked_on: null
needs_bake: false
---

The stockade sank into the raised mound: four feet of picket show from the parade.

Found while gating T-0123 ("prove the fort stockade stands its full twelve feet").
The bake is right and the record is right — `fort_dearborn_palisade` states
`picket_height_m` 3.7 m and the committed GLB measures **3.80 m** of picket. What
a walker MEETS is not: the wall shows about **1.15 m** above the ground along its
whole south, west and east faces, and a level gaze at the south wall from the
fort road sails clean over the pickets into the compound.

## Measured, 2026-08-20, on the published mirror

- The placement contract anchors a rigid mesh at the LOWEST ground under it
  (`buildings.groundUnder`; the "shares the terrain surface" gate allows bedding
  up to 3 m and forbids floating). For the stockade that lowest point is the
  river bank under the north-west bastion: ground **1.02 m**, so the wall top
  stands at **4.82 m** world.
- The mound raise of changelog **v202** ("Fort Dearborn stands higher on its
  mound", 2026-08-20) lifted the parade-side ground under the fort to
  **3.62–3.68 m**. Wall top 4.82 − ground 3.65 ≈ **1.17 m of visible picket** —
  four feet, on a twelve-foot wall. Before v202 the mound rose "only a foot or
  so" and the wall stood essentially full height.
- Sampled every ~6.6 m around the authored 53 m square: visible height is
  1.14–1.21 m along the south, east and west walls, rising to 2.7 m only at the
  north-west corner where the bank falls away. The walker's eye is 1.68 m.
- So the owner's 2026-08-19 report on T-0123 ("way too short … below my
  height") is now literally true of the fort's own wall from every landward
  approach — whatever he was looking at that day, this is what a visitor meets
  today.

## The remedy is a judgement about the reconstruction — the owner's

A rigid 53 m mesh on 2.6 m of relief cannot both hug the ground and hold its
height; something has to give, and each option changes a different claim:

1. **Bake the stockade stepped or draped** (pickets follow the grade, tops
   stepping down the bank the way a real set-picket wall does). Truest to the
   type; needs the bake pipeline and terrain knowledge at bake time.
2. **Regrade the mound under the wall line** (flatten the fort's pad so the
   relief under the palisade box is small). Touches v202's researched mound.
3. **Move the placement a few metres south-east** off the bank slope
   (uncertainty is ±20 m). Shrinks the relief under the box; does not zero it.

None of these is a dimension change to `picket_height_m`, and none should be
taken without the owner's say-so (T-0123 rule 3). The smoke now pins the two
truths that must survive any remedy: the baked picket carries the record's
3.7 m, and the wall tops a walker's eye where wall and anchor meet (the bank
foot). The parade-side clearance is deliberately NOT gated — that number is
exactly what this ticket exists to settle.

**Acceptance:** standing on the parade side (the fort road approach, local ENU
about (1148, 189) facing north), the rendered wall top clears the walker's eye
— then gate that stand in `tools/smoke_renderer.mjs` beside the T-0123 block,
and record in the changelog what gave (bake, ground or placement) and on whose
word. No change to `picket_height_m` without the owner's written say-so.

**Links:** `data/structures/fort_dearborn_palisade.json` (`picket_height_m` 3.7)
· `renderers/web/js/buildings.js` (`groundUnder`, the lowest-ground anchor) ·
changelog v202 (the mound raise) · T-0123 (the gate that found this, and the PR
carrying the frames).

---

## The owner's ruling, 2026-08-21

> Regrade the mound under the wall line (touches v202's researched mound)

Option 2 of the three. Taken as written: the ground gives, not the bake and not
the placement, and `picket_height_m` stays 3.7 m.

## What the regrade has to move, measured on dev at b67b949

Sampled every 5.3 m along the authored 53 m wall square (placement E 1122.07 /
N 198.45, rotated 8°) against the committed heightfield:

| wall | ground, min → max |
|---|---|
| south | 3.64 → 3.67 m |
| east | 1.81 → 3.67 m |
| north | **1.26 → 1.81 m** |
| west | 1.26 → 3.64 m |

The lowest ground under the footprint is **1.26 m** at the north-west corner, so
the rigid mesh anchors there: wall top 5.06 m, and from the parade at 3.65 m only
**1.41 m** of picket shows against a 1.68 m eye. The fall is entirely on the
NORTH wall, the one facing the river.

**The mound's flat top is not the mechanism.** The radial flat top (45 m) does
leave the north-west corner 48.2 m out on the skirt, but that costs only a few
centimetres. What sinks the wall is the BANK RAMP: `terrain_gen.py` multiplies
every land level by `1 − (1 − d/face)²`, zero at the waterline and full only at
`face` metres inland. The south division's `face_profile` states **20 m** across
the fort's frontage — and the traced 1834 waterline sits **4.5 m** north of the
north-west corner and **7 m** north of the north-east corner. A 20 m face cannot
fit between the fort and the river, so the ramp eats some 15 m INTO the fort and
scales the north wall's ground to about a third of its height.

This also contradicts the mound's own note, which claims the north face "carries
the full +12 ft over about a 25 m run — 1:6.8". There is no 25 m run at the
fort's corners. The note describes ground the spec does not build.

**The regrade, therefore:** narrow the bank face across the fort's river
frontage so the ground reaches the mound's level at the wall line and the fall
happens OUTSIDE the stockade — which is what the source describes in the first
place ("formed by the curve of the river at its base on its three sides": the
river at the mound's BASE, not partway up the fort's wall). The 1834 harbour cut
is a dredged channel, and the south edge of a made cut stands steeper than the
alluvial banks upstream; the resulting face is held at the natural angle of
repose for sand rather than pushed past it. Every changed number keeps its
liberty entry, and the mound's note is corrected to the ground actually built.
