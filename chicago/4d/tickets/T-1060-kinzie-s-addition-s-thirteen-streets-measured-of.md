---
id: T-1060
title: Kinzie's Addition's thirteen streets, measured off Wright's sheet and seated on the committed grid
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0789
opened: 2026-09-12
closed: 2026-09-12
pr: 1182
claimed_by: run 9/12/2026, 3:21:34 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-12T08:52:21.346Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34682047965
---

Kinzie's Addition's thirteen streets, measured off Wright's sheet and seated on the committed grid.

Piece 1 of 4 of **T-0789 — Kinzie's Addition is on the sheet whole — 54 numbered blocks, 13 named streets, the Kinzie Block and the river-front water lots — and the North Division carries four streets**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (stated before working)

1. All thirteen streets of Kinzie's Addition are in `data/streets/1835.json` — the eleven
   the layer lacked, plus `michigan_north` and `wolcott` carried to the tract's edge.
2. Every corridor is READ off the sheet, not assumed: the two ruled lines bounding it, in
   raster pixels, with the window they were found in, in a committed trace file that a
   tool re-derives.
3. The corridor width question the parent asks is ANSWERED WITH ITS CONTROL — the Original
   Town's platted 80 ft corridors measured on the same sheet by the same method, so the
   Addition's width is a ratio and not a number off a warped raster.
4. The extents are the reading's: a street is committed only as far as a window found its
   rules, and where the sheet carries it further the note says so and names the ticket.
5. `tools/check.sh` green, and both halves of the new reading gated in it.
