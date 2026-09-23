---
id: T-1156
title: Wire measure_boot_payload.mjs --check into the nightly gate so the 12 MB boot budget refuses without a human
state: done
epic: META
requested_by: steward
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-16
closed: 2026-09-17
pr: 1404
claimed_by: run 9/17/2026, 11:04:24 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-17T16:34:03.688Z
claimed_run: null
---

Wire measure_boot_payload.mjs --check into the nightly gate so the 12 MB boot budget refuses without a human.

**Acceptance:**
- The nightly bake runs `measure_boot_payload.mjs --check` exactly once, after
  downloading its published mirror and installing Chromium, in desktop stage 1-2.
- An over-budget exit fails the smoke job and withholds `open-pr`; no advisory
  `continue-on-error`, shell suppression, or source-tree republish.
- Keep the existing 12 MB budget and all eight smoke legs. Demonstrate the normal
  reading and a forced over-budget refusal, and record the added runtime.

Owner selected this ticket explicitly on 2026-09-17, including its workflow edit.
The local claim command succeeded with its documented no-push-credentials fallback;
the GitHub connector created `steward/t-1156-nightly-boot-budget` before work so the
branch scan advertises the claim.

**Verification:** clean published-tree boot: 7.270 MB / 12 MB, no failed requests,
25.747 s; separate 13.004 MB fixture refused with exit 1. Workflow YAML parsed
and checked for artifact ordering, single-leg selection, all eight smoke legs,
and the blocking `open-pr` dependency. Full nightly CI remains the integration
verification; local gate results are recorded in the PR.
