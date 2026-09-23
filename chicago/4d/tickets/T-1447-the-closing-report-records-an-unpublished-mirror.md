---
id: T-1447
title: The closing report records an unpublished mirror as a measurement of zero, so three PRs in one morning went red saying STALE
state: done
epic: PIPELINE
requested_by: steward
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-20
closed: 2026-09-20
pr: 1565
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-20T12:32:57.938Z
claimed_run: null
---

The closing report records an unpublished mirror as a measurement of zero, so three PRs in one morning went red saying STALE.

`tools/rebuild_closing_set.py` measured the mirror like this:

```python
"files": len(list(PUBLISHED_RESIDENTS.rglob("*.json"))) if PUBLISHED_RESIDENTS.exists() else 0,
```

`site/chicago/4d/` is generated and untracked (T-0938), so a fresh clone HAS no mirror
until `tools/publish.sh` runs. A run that rebuilt this report before publishing therefore
wrote `| 1336 | 0 | -1336 |` — a delta of minus everything — as though it had counted an
empty mirror. It had counted nothing. The absence was recorded as a measurement.

`tools/check.sh` publishes as its FIRST step, so by the time `--check` ran the mirror was
there, the committed zero disagreed with the tree, and the gate went red with

    FAIL docs/RESEARCH/closing-convergence-2026-09.md is stale — the tree has moved under it

which is the WRONG SENTENCE. Nothing about the town had moved. The reader was sent looking
for a change that did not exist, and the actual remedy — publish, then rebuild — was not
on the page.

**Measured, 2026-09-20.** Three PRs by three different runs, each red for about an hour:

| PR | ticket | committed | dev |
|---|---|---|---|
| #1557 | T-1430 | `1336 → 0, -1336` | `1336 → 2152, +816` |
| #1560 | T-1428 | `1336 → 0, -1336` | `1336 → 2153, +817` |
| #1561 | T-1194 | `1336 → 0, -1336` | `1336 → 2153, +817` |

#1557 was fixed by hand. #1560 healed itself when a later lap regenerated the report on a
published tree — so the fault is self-clearing and expensive rather than fatal, which is
why it survived three mornings without being named.

**This is the project's own rule, applied to itself.** `check.sh` already refuses to count
a skipped step as a pass — *"a GATE may not count a skip as a pass — pip install numpy"* —
and this file's own docstring says *"a count with no baseline is not a delta"*. An
uncounted mirror is the same thing one layer down.

**Acceptance:**

- `measure()` returns `None`, not `0`, when `site/chicago/4d/data/residents/` is not on
  disk. A mirror that IS published and holds nothing still reads `0`: a count of zero and
  no count at all are different readings and the code must be able to tell them apart.
- `--build` and `--rebuild` REFUSE to write the report when the mirror was not counted,
  and say so with the remedy that fixes it rather than the one that does not. `--rebuild`
  refuses BEFORE it spends the members, because none of them publishes.
- `--check` says the mirror is unpublished instead of saying the report is stale. The two
  failures want different remedies and must not share a message.
- A value that was never counted renders as no reading, never as a number-shaped `None`.
- `--self-test` holds all of it, AND at least one case drives `measure()` and `check()`
  against a path that is really not there — a constructed fixture cannot reach this fault,
  because the fault is in the line that turns a missing directory into a number. Restoring
  `else 0` must turn the self-test red. (T-1427's finding, one week old: a check that is
  dead in production and green in the gate is worse than no check.)

**Stop condition:** no run can commit a figure it did not measure, and a gate that fails
over this names the reason it actually failed for.

**Links:** T-1333 (the closing set) · T-0938 (the mirror is untracked) · T-1427 (a fixture
richer than production) · PRs #1557, #1560, #1561.
