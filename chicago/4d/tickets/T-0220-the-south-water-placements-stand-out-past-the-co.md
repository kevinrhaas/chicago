---
id: T-0220
title: The South Water placements stand out past the committed plat, and the walk breaks on them
state: done
epic: TOWN
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-0127
opened: 2026-08-24
closed: 2026-08-27
pr: 371
claimed_by: run 8/26/2026, 11:58:26 PM CT
blocked_on: null
needs_bake: false
---

The South Water placements stand out past the committed plat, and the walk breaks on them.

Piece 1 of 5 of **T-0127 — The rest of the town gets the street edge**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

Ten documented buildings on the south side of South Water Street were placed against the
MODERN kerb, read off OpenStreetMap, rather than against this project's own committed plat,
and stand up to 6.9 m out past the platted lot line — inside the 80 ft corridor, nearly to
the travelled track. `tools/measure_corridor_intrusion.py` names them and measures the depth:
`h_jones_store` 8.17, `chicago_american_office` 6.91, `jh_kinzie_forwarding_store` 6.87,
`carpenter_south_water_store` 6.62, `frederick_thomas_shop` 6.25, `madore_beaubien_house`
5.98, `pruyne_kimball_drugstore` 5.55, `harmon_loomis_store` 5.31, `chicago_democrat_office`
5.11, `peck_store` 4.51.

That is why T-0069's walk on South Water comes out in pieces — 15.6 m and 20.8 m runs of a
97 m face — while Lake Street's runs whole: the march refuses every step a wall stands on,
and on this street the walls stand on the walk.

**What the sources actually fix, and what they do not.** Every one of these records cites a
street and a landmark — "on Water Street, near the draw-bridge", "at Clark", "on South Water"
— so the ALONG-STREET position is argued from a source and is not this ticket's business.
The SETBACK is not in any source: it came from `osm_streets_2026`, a 2026 kerb line, and this
project's answer to "where is the lot line" is its own committed plat
(`data/traces/vectors/thompson_lots.json`, re-derived by `tools/generate_plat_lots.py`).
Reconciling the setback with the plat is therefore not moving a building to make a number
smaller — the number it is measured against is the one the record should have used.

**Acceptance:** each of the ten either stands with its street-facing wall at or behind the
committed South Water frontage line — moved along the street's own normal only, its
along-street coordinate untouched, with the derivation and the metres recorded in its
`position.note` — or is refused in writing, per store; `measure_corridor_intrusion.py`
reports none of the ten lapping South Water's corridor and its baseline is rewritten to
record the repair; `tools/generate_frontage_works.py` re-derives and South Water's walk runs
unbroken along each face except where its own ground refuses it; `tools/check.sh` and
`tools/smoke_renderer.mjs` pass. Never by weakening a gate.

**Not in this ticket:** more streets (T-0191, T-0192, T-0193), hitching posts (T-0194), and
the shadow lever T-0115's ledger names — that is T-0192's to spend, since it is the piece
whose metres need it.

---
## 2026-08-24 — THE REPAIR IS DONE AND DERIVED. It collides with the block programme, and that collision is the owner's fork.

**What is on the branch `steward/t-0127-south-water-plat`, measured rather than described.**

Eleven records moved — the ten this ticket names, plus `temple_building`, which the walk found:
with the ten back on the plat it was the ONE remaining wall standing on a plank walk anywhere
on South Water, refusing the first 10.2 m of `blk_south_water_franklin`'s north face, and its
fault is the ten's fault exactly (an `osm_streets_2026` setback). Each was moved SOUTH along
South Water's own normal by the smallest translation, to the centimetre, that puts every
sampled point of its footprint outside the corridor `tools/plat_corridors.corridors()` builds
from the committed centreline and the committed 12.192 m platted half-width. No `local_e`
moved. Every metre is recorded in the record's own `position.note`.

