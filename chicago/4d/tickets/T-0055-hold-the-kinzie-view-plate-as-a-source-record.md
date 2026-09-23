---
id: T-0055
title: Hold the Kinzie-view plate as a source record
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-18
closed: 2026-09-13
pr: 1252
claimed_by: run 9/13/2026, 7:49:08 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-13T13:50:49.199Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34757978313
---

Hold the Kinzie-view plate as a source record.

Found by T-0052, which needed it and could not have it. The plate — the Kinzie mansion group,
plate "12", showing the piazza front, the row of Lombardy poplars and the picket-fenced garden
plots — is the ONLY picture this project has of a garden fence in Chicago, and it reaches the
repository as an owner-supplied reference image with a README and nothing else. There is no
`chicagology_*` source record for it, which is why `data/enclosures/town_dooryard_pickets.json`
carries an EMPTY `existence.sources` and cites a committed path instead. The README itself gives
the instruction: *"Anything used in a critique loop should be identified against chicagology's
plate numbering first and cited to the matching `chicagology_*` source record."*

Note it is tier 5 pictorial and retrospective, so it may drive massing, materials and setting as
`inferred` and may never drive a coordinate — the record has to say so, the way its siblings do.
Check `rights_status` before anything derives an asset from it.

**Acceptance:** a source record in `data/sources/` for the plate, resolving from
`data/enclosures/town_dooryard_pickets.json` and from `docs/ROADMAP.md` K5 (a), with its tier, its
rights status, what it attests and what it does not; and the enclosure record's `sources` filled in
where the citation is now a path.

**Links:** `data/sources/assets/prefire_views_kevin_2026_08/README.md` · `docs/LIBERTIES.md` L129 ·
T-0052.
