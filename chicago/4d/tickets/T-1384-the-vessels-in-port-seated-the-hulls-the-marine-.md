---
id: T-1384
title: The vessels in port seated: the hulls the Marine Journal enters at Chicago across the scene date, each with her master, last port and cargo, moored to the reach and carrying nobody
state: done
epic: META
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1372
opened: 2026-09-19
closed: 2026-09-19
pr: 1518
claimed_by: run 9/19/2026, 7:43:04 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-19T13:10:11.921Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35443021089
---

The vessels in port seated: the hulls the Marine Journal enters at Chicago across the scene date, each with her master, last port and cargo, moored to the reach and carrying nobody.

Piece 1 of 2 of **T-1372 — Crews, the works gang and the guest lists: the vessels in port and the pier-works hands seated, and every lodging card printing who lived there**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** The four hulls that lay at Chicago at nightfall on 1835-07-01, and the two
that cleared on the day itself, are each a record in
`data/reconstruction/1835_vessels_in_port.json` carrying the rig, the master, the last port
and the cargo the Marine Journal of 4 July 1835 prints beside her, the dated lines she is
entered on, and a mooring that resolves to the river reach off committed geometry and
authors no coordinate; the cohort model's `vessels_lying_at_chicago_on_1_july_1835` figure
and its port table are RE-DERIVED from those records rather than from a list typed into the
generator; and `--check` fails if a hull drifts from the column's own words, authors a
coordinate, claims a berth, or acquires a crew.
