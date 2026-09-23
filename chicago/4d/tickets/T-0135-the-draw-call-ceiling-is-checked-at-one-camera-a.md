---
id: T-0135
title: The draw-call ceiling is checked at one camera, and it is not the worst one
state: blocked-owner
epic: META
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-08-21
closed: null
pr: null
claimed_by: run 8/21/2026, 11:05:00 PM CT
blocked_on: The gate now reads the worst of five named stands and it is RED: 1,320,377 tris of 1,000,000 at full, 1,144,787 of 900,000 at balanced, 992,617 of 600,000 at light, and 200 draw calls of 140 — all at Lake Street looking east from Canal. Raise the ceilings to carry it (which puts light above the ceiling full carries today, so the ladder and the weak-machine floor both stop meaning anything), or trim the axial view to fit them (a rendering programme: distance culling or LOD down a long street)? Measured 2026-08-22; nothing regressed, this is the first honest reading.
needs_bake: false
---

The draw-call ceiling is checked at one camera, and it is not the worst one.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

The draw-call ceiling is checked at one camera, and it is not the worst one.

**Placed at the head of the queue by the owner, 2026-08-21**, after the ceiling was raised
twice in one afternoon. This is T-0115's item 1, which that ticket recorded and could not
carry; T-0115 has closed and the finding has outlived it, so it gets a ticket of its own.

## The defect

The release gate reads draw calls and triangles at **one camera** — `frame('sauganash_hotel',
26)`, the last move before the scene-detail check. Everything the project believes about its
own frame cost comes from that single stand, and it is not the town's worst frame.

**Measured 2026-08-21, on the tree where the day's four content parcels first drew together:**

| stand | `full` | `light` |
|---|---:|---:|
| the gate's own stand | **121 calls** | 55 |
| Lake Street at Canal, looking east down the axis | **152 calls** | **131** |

The axial view is 31 calls worse at `full` and more than twice as expensive at `light` — the
tier that exists so a weak machine can walk the town at all. Nothing gates that stand, so
nothing has ever failed for it.

**The cause is the thing that was supposed to help.** Three layers were chunked this week
(frontage T-0119, enclosures T-0067, yard T-0064) so the frustum can skip what is behind you.
That is a large win at an ordinary stand and a loss down a long street, where the whole town
is in frustum at once and every chunk becomes its own call. So the number the gate reads gets
BETTER as the number the visitor can actually hit gets worse, which is the worst possible
shape for a guard rail.

## Why it matters now

The ceiling moved twice on 2026-08-21 — 80 → 120 → 140 for draw calls, and `balanced`
800,000 → 900,000 — each time argued honestly against the gate's own reading, and each time
against a measurement now known to be optimistic. The loop is shipping content parcels
hourly and every one of them adds geometry. Raising a bar to fit a camera that flatters the
scene is how a budget stops meaning anything, and the owner's own ruling asks for the
opposite: **measure, then move.**

## What to do

1. **Gate the WORST of a set of stands, not one.** Choose a handful that between them cover
   the ways this scene gets expensive — a long axial street (Lake at Canal is the known worst),
   an open aerial, a dense core corner, the existing Sauganash stand — take the maximum, and
   fail on that. Name each stand and say in the code WHY it is in the set, so the set can be
   argued with rather than trusted.
2. **Report the spread, not just the max** — a gate that prints "121 at the easy stand, 152 at
   the worst" tells the next parcel where its cost actually lands.
3. **THEN re-argue the ceilings against the worst reading.** They may need to rise again; they
   may instead call for the chunkers to be tuned (the wagons ledger notes the chunker leaves
   calls on the table, and the shadow pass is ~28 of the enclosure layer's 45). Either outcome
   is fine. What is not fine is the number staying where it is because nothing measures it.
4. Do NOT weaken anything to make the worst stand pass on the day it is introduced. If it
   fails, that is the finding — record it, and let the owner decide whether to raise or trim.

**Acceptance:** the scene-detail and draw-call checks fail on the worst of a named set of
stands rather than on one; the set and its reasons are written where the stands are defined;
the run prints both the worst and the spread; and the current ceilings are re-argued against
the new reading, with whatever moves recorded at its definition site.

**Links:** T-0115 (closed; this is its item 1, with the numbers) · T-0064 (the measurement of
the axial view) · `renderers/web/js/main.js` `BUDGET` / `DETAIL` · `tools/smoke_renderer.mjs`
(the scene-detail block) · AGENTS.md § the frame-budget ruling.
