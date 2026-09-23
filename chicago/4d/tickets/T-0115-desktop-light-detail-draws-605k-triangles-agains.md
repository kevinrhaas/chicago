---
id: T-0115
title: Desktop light detail draws 605k triangles against its own 600k ceiling
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-20
closed: 2026-08-20
pr: 289
claimed_by: run 8/20/2026, 9:57:58 PM CT
blocked_on: null
needs_bake: false
---

Desktop light detail draws 605k triangles against its own 600k ceiling.

Found 2026-08-20 by the first unfiltered smoke pass to reach the scene-detail checks in
days (chicago-4d-smoke.yml run 32346862982, on T-0060's branch — the staged-gate work,
which changes no geometry): `desktop 1280x800: scene detail 'light' stays inside its own
ceiling — 605414 tris of 600000, 52 calls`. Mobile passes the same check. Less than one
percent over, which is exactly how a ceiling erodes: the recent content merges (boats,
signboards, wharves, approach earthworks, shed-roof gables, clapboard variety) each added
their triangles and nothing re-measured the "light" tier against its budget on desktop.

**Acceptance:** the overage is attributed (which recent layer pushed the tier past its
ceiling on desktop, with counts), and either the light tier draws under 600k again by
trimming what it draws at that level, or the ceiling is consciously re-budgeted in the
same place the 600k figure is set — with the reasoning written down, never silently.

---

## Attributed 2026-08-20: T-0005's carve is 9.3k of it

Measured while landing PR #273, running the desktop stages that run had left unrun:

| tree | light tier, desktop |
|---|---|
| dev `48f8c21` (before the sloughs) | **605,414** tris of 600,000 — 5,414 over |
| the sloughs branch | **614,679** tris of 600,000 — 14,679 over |

The carved swales add **~9,265 triangles** and take the overage from 0.9 % to 2.4 %. Not
a new failure — the tier was already red, which is why this ticket exists — but it is the
first attributed contributor, which is what the acceptance above asks for.

**A lead for the repair, from the same measurement:** the terrain is ONE mesh whose
density is set by the bake's `--decimate-deg` (T-0005 used 0.031, a 3 mm fit). The carve's
share is therefore adjustable at the bake without moving a swale — the sloughs stay where
the 1833 map puts them and the tier can still be bought back.

The rest of the overage predates this and is still unattributed: the recent content merges
(boats, signboards, wharves, approach earthworks, shed-roof gables, clapboard variety) are
the candidates, and each is measurable the same way — bake at a known commit, read the
light tier, difference it.

Full stage sweep on the merged tree, for the record: mobile 1/2/4 PASS, mobile 3 = T-0114's
two known road failures; desktop 1/4 PASS, desktop 2 = this ticket, desktop 3 = one of
T-0114's two. No failure outside the two open tickets.

**Measured worse by T-0083, 2026-08-20:** the Green Tree's corrected fabric adds ~310
triangles on top of the above. Still under one percent of the tier by itself; the
attribution method stands unchanged.

**Measured worse by T-0074, 2026-08-20:** the dooryard plantings add ~43k scene
triangles at the light tier — 66 trees at ~433 each and 59 currant clumps at ~164 each
(the clump archetype was cut from 685 to ~164 during the same work, saving ~31k) — so
desktop light now reads 648,404 of 600,000 (was 605,414). Mobile light stays under its
own ceiling at 582,479, measured by the release smoke. Attribution for the trim: the
dooryard layer draws at every level today and is the natural first candidate for the
keep discipline the dealt wood already follows.

**Measured worse by T-0118, 2026-08-20:** the slough repairs add ~753 scene triangles
at the light tier — desktop light reads 649,157 of 600,000 (was 648,404). Of that, +304
is the terrain mesh itself (the graded slough beds need `--decimate-deg 0.03` to hold the
30 mm heightfield-fit gate — the old 0.04 default departs by 34 mm against them — and
0.03 is now the recorded default; the committed T-0005 mesh was itself baked at 0.031,
so the density is essentially unchanged); the remainder is flora on the ground the
straightened mouth and closed bay returned to plantable prairie (the woody planter's
reach grew 189,492 → 189,518 nodes, re-banked per the gate). Mobile light stays under
its own ceiling at 582,828. The 0.13 % delta does not change the trim candidates above.

