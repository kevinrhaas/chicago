---
id: T-0190
title: A second street tier for the street edge, and the ceiling that refuses it
state: open
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-24
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
---

A second street tier for the street edge, and the ceiling that refuses it.

T-0127's clause 2 — *"at least one more street tier (Randolph, or the cross streets) carries the
street edge too"* — and the owner's ask behind it, of the first Cook County jail engraving: *"note
the fences lining the street and what appears to be plank sidewalks. **all of the streets** should
be updated like this... at least south of the river or near the river."* South Water and Lake carry
it (T-0069). Nothing else does, so a walker turning a corner steps off the boards.

## IT WAS BUILT AND MEASURED ON T-0188'S BRANCH, AND IT DOES NOT FIT

Randolph Street through `tools/generate_frontage_works.py`'s own rule adds **13 platted block faces,
+1,237.9 m of plank walk, +14 board crossings, +14 street-lining fences, +97 walking decks** — the
record goes 16 faces / 1,147.7 m to 29 / 2,385.6 m. It was generated, published and read at the
T-0135 stand set on the published mirror, at the axial stand (Lake Street at Canal, east), which is
the worst frame in the set:

| tier | dev | with Randolph | ceiling | headroom before | after |
|---|---:|---:|---:|---:|---:|
| desktop `full` | 1,378,984 | **1,497,588** | 1,400,000 | 21,016 (1.5 %) | **−97,588** |
| desktop `balanced` | 1,205,762 | **1,355,638** | 1,210,000 | **4,238 (0.35 %)** | **−145,638** |
| desktop `light` | 812,753 | 869,731 | 1,050,000 | 237,247 | 180,269 |
| mobile `full` | 1,337,059 | **1,452,419** | 1,400,000 | 62,941 | **−52,419** |
| mobile `balanced` | 1,165,921 | **1,316,605** | 1,210,000 | 44,079 | **−106,605** |
| mobile `light` | 764,401 | 829,741 | 1,050,000 | 285,599 | 220,259 |

Draw calls went 202 → 218 against a budget of 215 (desktop `full`).

**The lever T-0115 costed for exactly this was taken FIRST, and it is not enough.** T-0188 shipped
it: the plank-walk and board-crossing chunks carry `userData.groundHugging` and leave the shadow
map at every tier, while the street-lining fences moved to their own per-street meshes and keep
casting. Measured with Randolph in, the layer draws 282,876 triangles in 56 calls at that stand and
every shadow caster it has left (5 meshes) is worth **44,110 triangles and 3 calls** — against a
**145,638** shortfall.

**AND THE BINDING FACT IS NOT RANDOLPH.** `balanced` stood at 1,205,762 of 1,210,000 — **4,238
triangles, 0.35 %** — before any of this, and `full` at 1.5 %, where T-0135 set both on 2026-08-22
with *"about 6 % of headroom over the measured worst"*. Two days of content ate it. **No street
tier of any size fits today**, and the honest reading is T-0115 item 1 recurring: a ceiling set
against a measurement is a ceiling that erodes the moment the town grows.

## WHAT THE CROSS STREETS COST, ALSO MEASURED

Run through the same rule: **34 platted faces and 3,562.8 m of walk** — three times the whole
current record, 38 more culling chunks. They also need a code change and not only a name in
`EDGE_STREETS`: `_edge_faces` enumerates a block's NORTH and SOUTH faces, and a cross street bounds
its EAST and WEST ones. Washington Street adds 7 faces.

## THE ROUTES, AND THIS TICKET IS FOR CHOOSING ONE WITH NUMBERS

1. **Win the frame back first** — T-0149's remaining pieces and T-0147. The axial stand is where
   every chunked layer pays for all of its chunks; `light` already reads 42 % cheaper than `full`
   there because it has a furniture reach, and `balanced` reads only 9.5 % cheaper. A `balanced`
   that is barely a step is a ladder rung nobody is standing on.
2. **A conscious re-budget**, which AGENTS.md's frame-budget ruling permits and which T-0115's
   acceptance names as one of two honest routes — but it would be the FIFTH raise of these numbers,
   and the first aimed at a reading taken specifically to show that raising to fit the reading is
   the bug (T-0135 says so in `main.js`). It needs arguing, not assuming.
3. **A cheaper street edge.** T-0069 already took three decisions worth 61.6 → 42.8 triangles a
   metre. Whether a fourth exists that moves no board is unmeasured.

**Acceptance:** at least one more street tier carries the street edge, walkable end to end and with
board crossings round its corners, AND all three detail tiers stay inside their ceilings at the
whole T-0135 stand set with the draw-call count inside whatever the budget then is — with whichever
route above paid for it named and measured. If the answer is another re-budget, it is argued at the
definition site against the erosion table above and never silently. Never by weakening a gate.

**Links:** T-0127 (parent ask) · T-0188 (built it, measured it, took it back out) · T-0115 (the tier
ledger — this run's rows are in it) · T-0135 (the worst-stand instrument and the ceilings) · T-0147
· T-0149 · T-0150.
