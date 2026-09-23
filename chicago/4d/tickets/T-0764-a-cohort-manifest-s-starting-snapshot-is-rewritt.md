---
id: T-0764
title: A cohort manifest's starting_* snapshot is rewritten every time the manifest is regenerated, so the freeze records today's tree rather than the day it was fixed
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-05
pr: 952
claimed_by: run 9/5/2026, 9:21:37 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-06T02:35:51.572Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34006144198
---

A cohort manifest's starting_* snapshot is rewritten every time the manifest is regenerated, so the freeze records today's tree rather than the day it was fixed.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Each of the fifteen resident-research cohort manifests carries, per person,
`starting_grade`, `starting_evidence`, `starting_presence`, `starting_occupation`,
`sources` and `letter_list_returns` — a snapshot of the tree AT THE MOMENT THE COHORT WAS
FIXED, which is what "starting" means and what makes a finished pass legible ("this person
came into the cohort at `inferred`, on one source, and left it at `attested` on three").

The gate is `--gate`, which RE-DERIVES the whole document from today's tree and demands
equality. So the moment a source lands on any member the manifest reads `stale`, and the
documented remedy — regenerate without `--gate` — overwrites the snapshot with today's
values. The freeze then records the day of the last regeneration rather than the day the
cohort was fixed, silently, with no diff anybody reads.

**Measured 2026-09-05 at `cfda02f34`**, before the regeneration in PR #863: pilot, pass 2
and pass 3 read `stale` on 15 cells between them — three people had gained
`isa_public_domain_land_tract_sales` or `fergus_1843_old_settler_death_notices`, and
`doolittle_ehjah` and `vanderbogart_h` had moved `inferred` → `attested`. Those are the
research landing, which is the cohorts' whole purpose; the manifest is the one place that
recorded what they looked like beforehand, and regenerating is what loses it.

**Acceptance:** a cohort manifest's snapshot fields are written once and never rewritten by
a later regeneration, and the gate says so rather than calling the freeze stale — while
still failing when a person leaves the residents layer, becomes an unnamed placeholder, or
the reservation's ids or their order change, which is the staleness the manifests' own text
describes. A worked implementation of exactly this contract, with a nine-case self-test and
all eight `--gate` steps green, is on the branch `steward/t-0745-cohort-freeze-gate`
(`tools/resident_cohort_freeze.py`); it was cut against `cfda02f34` and is superseded in its
unblocking role by #863, but the freeze contract in it is what this ticket wants. Take it or
leave it, but do not lose it.
