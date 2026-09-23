---
id: T-1243
title: Author the e1830_natural terrain spec and generate the 1812 heightfield and the ground and water meshes across the Fort-to-Eighteenth-Street corridor
state: open
epic: SOUTH_TIME
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: T-0468
opened: 2026-09-17
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: true
closed_at: null
claimed_run: null
---

Author the e1830_natural terrain spec and generate the 1812 heightfield and the ground and water meshes across the Fort-to-Eighteenth-Street corridor.

Piece 2 of 2 of **T-0468 — Create an e1812 natural terrain epoch for the Fort Dearborn battle landscape**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

Starts from the planform T-1242 committed at `data/terrain/epochs/e1830_natural/shoreline.geojson`,
which claims NO elevation anywhere.

1. `data/terrain/epochs/e1830_natural/terrain_spec.json` is authored to the standard the
   `e1834_harbor_cut` spec sets: every elevation traces to a numbered zone in the terrain
   research, and no land elevation is graded better than `inferred`.
2. The spit's isthmus gets a surface and a height, or is written down as absent — it is
   `docs/LIBERTIES.md` L240 and `spit_attachment_gap_1812` is the feature that names the hole.
3. The 1812 river polygon and its banks follow from the spec; the heightfield and the ground
   and water meshes are generated, not hand-authored, and the Fort-to-Eighteenth-Street
   corridor is modelled ground.
4. The fit and provenance gates pass, including `validate.py --stale`; `./tools/publish.sh`
   runs in the same commit. This ticket is `needs_bake`.
5. T-0469, T-0470 and T-0471 are blocked on this ticket and unblock when it closes.
