---
id: T-1054
title: Every frontage run in the town is measured against the lots its recipe declares, and the reading is a gate rather than a one-off
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-0449
opened: 2026-09-12
closed: 2026-09-12
pr: 1178
claimed_by: run 9/12/2026, 1:47:25 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-12T06:55:28.941Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34678274590
---

Every frontage run in the town is measured against the lots its recipe declares, and the reading is a gate rather than a one-off.

Piece 1 of 2 of **T-0449 — Four South Water frontage entries declare lots their runs never reach, and each hides its block's headroom**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

MEASURED ON THIS BRANCH, 2026-09-12, against dev at 9d8e68945.

`tools/measure_frontage_declaration.py` projects every frontage entry's own committed
footprints onto its block face out of `tools/block_faces.py`, projects every lot that
comes to that face onto the same axis, and reports the lots the run's span overlaps.
Fourteen entries carry a run; eleven declare exactly the ground they stand on, and the
three over-declared ones are all on the South Water row:

| entry | declared | reached | run along the face |
|---|---|---|---|
| `phase3_platted_block_south_water_franklin` | 4, 6 | **6** | 77.13 – 95.04 m |
| `phase3_platted_block_south_water_wells` | 0, 2, 4 | **2, 4** | 36.15 – 71.71 m |
| `phase3_platted_block_south_water_dearborn` | 0, 2, 4 | **4** | 59.67 – 77.28 m |

`blk_south_water_clark` was in T-0449's table at 2, 4 and now declares 4 alone — a run
between then and now had already corrected it — and `blk_south_water_lasalle`, the entry
T-0429 corrected, is exact. Every one of the three is the same shape: a run anchored
`corner: east` whose roofs ran out before they crossed back into the westmost lot its
entry named.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- The reach of every frontage run in the recipe is re-derived from the committed
  footprints and the committed plat grid, not read once by hand. Lots that do not come
  to the run's face are not candidates, which is the same test `frontage_strip` applies.
- `tools/check.sh` runs it, so a NEW over-declaration fails at the commit that writes it.
- The three entries that cannot be corrected inside this piece are conceded BY NAME with
  their measurement and the coupling that refuses them, and a concession that outlives
  its defect is itself a failure — otherwise a stale exception hides the next one.
- The three entries record the reading in `frontage.runs` and `arrangement_note`.
  `frontage.why` is NOT touched: it is copied into every record of the run, so editing it
  would rewrite 126 structure files for a note.
- `tools/generate_block_infill.py --check` and `tools/reconcile_665.py --check` still
  re-derive, and `bash tools/check.sh` is green. No bake — nothing moves.

**Links:** T-0449 (the parent) · T-1053 (the correction this measurement refuses) ·
T-0429 (`lasalle`, where the defect was first found and corrected) · T-0432 (`dearborn`,
which found it again from the occupancy side and left it alone).

