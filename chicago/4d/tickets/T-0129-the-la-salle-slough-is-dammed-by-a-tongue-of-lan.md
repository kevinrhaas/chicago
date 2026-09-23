---
id: T-0129
title: The La Salle slough is dammed by a tongue of land where the street crosses it
state: done
epic: GROUND
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-08-21
closed: 2026-08-27
pr: 382
claimed_by: run 8/24/2026, 1:09:24 PM CT
blocked_on: null
needs_bake: true
---

The La Salle slough is dammed by a tongue of land where the street crosses it.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

The La Salle slough is dammed by a tongue of land where the street crosses it.

**The owner, 2026-08-21, from South Water Street looking west at 277°, approaching La Salle
Street, on the dev preview:** *"this slough has kind of a bulge of land and i would think that
it would not have that and be a continous water drain into the river and have plank crossings
for both the road and the sidewalk."*

His frame shows the La Salle slough reaching the river, and a **band of bare dirt carried
straight across the channel** at the street line — the wagon track fording the drain at grade.
Upstream of it the slough holds water; downstream it holds water; at the crossing the ground
rises out of the water and the two pools are separated. The drain reads as two ponds with a
causeway between them rather than as one watercourse emptying into the river.

## This is NOT the fault T-0118 fixed, and the distinction matters

T-0118 (merged, PR #284) fixed a **dry sill in the BED** — the two La Salle entries changed
depth at their join, so the ground between them stood above `SHORE_Y` and the water stopped.
That was cured by grading the bed continuously, and it is cured.

What the owner is looking at now is a **surface laid ON TOP of the watercourse**: the street's
own dirt track, drawn across the channel because the road layer and the swale layer do not
know about each other. Whatever the bed does underneath, the road paints land over it. So the
remedy is not in `terrain_spec.json` this time — it is in the relationship between the road,
the walk and the water.

## What to build

1. **The water runs through, unbroken.** Whatever the road does above it, the channel is
   continuous from its inland reach to the river — verified by sampling the surface along the
   centreline and finding no dry cell between the two pools.
2. **A plank crossing carries the ROAD over it.** Not a ford and not a causeway: the town's
   own idiom, the timber crossing already built for the Slough Log Bridge at the State
   Street mouth, sized for wagons. The road decal must stop at the abutments and the deck must
   carry the track across — the same discipline T-0124 settled for boards over the road decal
   (the planks draw after the ribbon, `renderOrder = 1`).
3. **A plank crossing carries the SIDEWALK over it, alongside the road's.** This is the
   pedestrian half the owner asks for, and it is the same object T-0069 is building along
   these streets right now — a walk that meets a watercourse needs a crossing, or the walk
   simply stops at the water.
4. **Both crossings are walkable** on T-0045's deck machinery, and both refuse rooted plants
   through their decks (the T-0124 checks).

## Coordinate — three tickets touch this one spot

- **T-0069 (in flight as this is written)** builds plank sidewalks and board crossings along
  the core streets south of the river. The sidewalk crossing here is naturally its object, and
  whichever lands second should read the other's result rather than building a second walk.
- **T-0119 (merged)** built the plank walk over the State slough mouth and the machinery for
  a walk that rides a committed deck (`deck_m`) — reuse it, do not invent a second kind.
- **T-0118 (merged)** owns the bed; if the bed turns out to need a further touch here, amend
  L149/L150 rather than opening a competing claim about the same ground.

**Acceptance:** from the owner's stand the La Salle slough reads as one continuous drain into
the river with no land bridge across it; a timber crossing carries the road and a plank
crossing carries the footway, both walkable, both refusing plants through their decks; the
road surface stops at the abutments instead of painting over the water; gates green, and the
terrain rebaked in the same commit if the bed moves at all.

**Links:** T-0118 (PR #284, the bed) · T-0119 (PR #285, the mouth walk and its machinery) ·
T-0069 (the street edge, in flight) · T-0045 (walkable decks) · T-0124 (boards over the road
decal) · `data/terrain/epochs/e1834_harbor_cut/terrain_spec.json` (`lasalle_slough_*`) ·
`renderers/web/js/streets.js`.
