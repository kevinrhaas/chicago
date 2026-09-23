---
id: T-0834
title: The 665 schedule sizes a block's principal room in party-line units and the generator places by whole lots, and on a business front the two disagree
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-12
pr: 1179
claimed_by: run 9/12/2026, 1:49:47 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-12T07:13:51.285Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34678971065
---

The 665 schedule sizes a block's principal room in party-line units and the generator places by whole lots, and on a business front the two disagree.

Found by T-0431, the second deal on `blk_south_water_clark`, and handed on as that deal's
successor under T-0028's programme rule.

**The two sizings.** `tools/reconcile_665.py` sizes a block's principal room as
`ROW_UNITS_PER_LOT * (free_lots - 1)` — party-line units of 6.072 m, counted against whole
LOTS — and dealt `blk_south_water_clark` **3 principal roofs**.
`tools/generate_block_infill.py`'s T-0105 ceiling is one principal roof per lot, and a
frontage run may carry no more roofs than the lots it was dealt. The second deal was dealt
**one** lot, so the ceiling was one, and two dealt roofs (D3, D4) went unbuilt. They could not
be `deferred` either: that list is only for families the generator refuses BY NAME.

**Measured, so the gap is not an impression.** On the committed north face lot 2 projects
24.643–49.751 m; after the plat module's 1.5 m side margins it offers 22.108 m of buildable
frontage. `pruyne_kimball_drugstore` holds 39.108–46.825 m. The C2 the deal built stands
33.356–39.107 m. **7.213 m of buildable frontage remain clear**, which is over the D3 band's
4.88 m minimum — so on this block the metres did NOT refuse the two roofs; the lot ceiling
did. On `blk_south_water_franklin` (T-0430) the same shapes agreed by accident, because the
free lot carried no documented roof at the street.

**Why it matters and is not cosmetic.** The business-front clause of 2026-08-27 makes a lot
free while a documented store stands on its frontage. Every such lot is now sized by one rule
and placed by another, and the difference is silently absorbed into the district balance: the
programme's own numbers say roofs were dealt and the ground says they were not placed, with
nothing tying the two statements together. `blk_south_water_dearborn` (T-0432) is next in this
family and will hit it again.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- The two sizings are reconciled, or the disagreement is made explicit and gated: a block
  whose dealt roofs exceed what its lot ceiling can carry says so in the programme, in a field
  a gate reads, rather than only in a recipe's prose.
- Whatever is chosen, no committed record moves and no mesh goes stale for it — this is a
  ledger question, not a placement one.
- `blk_south_water_clark` and `blk_south_water_franklin` both re-derive under the new rule and
  the difference between them is stated.

**Links:** T-0431 (found it) · T-0430 · T-0432 (will hit it) · T-0028 (the programme) ·
T-0105 (the lot ceiling) · T-0420 · `tools/reconcile_665.py` · `tools/generate_block_infill.py`.
