---
id: T-1339
title: A step that mutates the working tree cannot be caught by a convention: hold what every gate step WRITES as a measurement, and refuse an unmeasured one
state: done
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-18
closed: 2026-09-18
pr: 1479
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-18T23:15:38.757Z
claimed_run: null
---

A step that mutates the working tree cannot be caught by a convention: hold what every gate step WRITES as a measurement, and refuse an unmeasured one.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

1. **No tool the gate runs writes the live working tree**, and that is MEASURED rather than
   reasoned — one row per tool in `tools/step_isolation.json` listing every file it opened
   for writing inside the repo. A row with an empty `wrote` was measured and wrote nothing;
   a tool with no row was never measured, and the two must not look alike.
2. **A gate step added without a measurement is REFUSED.** Acceptance 1 alone is satisfied
   by an empty file, which is how the seventh offender arrives. `audit_step_isolation.mjs
   --check` fails on a declared python or node step with no row, and its self-test drives
   exactly that case.
3. **A tempdir write is not a finding.** A tool writing its own scratch is doing the right
   thing; only paths that resolve inside the repo are recorded. Getting this wrong once
   already produced a false finding against `resolve_id_collisions.mjs`, which copies two
   tools OUT to a fixture — so the probe records the DESTINATION of a copy and not its
   source, and says so where it does it.
4. **The measurement is one instrumented gate run, not a second sweep.** `PYTHONPATH`
   reaches every python subprocess through `sitecustomize` and `NODE_OPTIONS=--require`
   every node one, so the tools are measured exactly as the gate runs them. It runs
   `CHECK_JOBS=1` on purpose: serial, so a write is attributable to the step that made it
   rather than to whatever was running beside it.
5. **What is NOT measured is named, not counted as measured.** A step that is a shell
   function or a bash script names no python or node tool and cannot be keyed to one. The
   audit reports how many such steps there are instead of implying they were covered —
   which is the failure this ticket exists to correct.

**NOT IN SCOPE:** removing the T-1336 retry net. That keeps the verdict correct while an
offender exists; this stops the offender existing. They answer different halves and the
retry stays.


## WHY A CONVENTION CANNOT HOLD THIS

T-1336 found six self-tests that broke a live file to prove a check fires and put it back.
Under check.sh's job pool that window is read by whatever runs beside it, and four PRs went
red in one afternoon on trees that were green — each looking like a defect, each costing a
cycle.

**Two of the six carried comments saying they already worked on a copy.**
`compile_businesses.py` said "Broken in a temporary copy of the tree so the working tree is
never touched"; the temporary copy was the BACKUP and the edit went into the live record.
A comment is not a measurement, which is the same finding T-1302 reached about writers —
no pattern over a tool's source can say whether it writes — and the same answer applies.

T-1336 also left two gaps it did not claim to close, and this ticket owns both:

  * its sweep was PYTHON ONLY while the gate runs 17 node and bash self-tests (corrected in
    that ticket; all clean, but unmeasured at the time it said "every self_test")
  * only SELF-TESTS were ever measured. An ordinary `step` that mutates races identically,
    and `read_census_1830.py --check` used to repair in place until T-0856 caught it — so
    the pattern has existed outside a self-test before.