**Measured worse by T-0092, 2026-08-21:** the Sauganash's corrected fabric adds +1,280
scene triangles at the light tier — desktop light reads 650,437 of 600,000 (was 649,157).
The mesh itself grew 484 → 1,124 triangles (+640: 576 of them the louvred shutter slats,
the rest the wing door, its porch hood and posts, and the entrance frontispiece); the
scene figure is exactly twice that because the stats count the sun's shadow pass, which
draws every building again. Mobile light stays under its own ceiling at 584,108 (was
582,828). The 0.20 % delta does not change the trim candidates above; if the slats ever
need trimming back, they are the one part of this fabric that is bulk rather than form —
36 leaves at 16 triangles of slats each.
**Measured worse by T-0119, 2026-08-21:** the river plank walk adds ~17,856 scene
triangles to the measured frame at the light tier — desktop light reads 667,013 of
600,000 (was 649,157). The walk's full timber is ~64k triangles over its 439 m run,
but it is deliberately built as fifteen per-segment meshes with their own bounding
spheres (the first frontage geometry that is not one draw call), so only the reaches
inside the frustum draw: the detail check's own stand sees roughly a quarter of it,
and a visitor at the slough mouth looking west down the run sees most of it. Draw
calls rose 52 → 55 in the measured frame, still under the 80 budget. Mobile light
stays under its own ceiling at 590,922 of 600,000 (was 582,828 — headroom is now
~9k, worth knowing before the next content merge). The trim candidates above are
unchanged; if the walk itself ever has to give tiers back, the per-segment meshes
make a distance or detail-level cut on this layer a local change.

---

## Attributed and repaired 2026-08-21 — the tier's lever covered 39 % of its own frame

**Where the frame goes.** Measured on the published mirror at the release gate's OWN stand —
`frame('sauganash_hotel', 26)`, the last camera move before the scene-detail check — by hiding one
scene child at a time and reading the delta in `renderer.info.render.triangles`. The rows sum
exactly to the total, so this is the whole of it. Desktop 1280×800, `light`, at dev `b67b949`:

