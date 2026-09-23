---
id: T-1017
title: Is buying at the town's OWN school-section sale a check on a town-side name, or still a bare name? SKINNER JOSEPH and RUSSELL SAMUEL both turn on it
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-10
closed: 2026-09-13
pr: 1297
claimed_by: run 9/13/2026, 7:46:24 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-14T01:27:17.165Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34793537432
---

Is buying at the town's OWN school-section sale a check on a town-side name, or still a bare name? SKINNER JOSEPH and RUSSELL SAMUEL both turn on it.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

The question is *what kind of argument is admissible*, so the answer has to be a RULING and it
has to be reached by counting rather than by how the argument sounds.

- The sale is defined from the register's own record and not from a date range this project
  picked: which rows it is, over which days, by how many purchaser spellings, for how much.
- The argument FOR admitting it is measured first and stated at its strongest — if the sale is
  richer in town-side names than the rest of the register, say by how much, and say it in a
  measurement that uses no adjudication, so it cannot be an echo of rulings already made.
- The ruling is then reached and written where the rulings live, in
  `data/research/land_sales/resident_rulings.json`, naming what it changes. If it retracts
  anything, every retraction is named; if it retracts nothing, that is stated as a result and
  not as an absence.
- Whatever the answer, the figures it turns on are ASSERTED in `bash tools/check.sh`, not
  merely printed — the residents layer grows every week and the crosswalk re-derives from it, so
  a ruling resting on a measurement must go red when that measurement moves, and reopen.
- The reasoning is readable: a `docs/RESEARCH/` note and a section in this domain's README, both
  naming what was NOT done.
- `bash tools/check.sh` green. No card, grade or row moves — this ticket rules on an argument,
  not on a person. No bake.
