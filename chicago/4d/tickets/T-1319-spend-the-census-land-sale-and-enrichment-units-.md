---
id: T-1319
title: Spend the land-sale and enrichment units: the entered tracts whose purchaser join the adjudication upheld, and the corroborated_enrichment rows naming an arrival or origin no structured field carries
state: split
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-1316
opened: 2026-09-18
closed: 2026-09-18
pr: null
claimed_by: run 9/18/2026, 12:09:18 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-18T17:13:12.579Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35371938176
---

Spend the census, land-sale and enrichment units: the 1830 schedule lines that bound a held resident, the entered tracts whose purchaser join was upheld, and the corroborated_enrichment rows naming an arrival or origin no field carries.

Piece 3 of 3 of **T-1316 — Spend the 902 units the ledger hands to the arrival pass: the dated arrivals, nativities, origins and presence bounds the books, the 1830 census, the church register, the poll lists, the land sales and the press state, onto the cards they name**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

**Its generators.** `tools/spend_land_sales_rulings.py` (`the_purchase_bounds_a_held_residents_presence`) and `tools/spend_remainder_rulings.py` (`the_enrichment_names_an_arrival_or_origin_no_field_carries`).

**Where this came from.** T-1169 (PR #1449) was the arrival pass, and it is done: it filled
`arrival_year`, `origin` and `reason_for_coming` on all 1,258 households from the Calumet Club
Old Settlers roll and the town model, at the tier each household's own evidence allows. It did
not, and could not in one run, read the per-unit bounds those rulings hand to that field one unit
at a time. `spend_name_on_a_roll_rulings.py` says in its own comment what should happen when it
closes — "when either closes, these registers go red and the units come back for a real answer.
That is the point" — so the hand-off moves here, the way T-1145's moved to T-1296. A closed
ticket cannot own unresolved units; `measure_research_spend.py` refuses one, and a ledger that
allowed it would be reading them as spent.

**Acceptance:** every unit either asserted onto the card it names at `attested`/`inferred` with
its source, or refused in writing under a named rule, or handed on to a ticket that is open;
`measure_research_spend.py --check` green with **0** units owned by this ticket at the end.

**Links:** T-1169 · T-1317 · T-1318 · T-1319 · T-1157 · `data/research/*/spend_rulings.json` ·
`tools/measure_research_spend.py`.
