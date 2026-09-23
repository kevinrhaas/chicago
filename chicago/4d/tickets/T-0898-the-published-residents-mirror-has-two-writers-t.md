---
id: T-0898
title: The published residents mirror has two writers that disagree on its shape, and publish.sh losing the race turns the T-0838 drift ratchet red
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-06
closed: 2026-09-09
pr: null
claimed_by: null
blocked_on: superseded: fixed by T-0933 (#1024) and T-0938 (#1023) — the mirror is untracked, publish.sh is its one writer, DRIFT_ROOTS no longer includes site/, and --drift-self-test holds it; --drift is green on dev
needs_bake: false
closed_at: 2026-09-10T04:20:07.822Z
claimed_run: null
---

The published residents mirror has two writers that disagree on its shape, and publish.sh losing the race turns the T-0838 drift ratchet red.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Found by T-0714, 2026-09-06, the hard way — it cost that run a full `check.sh` lap.**
`site/chicago/4d/data/residents/` has three writers and they do not agree on the bytes:

| writer | shape |
|---|---|
| `tools/publish.sh` | minified (`separators=(",", ":")`), under the 32 MB published-tree budget |
| `tools/synthesize_resident_research.py` | minified, with a comment saying it matches publish.sh |
| `tools/apply_census_1840_bridges.py` | **`indent=1`, pretty**, for the 3 bridge households and `index.json` |

The T-0838 drift ratchet (`synthesize_resident_research.py --drift`) re-runs the real writer pair
against a scratch copy and compares BYTES, so whichever tool touched the mirror last decides
whether the gate is green. On `dev` the bridge tool ran last and those four files are pretty, so
the gate passes. Any run that calls `./tools/publish.sh` — which is every run that ships anything,
because the mirror is a publish-in-the-same-commit contract — minifies them and the gate goes red
on four files the run never touched. T-0714 healed it by restoring the four from `dev`, which is
a workaround and not a fix: the next publish does it again.

The bridge tool's pretty write is also the odd one out on the merits — the mirror is minified
deliberately, for a size budget the authored tree is not under.

**Acceptance:** one shape, written by one rule, for `site/chicago/4d/data/residents/`; `./tools/publish.sh`
run twice in a row and then `synthesize_resident_research.py --drift` is green; and running
`apply_census_1840_bridges.py` after a publish leaves the gate green too. `bash tools/check.sh` green.
