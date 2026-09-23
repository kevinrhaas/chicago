---
id: T-1317
title: Spend the books' arrival units: the dated arrivals, nativities and presence bounds Hubbard's autobiography, Andreas and Moses and Kirkland state about people this town holds, onto the cards they name
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
claimed_by: run 9/18/2026, 9:46:52 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-18T14:49:50.845Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35357917317
---

Spend the books' arrival units: the dated arrivals, nativities and presence bounds Hubbard's autobiography, Andreas and Moses and Kirkland state about people this town holds, onto the cards they name.

Piece 1 of 3 of **T-1316 — Spend the 902 units the ledger hands to the arrival pass: the dated arrivals, nativities, origins and presence bounds the books, the 1830 census, the church register, the poll lists, the land sales and the press state, onto the cards they name**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

**Its ruling.** `handed_to_the_arrival_pass` in the hand-authored `data/research/spend_rulings.json` — the books domain: Hubbard's autobiography, Andreas, and Moses and Kirkland.

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
