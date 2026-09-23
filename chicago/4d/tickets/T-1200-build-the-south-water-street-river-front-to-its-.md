---
id: T-1200
title: Build the South Water Street river front to its seats: the forwarding houses, warehouses, stores and store-residences on the party lines from Market to State, the freight sheds and landings behind, every roof with its firm and its keeper
state: open
epic: TOWN
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-09-16
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: true
closed_at: null
claimed_run: null
---

First of the build tickets. Each takes ONE district's slot list from T-1199 (and the
known seats of T-1198 that ask for a roof), raises the roofs through the infill
generators at the families and variants the crosswalk names, bakes them, and hands the next
district on — the T-0028/T-0432 shape: one run, one demonstration, one successor.

**The ground:** the four South Water blocks (`blk_south_water_{franklin,wells,lasalle,clark,dearborn}`)
plus the Market wedge (T-0183, if the owner's ruling has landed; otherwise stated as skipped) and
the river-bank freight band under the north-bank rule's southern twin (`measure_south_bank_ground.py`,
T-0253 decides the river margin — if unruled, no roof laps the corridor).

**Acceptance:**

- Every slot on the district's list stands: C2/C3/C4 store fronts and F1–F3 warehouses on the
  street line and the party lines per the density standard, with the archetype variants the
  crosswalk requires (gable direction, shop bays, hoist beams, freight doors, sign sockets —
  `1835_family_archetype_crosswalk.json` `required_variant`), finish and age per T-1210'
  rules (or the current sheet where that has not landed, restated then), each record carrying
  `occupants` = the firm and keeper from the business layer and `resident_assignment: assigned`.
- Every generator refusal is resolved on evidence (corridor, separation, no-build, buildable
  ground) and the refusals log is empty; `reconcile_665.py` shows the district's blocks at
  capacity or the headroom stated.
- Baked (`tools/bake.sh --only` per record), sidecars compiled, published; derived layers
  regenerated in the same commit (lot-line fences, frontage works, signboards, yard goods,
  land tracts).
- **The frame budget:** downtown is over every scene-detail ceiling today (T-1154). Before
  pushing, `measure_detail_ceilings.mjs` on the published tree: if T-1154's trim has landed and
  the build fits, state the margin; if not, take the conscious re-budget AGENTS.md § the frame
  budget allows — the number moves at the place it is defined with the reasoning, `light` stays
  the floor — and say which you did in the PR. Never ship a silent breach and never shrink the
  parcel to dodge one.
- **Visible:** a screenshot from the Dearborn bridge looking west along South Water shows the
  full river front; both viewports smoke green.
- Successor handed on: T-1201.

**Stop condition:** the district's slot list reads built, every roof occupied.

**Links:** T-1199 · T-1197 · T-0028 · T-0432 · T-0183 · T-0253 · T-1154 ·
`docs/RESEARCH/carpenter_south_water_store.md` · `docs/RESEARCH/dole_warehouse_south.md`.
