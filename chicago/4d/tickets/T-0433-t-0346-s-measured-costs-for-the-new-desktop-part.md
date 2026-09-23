---
id: T-0433
title: T-0346's measured costs for the new desktop parts 4, 5 and 6 were never filed, and the two places they are written down disagree
state: open
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-29
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
---

T-0346 cut desktop part 4 into parts 4, 5 and 6 on 2026-08-30 and measured all three at
desktop against `--published`. Neither half of that measurement survived usefully.

**They were never filed into the record.** `tools/dev-smoke-state.json` is the standing
smoke record (T-0216) and `tools/smoke_budget.mjs` reads the gate's cost out of it. Asked
today it reports **no reading at all for desktop parts 4-9** — the whole middle of the
desktop gate — so the only place those three figures exist is a PR description and a
comment. A reading that is not filed is a reading the next run pays for again.

**And the two places they are written down disagree.**

| part | `smoke_renderer.mjs` header | PR #583's own description |
|---|---|---|
| 4 | about 1 m 10 s | 1 m 09 s |
| 5 | about 6 m 17 s | **6 m 46 s** |
| 6 | about 1 m 55 s | **3 m 13 s** |

6 m 17 s is the figure the same header gives for the scene-detail ladder inside the
**uncut** part 4, so the header looks to have carried the pre-cut profile forward into the
post-cut row. Part 6 is the one that matters for anyone reasoning about margin: 3 m 13 s is
two-thirds again as much as 1 m 55 s, on a part cut precisely because the ceiling was
being breached.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- `SMOKE_VIEWPORT=desktop SMOKE_STAGE=4`, `=5` and `=6` are each run against
  `--published` on the steward runner and filed with `node tools/dev-smoke-state.mjs
  record <log>`, so `node tools/smoke_budget.mjs` prints a figure for each instead of
  "no reading".
- The `smoke_renderer.mjs` header's three post-cut figures are corrected to the filed
  readings, or the disagreement is explained if the header turns out to be right.
- Nothing is asserted that was not measured on this machine. Redirect each run to a
  FILE, not a pipe (docs/SMOKE-BUDGET.md).

**Links:** T-0346 (the cut) · T-0235 (`tools/smoke_budget.mjs`, docs/SMOKE-BUDGET.md) ·
T-0216 (the record) · T-0170, T-0173, T-0181 (the margins this would let them re-take)
