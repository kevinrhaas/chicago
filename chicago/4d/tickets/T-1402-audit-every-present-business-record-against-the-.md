---
id: T-1402
title: Audit every present business record against the research: proprietors and partners adjudicated against identity.json, dates honouring opening_announced and dissolved, type = its census class, goods, and every place the research names as a plural locations[] with its limit class — with the field x grade reconciliation table, the report and its --check gate
state: done
epic: META
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1182
opened: 2026-09-19
closed: 2026-09-19
pr: 1532
claimed_by: run 9/19/2026, 12:58:10 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-19T18:35:42.388Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35459507637
---

Audit every present business record against the research: proprietors and partners adjudicated against identity.json, dates honouring opening_announced and dissolved, type = its census class, goods, and every place the research names as a plural locations[] with its limit class — with the field x grade reconciliation table, the report and its --check gate.

Piece 2 of 5 of **T-1182 — Audit every attested and inferred business against the research: proprietors, partners, dates, primary and secondary premises, the Dec 1835 State census classes and the August 1835 American count — and raise an inferred business for every in-window trade that has none**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

The parent's clause 1 and clause 7, unchanged: proprietors and partners adjudicated
against `identity.json` (47 firm merges, 12 proprietor merges), dates from first/last
printing with `opening_announced`/`dissolved` honoured, `type` = its census class,
`goods`, and every location the research names — the premises AND the secondary places
(a warehouse on the river, a yard, an office at a hotel, an auction stand) — as
`locations[]` with the limit class. A reconciliation table: field x (filled attested /
filled inferred / empty with reason). Report `docs/RESEARCH/business-audit-2026-09.md`;
`--check` re-derives; gates in `check.sh`.

The dated relocations `compile_businesses.locations_for` keeps as unplaceable secondary
rows (`anchor_change`, four houses) are this ticket's to audit with the sources in front
of it — the comment there already says so.

