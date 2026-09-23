---
id: T-1055
title: The bar reads as mesic-prairie green because the terrain mesh is one material that never opens data/flora: carry each zone's declared ground colour onto the ground it covers
state: done
epic: GROUND
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0940
opened: 2026-09-12
closed: 2026-09-12
pr: 1183
claimed_by: run 9/12/2026, 2:47:23 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-12T09:01:55.067Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34681283724
---

The bar reads as mesic-prairie green because the terrain mesh is one material that never opens data/flora: carry each zone's declared ground colour onto the ground it covers.

Piece 1 of 2 of **T-0940 — The sand bar renders as mesic-prairie green with scrub on it, though z08_lakeshore and z09_sand_prairie cover it and declare sand at 55 and 18 per cent bare soil**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

## The cause, established before any number was changed

T-0940 named two candidates and asked which. It is the FIRST, and the renderer says so in
its own words. `renderers/web/js/terrain.js` builds exactly one `groundMaterial()` for the
whole box — a procedural prairie tile sampled in world space, shaded by TWO elevation keys
and nothing else: a wetness band `smoothstep(0.05, 0.70, y)` and a mesic tint
`smoothstep(0.95, 1.28, y)`. Its own comment states the limit and predicts this ticket:

> "It is not a community map: there is no plant-community record in `data/` for it to read
> yet, and a renderer that invented the boundary between wet and mesic prairie would be
> filling a gap silently. When those records land, the zone a point falls in belongs here —
> and the ground stops being one green."

`ground.js` says the same from the other side: "the ground is one earth colour from one edge
of the box to the other". And `data/flora/index.json`'s own `_doc` records the measurement:
"ROADMAP K42 measured that no renderer file fetches this manifest for the ground at all:
terrain.js never opens data/flora."

So the 2026-08-11 priority raise (z08 12 -> 45, z09 11 -> 40) was never a candidate. Priority
governs which community PLANTS; it cannot reach an albedo the mesh does not sample. The fix
worked where it was aimed — the bar's matrix is already thinned to z08's 0.35 — and the
month of green is the mesh underneath it, which no priority can move. **This is not a
regression of that fix.** The records the terrain comment was waiting for have landed:
every zone carries `ground.rgb` and `ground.wet_rgb`.

## Acceptance

1. The ground the substrate zones cover takes THEIR declared `ground.rgb` / `ground.wet_rgb`,
   read off the zone records at load rather than written into the shader.
2. **Nothing outside those zones moves, by construction rather than by tuning** — the recolour
   is a `mix()` whose weight is zero off the zone, so the prairie's fragment path is
   arithmetically identical to what it is today. Demonstrated, not asserted.
3. The wet/dry split inside a zone runs between the zone's OWN two declared colours on the
   same elevation key the prairie uses, so a zone that records a wet colour gets it.
4. The mean albedo inside a zone lands on the declared triple. Report the measurement.
5. `tools/check.sh` green. No ground mesh moves, so nothing bakes.

Scope: the SURFACE COLOUR only. The woody scatter is T-1056, the tip's ground is T-0939,
the height is T-0800, the trace is T-0799.
