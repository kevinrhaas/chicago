---
id: T-1443
title: Carry the West Division's five east-west tier lines off their E -320 clip to Des Plaines Street, on each line's own committed bearing and control
state: done
epic: GROUND
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1431
opened: 2026-09-20
closed: 2026-09-20
pr: 1569
claimed_by: run 9/20/2026, 6:33:20 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-20T13:44:38.645Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35507852269
---

Carry the West Division's five east-west tier lines off their E -320 clip to Des Plaines Street, on each line's own committed bearing and control.

Piece 1 of 2 of **T-1431 — Carry the West Division's five tier lines off their E -320 clip and release generate_west_infill's 35 held slots on the extended ground**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:**

- `carroll`, `fulton`, `lake`, `randolph` and `washington` each reach west of local east
  -320 to the committed `des_plaines` centreline T-1430 seated — `carroll` to `fulton`'s
  own west end, because an interpolation claims no more ground than the pair it lies
  between — and no line stops at the modelled field's west wall, which is an extent and
  not a street.
- `lake`, `randolph` and `washington` are carried on the Thompson plat's own east-west
  bearing, the single number all three share to six decimals, so they arrive at Des Plaines
  as parallel as the sheet draws them. `fulton` keeps its own committed bearing, because
  its four-point fit disagrees with that grid and reconciling them is not this ticket's.
- Nothing east of the old clip moves: each line KEEPS its old west vertex, the reach is
  carried from it rather than fitted through it, and the direction change that leaves at
  that vertex is measured and on the record rather than rounded away.
- The carry reads no new source. Its corroboration is control the record already carried:
  two of `fulton`'s four surviving intersections stand west of the clip, the derivation
  never reads them, and the carried line passes inside the four-point fit's own RMS of both.
- Every metre of every reach is sampled against the committed heightfield and stands on
  dry modelled ground, with the lowest sample on the record.
- `tools/carry_west_tiers_west.py --check` holds every one of those clauses and
  `tools/check.sh` runs it, so a re-fitted, re-bent, over-stretched or quietly upgraded
  line fails there rather than going quiet.
- `measure_no_build_ground.plat_bearing` reads the grid over the Original Town reach and
  says why, because a derived reach may not redefine the grid it was derived from.
- Every derived record the carry moves is re-derived in the same commit and the move is
  stated: the north-of-box street reading, the town wagons' lattice, the sidecars.

**Stop condition:** no West Division street stops at local east -320, and
`carry_west_tiers_west.py` says where each one stops and what holds it there rather than
listing what is absent.
