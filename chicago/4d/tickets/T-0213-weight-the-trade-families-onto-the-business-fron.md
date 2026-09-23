---
id: T-0213
title: Weight the trade families onto the business front
state: done
epic: TOWN
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-26
closed: 2026-08-27
pr: 419
claimed_by: run 8/27/2026, 6:18:26 PM CT
blocked_on: null
needs_bake: false
---

Weight the trade families onto the business front.

The surviving half of ROADMAP K29. T-0022 refuted the other half — the schedule may deal
log cabins to commercial frontage, and did not need a term keeping them off it — but the
same census supports this one: South Water Street's DOCUMENTED street line is **80 % trade**
(7 stores plus a warehouse of 10 records carrying a `likely_family`), while the schedule
apportions families by DISTRICT and has no notion of a street. So a block dealt a South
Water face should be likelier to be dealt C, F and W than a block one street back, and today
it is not.

This is a re-apportionment in `tools/reconcile_665.py`, not a block parcel, and it is
INVISIBLE until a block is built — the five South Water blocks are all claimed, so the first
scene it could change is a later face. Pair it with a block that spends the new deal, or say
in the PR which of the three visible-progress exemptions it is claiming.

Read `tools/measure_frontage_fabric.py` first: it holds the frontage census and the one
assertion T-0022 left behind, and the trade share is one report away from it.

**Acceptance:** the frontage term is derived from the committed street hierarchy and the
committed `likely_family` reconciliation rather than authored as a constant;
`tools/reconcile_665.py --check` re-derives; the 665 family totals are unchanged in aggregate
(this moves families between schedule units, it does not raise or lower the target); a named
block visibly changes deal; `check.sh` green.
