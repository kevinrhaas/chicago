---
id: T-0058
title: A visitor can walk out along a wharf deck
state: done
epic: TOWN
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-18
closed: 2026-08-27
pr: 396
claimed_by: run 8/27/2026, 4:44:10 AM CT
blocked_on: null
needs_bake: false
---

A visitor can walk out along a wharf deck.

Filed by the run that shipped **T-0041** (the wharf layer), which deliberately did not claim it.
`terrain.walkHeight()` reports a wading barrier at +4 m over open water, and the wharf decks do not
override it, so both docks are things you see from the bank and cannot step onto. The bridges CAN
be stood on since T-0001, by a different route: `placement.walk_surface_m`, carried into a sidecar
from the archetype's resolved deck height. A wharf has no structure record and therefore no
placement, so it needs either a record of its own or a second route into `walker.js`'s
`surfaceAt()` — which is the design question, and the reason this is a ticket rather than a line in
T-0041.

Also open at the landward edge: the deck holds 0.90 m over the water and the bank at both sites is
0.2-0.6 m, so boarding it from the ground is a 0.3-0.7 m riser and the walker's 0.35 m step-up rule
refuses at least one of them — the same edge T-0001 hit at the bridge abutments.

**Acceptance (stated 2026-08-27, before working — one demonstration):** from plain ground behind
EACH of the seven docks, facing the river, the walker pushes forward and ends standing on the deck
over open water at the height the layer drew the slab, with **zero refused strides**, no stride
over the 0.35 m step-up rule, and the wading barrier above its head rather than under its feet.
Both halves in one clause on purpose: publishing the deck alone passes "walk along" and fails
"walk out onto", and that is exactly the half a run could declare done and leave broken.

**Measured before the work (this terrain, at load):** deck top 0.90 m at all seven — the record's
freeboard floor, since every bank is below it — against heels at 0.117–0.575 m. Risers 0.325 m to
0.783 m; **six of the seven over the 0.35 m rule.** Only Kinzie & Hunter's was boardable.

**Answered by a boarding stair** (`docs/LIBERTIES.md` L195), not by regrading the bank: the deck
height is the terrain's and moving the terrain to make a walk work is a claim about the LAND, and
it needs a bake. The stair divides whatever rise the ground leaves into equal treads under the
record's 0.30 m ceiling — one tread at the two Kinzie landings, two at the five South Water ones.

**Demonstrated:** `tools/smoke_renderer.mjs`, three new checks in the wharf section — the layer
publishes every plank it drew at the height it drew it; no tread rises past the record's ceiling or
the step-up rule; and the walk itself, all seven docks, 0 blocked strides, worst stride 0.205 m.
