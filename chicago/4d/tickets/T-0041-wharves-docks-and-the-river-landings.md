---
id: T-0041
title: Wharves, docks and the river landings
state: done
epic: TOWN
requested_by: owner
seen: true
effort: S
legacy_id: K5
parent: T-0003
opened: 2026-08-17
closed: 2026-08-18
pr: 239
claimed_by: run 8/18/2026, 6:02:05 AM CT
blocked_on: null
needs_bake: false
---

Wharves, docks and the river landings.

Piece 4 of 4 of **T-0003 — Town furniture: fences, signboards, wagons, porches, docks**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (stated 2026-08-18, before the work, and not weakened to pass)

The two records in this dataset that state a dock — `newberry_dole_warehouse` (`inferred`) and
`kinzie_hunter_warehouse` (`attested`), both of which carry `geometry: "absent"` over that
statement today — stand at a **drawn timber wharf on the water in front of them**: a plank deck
along the bank on crib bents, its outline derived from the committed bank trace, the committed
footprint and the committed heightfield by a rule that reads the records' own `dock` attribute,
re-derived byte for byte by `tools/check.sh`; every vertex graded `reconstructed`; the invention
claimed in `docs/LIBERTIES.md`; the two `geometry: "absent"` declarations corrected to what now
stands; a pick on a wharf opens the warehouse behind it; and the layer measurably reaches the
screen from the bank at 390×780 and 1280×800 with zero page errors.
