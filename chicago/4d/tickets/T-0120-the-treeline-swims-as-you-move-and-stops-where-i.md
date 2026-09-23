---
id: T-0120
title: The treeline swims as you move, and stops where it should carry on
state: done
epic: RENDERING
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-08-20
closed: 2026-08-20
pr: 282
claimed_by: run 8/20/2026, 3:25:24 PM CT
blocked_on: null
needs_bake: false
---

The treeline swims as you move, and stops where it should carry on.

**The owner, 2026-08-20, from South Water Street at SW 227°:** *"that tree line is still
off and should continue, and be stable when you walk — when you walk or fly it goes up and
down wildly."*

Two faults. The second one is fully diagnosed; the first has candidates and a measurement
to take.

## 1. Why it swims — a quantised solve under a rigid translation

The horizon band is a ribbon on a ring of radius 1100 m, and `trees.js update()` does two
things every frame that fight each other:

```js
horizon.position.set(p.x, p.y, p.z);          // EVERY frame — the ring rides the camera
…
if (Δe > RING_REBUILD_M || Δn > RING_REBUILD_M // 0.75 m
    || Math.abs(p.y - lastY) > 0.30           // ← the vertical trigger
    || viewport moved 2 %) solveHorizon(e, n, p.y);
```

Each vertex's height is `RING_RADIUS * tan(theta)` with `theta = (hgt - eyeY)/d -
d/(2·R_EFF)` — **eyeY baked in at solve time**. So between solves the band is welded to
the eye and rises and falls with it exactly, which is wrong for anything at a fixed
altitude; then the eye passes the **0.30 m** threshold, the whole profile is re-solved, and
it **snaps** to where it should have been.

Walking undulating ground crosses that threshold constantly. Flying crosses it continuously.
The result is a treeline that lurches instead of sitting still — precisely "up and down
wildly", and worse in the air, which matches the report.

**The fix is to make the vertical continuous rather than quantised.** `theta` depends on
`eyeY` through one linear term, so the expensive part — which bearings carry timber, at
what distance and crown height — can stay on the 0.75 m schedule while the eye-height term
moves per frame: keep `hgt` and `d` per vertex and finish `theta` in the vertex shader
against a `uEyeY` uniform, or apply the equivalent correction to the ring's own transform.
Do not simply lower `RING_REBUILD_M`/0.30: that buys smaller snaps at a higher cost, and
the band would still be welded to the eye between them.

## 2. Why it stops — three candidates, one measurement

The band is drawn only on bearings that carry timber; everything else is a gap, by design.
Three rules can open a gap that should not be there, and the run should measure which is
responsible at the owner's stand rather than guess:

- **`MIN_FAR_M = 330`** — a body nearer than 330 m is dropped from the band entirely. The
  comment explains why (a near stand on a ring reads as a mountain), but a wood that walks
  inside 330 m vanishes rather than handing over to real trees, and the handover is exactly
  what a visitor sees as the line "stopping".
- **The sub-pixel floor** — the crown/gap modulation may not take a bearing below the
  pixel floor, and bearings whose unmodulated crown is already under it are dropped. The
  file records **30 of 280 bearings cut on a phone, 14 of 281 on desktop**, worst
  silhouettes at 0.18 px and 0.31 px.
- **The dossier's own coverage** — the band can only draw bodies that are recorded. If the
  gap is there, it is a data gap and belongs in a research ticket, not a renderer one.

The frame also shows a **flat-topped band** at the left horizon rather than a crowned
silhouette — the file already warns that "a flat-topped six-pixel block reads as a distant
BUILDING, not as a tree", so check whether the modulation is being floored flat in that
sector at the same time.

**Acceptance:** walking a hundred metres of undulating ground and flying from grade to the
fly ceiling, the treeline holds its place against the horizon with no visible snap — shown
with a frame pair from the same stand at two eye heights, and the per-frame cost unchanged;
and the gap at the owner's stand is measured and either closed or explained on the record
(which of the three rules, with the numbers). Zero pageerrors, both viewports.

**Links:** `renderers/web/js/trees.js` (`update`, `solveHorizon`, `RING_RADIUS`,
`RING_FOOT_M`, `RING_REBUILD_M`, `MIN_FAR_M`, the pixel floor) · ROADMAP § S6a item 5 (the
photographic finding that 31 % of horizon columns carried timber) · T-0086 (the far sward —
same family of far-field problem).
