---
id: T-0435
title: 30 of the 47 cat-and-clay stacks stand against an eave wall, and both the archetype and the fabric argument say gable
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-30
closed: 2026-09-13
pr: 1237
claimed_by: run 9/13/2026, 1:37:55 AM CT
blocked_on: null
needs_bake: true
closed_at: 2026-09-13T07:35:24.196Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34743086606
---

30 of the 47 cat-and-clay stacks stand against an eave wall, and both the archetype and
the fabric argument say gable.

**Measured by T-0333's per-stack instrument** — `tools/measure_stack_projection.py
--walls`, 2026-08-30, which classifies each stack against the roof's own ridge frame and
is archetype-blind about it. The reading agrees with what the code says it should build. `log_dwelling._stack` builds the first stack
against the core's **−x face** unconditionally, and `log_dwelling._roof` runs the ridge
along the **longer plan axis** (`_ridge_along_x`: `(x1-x0) >= (y1-y0)`). So a cabin deeper
than it is wide gets its stack against a LONG wall — an eave — and only a cabin at least as
wide as it is deep gets the gable the archetype describes.

- **17 stacks on 15 cabins** stand at a gable end: 0.720 m clear, every one of them.
- **30 stacks on 29 cabins** stand against an eave wall: 2.344 m to 3.197 m clear, because
  the flue runs up past a roof that is at eave height beside it and keeps going to the
  ridge. `brown_boarding_house` is the extreme at 3.197 m — a stack standing over ten feet
  above the roof surface it is built against.

**Why it is not cosmetic.** `log_dwelling._stack`'s own docstring says *"One exterior stack
against a gable end — the −x end, or mirrored to +x"*, and `docs/RESEARCH/chimneys.md` §3
argues the whole cat-and-clay FABRIC from that disposition: a stack *"built against the
gable so it can be pulled away from the building when it catches fire"*. Two-thirds of the
town's log stacks are not in the disposition the fabric argument is made from.

**Not a defect of the count and not a provenance fault.** The count is the record's; the
placement is the archetype's and `docs/LIBERTIES.md` **L26** owns it. Nothing here is
mis-sourced. What is wrong is that the code and the research file describe an arrangement
the geometry does not build.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- The census re-run reports how many stacks stand at a gable end and how many at an eave,
  and the eave figure is either **zero** — the stack follows the ridge to whichever end is
  a gable — or it is **argued and written into both** `log_dwelling._stack`'s docstring and
  `chimneys.md` §3, with the fabric consequence stated either way.
- If geometry moves, the affected masters are rebaked in the same commit
  (`validate.py --stale` will refuse the commit otherwise) and the before/after clearance
  is stated for at least `brown_boarding_house`.
- `tools/check.sh` green, including T-0333's eighteen-inch gate, which must not regress:
  an eave stack that follows the ridge to a gable end gets SHORTER, and 0.72 m is the
  figure it lands on.

Links: [[T-0333]] (the census and the gate), [[T-0008]] and [[T-0137]] (the fabric).
