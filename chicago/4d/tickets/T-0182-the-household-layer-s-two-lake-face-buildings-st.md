---
id: T-0182
title: The household layer's two Lake-face buildings stand on a hand-authored coordinate, not on the face they front
state: done
epic: TOWN
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-24
closed: 2026-08-27
pr: 420
claimed_by: run 8/27/2026, 6:20:52 PM CT
blocked_on: null
needs_bake: false
---

`inf_bakery_lake` and `inf_butcher_market` stand on the Lake face of `blk_lake_clark` and
neither of them knows it.

Found by T-0104 while measuring that face. `tools/generate_inferred_households.py` places both
from a hand-authored `center_local_enu_m` in
`data/reconstruction/1835_inferred_household_programme.json` — `[619, -132]` and `[659, -132]`,
at `rotation_deg: 0` — and the face itself runs at bearing **0.465**. Measured off the committed
block boundary their front walls land at **0.804 m** and **0.784 m**, where the seven frontage
records on that face all stand at 0.800 m. So they are not on the line and they are not parallel
to it; they are near it, by arithmetic nobody re-derives.

Two consequences, and the second is the one that costs something:

- **The party wall does not close.** `recon_1835_south_d3_013` declares
  `frontage.abuts: inf_butcher_market` — a shared wall, gated as a shared wall — and the two
  front walls are 0.016 m apart. `tools/measure_street_line.py` banks that residual by name and
  by size (it may shrink, it may not grow); nothing else in the repository could see it, because
  both generators' own frontage gates only read their own run.
- **L141's 0.80 m rests on it.** The row's own note says its setback is "the alignment the two
  frontage buildings already standing on this face use". It is: two free-ground placements,
  neither of which is on a line. The face's street line is therefore a reading of a coincidence.
  It is now ONE line town-wide-per-face (T-0104) and that is worth having, but the number's
  warrant is weaker than the note claims.

Sixteen millimetres is invisible, so this is not urgent — what it is, is the last hand-typed
coordinate standing on a committed block face, which is the exact defect
`tools/block_faces.py` and the plat module exist to retire.

**Acceptance:** both buildings stand ON the committed face — their line, bearing and position
read from `data/traces/vectors/thompson_lots.json` rather than authored in the programme — with
their front walls on the face's one street line and the party wall with
`recon_1835_south_d3_013` closing to the 5 mm tolerance every other join uses. The banked
residual in `tools/measure_street_line.py` is removed in the same commit, not relaxed. No roof
is added, removed, renamed, re-familied or re-dimensioned, and the household programme's totals
do not move.

**Links:** T-0104 · L141 · L177 · `tools/measure_street_line.py` § `BANKED_PARTY_WALLS` ·
`tools/generate_inferred_households.py`.
