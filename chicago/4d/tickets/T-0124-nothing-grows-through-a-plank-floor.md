---
id: T-0124
title: Nothing grows through a plank floor
state: done
epic: FLORA
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: null
opened: 2026-08-20
closed: 2026-08-20
pr: 281
claimed_by: null
blocked_on: null
needs_bake: false
---

Nothing grows through a plank floor.

**The owner, 2026-08-20, verbatim: "Everywhere you have plank sidewalks the grass comes
through. This is also the case on the docks on the river. They should not let grass come
through the floor, fix that."** The loop had already sighted one instance — T-0085, the
sward through the Green Tree's walk — and this ticket is the general case, fixed in the
same PR that files it.

## The two holes, both found in the code

1. **The frontage layer never told the planting layer it existed.** `main.js` built the
   planting block-list as `footprints + wharves.keepOut + boats.keepOut` — the plank
   walks and board crossings were simply not in it, so the sward rooted straight through
   every sidewalk. The wharf decks WERE in it, and yet reeds came through them, because:
2. **The floor test ran after the water test.** `flora.station()` returned a station for
   water-substrate species (`return … waterY`) BEFORE the block-list loop ran — so the
   block-list only ever governed dry ground, and every deck standing over water was
   invisible to it. An emergent bulrush rooted through a dock deck without any gate ever
   being asked.

## The fix

- `flora.js`: the block-list rejection hoisted above the `wet` early return — a floor
  refuses a plant whatever the substrate under it.
- `frontage.js`: publishes `keepOut` — one ENU rectangle per drawn walk and crossing,
  exact width (a tuft leaning over the edge is a verge; one rooted mid-deck is a hole).
- `main.js`: the planting block-list now carries `frontage.keepOut` and the registry's
  own walkable `decks` (the bridges, the slough crossing) alongside the wharves' and
  boats' entries.
- `smoke_renderer.mjs`: two new checks ask the placer directly at the centre of every
  published deck rectangle — no rooted stand for the generic community, and no station
  granted for ANY species the ground's own zone could deal, wet species included. The
  wet half is the half that regressed silently before.

## And the third hole, reported while the first two were being fixed

**The owner: "while you're at it the planked surfaces sometimes get over written with the
road."** The street ribbon is a decal — `depthWrite: false`, `polygonOffset -8/-32` — and
at grazing angles that offset outweighs the 11 cm a board stands above the ground, so a
ribbon drawn after the planks painted straight over a crossing. Fixed by draw order:
`frontage`'s timber mesh now renders after the ribbon (`renderOrder = 1`); the decal
writes no depth, so the boards paint over it exactly where they should, and real
occlusion (terrain, walls) is untouched.

**Acceptance:** the two smoke checks pass — every walk and wharf deck refuses every
species its zone offers — and a walk along the Green Tree's frontage and out onto a
South Water dock shows clean planks. Closes T-0085 with it.
