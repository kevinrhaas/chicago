---
id: T-1109
title: pass_14_findings.json no longer matches what complete_resident_research_pass_14.py re-derives
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-13
closed: 2026-09-14
pr: 1341
claimed_by: run 9/14/2026, 3:25:36 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-14T21:07:03.590Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34892468308
---

pass_14_findings.json no longer matches what complete_resident_research_pass_14.py re-derives.

**Found by T-0896, 2026-09-13**, which measured `--check` on every tool `tools/check.sh` never runs one on. The reason is recorded beside the tool in `data/research/check_gate_baseline.json`, and the gate there now refuses a row that states none — so this ticket is what makes that row go away.

    $ python3 tools/complete_resident_research_pass_14.py --check
    pass_14_findings.json does not match a re-derivation

A research pass whose committed findings have stopped following from its inputs. Nothing
has ever asked it to re-derive, so the drift has no known start date — the pass ran, the
file was committed, and the tool has not been run since.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- WHAT moved is stated before anything is rebuilt: the diff between the committed findings
  and the re-derivation, read, and said out loud. A regeneration that silently adopts the
  new answer proves nothing and may destroy a ruling somebody made by hand.
- `--check` green, gated in `tools/check.sh`, and `audit_check_gates.py --write` re-run in
  the same commit.