| record | was inside the corridor | moved south |
|---|---|---|
| `h_jones_store` | 8.17 m | 8.18 m |
| `chicago_american_office` | 6.91 m | 6.92 m |
| `jh_kinzie_forwarding_store` | 6.87 m | 6.88 m |
| `carpenter_south_water_store` | 6.62 m | 6.62 m |
| `frederick_thomas_shop` | 6.25 m | 6.25 m |
| `madore_beaubien_house` | 5.98 m | 5.99 m |
| `pruyne_kimball_drugstore` | 5.55 m | 5.55 m |
| `temple_building` | 5.49 m | 5.68 m |
| `chicago_democrat_office` | 5.11 m | 5.12 m |
| `harmon_loomis_store` | 5.31 m | 5.31 m |
| `peck_store` | 4.51 m | 4.51 m |

**What it bought, which is the acceptance's own test.** `tools/generate_frontage_works.py`
re-derives and the town's street edge goes from **1,147.7 m of plank walk in 21 runs** to
**1,297.3 m in 18 runs**, with **9 corner crossings becoming 11** and 86 walking decks
becoming 96 — fewer, longer, joined-up walks. On South Water's own five faces the walk goes
from 237.2 m in nine broken pieces (46–71 m of a 97 m face) to 376.5 m in six runs plus two
new corner crossings, and three faces now run whole. **The march refuses ZERO steps for a
wall anywhere on South Water.** Every remaining refusal on that street is its own ground —
0.07–0.13 m of roll under one walking deck, and one step at +0.02 m, at or under the water —
which is what the acceptance asked for in those words.

`tools/measure_corridor_intrusion.py`: **29 lapping phases become 21**, eight cleared outright
and three left shallow. `tools/check.sh` passes every step it failed on the way here — the
staleness gate (placement is not in the mesh hash, so this costs no bake), the 665 programme,
the census, the intrusion ratchet with its baseline rewritten to bank the repair.

## THE COLLISION, and why this ticket stops here

`tools/generate_block_infill.py --check` fails, and it is right to.

A lot is occupied by whatever footprint reaches inside its 1.5 m buildable inset
(`plat_occupancy.occupied_lots`, T-A7). While these eleven stood out in the roadway, six of
them reached only the margin strip of their own lots — `blk_south_water_franklin`'s
arrangement note says so in as many words, measuring J. H. Kinzie's lap at *"9.7 m², all of
it in the 1.5 m margin strip"*. **Put them back on the plat and they seat.** Six lots that
read free now read taken:

| block | lot | now seats | which the block parcel had dealt to |
|---|---|---|---|
| `blk_south_water_franklin` | 2 | `jh_kinzie_forwarding_store` | a frontage roof |
| `blk_south_water_wells` | 0 | `h_jones_store` | a frontage roof **and** a yard building |
| `blk_south_water_wells` | 2 | `carpenter_south_water_store` | a frontage roof |
| `blk_south_water_clark` | 2 | `pruyne_kimball_drugstore` | a frontage roof |
| `blk_south_water_dearborn` | 0 | `chicago_american_office` | a frontage roof **and** a yard building |
| `blk_south_water_dearborn` | 2 | `frederick_thomas_shop` | a frontage roof |

Six anonymous principal roofs and two yard buildings, across four blocks. **Nothing overlaps
anything** — every one of the eleven was checked against every committed footprint in the
town and the worst overlap is zero. The store stands at the street and the cottage stands
behind it, and they fit. What fails is a RULE: one principal roof to a lot.

**So the finding underneath the finding is this.** The block programme dealt six principal
roofs onto lots that documented buildings actually stand on, and it passed its own occupancy
gate only because those buildings were drawn out in the road. The plat reconciliation did not
create that; it made it visible.

## THE FORK — and it is not a number that can be derived

**(a) The lot rule holds, and the town gives the roofs back.** Each affected block's South
Water face has only two free even lots left, so the frontage runs shrink: franklin 3→2, clark
2→1, wells 3→1, dearborn 3→1. Eight roofs leave the town (338 standing → 330), four block
recipes and their arrangement notes are re-authored, and the households whose `lives_at`
names a removed roof have to be re-homed or leave with it — `..._franklin_d3_03` and
`..._dearborn_d3_03` are dealt to the lots in question and both carry households. Honest,
and it costs the business front its density.

