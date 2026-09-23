---
id: T-1271
title: Reconcile and time the complete 25-jaunt library
state: open
epic: RENDERING
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-09-17
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: null
claimed_run: null
---

**Converge the 25-jaunt library** into one coherent, measured collection. A bounded acceptance pass with in-scope corrections — not a research epic and not a deferral list. The owner: *"a normal jaunt should take roughly 5 minutes … roughly 4–8 stops … jaunts should not all feel like games … a varied initial set of approximately 25."*

**Depends on:** T-1260–T-1265 and T-1266–T-1270 (all 25 authored). T-1272 depends on this.

**Build / do:**
1. `tools/play_jaunt.mjs --all` (extend the walker from 5H): walks every reachable path of every jaunt through the reducer; records per-jaunt stop count, primary-path word count, declared resources, endings reached, keepsake family, and the estimate at recommended / fastest mode; prints one table.
2. `tools/audit_jaunts.py`: for every claim — source resolves, locator present on DOC, entity date-eligible, no `review_required` content released, no reconstructed Indigenous encounter, no human-figure depiction, no quotation attributed to a named person, asset rights respected; per jaunt — 4–8 stops (exceptions listed with their sentence), 25–60 words per stop, at least five quiet outings with no declared resource, every family with ≥ 3 distinct keepsakes, every rank reachable without replay.
3. Measure the primary path of all 25 on the published mirror at the recommended mode (the harness ride, `travel.simulate`, plus the content's read times) and at Fly/Instantly; fix within this PR anything outside 3–6 min by re-cutting text, choosing a nearer supported stop or changing the recommended mode; never touch the displayed estimate formula.
4. Diversity check against the owner's list — commerce, travel, taverns, lodging, employment, land, newspapers, mail, river transportation, Fort Dearborn, household provisioning, trades, repairs, migration, social life — one table mapping each subject to its jaunts.
5. Prove the growth path: add a 26th fixture jaunt by JSON + `compile_jaunts.py` only, show it on the menu, then remove it (or keep it if it is a real 26th; say which).
6. `docs/measurements/jaunts_acceptance_2026-xx.md`: the tables above, every correction made, every justified exception.

**Acceptance:**
1. Exactly the 25 named premises are `available` (a substituted stop is recorded in its brief); no duplicate pilot; all six priority titles are complete and featured.
2. The audit passes with zero findings in `check.sh` (it stays in the gate).
3. All 25 recommended-mode primary paths measure 3–6 min, or carry a one-sentence justification in the report; Fly/Instantly are faster for each.
4. ≥ 5 quiet outings; every family ≥ 3 keepsakes; Seasoned Chicagoan reachable in ≤ 15 distinct completions and not by replay (walker proof).
5. The 26th-jaunt demonstration needed no JS/CSS diff.

**Harness and gates:** `./tools/check.sh` (+ audit); `smoke_budget.mjs --for-diff`; `preflight.sh`.

Changelog: one visible entry (the full library). Contract: [architecture](../docs/ARRIVAL-JAUNTS-ARCHITECTURE.md) · [briefs](../docs/JAUNTS-INITIAL-LIBRARY.md) · [plan](../docs/ARRIVAL-JAUNTS-EXECUTION.md). One PR into `dev`; claim with `ticket.mjs`.
