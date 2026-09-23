---
id: T-1483
title: Measure and gate the migration surface the 26 moving ids stand on: every reference classified renamed, re-derived, frozen or adjudicated, with the seven inferred-household workplaces and the two signage and yard refusal rows a bare rename would falsify named — a derived report and a --check in check.sh that refuses drift, so the three carry-out tickets are mechanical
state: done
epic: TOWN
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1480
opened: 2026-09-20
closed: 2026-09-20
pr: 1588
claimed_by: run 9/20/2026, 1:51:51 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-20T19:12:57.179Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35529393603
---

Measure and gate the migration surface the 26 moving ids stand on: every reference classified renamed, re-derived, frozen or adjudicated, with the seven inferred-household workplaces and the two signage and yard refusal rows a bare rename would falsify named — a derived report and a --check in check.sh that refuses drift, so the three carry-out tickets are mechanical.

Piece 1 of 2 of **T-1480 — Migrate the North Division parcel's nine refamilied roofs whose id moves: the recipe's family and suffix columns re-dealt, generate_north_infill re-deriving byte for byte, the assets renamed and every file on the measured reference list carried across — the lodging model, the lodgers, the seating, the business layer and the signage and yard the old family earned — with tools/execute_roof_redeal.py --migrate/--check as the executor, rebaked and published**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

**The surface as measured, 2026-09-21 — read this before T-1484 moves anything.**

`tools/measure_roof_id_migration.py --build` on the merged tree:

> 26 moving id(s) across **75** file(s): 2 adjudicated, 19 renamed, 50 re-derived, 4 frozen

The file count is **75, not the 74 this PR first reported** — dev has since added a file
that names a moving id. That drift is the whole point of gating the surface rather than
writing it down once: the list T-1484 works from has to be re-measured on the tree it
actually runs against, never carried across from this ticket's prose.

The tool is a pure reader — its only output is `docs/RESEARCH/1835_roof_id_migration.md`,
and its writer-inventory row is measured with a real perturbation test (bend the header's
"26 moving id(s)" to 999, a bare run goes red with `DRIFT: ... is not what a re-measurement
produces`, `--build` restores it, tree clean). `measure_step_isolation.mjs --build` re-ran
the whole gate instrumented and serial: **398 tools measured, 593 steps declared, none of
them writes the live tree.**

**No changelog entry, deliberately.** This ticket measures a surface and adds two gate
steps. It renames nothing, moves no roof, and changes nothing a visitor or the release feed
can see — T-1484 is the migration, and that one will ship an entry. Recorded as a
`Changelog: none` trailer rather than left for the gate to trip over, which is what happened
here: `tools/check.sh` does not run the changelog-entry gate, so a branch can be green
locally at 593 steps and still red in CI on a missing entry.
