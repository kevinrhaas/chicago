---
id: T-0733
title: 103 people carry a conflicting-evidence flag the final audit can see and no ruling reaches
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-05
pr: 930
claimed_by: run 9/5/2026, 5:35:01 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T22:54:32.517Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33996203401
---

103 people carry a conflicting-evidence flag the final audit can see and no ruling reaches.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Found by the final resident audit (T-0512), which is the first artifact that could see it
in one place: `flag_conflicting_evidence` is true on **103** of the 1,404 rows — the
research ledgers record a candidate with a stated conflict against it, or the household
carries `review_required`. Nothing rules on any of them. A conflict that is recorded and
never adjudicated reads, to anybody downstream, exactly like a conflict nobody found.

The audit CSV is the worklist: filter `flag_conflicting_evidence` in
`chicago/reference/resident-research/final/audit/resident_audit_master.csv` and the 103
rows come out with their cohort ticket, their outcome and their source ids beside them.

**Acceptance:** every one of the 103 either carries a ruling — the conflict resolved, the
candidate rejected, the flag retired — or a written sentence saying why it stands
unresolved, and the audit re-run shows the count moved. No grade rises to close a conflict.

**Links:** T-0512 (found it) · T-0517 (the re-run that measures it).
