---
id: T-0266
title: On a phone from across the river the stockade's picket rhythm falls under the pixel grid and beats
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-28
closed: 2026-09-13
pr: 1239
claimed_by: run 9/13/2026, 2:53:34 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-13T08:16:40.453Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34746186584
---

On a phone from across the river the stockade's picket rhythm falls under the pixel grid and beats.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Found by T-0185, which measured whether the fort's picket rhythm reads as posts at the stands a
visitor occupies and found that at one of them it does not.

Measured (`tools/measure_picket_reading.mjs`, published mirror, `full`): from `p4_0`'s own stand
on the north bank — local 1145, 300, yaw 180, fifty metres off the north curtain — the whole 53 m
wall is drawn across 287 px on a 390x780 phone, so the record's 0.30 m pitch is **1.62 px**. The
column profile nonetheless autocorrelates +0.66 at **4 px**, with a harmonic at 8 — a rhythm two
and a half times coarser than the wall has. That is a moire: the picket line beating against the
pixel grid it has fallen under. On a desktop at the same stand the same reach measures 4 px
against an expected 4.49 px, +0.93 with a +0.85 harmonic, and is simply resolved. At the north
gate the wall resolves on both viewports (34 px desktop, 16 px phone).

**This is not an argument for coarsening the wall.** T-0185 settled that the fine rhythm is right
at every range a visitor can choose, and the one and only picture of this fort is coarse for the
same reason this shot is confused — its medium could not hold the gap. What is unanswered is what
the renderer should DO about a 1.62 px rhythm on a phone: a beat that moves as you walk is worse
than a wall that has quietly gone smooth, and neither has been compared against the other here.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

Whether the phone's moire is worth answering is decided against a measurement of what the
alternatives cost, not against a screenshot; if it is answered, the wall still resolves as posts
at the north gate on both viewports and `measure_picket_reading.mjs` reads the river stand
resolved or smooth rather than beating. Evidence at `docs/evidence/t-0185-p4_0-phone.png`.

**Links:** T-0185 (the pass that found it, and why the rhythm is not the thing to change) ·
T-0094 (the plate's own reading) · `tools/measure_picket_reading.mjs` (the instrument) ·
docs/RESEARCH/fort_dearborn_image_accuracy.md.
