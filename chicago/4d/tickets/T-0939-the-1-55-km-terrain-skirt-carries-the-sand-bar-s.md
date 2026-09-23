---
id: T-0939
title: The 1.55 km terrain skirt carries the sand bar's 80 m cross-section south at a dead-constant +1.21 m, so the bar never ends and Wright's hook never forms
state: done
epic: GROUND
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-06
closed: 2026-09-12
pr: 1193
claimed_by: run 9/12/2026, 7:22:26 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-12T13:14:25.506Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34693070189
---

**OWNER-REPORTED from the walkthrough, 2026-09-07 — "the forever sandy stretch".** From
water level the bar runs to the horizon as a perfectly straight, constant-width ribbon and
simply never stops.

**This ticket was first filed on a WRONG diagnosis and is corrected here.** The first draft
said the terrain box ends at n = -400, Wright's bar runs to -434, and therefore "south of
-400 there is no heightfield at all, so the hook is not low ground, it is *no* ground". That
is not what happens. There is ground south of the box, and there is far too much of it.

## What actually happens

`renderers/web/js/terrain.js` documents a **1.55 km skirt** outside the modelled box — the
mesh is "5,120 m wide (a 2,020 m box plus 1.55 km of skirt)". Its rule, quoted from the
generator:

> "The skirt is carried, not flattened. It lies outside the modelled box, where `sample()`
> returns its fallback rather than clamping, and snapping it to that would drop 1.55 km of
> apron onto the water plane. Sampling at the clamped position instead reproduces the
> generator's own rule for it — **'carry each boundary vertex outward, keeping its own
> height'** — so the seam at the box edge closes exactly."

So every point south of n = -400 takes the height of the boundary row at n = -400. Sampled
across that row:

| e | height | |
|---:|---:|---|
| 1310 | -0.160 | water |
| **1320** | **+0.825** | **land** |
| 1330 .. 1380 | **+1.210 to +1.215** | land |
| 1390 | +0.940 | land |
| 1400 | 0.000 | water |

**80 m of bar stands on that boundary row, and the skirt extrudes it 1.55 km south at a
dead-constant +1.21 m.** The bar's own modelled length inside the box is about 640 m, so
what a visitor sees is a ribbon roughly three and a half times longer than the landform,
running to the haze without a taper, a curve or an end.

**The skirt is not a bug and must not simply be removed.** For the mainland shore in the
same photograph it is doing exactly the right thing — that ground genuinely continues south
past the box, and flattening the apron would drop 1.55 km of it onto the water plane. The
same row of vertices is right for the mainland and wrong for the bar. That is the whole
problem: the skirt assumes the boundary is a cross-section of something that CONTINUES, and
the bar is a landform that ENDS 34 m past the edge.

## The general case, which is the reason this is worth doing properly

Any landform that terminates inside the skirt zone is extruded to a 1.55 km prism instead of
ending. The bar is the case that is visible today because it is thin, isolated and stands in
open water; it will not be the last. Whatever is decided here should be a rule about
boundary landforms, not a special case for one bar.

## Acceptance

1. The bar ends. From water level and from the air it terminates in a recognisable hook or
   taper rather than running to the horizon — and the length it ends at is the one the
   evidence gives, not one chosen to look right.
2. **The mechanism is stated and is general.** Either the epoch box grows to contain the
   whole landform, or the skirt learns that a boundary run is a feature that ends. Say which,
   say why, and write it where the skirt rule is documented in `terrain.js` so the next
   landform to reach an edge meets the answer.
3. **The skirt still does its job everywhere else.** The mainland's southern apron is
   unchanged, and the box-edge seam still closes exactly. Report what moved outside the bar's
   footprint; the answer should be nothing.
4. `tools/measure_terrain_horizontal.mjs --gate` stays green — it currently reports plan
   movement 0.0 mm and the drawn surface within 6.7 mm of the field at all 259,689 sample
   points, and that is not to be spent here.
5. The bar's above-water plan fit does not get worse: 124-176 m of land against Wright's
   traced 141-171 m, re-reported after the change.
6. Bake in the same PR; this moves ground, so `needs_bake` applies.

## What this is not

- **Not the bar's height.** `T-0800` owns "the bar's height argued". The +1.21 m crest is
  its question, and this ticket does not change it — it only stops it being extruded.
- **Not the tip's trace.** `T-0799` traces "the sand bar to its tip" off the full sheet, and
  its own `_doc` calls the southern hook "the least certain part of the sheet in this area"
  at 30 m uncertainty. **T-0799 should run first if both are picked up**, or this ticket
  states the uncertainty it inherited from the windowed reading.
- **Not the bar's surface.** `T-0940` owns the green-instead-of-sand and the scrub.
