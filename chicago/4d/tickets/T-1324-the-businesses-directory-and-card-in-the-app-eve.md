---
id: T-1324
title: The Businesses directory and card in the app: every firm in the layer findable by trade, street, division, tier and location limit, and read on one card with its proprietors, staff, dated locations, goods, liberties and evidence
state: done
epic: RENDERING
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1181
opened: 2026-09-18
closed: 2026-09-18
pr: 1455
claimed_by: run 9/18/2026, 8:49:31 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-18T15:36:37.826Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35351828193
---

The Businesses directory and card in the app: every firm in the layer findable by trade, street, division, tier and location limit, and read on one card with its proprietors, staff, dated locations, goods, liberties and evidence.

Piece 1 of 2 of **T-1181 — A Businesses view in the app: every firm by trade, street and tier, with its proprietors, staff, dated locations and location limit on one card — the visible surface for the audit and reconstruction bands**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (stated before working — one demonstration, never weakened to pass)

- A **Businesses** section in the drawer, beside People, listing all 196 firms
  `data/businesses/index.json` holds: filterable by kind (census class), trade, street,
  how far the record could place it (a roof / a landmark / a street / nowhere) and grade,
  with a toggle for "trading on 1 July"; searchable on firm style, keeper, trade and goods.
- The **business card**: name, type and grade; keepers with role, dates and tier dot, each
  linking to the person's own card where the town holds one; the dated locations in full,
  a "Go to" on a premises or a landmark the town holds, and the record's own `limit_reason`
  printed where it stops short; opened/closed with their basis; goods; the printings and
  claim ids; the liberties the record owes; `replaceable_by`.
- The layer ships: `tools/publish.sh` mirrors `data/businesses/`, and the publish gate
  accounts for every file of it.
- Smoke: the tab renders at 390×780 and 1280×800 with zero page errors, the rail still fits
  on one line at both, the unplaceable filter reaches all 83 and each prints its limit.

**A finding, recorded here rather than invented around:** the business layer states no
DIVISION for a firm. Streets carry none and neither do structures, so the row's coarsest
locator is its street; a division filter would have had to derive one, which is a claim the
record does not make. The parent's "by division" waits for a ticket that gives a business a
division from evidence.

**Not in this piece** (T-1325): a person's card does not yet list the firms they hold a role
in, and a signboard tap and a building card's "Use" line still open the building.
