---
id: T-1104
title: The land sales sorted onto the survey tracts
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-1102
opened: 2026-09-13
closed: 2026-09-13
pr: 1230
claimed_by: run 9/13/2026, 12:20:20 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-13T05:49:45.298Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34739061978
---

The land sales sorted onto the survey tracts.

Piece 1 of 2 of **T-1102 — The land sales sorted onto the survey tracts, and the generators reading the tract layer**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

MEASURED ON THIS BRANCH, against dev at f640db76c.

Item 3 of the parent T-1097's four: *"Sort the land sales onto the tracts. Every row in
`data/research/land_sales/` that names a section or a tract gets the polygon it falls
in."* And the question `canal_section_9_remainder`'s own `owner_on_scene_date` refusal
defers here by name: *"The same seven 1830 canal entries cover section 9 as a whole;
which of them fall outside the Original Town is T-1102's question."*

- A derived record joining `data/research/land_sales/ground.json` to
  `data/reconstruction/1835_survey_tracts.json`, every share re-clipped by its own gate
  step and refused on drift. It authors no coordinate.
- The seven section-9 entries adjudicated against the Original Town polygon, with the
  answer stated as a measurement rather than as a sentence.
- Every refusal counted and reasoned, including the 616 town-plat lots — which stay
  refused under T-0830's standing rule, with the block-range argument that would get
  round it measured and shown not to work.
- `bash tools/check.sh` green. No bake.
