---
id: T-1108
title: Three generators refuse together and none is gated: inf_cooperage_south_branch stands 2.1 m inside the platted Market Street corridor
state: split
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-13
closed: 2026-09-17
pr: null
claimed_by: run 9/17/2026, 4:12:58 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-17T09:19:30.843Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35203627603
---

Three generators refuse together and none is gated: inf_cooperage_south_branch stands 2.1 m inside the platted Market Street corridor.

**Found by T-0896, 2026-09-13**, which measured `--check` on every tool `tools/check.sh` never runs one on. The reason is recorded beside the tool in `data/research/check_gate_baseline.json`, and the gate there now refuses a row that states none — so this ticket is what makes that row go away.

Three generators refuse on ONE line, and none of the three is gated:

    $ python3 tools/generate_inferred_households.py --check
    $ python3 tools/generate_inferred_names.py --check
    $ python3 tools/replace_invented_residents.py --check
    inf_cooperage_south_branch stands 2.1 m inside the platted Market Street corridor

That is a refusal working exactly as designed — a record may not stand in a street — so
the fault is in the record or in the corridor, not in the check. 2.1 m against a corridor
the plat draws is inside the ~20 m working horizontal uncertainty this project states for
anything traced off the 1834 sheets, so "move it" is a ruling and not a nudge: either the
cooperage's placement has evidence that survives being held against Market Street, or it
does not and the inference goes.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- The cooperage's position is settled ON EVIDENCE — its own, or the corridor's — and the
  reasoning is recorded on the record, not only in the commit.
- All three `--check` modes are green, and all three are gated in `tools/check.sh` in the
  same commit that makes them green.
- `tools/audit_check_gates.py --write` re-run in that commit, so the ratchet tightens by
  three. The gate fails if it is not.
