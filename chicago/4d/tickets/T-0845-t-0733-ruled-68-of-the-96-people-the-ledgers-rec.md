---
id: T-0845
title: T-0733 ruled 68 of the 96 people the ledgers record a conflict against: the audit reads only the newest override, so 28 conflicts an earlier pass wrote are unruled and invisible
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-05
pr: 937
claimed_by: run 9/5/2026, 6:23:25 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-06T00:28:34.200Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33996384592
---

T-0733 ruled 68 of the 96 people the ledgers record a conflict against: the audit reads only the newest override, so 28 conflicts an earlier pass wrote are unruled and invisible.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

T-0733 closed on PR #930 with a ruling for every person the audit could see carrying a
conflict. The audit cannot see them all. `export_resident_audit.py`'s `findings()` walks
`pass_*_findings.json` in order and ASSIGNS — `out[person_id] = row` — so a person reviewed
twice keeps only the last pass's override. A conflict written in pass 02 and overwritten by
a later pass is still written, and the audit stops reporting it.

The ledgers record conflicts against **96** people. The audit sees **68**. The rulings file
therefore rules on 68, and the twenty-eight in the gap are not resolved — they are
overwritten. `flag_conflicting_evidence` reads clean for all twenty-eight, which is the
exact fault T-0733 exists to prevent, one layer up.

`vann_angeline` is the demonstration and the worst of them. Pass 02 (T-0462) recorded
"Born 1834 and later Missouri geography" against Angeline Vann of Missouri — an infant is
not the addressee of an 1834 waiting letter, so this is the one conflict in the whole set
that DISQUALIFIES rather than merely fails to bridge. Pass 13 rewrote her override with
`no_corroboration` and no candidates, and it has been invisible since.

**Acceptance:** the audit's view of a person's recorded conflicts accounts for every pass
that reviewed them, not the newest; all 96 carry a ruling; and an unruled conflict fails the
gate rather than sitting in a report nobody reads. The count of unruled conflicts is stated
and is nought. No grade moves, no candidate is adopted.

**Where the gate goes, revised in the doing.** This was first written as "the exporter
refuses a ledger conflict no ruling reaches, the mirror of the orphan-ruling refusal". It
should not. #930 made a deliberate choice the other way and wrote it down: the flag fires
again "and somebody has to look", so `--build` still produces the artifact and a reader can
SEE what nobody has adjudicated. Refusing to build would delete exactly that view. The gate
belongs instead in `--self-test`, which `check.sh` runs — an unruled conflict fails the
commit while the report continues to name it. Same enforcement, and the landed design keeps
its point.

**Links:** T-0733 / PR #930 (ruled the 68) · T-0512 (the audit) · T-0462, T-0463 (the
passes whose conflicts were overwritten).
