---
id: T-1098
title: The West Division past Clinton read by the block-cut method - 8-13, 22-27, 46-51
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-1095
opened: 2026-09-12
closed: 2026-09-12
pr: 1221
claimed_by: run 9/12/2026, 7:56:38 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-13T01:35:46.933Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34728455576
---

The West Division past Clinton read by the block-cut method - 8-13, 22-27, 46-51.

Piece 1 of 2 of **T-1095 — The West Division past Clinton (8-13, 22-27, 46-51) and 14-15 on the North Branch's west bank: still no committed street line reaches them**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** every one of the eighteen West Division numerals — 8-13, 22-27, 46-51 — is read by
the T-0788 block-cut method, one crop per block, each cut from that block's own committed street
lines by a tool the gate re-runs, or it is refused in writing. No numeral located by eye. Where a
box's side is not a committed line, the rule that stands in for it is stated in the tool and in the
memo, the substitution is corroborated against control this repository already holds, and the
reading is graded no better than `inferred`.

**Done, 2026-09-13.** Eighteen numerals: **8 9 10 11 12 13**, **22 23 24 25 26 27**, **46 47 48 49
50 51**. Fifty-six of Wright's fifty-eight blocks are read.

- `tools/read_west_division_numerals.py` cuts the boxes and `tools/check.sh` runs its `--check` and
  `--self-test`. Four boxes are flanked by two committed lines; the five tier lines are committed but
  clipped at east −400/−320 m and are continued west along their own bearings; Jefferson and Des
  Plaines are `clinton` stepped one and two modules west, because both streets stay REFUSED
  (`docs/RESEARCH/west_division_streets.md` §2) for standing wholly west of the modelled ground.
  Nothing is written into `data/streets/1835.json`.
- The step is corroborated three ways from control already committed: it reproduces `canal` to
  **0.46 m** at Lake Street and **2.34 m** at the scene's south edge, and lands **8.70 m** and
  **8.22 m** west of the two surviving intersections T-0446 committed in `fulton`'s note — both to
  the same side. The gate re-measures all four and fails above 15 m.
- The reading asserts the boustrophedon **across other tickets' blocks**: 26 27 joins T-0788's 28 29
  rising eastward, 47 46 joins its 45 44 43 falling eastward, 48 49 50 51 runs into T-1094's 52, and
  10 9 8 joins T-1088's 7 across the North Branch. All four joins hold.
- Eighteen boxes, eighteen numerals inside them, **no overhang anywhere**.
- They wait in `blocks_not_in_the_grid`: `generate_plat_lots.py` emits nothing west of the river, so
  there is no cell to stamp them onto.

Two blocks are left and they are T-1099, which also carries the collision this run found: a glyph
reading as 14 stands inside the box T-1088 cites for block 7.
