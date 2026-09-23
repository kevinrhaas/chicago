---
id: T-0403
title: The Democrat's office keeps its 1834 corner through a merge, and the paper moved along South Water Street before the scene date
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-29
closed: 2026-09-11
pr: 1158
claimed_by: run 9/11/2026, 6:37:00 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-12T00:28:41.309Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34658581918
---

Found while judging T-0399's restyle clusters, and it is a placement fact rather than an
identity one.

`placement_rank()` in `tools/compile_gazetteer.py` prefers a CORNER to a relative offset,
and a firm merge takes the higher-ranked placement of the two. So when
`the Chicago Democrat's printing office` (1834-01-07 c006, *in the building on the corner of
South Water and Clark streets*) merged into `Chicago Democrat printing office` (1835-05-20
c007, whose colophon reads *over Messrs. Jones & King['s] Hard[ware store]*), the surviving
record kept the EARLIER address because it is the more precise CLASS.

That is the wrong answer for a scene dated 1835-07-01, and the paper is unusually well
witnessed about it:

    1833-11-26 c033 · 1834-01-07 c006 · 1834-08-27 c009 · 1834-09-17 c010 · 1834-12-03 c023
        the corner of South Water and Clark streets
    1834-10-08 c005
        that store — 'now occupied by W. Kimball, and as the office of the Democrat' —
        is OFFERED FOR SALE, possession in November
    1835-05-20 c007 · 1835-08-05 c026
        South Water street, OVER MESSRS JONES & KING'S HARDWARE STORE

So the office moved, the corpus says when, and three records now assert the corner at the
scene date: `The Chicago Democrat`, `Chicago Democrat printing office`, and this project's
own `data/structures/chicago_democrat_office.json`, which rests on the 1833 issue and on
Andreas.

Two things are tangled here and they should be untangled before either is fixed:

1. **The machinery.** A merge that must choose between two placements chooses on precision
   and never on date. A corner read eighteen months before the scene date is not better
   evidence for where a house stood at the scene date than a relative offset read six weeks
   before it. Whether `placement_rank` should be date-aware, or whether the merge should
   keep BOTH readings the way `trade_variants` keeps both trades, is a change to
   `docs/GLB-CONTRACT.md`'s sibling contract in the gazetteer and should be proposed rather
   than made.
2. **The town.** If the Democrat office building on the ground is placed from the 1833
   corner, it is placed from a reading the paper itself superseded, and that is a structure
   record with a source question, not a compiler question.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- The Democrat's office at 1835-07-01 stands at ONE address in the register, and the
  reading it stands on is the latest one the corpus carries, or the record says in words
  why the earlier one outranks it.
- Whatever is decided about `placement_rank` is decided once and written where the next
  merge will read it, not patched at this one house.
- If `data/structures/chicago_democrat_office.json` moves, it re-bakes in the same commit.

Links: T-0399 (which found it), T-0304 (the firm-merge machinery), T-0402.
