---
id: T-1105
title: The generators reading the tract layer: the plat module's street width and block module, and the reserved-ground record citing the reservation polygon
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-1102
opened: 2026-09-13
closed: 2026-09-13
pr: 1234
claimed_by: run 9/13/2026, 1:06:50 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-13T16:53:20.289Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34741831489
---

The generators reading the tract layer: the plat module's street width and block module, and the reserved-ground record citing the reservation polygon.

Piece 2 of 2 of **T-1102 — The land sales sorted onto the survey tracts, and the generators reading the tract layer**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

Item 4 of the parent T-1097's four, and the half T-1104 explicitly did not do:

1. **The plat module reads the tract it is inside.** `tools/generate_plat_lots.py`
   chooses ONE street width and ONE block module — the Thompson 80-ft/18-ft module — for
   the whole town, because until T-1101 there was no layer to ask. There is now.
   `data/reconstruction/1835_survey_tracts.json` says which survey a block stands in, and
   this project already holds separate module readings for at least two of them
   (`tools/measure_west_division_module.py`, `tools/read_west_division_lots.py`'s 75⅗-ft
   lot west of the river, `tools/read_wabansia_streets.py`). A block in Wabansia or
   Kinzie's Addition should not silently take the Original Town's module.
2. **`data/reconstruction/1835_reserved_ground.json` cites the reservation polygon.** The
   reserved-ground record is about platted BLOCKS and says nothing about the federal
   ground the blue chip covers; the tract layer now holds that ring with a grade.

**Watch the bake.** Changing which module a block is built on MOVES geometry, and
`validate.py --stale` will hard-fail any record that stops matching its committed mesh.
Budget `./tools/bake.sh --only <structure-id>` for the structures the change touches, or
split again if it turns out to be town-wide.

Two things T-1104 measured that this ticket will meet:

- **The layer does not tile.** Four tract pairs overlap ground a committed parcel stands
  on; the largest is Wabansia standing wholly inside `canal_section_9_remainder`. A
  generator asking "which tract is this block in?" needs the same precedence clause
  T-1104 states, or its own stated reason for a different one.
- **`canal_commissioners_1830` is `conjectural`.** Its four bounds are the standard
  account and no source record here states them. A module chosen off that ring inherits
  that grade and must say so.

See `docs/RESEARCH/land_sales_by_survey_tract.md` § What this does not do.
