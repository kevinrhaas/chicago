---
id: T-1249
title: The 1880s representative scene date, and the e1871_postfire epoch record it selects
state: done
epic: SOUTH_TIME
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0473
opened: 2026-09-17
closed: 2026-09-17
pr: 1403
claimed_by: run 9/17/2026, 10:16:44 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-17T16:19:23.324Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35238482063
---

The 1880s representative scene date, and the e1871_postfire epoch record it selects.

Piece 1 of 4 of **T-0473 — Create an 1880s South Side terrain and urban-ground epoch**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

1. The representative date is **chosen from landmark construction dates that are committed as
   sources and quoted**, not from memory and not from the open web. At least one retrieved record
   must supply a hard bound, and a record opened for a date that turns out not to carry one is
   committed in that state rather than dropped.
2. The date is **derived, not typed**: one committed readings file carries the bounds, the window
   and the arithmetic, and a gate step re-derives it on every commit and refuses a hand edit.
3. `e1871_postfire` stops being a placeholder — it carries the date, its derivation, its research
   doc and a `layer_status` naming which sibling ticket owes each unwritten layer.
4. `shore_1880s_ic_edge` addresses the same day, and **still has `geometry: null` and
   `status: planned`** afterwards. Settling a date may not buy a coastline; the gate must fail if
   it does.
5. The undocumented `date(1885, 7, 1)` in `tools/check_shoreline_states.py` is **removed**, not
   corrected, and the date it was replaced by is recorded together with what it was.
6. `tools/check.sh` green, its self-tests fire when the derivation is broken, and the arbitrary
   half of the choice is in `docs/LIBERTIES.md`.

**Out of scope, stated so the next run does not look for it:** no `data/scenes/1880s.json` — a
scene must stand on a heightfield and there is none, so the scene file lands with T-1252.
