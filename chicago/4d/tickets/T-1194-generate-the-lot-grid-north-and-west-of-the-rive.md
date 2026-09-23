---
id: T-1194
title: Generate the lot grid north and west of the river: Thompson's North Division blocks, Kinzie's Addition, Wabansia, the West Division blocks and the School Section tier — numbered lots from each sheet's own module, the small lots kept small, buildable ground tested
state: split
epic: GROUND
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-09-16
closed: 2026-09-20
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-20T09:55:49.141Z
claimed_run: null
---

`data/traces/vectors/thompson_lots.json` (`generate_plat_lots.py`) is the ONLY lot layer, and it
stops at the river: 19 blocks, 144 lots, all Original Town south of the main stem. Kinzie's
Addition (52 blocks), Wabansia (21), the West Division (22 blocks with lot figures), the School
Section (142 polygons) and the Michigan Street tract (5) are numbered but have no lots. Every
placement ticket below needs a lot to deal a roof to.

**Acceptance:**

- `generate_plat_lots.py` (or a sibling that shares its module code) emits lots for every block
  under the corridors T-1191 and T-1192 seat, from each plat's OWN module:
  Thompson's four-to-a-face north tier; Kinzie's Addition's lot figures where the sheet gives
  them (`read_kinzie_addition_numerals.py`, the water lots); the West Division's per-block
  `lot_frontage_ft`/`lot_depth_ft`; Wabansia's grid and water-lot wedge; the School Section's
  tier skew. A block whose sheet lots cannot be read keeps `lots_per_face_withheld` with the
  reason, never a guessed subdivision.
- Per lot: `plat_lot_number`, `plat_lot_confidence`, `tier`, `frontage_m`, `depth_m`, polygon,
  and a `buildable` reading from the extended heightfield (T-1193) — wet, sloping
  or in a water lot recorded, not silently skipped.
- `1835_reserved_ground.json` and `1835_no_build_ground.json` honoured; the Kinzie homestead,
  the Agency house, the Lake House construction, the brickyard and every documented north/west
  record's lot recorded on the record (`lot_claim` / `reconstruction.frontage.lots`) where the
  lot grid now names it.
- Gates: `generate_plat_lots.py --check` covers the new blocks; `measure_block_gating.py`
  re-run; `measure_street_line.py` for the new faces.
- **Visible:** the lot lines draw on the minimap / the ground overlay north and west of the
  river (the same overlay the Original Town uses).

**Stop condition:** every block inside the extended box that either sheet subdivides has lots,
and the placement tickets can name one.

**Links:** T-1191 · T-1192 · T-1193 ·
`docs/RESEARCH/thompson_plat_grid.md` · `docs/RESEARCH/west_division_module.md`.
