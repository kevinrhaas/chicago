---
id: T-1238
title: Plural dated home, workplace and other-significant-location relationships on every person and household, with associated_with[] defined
state: done
epic: META
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1147
opened: 2026-09-17
closed: 2026-09-17
pr: 1405
claimed_by: run 9/17/2026, 9:57:55 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-17T16:41:53.177Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35236460812
---

Plural dated home, workplace and other-significant-location relationships on every person and household, with associated_with[] defined.

Piece 2 of 5 of **T-1147 — Spend every defensible home, workplace and business-location finding, preserve the 123 location limits, and close research with zero unclassified attested or inferred fact**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

1. `associated_with[]` is DEFINED: one closed vocabulary of kinds, one ladder of
   resolution rungs, one row shape carrying T-1147 clause 7's six fields, declared in
   `index.json`'s `vocabulary` block so a renderer knows the sets it must implement.
2. The rules are GATED, not documented: every refusal is broken on purpose by a self-test
   that `tools/check.sh` runs, and `tools/validate.py` enforces them at both the household
   and the person level.
3. The two shapes MAY NOT DRIFT while both stand. A record carrying plural rows and a
   non-null `lives_at`/`works_at` must carry that structure among its rows, or the build
   fails. A half-migrated layer that says two things about one man is the defect this
   ticket would otherwise create.
4. Demonstrated on real records, restating what those records already claim and adding no
   finding: same value, same confidence, same source, now plural, dated and tiered. At
   least one relationship that ENDED before the scene date and one that is honestly
   undated, because those are the two things a singular field cannot express.
5. The remaining distance is a NUMBER, re-derived every run, and what is not yet written
   is named — including which rungs are declared and unspent, and whose ticket they are.

**What this does NOT do, deliberately.** It writes no new finding and adjudicates no
evidence — T-1239 spends the remaining defensible location findings. It changes no
renderer — T-1240 is the view. It moves no other record and retires no singular field —
T-1253 is that migration, and it is more than one run.
