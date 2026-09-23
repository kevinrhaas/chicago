---
id: T-1196
title: Re-derive the roof programme from the order book: the 668-roof schedule re-cut by what the population, occupation and lodging models say the town needed — families, districts and blocks re-targeted, every delta from the spec stated, the census's 398 dwellings reconciled
state: open
epic: TOWN
requested_by: owner
seen: true
effort: M
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

The roof programme (`1835_building_inventory.json` → 668 roofs; `reconcile_665.py` → 371 standing,
297 remaining: south 143, west 87, north 67) is a production decision from the owner's 2026
specification, calibrated before the population layer existed. The order book (T-1166)
now says how many dwellings, stores, workshops, boarding houses and outbuildings the reconstructed
town actually needs, by division. Where they disagree, the programme moves — consciously, at the
file that defines it, with the delta from the spec written down — because a roof programme that
seats one family per roof "will undercount the town it is reconstructing" (T-0507) and the
inventory's own defensible range is 565–765.

**Acceptance:**

- `1835_building_inventory.json` targets re-derived by `tools/reprogramme_roofs_1835.py --build`
  from: the order book's structure buckets; the census's 398 dwellings against the household
  count and the multi-household-per-dwelling rate from T-1163; the lodging model's
  boarding-house count; the occupation model's workshop and store counts; the outbuilding
  ratios (A-families per principal roof by household type — a merchant's stable, a labourer's
  privy and woodshed). Every family target that moves carries `{ spec, model, adopted, why }`;
  the total stays inside 565–765 or the ticket says why the range itself must move.
- District and block targets re-cut with the extended ground (T-1193,
  T-1194): the north and west now have lots to hold their targets; per-block
  capacity re-dealt by `reconcile_665.py` with the density standard; the party-line units on
  the main streets per T-1195's multi-building rule.
- `1835_family_archetype_crosswalk.json` remaining counts re-derived; `measure_family_deal.py`,
  `measure_group_district_rows.py`, `measure_frontage_entitlement.py` re-run green against the
  new targets.
- `docs/RESEARCH/inferred_infill_1835.md` and `1835_family_archetype_crosswalk.md` amended with
  the new table and the delta history (append, do not rewrite the 2026-08 reasoning).
- Visible: the gate screen's `target` moves and says why in its note.

**Stop condition:** the roof programme and the order book are one number per bucket.

**Links:** T-1166 · T-1163 · T-1164 · T-1162 · T-0032 · T-0079 · T-0507
· `docs/RESEARCH/1835_existing_roof_reconciliation.md`.
