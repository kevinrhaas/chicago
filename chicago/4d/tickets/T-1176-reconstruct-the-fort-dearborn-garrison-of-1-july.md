---
id: T-1176
title: Reconstruct the Fort Dearborn garrison of 1 July 1835: the officers the sources name, the companies of the 5th Infantry to their strength, the surgeon, the sutler, the laundresses and soldiers' families, the Indian Agency establishment as attested — seated in the fort's roofs
state: open
epic: META
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

Two households are `division: fort` — the commandant (Maj. John Greene, inferred) and the post
surgeon (Philip Maxwell). `docs/RESEARCH/fort_dearborn.md` establishes the post was HELD on
1835-07-01 (re-garrisoned June 1832, withdrawn 29 December 1836) and warns that the "about fifty,
many invalids" line describes 1812, not 1835. The garrison is the largest single institutional
population in the scene and it is entirely missing. Stage `garrison` of T-1167.

**Research first, then reconstruction:** the ticket reads what the project holds for the 1835
garrison — Andreas's chain, the drloihjournal chronology, the Army Register 1835 if held (add the
source record if not — `check_required` rights are fine for a citation), the fort dossiers
(`fort_dearborn_barracks.md`, `_officers_quarters.md`, `_commandants_quarters.md`,
`_sutlers_store.md`, `_guard_house.md`) — and writes: officers by name and rank at
`attested`/`inferred` with sources; company count and strength from a source or, failing one,
from the 1835 establishment of an infantry company (stated as `reconstructed`, with the number
and where it comes from); enlisted men as reconstructed persons (names from the pools weighted to
the Army's recruiting communities — Irish, German, Yankee — the model's shares), ages by the
enlistment band; the four laundresses per company the regulations allowed (reconstructed,
sex female), soldiers' wives and children at the model's low rate; the sutler and the sutler's
store; the Agency establishment (the agent, sub-agent, interpreter, blacksmith of the agency) as the
sources name them, its Native and Métis employees and their families reconstructed where only
counted — through T-1177's rules, `review_required`, `touches_removal`.

**Acceptance:**

- `division: fort` households cover officers, companies, families and the Agency as above;
  every enlisted man seated in a barracks roof by company (`lives_at` at reconstructed), officers
  in the quarters the dossiers assign, the surgeon at the hospital/quarters the dossier names.
- The garrison strength and its basis printed; the population model's garrison row reconciled.
- The standing constraint honoured and proved by `measure_review_constraint.py --gate`.
- Visible: the fort's building cards list their garrison; the People view filters `fort`.

**Stop condition:** the fort is manned to a stated strength on 1 July 1835, officers attested,
ranks reconstructed.

**Links:** T-1167 · T-1161 · `docs/RESEARCH/fort_dearborn.md` · `fort_dearborn_barracks.md`
· `fort_dearborn_sutlers_store.md` · AGENTS.md § Standing constraint.
