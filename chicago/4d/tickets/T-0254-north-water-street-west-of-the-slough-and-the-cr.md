---
id: T-0254
title: North Water Street west of the slough, and the crossing it needs
state: done
epic: TOWN
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-27
closed: 2026-08-28
pr: 473
claimed_by: run 8/28/2026, 10:43:06 AM CT
blocked_on: null
needs_bake: false
---

North Water Street west of the slough, and the crossing it needs.

Filed by T-0226, which re-derived North Water Street from the committed north bank after
finding its old line 477.4 m inside the water mask. The derived line begins at
`[240, 136.5]`, on the east shoulder of the attested "Unnamed slough, north side"
(`data/terrain/epochs/e1834_harbor_cut/hydrology.geojson`, confidence `attested` — Wright
1834 draws it running north out of the main stem, across Kinzie Street, to Michigan
Street) and 16.5 m clear of its nearest water. West of that the street is not carried.

**Why it stops there rather than crossing.** The slough meets the river in a funnel
between E +170 and E +270 reaching N +145; north of the funnel the channel narrows to
about 5-7 m. R-BUG4 forbids a ribbon painting a ford, and the town's other two slough
crossings are modelled STRUCTURES on the street rather than roadway —
`data/structures/slough_log_bridge.json` on Water Street and the La Salle Slough Crossing
on South Water Street, both held by `tools/measure_slough_crossing.py`. A third one here
is the same shape of work, and it is not a line edit.

Note that a panel is only DROPPED when a centreline endpoint is wet, so simply carrying
the line across the narrow reach would draw a 7 m ford in silence — the fault this
ticket exists to avoid, not a shortcut past it.

**Nothing drawn is lost by deferring it.** The old line's west end at `[200, 55]` was
85.8 m out in the river and the renderer drew no roadway there at all.

**Acceptance:** either a crossing record on North Water Street at the slough, gated by
`tools/measure_slough_crossing.py` alongside the two that exist, with the street's line
carried west of it to the North Branch by `tools/derive_north_water.py`; or a stated
finding that the reach cannot be carried, with the evidence, in `docs/RESEARCH/`.

**Links:** T-0226 · `docs/RESEARCH/north_water_street_and_the_bank.md` ·
`tools/derive_north_water.py` · `tools/measure_slough_crossing.py` · ROADMAP **B-BUG4**.
