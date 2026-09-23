---
id: T-0474
title: Reconstruct the 1880s Prairie Avenue street, parcel and service grid
state: open
epic: SOUTH_TIME
requested_by: owner
seen: false
effort: M
legacy_id: null
opened: 2026-09-01
closed: null
pr: null
claimed_by: null
blocked_on: T-1252
needs_bake: true
---

Build the urban framework the mansion records must sit on: Prairie, Calumet and Michigan-area streets and the east-west tiers from roughly 16th through 22nd/Cermak, with period widths, sidewalks, alleys, lots, curbs and service access appropriate to the chosen 1880s scene date.

Derive geometry from period plats, atlases and fire-insurance maps; do not back-project today's curb lines where the period maps disagree. Include the Illinois Central/lakefront edge where it affects access or sightlines. Treat modern address numbers as cross-references, not primary period geometry.

Acceptance: each Prairie Avenue landmark ticket can cite a stable period parcel/lot and street face; major streets and alleys render on the correct terrain; lot boundaries have source/tier metadata; and the grid reaches the whole 16th-to-22nd corridor without relying on modern OSM as the historical source.

**Blocker repointed 2026-09-17 (T-1249).** T-0473 was split into T-1249 (the representative scene
date and the epoch record), T-1250 (the lake edge), T-1251 (the terrain spec) and T-1252 (the
heightfield, the bake and the scene file). This ticket's dependency was never on the parent as
such — it is on the GROUND, which is T-1252's, so `blocked_on` now names that piece. The date it
resolves against is settled: **1 July 1888**, `data/terrain/1880s_scene_date_constraints.json`.
