---
id: T-1083
title: check.sh steps that need numpy pass in CI by skipping: the Chappel gate is red on a 65 m baseline drift and the dev gate has never seen it
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-12
closed: 2026-09-12
pr: 1216
claimed_by: run 9/12/2026, 6:05:01 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-12T23:45:35.825Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34724317591
---

Found by T-1078, which installed numpy to re-run a trace and watched `tools/check.sh` go from
green to red on a step nobody had touched.

`.github/workflows/chicago-4d-check.yml` — **the dev gate, and per docs/PIPELINE.md it is
check.sh and nothing else** — installs `jsonschema pyproj openpyxl pypdf`. Several tools that
check.sh runs need **numpy, scipy or Pillow**, and each degrades to a clear SKIP without them.
A clear skip is the right behaviour for a tool. It is the wrong behaviour for a GATE: the step
prints its skip, exits 0, and check.sh counts it green.

**Measured**, on dev at 33638aa69 with numpy/scipy/Pillow installed and nothing else changed:

```
$ python3 tools/measure_chappel_shore_lighthouse.py --gate
   FAIL sauganash_range_m moved from 1066.3 to 1001.2 (tolerance 1.0)
```

65.1 m of drift against a 1.0 m tolerance, on a step check.sh has been reporting green. The
drift itself is almost certainly a real reading landing — T-0616/T-0617 moved the Sauganash —
and the baseline was not re-derived with it, which is exactly what that gate is for.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

1. Every `tools/check.sh` step that can skip for a missing import is ENUMERATED, by running
   check.sh twice on the same tree — once with the CI install set, once with numpy, scipy and
   Pillow added — and diffing which steps changed behaviour. The list goes in the PR.
2. The gate stops counting a skip as a pass. Either the workflow installs what those steps
   need, or a skipped step reports as a distinct third state that fails the gate unless it is
   named in a baseline (the `data/research/check_gate_baseline.json` pattern, which is the same
   ratchet one layer up).
3. `sauganash_range_m` is settled: the baseline re-derived if the 1001.2 m reading is the right
   one, or the record repaired if it is not. Do not re-derive a baseline to make a gate green
   without reading which of the two numbers the sources support.
4. Whatever else the enumeration turns up gets a line in the PR, and a ticket only if it is
   real work — this one owns the blindness itself.

Sibling of T-0862 (a registration every Wright-band ticket stands on, with no gate at all):
same class of fault, one layer down. A gate that cannot run is a gate that is not there.
