---
id: T-0524
title: The renderer smoke still asserts a reconstructed resident, 956 person entries and 150 research reviews, and the layer has none of the three
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-03
closed: 2026-09-03
pr: 696
claimed_by: run 9/3/2026, 7:01:24 AM CT
blocked_on: null
needs_bake: false
---

**Twelve assertions in `tools/smoke_renderer.mjs` describe a resident layer that stopped
existing on 2 September 2026**, and every branch cut from `dev` inherits all twelve. Found
while verifying T-0491 (#682), which measured them rather than argued about them: the same
stage run against a clean `origin/dev` worktree and against that branch produced the same
pass counts and the same failures, differing only where T-0491 is correct.

```
mobile 390x780, part 3    dev 68 pass / 6 fail    branch 68 pass / the same 6
desktop 1280x800, part 3        (identical set)
mobile 390x780, part 13   dev 103 pass / 6 fail   branch 103 pass / the same 6
```

Zero pageerrors in every run. The failures are stale expectations, not a broken renderer.

**They are one family.** T-0489's owner ruling of 2 September retired the reconstructed
resident population — `data/residents/index.json` now reads `by_grade.reconstructed: 0` —
and the assertions were not moved with it.

Part 3, six of them, all downstream of one lookup:

```js
const person = hh.persons.find((p) => p.grade === 'reconstructed');   // undefined, always
```

so `name`, `name_basis`, the household title, the card title, the search-by-household
check and the inferred-household building basis all read `undefined` or `""`.

Part 13, six more, hardcoded population figures the ruling moved:

```
the 956 person entries are counted                          -> 849
150 resident research reviews reach resident cards          -> 375
every household in the layer is on the card                 -> "no residents on the handle"
the letter-list cohort is held apart from the evidenced town
the households no building card can reach are marked
an invented name says on the card which pool it came from
```

**The work is to DECIDE what each one should now say, not to retune a number.** Three
shapes, and the third is the reason this is `M` rather than `XS`:

- Figures that are simply the layer's size (`956`, `150`) should be read out of the
  committed manifest the page fetched, the way T-0491 repaired the gate-census assertion —
  a test that hardcodes a count rots the next time the count is right.
- Assertions that need a `reconstructed` person have no subject any more. Either they
  retarget the `hh_inf_` evidence-only households that replaced them (whose people are
  `inferred`, retained and unplaced), or they are retired with the ruling that removed
  their subject cited in the commit. Silently deleting a passing-shaped assertion is the
  one thing that must not happen here.
- `an invented name says on the card which pool it came from` and `every household in the
  layer is on the card — no residents on the handle` may be asserting something the panel
  no longer offers at all. Read `renderers/web/js/residents.js` before assuming a number.

**Acceptance:** (state it before working — never weakened to pass)

- Both viewports run parts 3 and 13 green on `--published`, and the PR states which
  assertions were retargeted, which were retired, and the ruling behind each retirement.
- No assertion is deleted without a sentence saying what replaced its subject; no figure
  is hardcoded where the manifest can be read.
- A clean `origin/dev` worktree is run alongside, so the PR can say what it inherited.
- `bash tools/check.sh` stays green (`smoke_budget.mjs --self-test` reads this file).

**Links:** T-0491 and PR #682 (the measurement, and the gate-census assertion repaired the
way this one should be) - T-0489 (the ruling that removed the subject) - T-0516 (the other
half of the retirement, on the roofs) - the QUEUE band "DEV'S OWN SMOKE IS RED" -
`tools/smoke_renderer.mjs` - `tools/dev-smoke-state.mjs`.