| layer | triangles | share | does the detail level move it? |
|---|---:|---:|---|
| trees | 246,204 | 36.8 % | **yes** — `keep` 0.60 at `light` |
| terrain | 162,651 | 24.3 % | no |
| structures (the town's buildings) | 75,946 | 11.4 % | no |
| enclosures (fences) | 66,332 | 9.9 % | no |
| streets | 44,872 | 6.7 % | no |
| frontage (plank walks, boards, posts) | 32,472 | 4.9 % | no |
| yard (goods, wagons, the shed) | 20,672 | 3.1 % | no |
| flora (the sward) | 12,596 | 1.9 % | **yes** — the tune at `light` |
| signage | 2,760 | 0.4 % | no |
| boats | 2,144 | 0.3 % | no |
| wharves | 1,632 | 0.2 % | no |
| sky | 12 | — | no |
| **total** | **668,293** | | **39 % of it moves** |
| *of which the sun's shadow pass* | *222,784* | *33.3 %* | *(it redraws every caster)* |

That last row is worth its own line: a third of what the gate reads is the shadow map redrawing
geometry the colour pass already drew. Per layer, the shadow pass costs trees 125,268, structures
36,742, enclosures 33,166, frontage 14,004, yard 10,336, signage 1,380, boats 1,072, wharves 816.
Terrain, streets and flora cast nothing.

**And the diagnosis the table gives, which is bigger than any one merge.** The same three levels at
the same stand:

| level | drawn | its ceiling | |
|---|---:|---:|---|
| `full` | 850,657 | 1,000,000 | 85 % |
| `balanced` | 769,279 | 800,000 | 96 % |
| `light` | **668,293** | **600,000** | **111 %** |

The ladder PROMISES a 40 % step from `full` to `light` — that is what 1,000,000 → 600,000 says. It
was DELIVERING 21.4 %, and it could not deliver more: **a 40 % cut cannot be taken out of the 39 %
of the scene the setting had a lever on.** Every layer in the ledger above — the sloughs' terrain,
the dooryard plantings, the Green Tree's and the Sauganash's fabric, the river plank walk — landed
outside the tier's reach, which is why no single one of them was doing anything wrong and the
bottom rung still went eleven percent over. The rung was arithmetically unreachable.

**The route taken: trim, not re-budget.** The 600,000 stands exactly where it was. What changed is
that `light` now gives way on two more things, both chosen by the same test the sward passes — a
rendering decision rather than a claim — and both of them the SUN rather than the town:

* the shadow box steps back from ±240 m to ±120 m **and the map halves with it**, so the texel is
  arithmetically unchanged (11.7 cm desktop, 23.4 cm phone). ±120 m is not invented here: it is the
  reach this project shipped between R-W3b(a) and R-W5a2, and `light` is the level for machines
  that cannot afford what R-W5a2 bought. It also quarters the shadow map's memory.
* the **derived furniture** — fences, yard goods, plank walks, wharf decks, moored hulls — is no
  longer drawn into the shadow map. It stands where it stands, drawn as it is drawn, still
  receiving the shadows around it. Buildings, terrain and timber keep casting at every level.

**The hanging signboards were in that list and were taken back out, by measurement.** A board is
the only furniture in this town whose whole function is to be READ from the street, and its shadow
is what lifts it off the wall. With the boards not casting, the gate's own liveness check —
hide the signage layer at the Tremont's footway, require the frame to change — fell to mean 0.28
against its 0.30 bar, where it reads 0.72 with the shadow in. The shadow was most of what the board
contributed to the frame. The bar was NOT moved; the boards keep casting, at a cost of 1,380
triangles, 1.6 % of this parcel's saving.

| viewport, `light`, gate's stand | before | after | ceiling |
|---|---:|---:|---:|
| desktop 1280×800 | 668,293 (55 calls) | **584,761 (49 calls)** | 600,000 / 80 |
| mobile 390×780 | 639,379 (53 calls) | **555,847 (47 calls)** | 600,000 / 80 |

Both rows are the same probe standing at `frame('sauganash_hotel', 26)` before and after, so they
are comparable to the triangle. The GATE's own mobile reading is lower again — 507,280 of 600,000
at 44 calls — because the mobile pass runs its thumbstick test after that framing and walks the
camera on a little before the detail check; the desktop pass does not, and the gate's desktop
reading is 584,761 at 49 calls, to the triangle. `full` and `balanced` are untouched. The ladder now delivers 31.4 % of its promised
40 %. Recorded as docs/LIBERTIES.md **L155** (L121's entry for the wood, one layer over).

**Found on the way, and fixed here because the new gate depends on it:** `api.detail` was a getter
written inside an `Object.assign` literal, so it was invoked once and its VALUE copied — the
harness had been reporting whichever level the page BOOTED into, forever. The smoke's "the level
the visitor started on is restored" check was comparing a constant with the constant it was made
from and could not fail. `main.js` names the trap twenty lines further down; the rule had simply
not been applied to this one. It is a live getter now.

**What is still open, measured rather than guessed — for whoever takes the fence tickets.**

1. **The ceiling is a ONE-STAND measurement and the gate's stand is not the worst frame.** Standing
   on Lake Street at Canal looking east down the street — a long axial view that puts most of the
   town in the frustum — the same `light` tier draws **796,840 triangles at 68 calls** after this
   repair (and would have drawn ~882,000 before it). Nothing here regressed that; it has always
   been true and nothing has ever measured it. A ceiling checked at one camera is a spot reading,
   not an invariant, and the honest instrument is the worst stand of a set.
2. **The town-wide furniture meshes are never culled.** `enclosures` is one 33,166-triangle mesh
   spanning the whole town, so every fence in Chicago draws in every frame including the ones
   behind the camera; `yard` (10,336) and `signage` (1,380) are the same. T-0119 already solved
   this for the river walk by chunking it per segment. Doing the same to the fences would cost the
   visitor NOTHING at any tier and is the largest free saving left.
3. **The next lever inside this tier, costed:** a picket pale is a 10-triangle prism whose two
   22 mm edge faces and 22 mm top cap are 6 of those 10. Drawing a pale at `light` as a
   zero-thickness double-sided plank would save ~14,000 triangles on the 2,335 pales standing
   today, and — the part that matters for T-0067/T-0068/T-0069 — would make every pale those
   tickets add cost 4 triangles at `light` instead of 10.

Desktop headroom after this parcel is 15,239 (2.5 %) and mobile 44,153 (7.4 %). That is real
headroom and it is not a lot of it; item 2 above is where the next one should come from, because
it is the only one on the list that costs a visitor nothing.

**Measured BETTER by T-0066, 2026-08-21 — the first content merge since this repair that gives
tiers back.** Naming the town's signboards and varying their mountings takes the signage layer
from 1,380 triangles to **1,106** (−274, −19.9 %), and because the boards are the one piece of
furniture still casting at `light` the measured frame falls by twice that: **−548**. Desktop
`light` at the gate's own stand reads **584,167 of 600,000** (was 584,715), to the triangle, and
`full` reads 850,063 (was 850,657). Draw calls are unchanged at 49 — the layer is still ONE call,
because the lettering is a texture atlas rather than geometry. Desktop headroom at `light` is now
15,833 (2.6 %), up from 15,285. The gate's own mobile reading is 508,233 of 600,000 at 44 calls,
which is not differenced against this ticket's 507,280 above: the mobile pass walks the camera on
after its thumbstick test, and three content merges have landed between the two readings.

Where the saving comes from, since more signs now stand in the town, not fewer (23 → 33): a
mounting's triangles vary by an order of magnitude and the cheap ones are the ones the ticket
needed most. A name painted straight onto a building is **2** triangles; a board fixed flat on the
front under a cap is **24**; a bracket board is **60** (unchanged — it is still the wolf sign's own
geometry); an awning hood with a board under it is **72**; a post at the street edge is **72**. The
town now draws 13 painted names, 6 wall boards, 6 brackets, 7 awnings and 1 post. **The lettering
itself costs nothing at all**, which was the design constraint this ticket set on T-0066: every
triangle carries a `uv` into a single canvas atlas painted at load, so thirty-three colourways and
thirty-three names are one material and one draw call.

The trim candidates in the list above are unchanged, and item 2 — the town-wide furniture meshes
that are never culled — still names `signage` at 1,380; read it now as 1,106.

**Measured worse by T-0069, 2026-08-21 — a kilometre of sidewalk, and the day the
draw-call ceiling was consciously re-budgeted.** The town street edge
(`data/frontage/town_street_edge.json` — 1,147.7 m of plank walk, 212.5 m of board crossing
and 504.9 m of street-lining fence along South Water Street and both frontages of Lake
Street) reads, at the gate's own stand (`frame('sauganash_hotel', 26)`), desktop, on the
published mirror:

| tier | before | after | ceiling |
|---|---|---|---|
| full | 794,916 at **65 calls** | **855,832** at **78 calls** | 1,000,000 / **120** calls |
| balanced | 718,994 | **752,164** | 800,000 |
| light | 557,311 at 51 calls | **576,335** at 55 calls | 600,000 |

Headroom after: full 144,168 (14.4 %); balanced 47,836 (6.0 %); light **23,665 (3.9 %)** —
`light` has MORE headroom than it had before this parcel's chunking experiments, which is
the point of the paragraph below. Both rows are the same probe before and after, so they
are comparable to the triangle.

**THE CEILING THAT MOVED WAS DRAW CALLS, AND IT MOVED ON THE OWNER'S RULING.** Verbatim,
2026-08-21: *"ok to raise the draw call budget, if you need to make that a user friendly
option in settings because it wont work on some machines but will on others/most then that
is ok"* — and immediately after, *"or just raise the budget?"*. `BUDGET.drawCalls` is
**120** now, up from 80, argued in full at its definition site in `main.js`; the triangle
ceilings are untouched and no new setting was built, because the scene-detail control
already IS the user-facing option. The short of the argument: 80 was set when every derived
layer was ONE town-spanning mesh, and item 2 of the list above — chunking them so the
frustum can cull them — was taken by T-0067, T-0119 and now T-0069. Chunking DELIBERATELY
converts triangles into draw calls, and the sun's own pass draws every chunk inside its
±240 m box a second time, so a chunk costs two. Holding 80 would mean giving the culling
back.

**Chunk size is the trade, and it was measured three ways rather than guessed** — all with
the same geometry, on both streets, at the same stand:

| chunk | draw calls | `light` (the floor) |
|---|---|---|
| per run (~55 m) — **shipped** | 78 | **576,335** |
| per 120 m reach | 75 | 586,331 |
| per 200 m reach | 72 | 595,079 |

Coarser chunks buy calls and spend them on the tier that can least afford it: at 200 m the
MAIN pass drew nearly half the town's street edge from a stand that could see sixty metres
of it. With calls the cheaper currency, the finest chunking wins, and `light` gains
20,000 triangles of headroom against the coarsest option.

**Three drawn decisions paid for the triangles and none of them moves a board.** A walk
board carries no underside (2 of its 12 triangles, facing the earth it lies on); the
stringers are laid in 2.08 m BAYS rather than under every board, wherever the generator has
audited the ground flat enough for a bay-length stringer to reach it; and each run of walk
shares ONE mesh with the crossings and the fence on it. Together they take the walk from
**61.6 to 42.8 triangles a metre** — without them this parcel would not have fitted at any
chunk size.

**The next lever, costed, for T-0127.** A plank walk lies 11 cm proud of the ground and its
own cast shadow is about 4 cm wide at noon on 1 July — nothing, and `yards.js` already makes
exactly this argument for a ground treatment. If the WALK chunks stopped casting into the
shadow map while the FENCES (1.37 m tall, and a real shadow) kept casting, this layer's six
shadow-pass calls at this stand and roughly half its triangles at `full`/`balanced` would go
at no visible cost — which is what the cross streets need. It is not free to implement:
`applyShadowTier` in `main.js` overwrites `castShadow` on every furniture mesh at every
tier, so it needs a per-mesh opt-out, and the smoke's *"the light tier draws no furniture
into the shadow map"* check needs to count the ground-hugging meshes explicitly instead of
assuming every furniture mesh casts. Item 1 of the list above — that the ceiling is a
ONE-STAND measurement — is untouched and still true.

**Measured by T-0068, 2026-08-21 — the town's lot-line yard fences, and the first parcel whose
binding number was DRAW CALLS rather than triangles.** 109 of the town's 120 improved platted
lots are enclosed on three sides, 4.55 km of fence in board, picket and split rail. At the
release gate's own desktop stand, on the published mirror:

| tier | dev before | after T-0068 | delta | ceiling | headroom |
|---|---|---|---|---|---|
| `full` | 794,916 @ 65 calls | **876,826 @ 79 calls** | +81,910, +14 calls | 1,000,000 | 123,174 |
| `balanced` | 718,994 | **759,078 @ 79 calls** | +40,084 | 800,000 | 40,922 |
| `light` | 557,311 @ 51 calls | **565,489 @ 53 calls** | +8,178, +2 calls | 600,000 | 34,511 |

`light` takes a fifth of what `full` takes from the same fence, which is the pale-as-plank tier
doing exactly the work it was built for.

**THE DRAW-CALL CEILING MOVED, 80 → 96, and this is the ticket's second acceptance route taken
deliberately.** The owner ruled, verbatim: *"ok to raise the draw call budget"*. The reasoning is
at the definition site in `renderers/web/js/main.js` and the release gate now PINS the number
rather than merely reading it, so the next change to it has to move the gate in the same commit.
Why it needed to move: 80 was a guard on the BATCHING strategy, set when the scene was buildings
and vegetation, and the scene now has layers that CULL. Chunking buys its saving by spending
calls — a mesh small enough for the frustum to drop costs a call when it is kept, and a second in
the shadow map — and that trade is worth taking, but it means the count scales with how much town
is in front of you rather than with how many batches the loader made.

Measured, at the same stand, on the SAME geometry, with only the chunker's own constants moved:

| the town's 4.55 km of lot line | enclosure meshes | desktop `full` calls |
|---|---|---|
| `CHUNK_M` 30, one chunk per run (T-0067's rule) | 139 | 116 |
| `CHUNK_M` 50, chunks packed by locality | 87 | 95 |
| `CHUNK_M` 65, packed and walked in 140 m bands | 48 | **79** |

All three rows draw the same fence in the same place; only the packing moved. The bounding-sphere
discipline is untouched — the widest sphere reads 32.4 m against the gate's 40 m bar — and the
gate now asserts the mesh count stays under half the run count as well, so a re-merge fails in
both directions.

**Given back on the way:**

1. **`balanced` joined `light` in drawing a pale as a plank** (`enclosures.js` `PLANK_LEVELS`).
   The middle tier had never given anything up on this layer — a pale cost the same ten triangles
   there as at `full` — and with 4.55 km of fence on it that tier would have read 794,000 of its
   800,000 while `full` sat 123,000 clear of its own. It gives up the same 22 mm `light` gives up,
   worth about 56,000 triangles, and no triangle ceiling moved to pay for it.
2. **A post no longer draws the face buried under it** (12 → 10 triangles) **and a rail no longer
   draws the two end caps that sit INSIDE the posts at either end** (12 → 8). On a split-rail bay
   that is a quarter of the timber, invisible from any stand, at all three tiers.

**The next levers on this layer, costed, for T-0069 and whoever takes T-0056:**

1. **The shadow map is the larger half of the call count.** Measured with the layer at 87 meshes:
   45 calls, of which **28** are the shadow pass and 17 the frame; 84,000 triangles of which
   55,000 are the shadow pass. A near-field rule — furniture casts only within a few tens of
   metres — would take most of both. It cannot be done without moving this file's own gate that
   asserts EVERY furniture mesh casts at `full` and `balanced`, so it is a policy change to make
   in the open.
2. **Packing.** The chunker is greedy over a band-ordered stream and lands 48 meshes where an
   ideal two-per-block packing would be nearer 36. That is about 5 calls, and it costs a visitor
   nothing.
3. **The gate's stand is still ONE stand.** Item 1 of the 2026-08-20 list above is unchanged and
   unaddressed: the axial view down Lake Street from Canal is the worst frame in the town and
   nothing measures it.
**Measured by T-0064, 2026-08-21 — item 2 taken on the last of the three layers it named, and the
draw-call budget consciously re-budgeted.** T-0064 puts **64 more wagons** across the town (4 →
68), so the yard layer's geometry goes from **10,336 to 59,064 triangles**, ×5.7. Read the frame
rather than the layer, desktop 1280×800 at the release gate's own stand — `frame('sauganash_hotel',
26)`, the same probe every row of this ledger uses:

| desktop, gate's stand | before (dev `fd7b108`) | after T-0064 | ceiling |
|---|---:|---:|---:|
| `full` | 794,916 (65 calls) | **817,508 (94 calls)** | 1,000,000 / 110 |
| `balanced` | 718,994 (65 calls) | **741,586 (94 calls)** | 800,000 / 110 |
| `light` | 557,311 (51 calls) | **560,743 (62 calls)** | 600,000 / 110 |

**48,728 triangles of new geometry cost the SAFE FLOOR 3,432 of them.** That is item 2 of the list
above, taken on the layer this ledger measured at 10,336: the goods and wagons now go into **100 m
chunks by where they stand, one mesh each, all on the same material** — 48 of them — so a wagon two
blocks behind the camera is culled instead of drawn. `frontage.js` (T-0119) and `enclosures.js`
(T-0067) had already done this; the yard layer was the third and last of the three, and item 2 is
now closed.

**A wheel also gave triangles back, which is the rest of what paid for the parcel.** A wheel drew
SIX spoke boxes (twelve spokes' worth) where five reads identically at any distance a visitor can
stand, and its hub was a 10-sided cask 9 cm in radius — a cylinder drawn finer than the plank
beside it, which is the barrels' own missing-hoops argument. Five spokes and a six-sided hub save
**32 triangles per wheel**: 128 on a four-wheeled wagon, 64 on a cart, **7,744 across the 68 now
standing**, for a change nothing can see.

**THE DRAW-CALL BUDGET IS RAISED FROM 80 TO 110, and it is a re-budget rather than a drift.** This
ticket's acceptance offered two routes — trim, or re-budget consciously in the place the number is
set, with the reasoning written down — and the triangle ceiling took the first in August. The
draw-call number takes the second now, on the owner's ruling of 2026-08-21: *"ok to raise the draw
call budget"* … *"or just raise the budget?"*. The argument is at `main.js`'s own definition of
`BUDGET.drawCalls` and is short: **80 was set when the town was one batched mesh plus a handful of
whole-layer meshes**, so a rising call count meant the batch strategy had broken. That is no longer
what it measures. Three layers now chunk themselves ON PURPOSE, trading calls for triangles, and
the two budgets pull against each other — measured on this parcel at the same stand, same
68-wagon build:

| chunk | chunks | `full` tris | `full` calls | `balanced` tris | `light` tris | `light` calls |
|---|---:|---:|---:|---:|---:|---:|
| 100 m | 48 | **817,508** | 94 | **741,586** | **560,743** | 62 |
| 300 m | 15 | 857,680 | 77 | 781,758 | 582,367 | 58 |
| 400 m (52 wagons) | 8 | 838,268 | 74 | 762,346 | 569,835 | 55 |

The coarse builds are inside the OLD ceiling and draw more of everything at every tier. The
ceiling was buying nothing and costing fidelity, which is the definition of a number that has
outlived its reason.

**What did NOT move, and it is the half that matters.** The three triangle ceilings are untouched,
and **`light` still draws inside the old 80 calls** — 62 desktop and 62 mobile at the gate's stand,
asserted now by its own check in `tools/smoke_renderer.mjs` so the promise cannot quietly lapse.
The tier for a machine that cannot afford the other two is exactly as safe as it was; the new
headroom is spent at `full` and `balanced` only.

**Headroom after this parcel, at the gate's stand:** `full` 182,492 (18.2 %), `balanced` 58,414
(7.3 %), `light` **39,257 (6.5 %)** — up from 5.0 % before this parcel despite 64 more vehicles —
and 16 draw calls of 110.

**Item 1 of the list above, re-measured and worse, said out loud.** The axial Lake-Street-at-Canal
view this ticket names as the worst frame in the scene now reads, on the same build: `full`
1,101,347 triangles at **152 calls**, `balanced` 1,020,908 at 151, `light` 819,116 at **131** (it
read 796,840 at 68 calls after the August repair). The triangles barely moved; **the CALLS roughly
doubled**, because chunking is exactly the thing that spends calls when a long axial view puts most
of the town in the frustum. Nothing gates that stand and nothing ever has — item 1 is precisely the
observation that a ceiling checked at one camera is a spot reading — but a budget raised to 110 on
a 94-call measurement does not cover it either, and the honest instrument this ticket asked for
(the worst stand of a set) is still unbuilt. Whoever takes it should expect the chunked layers to
be most of what it finds.

**Measured by T-0130, 2026-08-22 — a parcel with a delta of exactly zero, which is worth banking
as much as a costly one.** T-0130 re-worded all thirty-three signboards, turned each one from a
single string into a two- or three-line hierarchy with its own type sizes, and painted a trade
device — a gilt mortar and pestle — onto one of them. Measured on the published mirror, the
signage layer before and after:

| signage layer | dev `745d9d5` | after T-0130 |
|---|---:|---:|
| triangles | 1,106 | **1,106** |
| meshes (draw calls) | 1 | **1** |
| atlas canvas | 4096 × 1536 | **4096 × 1536** |

**Why it is free, and it is the reason T-0066 built the layer this way.** The lettering lives in
ONE canvas atlas that every triangle already carries a `uv` into, so a three-line wording set in a
hierarchy costs exactly what a one-line name cost: nothing. The painted device is canvas as well —
**zero triangles for an image on a board**. The only geometry that moved is board SIZE, and a
board's vertex count does not depend on its dimensions: the same five mountings in the same
distribution (13 painted bands, 7 awnings, 6 brackets, 6 wall boards, 1 post) emit the same 1,106
triangles.

Frame at the T-0135 gate's stand, desktop 1280×800, `full`: **960,668 triangles of 1,000,000 and
121 draw calls of 140** — the same numbers dev carries, since the delta above is zero. Noted per
T-0135: that gate now stands at the worst frame rather than the friendliest, so this headroom is
real headroom and not the old camera's flattery. Nothing here was spent, and nothing is claimed
back.

**Measured by T-0188, 2026-08-24 — THE GROUND-HUGGING LEVER THIS LEDGER COSTED FOR T-0127 IS BUILT,
AND IT DOES NOT BUY WHAT THE ENTRY ABOVE PROMISED.** The entry said a walk lies 11 cm proud of the
ground and casts about 4 cm of shadow at noon, so if the walk chunks stopped casting *"this layer's
six shadow-pass calls at this stand and roughly half its triangles at `full`/`balanced` would go at
no visible cost — which is what the cross streets need."* Both halves were tested.

**What was built.** `applyShadowTier` no longer overwrites `castShadow` on every furniture mesh: it
reads `o.userData.groundHugging`, which `frontage.js` sets on the plank-walk and board-crossing
chunks. The street-lining fences (1.37 m, about half a metre of real shadow along the walk they
stand behind) had shared their walk's mesh since T-0069, so they moved to a mesh of their own —
**one per covered street, not one per fenced face**. That packing IS the trade: 3 meshes in the
colour pass and 3 in the shadow pass, against 20 ground-hugging chunks leaving the shadow pass
entirely. Per-face standing meshes would have cost 26 of each and turned a saving into a loss.
`furnitureShadows` now reports `groundHugging` and the release gate asserts
`casting === meshes - groundHugging` with `groundHugging > 0`, which is the counting this ledger
asked for — the old single equality could not survive an exemption, and an unasserted difference is
where an exemption nobody declared would hide.

**What it is worth, and it is not enough for a street.** Randolph Street — the second tier T-0127's
clause 2 asks for, 13 platted faces, +1,237.9 m of walk, +14 crossings, +14 fences, +97 walking
decks — was generated, published and read at the T-0135 stand set on the published mirror, WITH the
lever in place, at the axial stand (Lake Street at Canal, east):

| tier | dev | with Randolph, lever in | ceiling | headroom before | after |
|---|---:|---:|---:|---:|---:|
| desktop `full` | 1,378,984 @ 202c | **1,497,588 @ 218c** | 1,400,000 / 215c | 21,016 (1.5 %) | **−97,588** |
| desktop `balanced` | 1,205,762 @ 200c | **1,355,638 @ 216c** | 1,210,000 | **4,238 (0.35 %)** | **−145,638** |
| desktop `light` | 812,753 @ 70c | 869,731 @ 74c | 1,050,000 | 237,247 | 180,269 |
| mobile `full` | 1,337,059 @ 193c | **1,452,419 @ 209c** | 1,400,000 | 62,941 | **−52,419** |
| mobile `balanced` | 1,165,921 @ 191c | **1,316,605 @ 207c** | 1,210,000 | 44,079 | **−106,605** |
| mobile `light` | 764,401 @ 66c | 829,741 @ 70c | 1,050,000 | 285,599 | 220,259 |

Exempting the street-lining FENCES from the shadow map as well — the half this ledger argued should
be kept — was measured rather than estimated: with Randolph in, the layer draws 282,876 triangles in
56 calls at that stand, and turning off every shadow caster it has left (5 meshes: the shared timber
with the sign post on it, and the three street-fence meshes) reads **44,110 triangles and 3 draw
calls**. Against a **145,638** shortfall there is no version of this lever that carries a street
tier.

**AND THE BINDING FACT IS NOT RANDOLPH, WHICH IS THIS LEDGER'S ITEM 1 COMING BACK.** `balanced`
stood at **1,205,762 of 1,210,000 — 4,238 triangles, 0.35 %** — before this parcel touched anything,
and `full` at 1.5 %, where T-0135 set both on **2026-08-22** with *"about 6 % of headroom over the
measured worst"*. Two days of content ate the margin. **No street tier of any size fits today**, and
a ceiling that has to be raised every time the town grows is not measuring anything. Note also that
`balanced` reads only **9.5 %** cheaper than `full` at that stand while `light` reads **42 %**
cheaper, because `light` alone carries a furniture reach — the middle rung is barely a step.

Randolph was therefore taken back out rather than paid for with a fifth raise of these ceilings,
which is what T-0135 named as the bug rather than the remedy, and because T-0127's acceptance asks
for a lever to pay for the tier and not for a re-budget. The reading is written at
`generate_frontage_works.py`'s `EDGE_STREETS`, in `data/frontage/town_street_edge.json`'s own
`refused`, and in **T-0190**, which owns the choice between winning the axial frame back (T-0147,
T-0149), a conscious re-budget argued at the definition site, and a cheaper street edge.

**What the lever DID buy, kept:** with Randolph out, the street edge's 20 ground-hugging chunks and
the river walk's 15 no longer draw into the shadow map at `full` or `balanced` — 35 meshes and their
whole triangle count, once per frame, for a shadow 4 cm wide. That is a straight saving against dev
at every stand, and it costs 3 draw calls in each pass.
