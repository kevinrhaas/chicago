---
id: T-0446
title: Carroll and Fulton: two platted tiers the West Division has no street between
state: done
epic: GROUND
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-0443
opened: 2026-08-31
closed: 2026-09-04
pr: 805
claimed_by: run 9/4/2026, 2:21:18 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-04T20:38:23.084Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33909436862
---

Carroll and Fulton: two platted tiers the West Division has no street between.

Piece 3 of 4 of **T-0443 — The West Division's street grid is short three north-south streets and two east-west, and what is drawn as Canal may be Clinton**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

Four east-west streets reach west of the river, all stopping at east −320 m:
`kinzie`, `lake`, `randolph`, `washington`. The plat's West Division tiers run
north to south **Kinzie, Carroll, Fulton, Lake, Randolph, Washington**.

`carroll` and `fulton` are in no committed file, so two platted tiers have no
street between them and the preview shows unbroken ground where the sheet shows
two rows of blocks.

**Acceptance:**

1. `carroll` and `fulton` exist with sources and a stated `geometry_confidence`,
   or each is refused in writing with the reading that refuses it.
2. The tier spacing they imply is reported against the South Division's
   east-west spacings, the same way T-0444 reports the north-south module.
3. `tools/check.sh` green.
