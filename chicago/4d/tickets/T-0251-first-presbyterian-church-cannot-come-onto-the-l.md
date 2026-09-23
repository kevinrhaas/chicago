---
id: T-0251
title: first_presbyterian_church cannot come onto the Lake Street plat without displacing physicians_office
state: blocked-owner
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-27
closed: null
pr: null
claimed_by: null
blocked_on: Does a documented building displace an inferred-household unit when the plat repair puts them on the same lot? first_presbyterian_church needs 3.395 m to come onto the Lake Street plat and physicians_office stands 3.15 m behind it — the church, the household, or neither moves.
needs_bake: false
---

first_presbyterian_church cannot come onto the Lake Street plat without displacing physicians_office.

Found by T-0196, which reconciled the other three Lake Street placements and refused this one
in writing rather than moving it. **Filed as T-0245 and renumbered to T-0251 on 2026-08-28**: two
parallel slices took T-0245 and then T-0250 for their own findings in the same minutes, and the collision surfaced at
the merge. The number in this ticket's own PR body is the old one; every committed reference —
the record's `position.note`, `docs/STATUS.md`, `tools/generate_frontage_works.py` and T-0246 —
carries T-0251.

## The fault is the same one; the repair is not available

Like `old_bank_building`, `dole_warehouse_south` and `st_marys_church`, this record's
cross-street coordinate came off a MODERN kerb line read from OpenStreetMap rather than off
this project's committed Lake Street centreline. Measured against the committed line its north
wall stands **1.90 m out past the `blk_lake_lasalle` frontage line**, in the platted roadway,
and `tools/generate_frontage_works.py`'s march refuses two steps of Lake Street's plank
sidewalk for it — 88.6 to 99.0 m along that face.

The standard repair is a translation of **3.395 m** along the face's inward normal, which is
what the other three took. It is not available here, and the numbers are why:

| move along the inward normal | gap to `physicians_office` |
|---:|---:|
| 0.0 m (as committed) | 3.15 m |
| 0.2 m | 2.95 m — **inside the 3.0 m separation gate** |
| 3.2 m | **0 — the footprints overlap** |
| 3.395 m (the repair) | overlapping |

There is no translation along this normal that both clears the walk and leaves the pair
standing apart. T-0198 named this collision when it refused to walk into it; this is the
measurement behind that refusal.

## Why it is the owner's and not the loop's

`physicians_office` is a product of the **inferred-household** programme — it carries
`reconstruction.status: "inferred_household"`, which is why `plat_occupancy.researched_ids()`
asks the record rather than its name. It stands 8.90 m back from the frontage line on
`blk_lake_lasalle` lot 6, the lot a documented church would come onto, alongside
`recon_1835_south_a3_043` and `recon_1835_south_d6_012`.

**The owner's 2026-08-27 business-front clause does not reach this.** That clause is bounded
to a lot named in its block's own `frontage` run in the committed parcel recipes, and
`blk_lake_lasalle` has no frontage run at all — its roofs came from the pre-plat South
Division parcel. So nothing in the committed rules says what happens when a **documented**
building's correct position is occupied by an **inferred** one.

The options, and each is a different answer about what the evidence layers owe each other:

1. **The church takes the ground and the household unit moves or goes.** A documented
   building outranks an inferred one; the town loses or relocates one inferred household.
2. **The church is placed a lot along.** Its own note already states the direction of its
   likely error — south, by up to a lot depth — and Andreas gives the corner but not the lot.
   Moving it along the face is a second claim about where it stood, not a repair.
3. **Nothing moves.** The church stays 1.90 m out in the platted roadway, two steps of Lake
   Street's walk stay unlaid, and the refusal stands written down where a visitor can read it.

Option 3 is what ships today.

**Acceptance:** the owner chooses among the three (or names a fourth); the chosen answer is
applied, `tools/generate_frontage_works.py` re-derives, and whatever it does to Lake Street's
walk on `blk_lake_lasalle`'s north face is measured and recorded. Never by weakening the
separation gate.

**Links:** T-0196 (the three that were reconciled, and this refusal) · T-0198 · T-0199 (the
owner's business-front ruling and its bounds) · `tools/plat_occupancy.py` ·
`tools/generate_frontage_works.py`.
