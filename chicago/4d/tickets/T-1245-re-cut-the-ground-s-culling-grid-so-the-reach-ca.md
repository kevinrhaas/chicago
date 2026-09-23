---
id: T-1245
title: Re-cut the ground's culling grid so the reach can bite, and bring the downtown five inside all three ceilings at both viewports
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-1154
opened: 2026-09-17
closed: 2026-09-17
pr: 1406
claimed_by: run 9/17/2026, 9:27:04 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-17T17:00:21.415Z
claimed_run: null
---

Re-cut the ground's culling grid so the reach can bite, and bring the downtown five inside all three ceilings at both viewports.

Piece 2 of 2 of **T-1154 — The five downtown stands are over every scene-detail ceiling at both viewports, and the town has been over since some point after 6 September**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** the grid is re-cut by a rule that remains valid when the terrain
extent changes; the detailed ground is retained near the visitor and a continuous
lower-detail ground carries the same heightfield beyond it; walking, collision,
flora and structure anchoring remain on the original heightfield; and the gate's
five downtown stands fit under `full`, `balanced` and `light` at desktop and mobile
without moving any ceiling or exceeding the 215-call budget. The before, rejected
grid-only candidates, chosen rule and closing readings are committed.
