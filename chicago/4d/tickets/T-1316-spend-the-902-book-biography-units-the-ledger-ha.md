---
id: T-1316
title: Spend the 902 units the ledger hands to the arrival pass: the dated arrivals, nativities, origins and presence bounds the books, the 1830 census, the church register, the poll lists, the land sales and the press state, onto the cards they name
state: split
epic: META
requested_by: loop
seen: false
effort: L
legacy_id: null
parent: null
opened: 2026-09-18
closed: 2026-09-18
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-18T10:08:27.490Z
claimed_run: null
---

Spend the 902 book-biography units the ledger hands to the arrival pass: the dated arrivals, nativities and presence bounds Hubbard, Andreas and Moses and Kirkland state, onto the cards they name.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Where this came from.** T-1169 (PR #1449) was the arrival pass, and it is done: it filled
`arrival_year`, `origin` and `reason_for_coming` on all 1,258 households from the Calumet Club
Old Settlers roll and the town model, at the tier each household's own evidence allows. It did
not, and could not in one run, read the **902 research units** nine `spend_rulings.json` rules
hand to that field one unit at a time. Those rules re-point here, the way T-1145's handoff moved
to T-1296, because `measure_research_spend.py` refuses an unresolved unit whose owner ticket is
not open — a closed ticket cannot hold 902 units, and a ledger that let it would be reading them
as spent.

**What the 902 are.** Per-unit readings that each spend ONE source onto ONE card:

- `books` — a dated arrival, a nativity or a dated presence bounding one, from Hubbard's
  autobiography, Andreas and Moses & Kirkland.
- `census_1830` — an 1830 schedule line that bounds a held resident's presence, and the surname
  variants the crosswalk calls candidates and not merges.
- `church` and `newspapers` — a dated appearance that bounds a presence and states nothing else.
- `civic` — the poll books, the 1833 tax roll (property, not presence) and the 1832 Black Hawk
  enrolment that may bound a rolled man's arrival.
- `land_sales` — an entered tract whose purchaser join the adjudication upheld.
- `residents` — `corroborated_enrichment` rows naming an arrival or origin no field carries.

**Acceptance:** every unit either asserted onto the card it names at `attested`/`inferred` with
its source, or refused in writing under a named rule, or handed on to a ticket that is open;
`measure_research_spend.py --check` green with **0** units owned by this ticket at the end.

**Effort is L and `claim` will refuse it — that is correct.** Split it by DOMAIN when it is
reached: the books reading is its own run or more, and each of the other six is a bounded pass.
Do not take it whole.

**Links:** T-1169 · T-1157 · T-1241 · `data/research/*/spend_rulings.json` ·
`tools/measure_research_spend.py`.
