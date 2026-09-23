---
id: T-0684
title: The South Branch bank spike, resolved against Wright's own ink line, and the departure scan run over every water feature
state: done
epic: GROUND
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-0453
opened: 2026-09-04
closed: 2026-09-04
pr: 800
claimed_by: run 9/4/2026, 2:24:28 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-04T19:43:14.816Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33909450806
---

The South Branch bank spike, resolved against Wright's own ink line, and the departure scan run over every water feature.

Piece 1 of 2 of **T-0453 — The river banks are traced from Wright 1834 and the owner reads the Thompson plat differently at Wolf Point**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

This piece carries T-0453's acceptance 5 and 6 — the named defect on the South
Branch and the scan that makes sure it is not fixed while its siblings survive.
T-0453's acceptance 4 governs it: **nothing moves.** A vertex is not deleted
because it looks wrong; the source is re-read and the reading is recorded.

T-0453's acceptance 1, 2 and 3 — the Thompson plat traced beside the Wright
line, the disagreement measured, the owner's ruling — are T-0685, because the
Thompson sheet has never been georeferenced in this project and its own source
record forbids tracing it for geometry until it is.

**Acceptance:**

1. The committed river geometry is shown to be the trace's own output and not a
   hand edit: `tools/trace_river.py --check` re-fetches the Wright 1834 region
   and reproduces `river.geojson` byte for byte, and the run is recorded.
2. The spike at local (87.2, -96.8) is resolved **against the drawn bank**, not
   against its own neighbours: every bank vertex is measured to the nearest
   inked bank pixel on the scan, so the finding is about the source rather than
   about the shape of the polyline.
3. The neighbour-departure scan is run over **every** water feature of the epoch
   — the river polygon, all three bank lines, the harbour reach, the sand bar,
   both harbour shores and the north-side slough — and every vertex above the
   tolerance is listed, ranked, with its local ENU position.
4. The scan is a committed tool that anyone can re-run, not a number in prose.
5. Nothing in `data/terrain/` moves.
