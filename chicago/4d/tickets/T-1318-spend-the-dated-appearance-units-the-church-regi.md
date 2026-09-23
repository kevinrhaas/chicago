---
id: T-1318
title: Spend the roll-and-appearance units: the 1830 schedule lines, the poll books, the 1833 tax roll, the 1832 Black Hawk enrolment, the church register sponsorships and the press notices, each as a bound on a held resident's presence and never more
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
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-18T15:56:46.338Z
claimed_run: null
---

Spend the dated-appearance units: the church register sponsorships, the press notices, the poll books, the 1833 tax roll and the 1832 Black Hawk enrolment, each as a bound on a held resident's presence and never more.

Piece 2 of 3 of **T-1316 — Spend the 902 units the ledger hands to the arrival pass: the dated arrivals, nativities, origins and presence bounds the books, the 1830 census, the church register, the poll lists, the land sales and the press state, onto the cards they name**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

**Its generators.** `tools/spend_name_on_a_roll_rulings.py` (`ARRIVAL`, covering the civic and 1830-census domains) and `tools/spend_remainder_rulings.py` (`a_dated_appearance_bounds_a_presence`, covering church and newspapers). The grouping follows those two generators rather than the corpora, because one constant in the first of them routes the rolls and the census together.

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
