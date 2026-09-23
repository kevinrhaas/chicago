---
id: T-1382
title: The People view's Trade filter offers only the ten commonest trades, and the 308 reconstructed trade heads pushed the town's tavern keepers, physicians and lawyers off it
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-19
closed: 2026-09-19
pr: 1512
claimed_by: run 9/19/2026, 5:41:35 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-19T11:23:46.435Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35437831768
---

The People view's Trade filter offers only the ten commonest trades, and the 308 reconstructed trade heads pushed the town's tavern keepers, physicians and lawyers off it.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

`renderers/web/js/filterSpecs` in `renderers/web/js/people.js` cuts the Trade row to the
**top ten** trades by count (`.slice(0, 10)`). That was a reasonable cut over a layer of
457 named residents. T-1347 then drew 308 reconstructed heads — 57 domestics, 38
boarding-house keepers, 26 labourers, 24 clerks, 21 carpenters — and the ten commonest
trades are now almost entirely that draw. `tavern_keeper` is rank 78 of 83 with 8 people
and has no pill at all, so a visitor cannot ask the directory for this town's tavern
keepers, its physicians or its lawyers: the attested trades a reader would actually look
for are exactly the ones the reconstruction buried.

**How it was found.** `tools/smoke_renderer.mjs`'s check *"the tavern-keeper pill narrows
the list to tavern keepers"* has been RED on dev since T-1347 landed — it asserts
`.pill[data-filter="occupation"][aria-pressed="true"]` and gets an empty string, because
the pill is not rendered. Measured on 2026-09-19 at both viewports (stage 12), and dated on
dev's own record at 2026-09-19T06:31, before T-1353's branch existed. `dir.filter()` itself
is fine — it returns the 8 tavern keepers. It is the OFFER that is gone.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- The Trade row offers the trades a reader looks for, and the rule that decides which is
  written down rather than a bare `slice(0, 10)` — the attested layer's own commonest
  trades, or a "more" affordance, or a cut that does not let a reconstruction pass push a
  documented trade off the list. Whatever the rule, say why it is that one.
- The smoke's tavern-keeper check passes again at both viewports, and it is still asserting
  something — a check that was quietly satisfied by deleting the assertion is not a fix.
- Found by T-1353 while gating the transient cohort; that stage adds no trades and did not
  move this (its tallies are resident-only and the occupations vocabulary is byte-identical
  to dev's).

**Links:** T-1347 (which moved it) · T-1179 (the convergence this sits in) · T-1353.
