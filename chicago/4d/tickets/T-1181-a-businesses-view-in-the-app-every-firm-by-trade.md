---
id: T-1181
title: A Businesses view in the app: every firm by trade, street and tier, with its proprietors, staff, dated locations and location limit on one card — the visible surface for the audit and reconstruction bands
state: open
epic: RENDERING
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: null
opened: 2026-09-16
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: null
claimed_run: null
---

The renderer never fetches `register_1835.json` or `gazetteer.json`; a business reaches a visitor
only through a building card's "Use"/"Keepers" lines, a signboard tap, or the agencies panel
(`renderers/web/js/popup.js`, `signage.js`, `agencies.js`). A street-only or unplaceable firm —
123 of 179 — is invisible. T-1147.5 asks that a user "can find a street-only/unplaceable business
without seeing a fabricated building"; this ticket is where that is built, on the record
T-1180 creates, and it is the visible payoff of the business band.

**Acceptance:**

- A **Businesses** tab beside People in the Evidence hub (`renderers/web/js/` — reuse the People
  view's list/filter/card pattern): list of all business records, filterable by type (census
  class), trade, street, division, tier (attested / inferred / reconstructed) and location limit
  (on a roof / street only / unplaceable); search on firm style, proprietor and goods.
- The **business card**: name and type; proprietors/partners/staff with role, dates and tier dot;
  locations as a dated list — primary premises (a "Go to" link when it has a roof; the street face
  highlighted when street-only; the printed reason when unplaceable); opened/closed; goods; the
  printings that attest it; its liberties (L211/L212/L218/L232 where they apply); `replaceable_by`
  on a reconstruction, in the visitor's words ("invented — would be replaced by …").
- A person's card lists every business they hold a role in, with the role and dates; a business
  card links back to every person.
- Signboard tap and building card "Use" open the business card.
- Smoke: the tab renders at 390×780 and 1280×800 with zero page errors, on the published tree
  (`--published`); `smoke_renderer.mjs` gains the tab in its walk.

**Stop condition:** every business in the layer can be found, read and traced to its evidence or
its invention from the app.

**Links:** T-1180 · T-1147 · T-0701…T-0712 (the People view and Evidence hub) ·
`renderers/web/js/residents.js` · `renderers/web/js/popup.js`.
