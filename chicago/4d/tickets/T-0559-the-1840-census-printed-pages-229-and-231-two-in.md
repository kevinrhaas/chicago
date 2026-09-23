---
id: T-0559
title: The 1840 census printed pages 229 and 231: two independent cell readings disagree on 45 of 61 lines — reconcile them against the sheets, column by column
state: done
epic: META
requested_by: steward
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-03
closed: 2026-09-05
pr: 850
claimed_by: run 9/4/2026, 11:58:16 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T19:51:52.842Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33945838683
---

The 1840 census printed pages 229 and 231: two independent cell readings disagree on 45 of 61 lines — reconcile them against the sheets, column by column.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**What happened.** Printed pages 229 (`33S7-9YYJ-9M5`) and 231 (`33S7-9YYJ-38`) were read to the cell
twice on 2026-09-03 by two runs that did not know about each other: T-0550 (PR #697, the reading now
committed in `pages/`) and the run that had claimed T-0534 before it was split (PR #698, preserved
verbatim in `data/research/census_1840/second_readings/`). The names agree on every line of both.
The cells do not: **20 of 30 lines on 229 and 25 of 31 on 231** carry different
cells, and the two readings read the enumerator's own FOOTINGS differently in exactly the columns
where they part — so each balances a different set of columns and each records a different pair as
unreconciled. A column that balances is therefore necessary and not sufficient, and the committed
cells of these two pages are ONE reading until this ticket settles them.

**Where they part** (second reading / committed reading):

| page 229 column | PR #698 | T-0550 (committed) |
|---|---|---|
| free white males Under 5 (column 1) | 9 read / 14 footed | 10 read / 10 footed |
| free white males 30 under 40 (column 6) | 8 read / 7 footed | 8 read / 1 footed |
| free white females Under 5 (column 14) | 19 read / 19 footed | 19 read / 11 footed |

| page 231 column | PR #698 | T-0550 (committed) |
|---|---|---|
| free white females 5 under 10 (column 15) | 9 read / 9 footed | 12 read / 12 footed |
| free white females 20 under 30 (column 18) | 20 read / 20 footed | 20 read / 21 footed |
| free white females 40 under 50 (column 20) | 3 read / 3 footed | 3 read / 5 footed |

On 229 the strokes one reading puts in column 1 (free white males Under 5) the other puts in column
14 (free white females Under 5); on 231 marks sit in column 15 on one reading and 18 on the other. That
is a grid disagreement, not scatter — start there. Each page file's `grid_note` says how its grid was
fitted; the two methods differ (single pitch fitted over the sheet body vs. fitted off the printed
heading band and re-fitted every 250 px), and the printed heading is the arbiter: column 1 must read
`Under 5`, column 14 `Under 5` under FREE WHITE FEMALES, column 27 `Under 10` under FREE COLORED
MALES, before a single cell is read.

**Acceptance:** (one demonstration, never weakened to pass)
- Both pages re-read at a grid checked against the printed heading, column by column in the columns
  named above FIRST, then the rest; every cell where the two readings differ is decided on the image
  and the decision is stated per column in `cells_note` (which reading prevailed, and why).
- The footings of columns 1, 6 and 14 (229) and 15, 18 and 20 (231) re-read at full resolution and
  the reading stated with its alternates, as the page files already do elsewhere.
- `pages/<id>.json` updated with the reconciled cells and column checks; `second_readings/<id>.json`
  left exactly as it was read, its `cells_note` untouched, and the census README's "second reading"
  section updated to say the pages are reconciled and by whom.
- `coverage.json` notes on both images updated; `counts.second_readings` restated.
- Names are not re-read; both readings agree on them. No IPUMS serial attached; nothing here mints
  or regrades an 1835 resident.

**Budget.** Two sheets, ~60 tool calls each: one run. Commit each sheet as you go.

**Links:** `data/research/census_1840/README.md` · `coverage.json` group `images 1-25 of 74` ·
`second_readings/README.md` · T-0534 (parent of both runs' work) · T-0550 (PR #697) · T-0551 (PR #698)
· T-0507 (composition calibration reads these cells) · T-0532 (the commit-only-where-it-balances rule)
