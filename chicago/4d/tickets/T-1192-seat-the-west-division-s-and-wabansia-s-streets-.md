---
id: T-1192
title: Seat the West Division's and Wabansia's streets and alleys as platted corridors off Wright and Hathaway — Canal, Clinton, West Water, Carroll, Fulton, the School Section tier and the Wabansia grid north-west of the forks — with the small lots the sheets draw
state: open
epic: GROUND
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
needs_bake: false
closed_at: null
claimed_run: null
---

The sibling of T-1191 for the ground west and north-west of the river. The West memo
(`west_division_infill_1835.md`) reads eleven corridors at 75.7–92.8 ft on the two sheets and a
116.6–123.2 m north–south pitch; `thompson_west_division_lots.json` holds 22 West Division blocks
with lot numerals, counts, depths and frontages; Wabansia's 21 blocks and six streets are seated
(`wabansia_seating.json`); the School Section's 142 block polygons exist (`school_section_blocks_1834.json`).
None has corridor control, and 35 of the West recipe's 55 slots are held on terrain.

**Acceptance:**

- Corridor entries for every West Division street the sheets draw west to the Des Plaines edge
  the memo names (E −700), and for the Wabansia grid, with sheet readings, widths and
  uncertainty as T-1191 does; alleys where drawn; `data/streets/1835.json` records
  updated with `status_1835` from the evidence (Canal and the Lake Street approach worn; the rest
  platted-unopened unless a source says otherwise).
- The **small lots**: the West Division and Wabansia lot figures (`lot_frontage_ft`,
  `lot_depth_ft` per block) recorded on the block records so T-1194 can generate
  them; where a block's sheet lots are narrower than the 80 ft module the record says so with
  the reading.
- Gates as T-1191; visible ribbons and minimap west of the forks; `needs_bake: false`.

**Stop condition:** the west and north-west grids are corridors, not names.

**Links:** T-1191 · `docs/RESEARCH/west_division_streets.md` ·
`docs/RESEARCH/west_division_lot_figures.md` · `docs/RESEARCH/north_branch_wabansia.md` ·
`docs/RESEARCH/school_section_grid_1834.md`.
