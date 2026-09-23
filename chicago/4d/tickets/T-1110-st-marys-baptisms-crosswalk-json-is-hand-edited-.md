---
id: T-1110
title: st_marys_baptisms_crosswalk.json is hand-edited away from what read_st_marys_baptisms.py rebuilds
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-13
closed: 2026-09-14
pr: 1340
claimed_by: run 9/14/2026, 2:55:34 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-14T20:20:55.784Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34888726286
---

st_marys_baptisms_crosswalk.json is hand-edited away from what read_st_marys_baptisms.py rebuilds.

**Found by T-0896, 2026-09-13**, which measured `--check` on every tool `tools/check.sh` never runs one on. The reason is recorded beside the tool in `data/research/check_gate_baseline.json`, and the gate there now refuses a row that states none — so this ticket is what makes that row go away.

    $ python3 tools/read_st_marys_baptisms.py --check
    FAIL  data/research/church/st_marys_baptisms_crosswalk.json is not what
          tools/read_st_marys_baptisms.py says; it has been hand-edited or the tool
          has changed. Rebuild it.

The tool's own message names both possibilities and cannot tell them apart. Which it is
decides everything: a hand edit is a ruling somebody made that the rebuild would erase, and
a changed tool is a rebuild that is simply owed.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- The diff is read and the cause named — hand edit or tool change — before the file moves.
- Any hand-made ruling found in it survives, in the tool where it can be re-derived rather
  than in the output where it cannot.
- `--check` green, gated in `tools/check.sh`, and `audit_check_gates.py --write` re-run in
  the same commit.
