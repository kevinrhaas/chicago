---
id: T-1193
title: Extend the modelled ground to N +760 and E −700: heightfield, collision, water mask, North and South Branch banks, flora and minimap together, so the North Division's second parcel and the West Division's held slots have ground to stand on
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
needs_bake: true
closed_at: null
claimed_run: null
---

The ground box binds before any rule does: modelled ground ends at local N +400, E −320, N −400,
E +1700. The North memo asks for N +760 before its remaining 90 roofs; the West memo asks for
E −700 (its farthest recommended centre is E −668) before its 35 held slots; `generate_west_infill.py`'s
`terrain_and_hydrology_gate` holds them today. Both memos say the same thing: extend terrain,
collision heightfield, water mask, branch banks, vegetation zones and streets TOGETHER, or the
outer additions read as an occupied city standing on nothing.

**Acceptance:**

- `data/terrain/epochs/e1834_harbor_cut/` heightfield + bin, `terrain_spec.json`, river/branches
  geojson and the water mask extended to N +760 and E −700 with the same datum and sampling; the
  North Branch banks traced from `north_branch_bank_wash.json` / `thompson_1830_forks_banks.json`
  through the new box; the north-side slough carried; the shoreline states unchanged east.
- Flora zones (`data/flora/`) and the minimap box extended; `measure_southern_ground.py`,
  `measure_no_build_ground.py`, `measure_slough_crossing.py` re-run green; the walker's collision
  covers the box.
- The bake lands (`needs_bake: true`): ground tiles regenerated; `smoke_renderer.mjs` at both
  viewports with a new stand on the addition's ground; the scene-detail ceilings re-measured
  (`measure_detail_ceilings.mjs`) and the ground-tiling budget (`data/render/ground_tiling_budget.json`)
  re-set consciously if the box costs triangles — at the place it is defined, with the reason,
  per AGENTS.md § the frame budget.
- **Visible:** a screenshot from Kinzie and Wolcott looking north shows prairie to the addition's
  line instead of a wall.

**Stop condition:** `generate_north_infill.py` and `generate_west_infill.py` no longer refuse a
slot for want of ground.

**Links:** `docs/RESEARCH/1835_north_division_extent_and_infill.md` ·
`docs/RESEARCH/west_division_infill_1835.md` · `docs/RESEARCH/terrain_forks.md` · T-0010 · T-1154.
