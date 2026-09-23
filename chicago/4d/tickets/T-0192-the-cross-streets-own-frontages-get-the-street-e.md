---
id: T-0192
title: The cross streets' own frontages get the street edge
state: blocked-tech
epic: TOWN
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-0127
opened: 2026-08-24
closed: null
pr: null
claimed_by: run 8/29/2026, 3:20:54 AM CT
blocked_on: the frame budget: all three scene-detail ceilings go over with the seven cross streets in (full +145,639, balanced +122,299, light +15,372 at T-0135's worst stand), and dev itself stands 6,927 and 6,107 triangles inside full and balanced before a board is laid, so not even the smallest cross street fits. The code half is done and shipped; this is one tuple when the headroom is won back.
needs_bake: false
---

The cross streets' own frontages get the street edge.

Piece 3 of 5 of **T-0127 — The rest of the town gets the street edge**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

**Acceptance, stated before working:** the seven cross streets carry the same plank walk
the covered east-west streets carry, laid by the same rule and not by a hand-placed
exception, with board crossings round the corners so the walk is walkable end to end —
and all three scene-detail tiers stay inside their ceilings at the whole T-0135 stand
set. Never by weakening a gate, and never by a sixth ceiling raise.

---
## 2026-08-29 — THE CODE HALF IS DONE; THE GEOMETRY IS REFUSED BY A MEASURED NUMBER

Two separate things refused this ticket, and only one of them was ever a number.

**The code half, and it is finished.** `_edge_faces` in
`tools/generate_frontage_works.py` enumerated a block's NORTH and SOUTH faces only. An
east-west street bounds a block on those; a cross street bounds it on its EAST and WEST.
So naming Clark Street in the covered tuple would have laid nothing at all — silently,
with no refusal on the record — whatever the frame budget said. All four faces are
enumerated now, and every ordering in that generator is axis-aware: a face's position
along Lake Street is its easting and along Clark Street its northing, so the face sort,
the along-a-side corner crossings and the across-the-road pairing all read the street's
own axis. A cross-street face carries no fence and no hitching post, and that is the
plat's answer rather than a gap — both rules are per-lot and every one of Thompson's
lots fronts an east-west street, so a cross-street face is the END of a lot row. It is
written as a refusal on the record, not left as a silence.

**The geometry half, measured rather than estimated.** All seven were generated,
published and read with `tools/measure_detail_ceilings.mjs` at T-0135's five stands,
desktop 1280x800, against `dev` at `83a4e221` in the same run. They are 34 platted faces
and **+3,557.7 m of walk** with +30 crossings — the record goes 36 faces / 3,170.7 m to
70 / 6,728.4 m, more than doubling it.

| tier | ceiling | `dev` worst | with the seven | over by | `dev`'s headroom |
|---|---:|---:|---:|---:|---:|
| `full` | 1,400,000 | 1,393,073 | **1,545,639** | 145,639 | 6,927 |
| `balanced` | 1,210,000 | 1,203,893 | **1,332,299** | 122,299 | 6,107 |
| `light` | 785,000 | 763,410 | **800,372** | 15,372 | 21,590 |

All three tiers, including the one a weak machine boots into. **And the binding fact is
not the cross streets**: `dev` itself stands 6,927 and 6,107 triangles inside `full` and
`balanced` — half of one per cent — before a board is laid. That is T-0237's finding
restated at this rung two days later. The SMALLEST of the seven, Market at 208.8 m, is
about 7,500 triangles at `balanced`'s own measured 36 a metre, so **not even one street
fits in 6,107**, and shrinking below one street is a hand-placed exception rather than
the rule this record is.

**So the ticket is blocked on the frame budget and not on anything in it.** What ships
here is the half that is done, plus the measurement on the record's own `refused` where
the next reader will find it. The east/west path would otherwise be dead code — written,
measured once and never executed again — so `tools/test_frontage_faces.py` drives the
whole seven through the rule on every commit (34 faces, both sides paired, ordered by
northing, outward normals across their street) and `check.sh` runs it with its own
self-test. The day the headroom is won back, this ticket is one tuple.

**Withdrawn from this ticket:** PR #418 (2026-08-27) laid Market Street alone on the same
code and parked on `hold` at 16,196 triangles over `balanced`. It was measured against a
`dev` 87 commits older; re-measured here, Market still does not fit. That branch is
superseded by this one.

**Links:** T-0127 (parent) · T-0190 (Randolph, built and measured and taken back out) ·
T-0193 (the West Division block, blocked on the same rung) · T-0237 (the headroom) ·
T-0135 (the stands) · T-0223 · T-0146 · T-0209.
