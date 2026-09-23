---
id: T-1127
title: The stem budget binds now the ground reaches Kinzie's Addition, so the wood is cut off in a straight line at the north edge
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-14
closed: 2026-09-15
pr: 1357
claimed_by: run 9/15/2026, 10:06:17 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-15T15:29:51.524Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34985754597
---

The stem budget binds now the ground reaches Kinzie's Addition, so the wood is cut off in a straight line at the north edge.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Found by T-1122, 2026-09-14**, as an inherited red on three smoke legs — not that ticket's
diff, which is prose in two python passes.

`renderers/web/js/trees.js` plants until a stem budget is spent and then stops, and the
smoke's loader check fails the moment it stops partway:

    trees: the full stem budget bound at 3030 trees, so the planting loop stopped partway
    north and the wood is cut off in a straight line rather than thinned — lower full's
    keep fraction, do not lower the budget

Measured on this tree, 2026-09-14: `desktop 3,12`, `desktop 13` and `mobile 3,12-13` all
fail on it and on nothing else (the light level binds at 1,110 stems, the full level at
3,030). The same failure is already on the record against
`steward/t-1123-north-ground-kinzie` at 11:48 — the branch that IS dev's tip — so it
arrived with T-1123 and dev has carried it since. T-1123 grew the modelled field by
seventy-seven per cent northward; the budget did not grow with it, and the planting loop
reaches the new ground last.

The message says what the repair is not: **do not lower the budget.** The wood is cut off
because the loop ran out of stems before it ran out of ground, so the fix is the keep
fraction — plant the whole field more thinly rather than part of it at the old density —
and a check that the north edge is thinned and not truncated.

**Acceptance:** the loader check passes at both viewports; the wood reaches the north edge
of the enlarged field; the stem budget is unchanged; and the smoke says which level bound,
as it does now.

**Seen again by T-0987 stretch 14's lap, 2026-09-14**, on a third branch and a different tree
(`sha256:f5bbf9a390817b94`), so it is dev's and not any one branch's: mobile part 3 and desktop
parts 3, 12 and 13 all carry it, the message word for word — mobile `the light stem budget
bound at 1110 trees`, desktop `the full stem budget bound at 3030 trees`. It is the only red on
those three legs; 511 other checks pass. The readings are filed in `tools/dev-smoke-state.json`.
