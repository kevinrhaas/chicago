---
id: T-0087
title: The wagon box floats: no bolsters, no reach, no hounds
state: done
epic: RENDERING
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: null
opened: 2026-08-18
closed: 2026-08-18
pr: 251
claimed_by: run 8/18/2026, 5:39:41 PM CT
blocked_on: null
needs_bake: false
---

The wagon box floats: no bolsters, no reach, no hounds.

**The owner, 2026-08-18, from the Green Tree's yard: "it looks like that bar is supposed
to be below the carriage of the wagon holding the wheels together but not sure. all the
wagons seem off."** The bar he is looking at is the tongue (T-0084) — but the instinct
behind the sentence is a second, independent defect, and the code confirms it: **there is
nothing under the box at all.**

`renderers/web/js/yard.js` builds a wagon from exactly three things: a plank floor with
four sides at `bed = base + form.wagonBedY` (0.95 m), two 0.05 m axle sticks at
`base + r`, and four wheels. Nothing connects the box to the axles, and nothing connects
the front axle to the rear one. Run the numbers and the gap is visible from where the
owner stood: the rear axle sits at 0.685 m and the front at 0.535 m, and the floor is at
0.95 m — so the box hovers **0.27 m above the rear axle and 0.42 m above the front one**,
supported by air. The eye reads a missing member, goes looking for it, and finds the
tongue lying in the grass — which is exactly the sentence he wrote.

What an 1830s farm wagon actually has between box and axles, all of it timber this layer
already knows how to draw:

- **bolsters** — a cross-timber over each axle; the box rests ON these, not on the axles;
- a **reach** (coupling pole) — the beam running fore-and-aft that ties the rear axle to
  the front gear and sets the wagon's length;
- **hounds** at the front, bracketing the reach and carrying the **kingbolt** the front
  axle pivots on (a farm wagon steers by swivelling its whole front gear — without the
  hounds the front axle is not attached to anything).

Draw them as boxes at their recorded sections, in the timber tone; the box floor then
rests on the bolsters rather than floating, and the wheels are tied together the way the
owner expected. Where a dimension is not recorded, it is **reconstructed** at the tier —
bounded by the recorded wheel diameters, track and body length — with a `docs/LIBERTIES.md`
entry, per AGENTS.md § RECONSTRUCTED IS A TIER. Do not shrink the wheels or drop the bed
to hide the gap: the wheel diameters are the recorded values.

**Acceptance:** from the Green Tree's yard, a wagon reads as a wagon — box carried on
bolsters over a reach, front gear on hounds, no daylight gap between body and running
gear — on every wagon on the layer, with the smoke's wagon bound unchanged and the
triangle cost stated. One frame from the owner's stand.

**Links:** T-0084 (the tongue, the other half of what he is seeing) · T-0040 (the wagon
layer) · `renderers/web/js/yard.js` (`wagonBedY` 0.95, `wagonRearWheel` 1.37,
`wagonFrontWheel` 1.07, `AXLE_T_M` 0.05) · owner_brief_2026_08_18 README (images 7 and
11 — farm wagons and the ox-drawn covered train, both showing the gear under the box).
