---
id: T-1212
title: Yards for every household: lot-line and dooryard fences, gardens, woodpiles, wells, privies and stables assigned by household type, wagons and barrels and trade goods at the shops by trade — the enclosure, yard and outbuilding layers extended to the reconstructed town
state: open
epic: TOWN
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

The enclosure layer (`data/enclosures/town_lot_line_*.json`, `town_dooryard_pickets.json`, T-0038,
`enclosure_owners.py` — "a home by lives_at, a workplace by works_at"), the yard-goods layer
(`data/yard/`, T-0040), the wells layer (2 records) and the dooryard-garden rule
(`docs/RESEARCH/dooryard-garden-admission-rule.md`) are dealt to the documented households. Now
every household has a lot and a type. Drawn at load — no bake for the layers; the A-family
outbuildings themselves are raised by the build tickets.

**Acceptance:**

- A **yard-by-household rule** (in the policy file): per household type × wealth class — fence
  kind (pickets at the better houses, boards, rails, none at the shanties), dooryard garden
  (the admission rule extended to reconstructed households at its own tier), woodpile, a well
  where the lot's household class and the wells research allow (`docs/RESEARCH/wells.md`),
  privy placement off the alley, stable/barn for the households that kept a horse (merchants,
  forwarders, physicians, teamsters, the taverns); per business — the trade goods and vehicles
  of T-0040 by trade (barrels at the coopers and packers, wagons at the forwarders and the
  teamsters, lumber at the joiners, hides at the tannery, hay at the stables within the hay
  limits).
- Applied town-wide by the existing generators (`generate_lot_line_fences.py`,
  `generate_yard_goods.py`, `generate_lot_building_material.py`, a wells generator added on the
  same pattern), every record `belongs_to` a household or business; `--check` green; the hay
  ordinance gate (`1835_hay_limits.json`) honoured.
- **Visible:** a screenshot of a back-street block shows fenced yards, gardens, privies and
  woodpiles that differ house to house.

**Stop condition:** no lot in the town is bare ground by default.

**Links:** T-0003 · T-0038 · T-0040 · `docs/RESEARCH/dooryard-garden-admission-rule.md` ·
`docs/RESEARCH/wells.md` · `data/reconstruction/1835_hay_limits.json` · T-1195.
