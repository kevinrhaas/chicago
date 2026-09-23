---
id: T-0406
title: 'the Tremont House' resolves to nothing, because the committed record is named 'Tremont House (the first)'
state: done
epic: PAPERS
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-29
closed: 2026-09-05
pr: 911
claimed_by: run 9/5/2026, 2:03:46 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T19:48:33.296Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33985752856
---

`tools/compile_register.py` resolves a printed anchor against the committed town by
WHOLE-SET equality of identity-bearing words — deliberately, because containment would put
"the store" on the first store in the town. `the Tremont House` reduces to
`{tremont, house}`. The committed record is `tremont_house_1`, named **"Tremont House (the
first)"**, which reduces to `{tremont, house, first}`, and it carries no `aka`. The two
sets are not equal, so the register reports *"The anchor 'the Tremont House' names nothing
the committed town holds"* about a building this project models, has placed at the
north-west corner of Lake and Dearborn, and draws.

Measured on the T-0345 branch: `the Tremont House` is printed as an anchor for SIX houses
in the gazetteer, and not one of them is placed by it. Three resolve `unresolved` on that
word alone — `business_matthias_mason_co` (the live anchor of its dated change, T-0345),
`business_andrews_eells`, which is therefore `unplaceable`, and `business_h_c_bennett`,
which falls back to its street. `business_new_york_clothing_store` falls back to a reach of
Dearborn street, which is T-0385's whole problem. Two, the Giles Spring pair, are saved
only because their offset text also names a corner of Franklin and South Water, so the
Tremont word contributes nothing there either.

Mason's is the sharp case: its SUPERSEDED anchor, Graves' Tavern, resolves cleanly to
`mansion_house`, so the register can place the reading that is ten months stale and cannot
place the one live at the scene date.

The `(the first)` in the name is real and worth keeping — there was a second Tremont
House, and the disambiguation is why the record is named that way. So the fix is an `aka`,
which the resolver already reads (`aka_head_words`, and the Wolf Point Tavern record
carries "Taylor's tavern" for exactly this reason), not a rename.

**Acceptance:**

- `the Tremont House` resolves to `tremont_house_1`, through an `aka` on the record rather
  than by loosening the whole-set rule.
- The record still says which Tremont House it is; nothing about the 1839 successor is
  implied to stand in 1835.
- The six houses above are re-measured after the change and the count that moves is
  stated. T-0385 (the New York Clothing Store, three doors north of the Tremont House) is
  the visible ticket this unblocks and it should be named in the PR.
- A case asserts that an aka still only matches when it matches WHOLE, so this does not
  become the containment rule the resolver refuses.
