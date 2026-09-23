---
id: T-0887
title: A well layer, drawn renderer-side: the fort's well is measured to a coordinate and this project has no way to draw one
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-06
closed: 2026-09-11
pr: 1155
claimed_by: run 9/11/2026, 5:46:37 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-11T23:33:50.972Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34655233735
---

A well layer, drawn renderer-side: the fort's well is measured to a coordinate and this project has no way to draw one.

FOUND WHILE MEASURING T-0881. The 1830 Harrison plan marks the fort's well with a ring, and
T-0881 measured it: pixel (1446.5, 887.0) on leaf n242, which is 0.5 m east and 81.5 m south of
the enclosure's centre — **UTM 448225.20 E, 4637535.33 N**, all but exactly due south of the fort
and 52.6 m clear of the stockade's ink. Two witnesses agree on the place (Hubbard: *"in the outer
inclosure and near the south gate"*), and the derivation is banked in `docs/RESEARCH/wells.md` § 5
so nobody re-reads the plate.

**Why it is still invisible.** `data/structures.schema.json` offers twelve archetypes and none of
them is a well. The nearest, `outbuilding`, builds a walled and roofed shed. A structure record
with no buildable form does not validate, so the well cannot even be carried as an evidence
record the way `estray_pen` is — the pen has `data/enclosures/` and `renderers/web/js/enclosures.js`
behind it, and there is no equivalent here.

**Acceptance:**

1. A well record — its own small data shape, or a third `drawn_by.layer` beside `enclosures` —
   carrying the coordinate above, its grade, its sources and its note, so the fort's well is an
   evidence record a visitor can open.
2. Drawn RENDERER-SIDE, so it needs no archetype and no bake: a curb and nothing more unless a
   source says otherwise. What is invented (curb material, height, and whether it was worked by a
   sweep, a windlass or a rope) is admitted in `docs/LIBERTIES.md` with its own L-number.
3. The ring on the plate is a POINT SYMBOL and carries no dimension — its 14 px would be 4.7 m —
   so no size may be taken from it, and the record says so.
4. ONE documented instance only. T-0592 refused a well CLASS for the town and that refusal stands;
   this draws the one well this project can place, and mints no others.

**Links:** T-0881 · T-0592 · `docs/RESEARCH/wells.md` § 5 · **L60** (the estray pen's precedent) ·
`data/sources/harrison_1830_river_mouth.json`
