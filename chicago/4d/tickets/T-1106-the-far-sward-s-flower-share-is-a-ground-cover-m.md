---
id: T-1106
title: The far sward's flower share is a GROUND-COVER mix, and a visitor at fifty metres reads SILHOUETTES — T-0280 cost prairie_west every head past 26 m
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-13
closed: 2026-09-13
pr: 1248
claimed_by: run 9/13/2026, 6:45:10 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-13T12:21:12.240Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34755100922
---

The far sward's flower share is a GROUND-COVER mix, and a visitor at fifty metres reads SILHOUETTES — T-0280 cost prairie_west every head past 26 m.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Found by T-0280, which caused it.** T-0280 took the forb ring's lattice ceiling out of the far
band's grass-or-flower split and put both sides of the ratio into the same unit — the fraction of
GROUND each stratum covers. That is right, and the split now varies with the records instead of
reading the constant 1.000 in eight of ten communities. It also cost the distant bloom almost
everything: at `prairie_west` the drawn heads go 2,522 → 1,993 and the furthest from 135.7 m to
26.4 m, and nothing survives past 40 m (`tools/measure_far_bloom.mjs --source`, desktop).

**The open question, and it is a real one.** Ground cover is the honest mix for ground. It may not
be the honest mix for a CARD SEEN FROM FIFTY METRES. At 50 m the line of sight is 1.9 degrees below
horizontal, the sward is seen edge-on as a wall, and what fills a pixel is the first element the ray
meets — so the quantity is silhouette-area density, `n × a`, not `n × footprint`.
`tools/measure_far_bloom.mjs` §1 already builds exactly that bridge for the BLOOM and states its
own liberty for it (an isotropic head disc). A compass plant at 1.8 m standing in 1.2 m grass
occupies more of that wall per square metre of ground than its footprint suggests, and the far
band's split does not know it.

**Acceptance** (state it before working — never weakened to pass): either the far band's split is
dealt on a silhouette quantity that is the same on both sides, with the mix and the drawn head
counts re-measured at `prairie_west`, `prairie_south` and `river_bank` against the ground-cover
reading T-0280 shipped and the difference stated per community — or the ground-cover reading is
defended in writing against the edge-on argument and this ticket withdrawn. Whichever way it goes,
the answer is a MEASUREMENT and not a tuning constant: no number enters this split that is not
summed off `data/flora`.

**Where to start:** `renderers/web/js/flora.js` `rebuildFar` and `subsetOn().cover`;
`tools/measure_far_split.mjs` (the before/after instrument, which would gain a third column);
`tools/measure_far_bloom.mjs` §1 (the silhouette model, already written);
`docs/STATUS.md` T-0280 and `docs/LIBERTIES.md` L235.
