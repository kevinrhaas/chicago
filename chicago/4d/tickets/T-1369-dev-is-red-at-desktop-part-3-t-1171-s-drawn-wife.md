---
id: T-1369
title: Dev is red at desktop part 3: T-1171's drawn wife lands on an evidence-only household (hh_inf_cooper_north_04), and the placeholder label no longer agrees with its asset
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-18
closed: 2026-09-21
pr: 1605
claimed_by: run 9/20/2026, 7:32:38 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-21T05:08:14.566Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35547828284
---

Dev is red at desktop part 3: T-1171's drawn wife lands on an evidence-only household (hh_inf_cooper_north_04), and the placeholder label no longer agrees with its asset.

**Acceptance:** the rule the smoke asserts and the rule `reconstruct_modelled_families.py`
applies are the same rule — an evidence-only container (`hh_inf_*`, named "Evidence-only
household — <head>") is refused by the stage's own eligibility, no `hh_inf_*` record carries a
person any stage drew, the refusal is counted in the ledger and stated in L244 and in the module's
own list of what it may not do, the whole derived layer re-derives (`check.sh` green), and
`SMOKE_VIEWPORT=desktop SMOKE_STAGE=3` passes `nothing was drawn into an evidence-only household`.
The label check named in the title is T-1331's and is out of scope here.

**Closed, 2026-09-21, and re-measured before closing.** The fix merged on #1605 at
03:12Z but the run that made it ended without calling `ticket.mjs done`, so T-1369 sat
`claimed` at row 0 of the queue with its work already on dev — the shape AUTOMATION.md
calls rotting, and the reason slice 1 kept landing on it. Re-measured on dev at 2d4ea3d05
before closing, rather than taken on the merge:

- `reconstruct_modelled_families.py --self-test` — 25 rules, 0 failed, including all four
  evidence-only rules: refused by id, refused by name alone, the two markers name the same
  five records, and no container carries a person this stage drew.
- The layer on disk: 5 evidence-only containers, 0 of them holding a reconstructed person.
- `./tools/check.sh` — CHECK PASS, 596 steps, none red.

**What was NOT demonstrated, and it is half the acceptance.** The acceptance also asks that
`SMOKE_VIEWPORT=desktop SMOKE_STAGE=3` pass `nothing was drawn into an evidence-only
household`. **That leg was not run to completion and this close does not claim it.** It was
attempted twice here and killed by the 600 s foreground ceiling both times, stalling in the
reconstruction-contract block *before* the evidence-only assertion is reached — so the
assertion is not red, it is unevaluated, and has been since 2026-09-18. That is a defect in
the part, not in this fix, and it is now **T-1501**. The reading is filed in
`tools/dev-smoke-state.json` naming the body-completion sentinel as the sole failure, so
the record shows a leg that could not finish rather than a town that is wrong.

The substance of the acceptance — that the rule the smoke asserts and the rule the stage
applies are the same rule — is demonstrated by the three checks above, on the same layer
the smoke would read. Closing on that, with the gap stated, rather than leaving row 0 to
burn another run.

**Done, 2026-09-21.** The stage was the wrong half: `division: unplaced` was admitted and nothing
knew what an `hh_inf_` record is. A seventh refusal was added beside the letter-list one, which it
is the sibling of — both refuse a record that argues for a person and not for a household. Ten
drawn kin were retired from four of the five containers; the order book re-spent their quota on
documented heads it had been refusing, so the stage now draws for 119 heads instead of 89 and
writes 296 people instead of 300. The whole derived layer was re-derived behind it, and the order
book's self-test stopped carrying a hand-typed town figure (2,267) that this change moved.

**Found by** T-1347's run, 2026-09-19, on the first `SMOKE_VIEWPORT=desktop SMOKE_STAGE=3`
leg anybody has run since 2026-09-18T01:35. Two checks fail, and BOTH are dev's, not that
branch's: it changed no byte of `data/residents/households/` or `data/assets/`.

```
FAIL desktop 1280x800: nothing was drawn into an evidence-only household
     — 1 reconstructed people on hh_inf_cooper_north_04, name_basis present: true
FAIL desktop 1280x800: the placeholder label agrees with the asset it describes
```

**The first.** `hh_inf_cooper_north_04` is an *inferred* household — an evidence-only
container — and it now carries `rc_inf_cooper_north_04_wife`, drawn by T-1171's
`modelled_families` stage. The smoke's rule is that nothing may be DRAWN into a household
that exists only to hold evidence; the stage's own eligibility rules do not exclude
`hh_inf_*`. Either the rule or the stage is wrong and the two have to be reconciled — the
stage's `--check` is green, so this is a disagreement about what an inferred container is,
not a reproduction failure.

**The second** is unrelated to the residents and was not investigated here.

**Why it stood a day.** Part 3 has no reading in `dev-smoke-state.json` newer than the tree
T-1171 and T-1172 landed on. The readings are now filed: desktop 3 `fail`, desktop 13 and
mobile 13 `pass`, all on sha256:733344d4499f0392.

**Scope note (2026-09-20).** Of the two failures in the title, the second — *the placeholder
label agrees with the asset it describes* — has since been root-caused by **T-1331**: the
check reads a field that does not exist, so it has been permanently red on a typo rather
than on anything about the asset. Take the evidence-only household here and leave the label
to T-1331; the two sit together at the top of the queue. Both are among the four assertions
that have been standing red on dev, which is why every PR's smoke budget reports its legs
"already red on dev" and skips them.
