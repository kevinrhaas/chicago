---
id: T-1484
title: Carry the North Division parcel's nine roofs across that surface: the recipe's family, suffix, inventory_class and totals re-dealt, generate_north_infill re-deriving byte for byte, the assets renamed, the household workplaces resolved, rebaked and published
state: withdrawn
epic: TOWN
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1480
opened: 2026-09-20
closed: 2026-09-21
pr: null
claimed_by: run 9/21/2026, 10:20:44 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-21T15:22:26.199Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35617821153
---

Carry the North Division parcel's nine roofs across that surface: the recipe's family, suffix, inventory_class and totals re-dealt, generate_north_infill re-deriving byte for byte, the assets renamed, the household workplaces resolved, rebaked and published.

Piece 2 of 2 of **T-1480 — Migrate the North Division parcel's nine refamilied roofs whose id moves: the recipe's family and suffix columns re-dealt, generate_north_infill re-deriving byte for byte, the assets renamed and every file on the measured reference list carried across — the lodging model, the lodgers, the seating, the business layer and the signage and yard the old family earned — with tools/execute_roof_redeal.py --migrate/--check as the executor, rebaked and published**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

## FOUND 2026-09-21 BY THE RUN THAT CLAIMED AND WITHDREW THIS (T-1499's run)

This ticket's work appears to be ALREADY IN `dev`, carried out by **#1596**, whose
commit is titled "T-1480: migrate the North Division parcel's nine refamilied roofs".
T-1480 had already been split into T-1483 and this ticket by the time that PR merged,
so the PR closed the parent and left the child open. Three measurements, all off the
committed tree, none of them requiring the ticket to be re-run:

- `docs/RESEARCH/1835_roof_id_migration.md` — the surface T-1483 measured and the one
  every carry-out stands on — now reports **6** moving ids, and every one of them is a
  `recon_1835_blk_*` id in the three platted blocks. It names no North Division roof.
- `data/reconstruction/1835_roof_redeal.json` returns **9** refamily verdicts: the six
  platted-block roofs and three West Division roofs. None is a North roof.
- `tools/execute_roof_redeal.py --check-migration` is green, which asserts of each of
  the nine North roofs that the adjudication now returns `keep` and that no live
  reference names the id it left behind.

**And the queue carries the same work twice over.** T-1495 is "piece 2 of 3 of T-1452"
and asks for the North Division parcel's nine roofs — this ticket's ask, under another
number. T-1482 and T-1496 are likewise the same three platted blocks. T-1481 (the
phase-one South parcel's eleven) reads as already carried out by **#1600**. So of the
five migration rows standing in the queue, the only outstanding work is the platted
blocks, and it is written down twice.

A run picking the top of the queue spends its first twenty tool calls discovering
this, which is why it is written here rather than only in a PR body. Closing or
merging these rows is the owner's ordering decision, not a loop's, so nothing has been
reordered or closed — only measured.
