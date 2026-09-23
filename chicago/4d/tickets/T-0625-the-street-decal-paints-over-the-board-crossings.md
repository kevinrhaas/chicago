---
id: T-0625
title: The street decal paints over the board crossings: renderOrder cannot order across three's opaque and transparent lists, so T-0460's ordering fix never ran
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-03
closed: 2026-09-03
pr: 753
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-04T02:45:44.295Z
claimed_run: null
---

The street decal paints over the board crossings: renderOrder cannot order across three's opaque and transparent lists, so T-0460's ordering fix never ran.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

FOUND BY THE OWNER, 2026-09-03, from the dev preview at Lake and South Water: *"this
case did not complete successfully"*, against T-0460, which had been closed as the
fix for the plank walk's jagged edge.

**T-0460 was not wrong; it was not the whole fault.** It replaced the walk's comb of
board ENDS with a continuous string piece, and that repair holds — its own geometric
probe still passes. What the owner was looking at is a second fault with the same
symptom from the street, and it is not geometry at all. Measured at the Sauganash
crossing: the boards are laid correctly (max step between consecutive segments 7 mm,
nothing of the road standing above the deck anywhere on its 15.9 m), and the picture
is still broken, in hard triangular patches that follow the terrain's triangulation.

**The mechanism.** `streets.js` draws the road as a decal: `depthWrite: false`,
`transparent: true`, and `polygonOffset -8/-32` so the terrain cannot punch through
its drape — a number tuned twice already (R-BUG2, then R-BUG3 deepening it).
`polygonOffsetFactor` scales with the polygon's depth SLOPE, which at the grazing
angle a road is viewed at is very large, so the ribbon's fragments are pulled far
enough toward the camera to beat a plank deck standing 0.06 m above it.

`frontage.js` already answered this — `mesh.renderOrder = 1`, with a comment saying
in as many words that the timber is "DRAWN AFTER THE STREET RIBBON". **That line
never did what it says.** three sorts opaque and transparent meshes into separate
render lists and draws every opaque before any transparent; `renderOrder` orders
within a list and cannot reach across the two. The ribbon is transparent, the timber
was opaque, so the ribbon was always drawn last however the renderOrder was set. The
comment has described a fix that did not run since the day it was written.

**The repair** is to put the timber in the same list, so the ordering already
written becomes the ordering that runs: `transparent: true` on the frontage-timber
material. Nothing about it blends — alpha is 1 and `depthWrite` stays on — the flag
is a render-list selector here and the comment says so.

Two alternatives were measured against a reference frame (the same pose with the
ribbon's offset neutralised, which is what "right" looks like but is not shippable
since the offset is R-BUG2/R-BUG3's fix). Mean absolute pixel difference from that
reference, and the share of pixels off by more than 8:

| | crossing view | street view | far view |
|---|---|---|---|
| dev today | 4.894 / 5.20 % | 0.499 / 0.78 % | 0.022 / 0.12 % |
| **timber into the transparent list** | **0.017 / 0.13 %** | **0.007 / 0.07 %** | **0.016 / 0.10 %** |
| timber polygonOffset -10/-40 | 0.121 / 0.55 % | 0.189 / 0.71 % | 0.048 / 0.25 % |
| timber polygonOffset -16/-64 | 0.214 / 0.74 % | 0.261 / 0.91 % | 0.060 / 0.29 % |

Biasing the timber's own offset past the road's is an arms race against a number
tuned twice, and it pushes the timber through what it abuts — worse at -10/-40 and
worse again at -16/-64. Making the ribbon opaque also clears the crossing and is
worse still: the road texture's alpha is genuinely graded (the track feathers at its
edges, the ruts and crown modulate it), so dropping the blend hardens every track
edge in the town.

**The gate.** `tools/smoke_renderer.mjs` gains an assertion next to T-0460's edge
rule — the two street/timber sets must be in the same render list AND the timber's
renderOrder must be the higher. T-0460's probe cannot catch this: the timber IS
there, at the right height, with a continuous edge; it is simply not what is on the
screen. Verified to fail on the old behaviour (`sameList=false`) and pass on the new.

**Acceptance:** (stated before the work — never weakened to pass)
- The crossing at Lake and South Water reads as continuous plank from the street.
- The new smoke assertion fails when the material leaves the transparent list.
- `bash tools/check.sh` green; the published mirror resynced.
