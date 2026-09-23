---
id: T-0452
title: The plat draws three sloughs off the Main Branch; this reconstruction holds one, as a centreline with no banks
state: done
epic: GROUND
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-08-31
closed: 2026-09-04
pr: 804
claimed_by: run 9/4/2026, 2:21:57 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-04T20:26:05.378Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33909457585
---

`data/terrain/epochs/e1834_harbor_cut/hydrology.geojson` holds **one** feature.
Its own note says:

> *"Wright 1834 draws a narrow winding watercourse running north out of the main
> stem, across Kinzie Street, ending at Michigan Street… this is a CENTRELINE
> because the bank wash survives only in 5 fragments… **Probably one of the three
> sloughs off the Main Branch shown on the 1830 Thompson plat.**"*

So the file already records that **the plat draws three and this holds one**, and
the one it holds is a `LineString` of 45 points with `drafted_width_m` and an
`assumed_depth_ft_below_datum` — **no banks, no polygon, no wet ground**. It is
`confidence: attested` for its existence and course, which is right, but nothing
downstream can stand a building off it or keep one out of it.

The owner marked the water north of the river on the dev preview on 2026-08-31
and asked that the slough be got right.

**Why this matters beyond the water itself.** T-0451 wants to lay the North
Division's grid, and the plat's own sloughs cross that ground — the committed one
runs north across **Kinzie Street** and ends at **Michigan Street**, both of which
this project already holds. A grid laid without them puts streets and lots over
water.

**Acceptance:**

1. The plat's **three** sloughs are read off the sheet and each is either
   committed with its course and source, or refused in writing with the reading
   that refuses it. "Probably one of three" is a note, not a dataset.
2. Where a slough crosses a committed street or a platted lot, that crossing is
   stated — this is the fact T-0451 needs and cannot derive.
3. Whether a centreline is enough is decided explicitly: if lots or buildings are
   to be kept out of the slough, it needs a width the ground can test, and that
   width is either sourced or declared as an invention in `docs/LIBERTIES.md`.
4. `tools/check.sh` green.
