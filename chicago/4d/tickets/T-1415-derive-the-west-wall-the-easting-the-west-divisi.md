---
id: T-1415
title: Derive the west wall: the easting the West Division's held slots need, held to the three tests the other three walls stand on, and a committed reading of everything that stands on the E -320 clip today, gated
state: done
epic: GROUND
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1193
opened: 2026-09-19
closed: 2026-09-19
pr: 1545
claimed_by: run 9/19/2026, 7:29:04 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-20T01:31:26.117Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35478371061
---

Derive the west wall: the easting the West Division's held slots need, held to the three tests the other three walls stand on, and a committed reading of everything that stands on the E -320 clip today, gated.

Piece 1 of 3 of **T-1193 — Extend the modelled ground to N +760 and E −700: heightfield, collision, water mask, North and South Branch banks, flora and minimap together, so the North Division's second parcel and the West Division's held slots have ground to stand on**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- The west wall's easting is DERIVED in `terrain_spec.json` § `box_derivation.e_min`, not
  adopted as a round figure, and it is held to the same three tests the other three walls
  are: it clears the westernmost thing the box must contain with a stated buffer, it clears
  that thing's own error bar, and it lands on the existing 2.5 m lattice so no sample the
  field already carries moves. The prose names what the buffer is measured against.
- `tools/measure_west_of_box.mjs`, the sibling of `measure_north_of_box.mjs`, measures what
  the renderer does TODAY with the committed town that stands off the E −320 wall — the
  boundary scarp, the one-way doors the walker's 0.35 m step-up makes of it, the drawn and
  platted-only street metres off the grid by the edge they leave through, and the West
  Division placements `generate_west_infill.py` holds for want of ground — and writes
  `data/terrain/west_of_box_reading.json`.
- `--gate` holds that reading against a re-derivation and `tools/check.sh` runs it, so the
  numbers cannot rot while the box or the street layer moves. The gate asserts AGREEMENT,
  not that the gap is small.
- The tool carries its own self-test, as its northern sibling does.

**What this piece does NOT do:** it moves no ground. The heightfield, the collision surface,
the water mask, the branch banks and the bake are T-1416; the flora, the minimap, the streets
and the release of the held slots are T-1417. This ticket sets the number those two build to
and measures the thing they are meant to close, so the next run can say what it changed.

**Why the parent needed splitting, measured before claiming** (2026-09-19): the parent's
north ask is already met — T-1123 carried the north wall to N +1120, well past the N +760 it
asks for — so what is left is the west wall alone, and that wall is not one run. Moving it to
E −700 brings the North Branch's traced terminus (water to N +1079.21, the north line of
Wright's survey) INSIDE the box, where today the E −320 wall cuts the branch off before it
ends; a river that stops in the middle of the modelled ground is a defect the regeneration
has to answer before it bakes. Five committed streets are clipped at E −320, two more
(`des_plaines_school_section`, `jefferson_school_section`) carry T-0445's refusal to seat
their West Division lines for the same reason, and `data/render/ground_reach.json`,
`ground_tiling_budget.json` and `anchor_ground_reading.json` all hold the old wall.

**Links:** T-1193 (parent) · T-1067 / `tools/measure_north_of_box.mjs` (the pattern) ·
T-1123 · T-0464 · T-0445 · `docs/RESEARCH/west_division_infill_1835.md`.
