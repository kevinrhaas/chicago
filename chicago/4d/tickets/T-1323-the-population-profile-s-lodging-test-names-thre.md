---
id: T-1323
title: The population profile's lodging test names three functions no building can spell: tavern, inn and coffee_house are not vocabulary terms, so every house of entertainment is classed a dwelling
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-18
closed: 2026-09-18
pr: 1468
claimed_by: run 9/18/2026, 2:10:55 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-18T19:47:41.935Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35384005344
---

The population profile's lodging test names three functions no building can spell: tavern, inn and coffee_house are not vocabulary terms, so every house of entertainment is classed a dwelling.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

`tools/profile_population_1835.py` classes a household's lodging by exact match:

    LODGING_FUNCTIONS = {"hotel", "tavern", "boarding_house", "inn", "coffee_house"}

Three of those five are not terms of the closed function vocabulary T-1311 wrote into
`data/structures.schema.json`, and never were spellings any record used: the town's
public houses are `tavern_inn` (7 roofs), and `inn` and `coffee_house` appear on no
building at all — the Exchange Coffee House records as a `hotel`. So a household lodged
at a tavern is counted under "a dwelling or a place of business", and the profile's
Lodging section under-reports the houses of entertainment.

Found while closing the vocabulary (T-1311) and NOT fixed there: correcting the set
changes the profile's own counts, which is a reading about the town rather than a
migration, and T-1311's demonstration was that the migration moves nothing.

**Acceptance:** the lodging test is stated against vocabulary terms, gated so a term
that no structure can spell is refused the way the signage rule's trades now are
(`tools/normalise_structure_function.py --check`); the Lodging section is rebuilt and
its before/after counts printed; the tavern households land in the right class.

**Links:** T-1311 · `tools/profile_population_1835.py` · `data/structures.schema.json`.