**(b) A business-front lot may carry a documented store at the street and an anonymous
dwelling behind it.** Nothing physical objects — the footprints already fit. The occupancy
rule is relaxed for `stands_on: frontage` where the standing building is documented, the
block parcels keep every roof, and no household moves. Cheaper, more urban, and it is a
statement about what a South Water lot WAS.

**This is the owner's, not the loop's.** It is the same argument T-0143 and T-0188 are about —
the core density standard — and it decides whether the town's business front is one roof to a
lot. Deriving it either way inside a sidewalk ticket would be settling a density question by
side effect. **Recommendation, if the owner wants one: (b)**, because the geometry already
permits it and (a) pays eight roofs and two households for a rule the corrected data has just
called into question.

**The branch is left OPEN with `hold`**, carrying the whole repair, so whichever way this
goes the eleven records do not have to be re-derived. `tools/publish.sh` was deliberately NOT
run: nothing here is shipping yet.

**Also filed on the way:** **T-0195** (three of the eleven still lap the CROSS street's
corridor by 0.10–0.31 m at their corners — moving south cannot reach that and moving along
the street would move the axis the sources argue) and **T-0196** (four buildings still stand
on LAKE Street's walk, the same OSM-kerb fault, and downstream of this same fork).

## Verification actually run, in the foreground

- `./tools/check.sh` — every step green **except** `generate_block_infill.py --check` (the fork
  above) and `check_published.mjs` (only because `publish.sh` was deliberately not run — the
  failure names exactly the eleven sidecars and the frontage record, and nothing else).
- `tools/smoke_renderer.mjs` at **390x780, all nine stages: 208 + 80 + 152 = 440 checks, 0 failed.**
  The frontage layer's pinned census in the smoke moved with the walk and was updated with it —
  walks 29→26, crossings 12→14, fence runs 12→11, meshes 38→35 (the town street edge's culling
  chunks are one per run of sidewalk, so twenty-one became eighteen). Those are the layer's shape,
  not a threshold, and no gate was loosened.
- `tools/smoke_renderer.mjs` at **1280x800, stages 1-3: 208 checks, 0 failed**; **stage 4: one
  failure, and it is not this branch's.** `scene detail 'balanced' stays inside its own ceiling at
  the WORST stand` reports 1,235,088 tris of 1,210,000 at Lake Street at Canal — and `origin/dev`
  with these eleven records unmoved reports **the identical figure, to the triangle**. The stand it
  fails at is at the far west end of the town and the walk this ticket lengthened is on South Water
  in the east, so the layer contributes nothing there. Pre-existing, and T-0089 / T-0147's to carry.
- Desktop stages 5-9 not run: each leg costs about seven minutes against a ten-minute per-command
  ceiling, and with the branch already red on the block-parcel gate there is nothing for them to
  clear. They run before this merges.

---
## 2026-08-27 — THE OWNER RULED. (b): two roofs may share a business lot.

**The fork above went to Kevin and he chose (b), verbatim in effect: a platted business-front
lot may carry a documented store at the street AND an anonymous dwelling behind it.** His
reasoning is this ticket's own recommendation — the geometry already permits it (all eleven
were checked against every committed footprint in the town and the worst overlap is zero),
and (a) would pay eight roofs and two households for a rule the corrected data had itself
called into question. **No roof left the town, no household moved, and the four block
recipes keep every roof they were dealt.** What changed is the STANDARD, and it is recorded
as a standard changing rather than as a bug being fixed: `tools/plat_occupancy.py`'s module
docstring carries the ruling, the fork as it was put to him and the three tests that bound
the clause; `docs/STATUS.md` and `docs/ROADMAP.md` K30(d) carry it in the project's own
narrative; the four blocks' `arrangement_note`s carry it where a reader of the recipe meets it.

**ONE rule changed, and only one.** Standing the five on the plat left one pair under the
three-metre separation gate — the wells run's westernmost unit at 2.40 m from Carpenter's store,
side by side along the face with their fronts level — and the first attempt at this repair wrote
a second clause for it. That was wrong. The break is AUTHORED, on that slot as `clear_west_of`
+ `clear_m`, and `place_frontage`'s own note says where the number belongs: *"the three-metre
separation rule — not this recipe — is what fixes the size of the break"*. The 2.4 m had been
authored while the store stood 6.62 m out in the roadway, where the along-face break was not the
real gap at all. So **the recipe moved to the gate, not the gate to the recipe**: `clear_m`
2.4 → 3.0 with `clear_why` beside it, one anonymous roof 0.6 m further west, measured gap now
exactly 3.00 m. No threshold moved anywhere in this work.

## WHAT WAS ALREADY DONE BY THE TIME THE ANSWER CAME — re-measured, not re-asserted

`origin/dev` moved on. **T-0198 (PR #373) merged and reconciled SIX of the eleven** by the
same method this branch used, so the honest answer to "what still needed moving" is FIVE, and
they are exactly the five T-0198 refused in writing because they seat on a dealt lot — which
is the fork, which is why they waited.

| of the eleven | after PR #373 | this run |
|---|---|---|
| `jh_kinzie_forwarding_store`, `temple_building`, `chicago_democrat_office` | on the plat, clear of every corridor | nothing to do |
| `harmon_loomis_store`, `madore_beaubien_house`, `peck_store` | on the plat; 0.16–0.21 m residual on a CROSS street | nothing to do — T-0195 |
| `h_jones_store` 8.17 m · `chicago_american_office` 6.91 m · `carpenter_south_water_store` 6.62 m · `frederick_thomas_shop` 6.25 m · `pruyne_kimball_drugstore` 5.55 m | still out in the platted roadway, refused in writing | **moved 9.67 / 8.41 / 8.12 / 7.75 / 7.05 m** |

The five were translated along their block face's inward normal until each street wall stands
1.50 m back from the committed frontage line — **T-0198's method, not this branch's original
one**, so the whole street is repaired by one rule rather than two. (This branch had put the
wall ON the lot line; the merged six stand at the margin every reconstructed unit on these
faces keeps, and consistency across the eleven is worth more than the 1.5 m.) `local_e` moves
only by the face's own skew (0.07–0.24 m); the along-street position the sources argue is
untouched. Every metre is in each record's `position.note` and its sidecar's.

## WHAT IT BOUGHT, MEASURED AGAINST `dev` AFTER #373 — NOT AGAINST THE STALE FIGURES ABOVE

| | dev (after #373) | after this run |
|---|---|---|
| town street edge | 1,214.5 m of walk in **20** runs | **1,297.3 m** in **18** |
| corner crossings | 9 (212.5 m) | **11** (266.5 m) |
| walking decks | 89 | **96** |
| `blk_south_water_wells` north | 20.6 m + 41.1 m | **one 97.6 m run** |
| `blk_south_water_dearborn` north | 15.6 m + 20.8 m | **one 67.6 m run** |
| `blk_south_water_clark` north | 25.9 m + 20.8 m | 41.5 m + 20.8 m |
| phases lapping a platted corridor | 26 | **21** |

**The march refuses ZERO steps for a wall anywhere on South Water Street** — asserted by
re-running `_march` over every committed face and reading the reason on every refused step.
Eleven refused steps are left in the town and all eleven are on LAKE Street
(`old_bank_building` 4, `dole_warehouse_south` 3, `first_presbyterian_church` 2,
`st_marys_church` 2), which is T-0196. Every remaining South Water refusal is that street's
own ground: 0.07–0.13 m of roll under one walking deck, and one step at +0.02 m at or under
the water. That is the acceptance clause in its own words.

**All five leave the corridor census entirely** — not one of them laps any platted corridor at
any depth now, cross streets included.

## Bookkeeping this run had to do

- **This ticket was `T-0190` and is now `T-0220`.** `dev` merged its own `T-0190` (a second
  street tier) while this branch was parked, so two files carried the id; `ticket.mjs restamp`
  renumbered the younger, which is this one, and `T-0190`'s place in the owner's QUEUE was put
  back where the restamp had taken it.
- **`T-0199` is closed by the same PR** — dev's two-way split of T-0127 named the five stores
  exactly, and this is that work. T-0127's five-way split on this branch and dev's two-way
  split both stand; T-0191–T-0194 still own items 2–5 of the parent's body, which neither
  T-0198 nor T-0199 covers.

## Verification actually run for the 2026-08-27 finish

- `bash tools/check.sh` — **CHECK PASS**, every step, including
  `generate_block_infill.py --check` (the gate this ticket was parked on) and
  `check_published.mjs` (`tools/publish.sh` was run this time — this is shipping).
- Smoke on the **published mirror, ALL NINE STAGES AT BOTH VIEWPORTS** — the legs this PR
  admitted it had never run are run:

  | leg | mobile 390×780 | desktop 1280×800 |
  |---|---|---|
  | 1-2 | 144 passed, 0 failed | 144 passed, 0 failed |
  | 3 / 3-4 | 111 passed, **1 failed** | 74 passed, 0 failed |
  | 4 | *(in 3-4 above)* | 42 passed, **2 failed** |
  | 5-6 | 42 passed, 0 failed | 42 passed, 0 failed |
  | 7-9 | 152 passed, 0 failed | 152 passed, 0 failed |
  | **total** | **449 checks, 1 failed** | **454 checks, 2 failed** |

  Every failure is the same assertion at the same stand, and desktop's two are `dev`'s.
  **Re-run whole at mobile after the second dev merge (#384, #387, #394): 450 checks, 1
  failed**, and the breach shrank to **762 triangles of 1,210,000 — 0.06 %** as dev's own
  roof-form and log-wall work gave most of the 5,350 back.
- **The one failure, and it is measured rather than argued.**
  `scene detail 'balanced' stays inside its own ceiling at the WORST stand`, at Lake Street at
  Canal. A/B: the same tree read twice, once with `dev`'s `town_street_edge.json` in the mirror
  and once with this one. The frontage layer costs **5,350 triangles** at that stand, to the
  triangle, at every tier and both viewports.

  | tier · viewport | ceiling | dev | here |
  |---|---:|---:|---:|
  | `balanced` · mobile | 1,210,000 | 1,208,033 — **1,967 to spare (0.16 %)** | **1,213,383** |
  | `balanced` · desktop | 1,210,000 | 1,253,630 — **already over by 43,630** | 1,258,980 |
  | `full` · desktop | 1,400,000 | 1,413,266 — **already over by 13,266** | 1,418,616 |
  | `full` · mobile | 1,400,000 | 1,366,289 | 1,371,639 |
  | `light` · mobile / desktop | 1,050,000 | passes | 807,943 / 859,229 |

  Desktop's two are `dev`'s, before this branch. Mobile's is this branch's, over a ceiling `dev`
  was 0.16 % from failing. **No ceiling was moved**: T-0135's own text leaves that choice to the
  owner, and raising a number to clear a red inside a sidewalk ticket is the defect it was opened
  to end. Filed with every figure as **T-0218**.
- Proved the new occupancy clause REFUSES what it should, one bound at a time, by breaking each:
  a store moved 6 m back into the depth of its lot → *"lot 2 already carries
  pruyne_kimball_drugstore, so the frontage run cannot be dealt its roof"*; a store given a
  `reconstruction` block so it reads as a record the programme wrote → *"lot 2 already carries
  carpenter_south_water_store"*; clark lot 2 dropped from its block's `frontage` run → the lot
  goes back to barring another roof; and with nothing excluded, wells lots 0 and 2 (which the run
  already stands on) are not shared at all, so the schedule cannot be offered them twice.
