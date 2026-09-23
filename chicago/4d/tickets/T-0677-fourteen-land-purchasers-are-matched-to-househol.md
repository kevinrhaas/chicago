---
id: T-0677
title: Thirty-five land purchasers are matched to households and not one is on the card: spend the land-sales resident crosswalk, tract, date and price
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-05
pr: 935
claimed_by: run 9/5/2026, 6:12:07 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T23:36:07.540Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33997872177
---

Thirty-five land purchasers are matched to households and not one is on the card: spend the land-sales resident crosswalk, tract, date and price.

`data/research/land_sales/resident_crosswalk.json` matches thirty-five purchasers in the
Illinois public-domain tract-sales deposit to people this town holds a card for — Hiram
Pearsons, Daniel Elston, Thomas Hartzell, Bronson, Hale, Ludby, Price, Wolcott and six
more — each row naming a `household_id` and a `resident_id`. Not one of the thirty-five is on
the card it names. T-0635 (consolidation pass 2) made them visible for the first time: it
stated the file's source at the top so the rulings became judgeable, and taught the second
hop of `tools/measure_research_spend.py` to read a row filed under `matches` as a match.
The finding is recorded as that domain's write-hop ceiling of 35 in
`tools/research_spend_baseline.json`, and this ticket is how the ceiling comes back down.

WHY IT IS WORTH A RUN. A purchase is POSITION. Each row joins to an entry in
`data/research/land_sales/entries.json` carrying a record id, an aliquot part, a section,
township and range, a date of sale, an acreage and a price — and this town has 20
households with any address at all. It is the cheapest position in the project.

WHAT IT MUST NOT DO. The crosswalk's own carry rule is that a purchase "dates and places a
transaction; it proposes no residence, and under the ratified ladder it corroborates rather
than mints". So no grade moves, no `lives_at` is written off a tract, and a purchase in a
ring township is not a house. `tools/spend_civic_voter_lists.py` and
`tools/spend_fergus_1839_later_lists.py` are the two worked precedents: two fields on the
card, a ledger whose name carries no "crosswalk", and a `--check` in `tools/check.sh`.

BEWARE THE MATCHER. T-0670 carries the surname-uniqueness weakness that made nine of these
matches ambiguous when T-0514 seated 531 new residents; the thirty-five are what survived it, after T-0675 and T-0676 (PRs #798, #816) took the register from 375 sales to 953 while T-0635 was in flight and its matches from 14 to 35.

**Acceptance:**

1. Every one of the thirty-five rulings is on the card it names, citing
   `isa_public_domain_land_tract_sales` and naming the entry record id it rests on.
2. `tools/measure_research_spend.py --gate` reads land_sales' write hop at 0, and the
   ceiling in `tools/research_spend_baseline.json` is LOWERED rather than raised.
3. No grade moves and no placement is written. The tool's `--self-test` holds it.

**A working tool already exists and is pushed.** `steward/salvage-t0635-mine` carries
`tools/spend_land_sales.py` — the civic pass's shape, two fields and no others, no grade
moved, a `land_sales_spend_1835.json` ledger, a `--check` in both directions and eight
self-test assertions — written against dev at `36d1dde2` and green there on all 35 rulings
over 31 cards. It was built by the run that landed T-0635 and held back rather than bundled
into that PR, because this is its own ticket. Read it, re-derive it against whatever dev
looks like by then, and gate it; do not start from nothing.

---

**CLOSED BY WHAT ALREADY LANDED — read this before the paragraph above (T-0677's own run,
2026-09-05).** Every acceptance clause was already met on `dev` when this run opened the
ticket, and not by this run: **T-0636, consolidation pass 3, PR #833** wrote the federal
tract sales onto the thirty-one cards the thirty-five rulings name. The ticket was filed
2026-09-04 against the state of that morning; pass 3 landed after it and did the work.
Verified here against `dev` at `a0a23acc7`, per clause and not by summary counter:

1. All 35 rulings are on the card they name — each named person carries
   `isa_public_domain_land_tract_sales` in `sources`, and every one of the entry record
   ids the ruling rests on is quoted in the note. Checked ruling by ruling: 35 of 35, none
   defective.
2. `tools/measure_research_spend.py --gate` reads land_sales at `35 reached, 35 judgeable,
   35 on a card, 0 unwritten`, and `unwritten_ceiling.land_sales` in
   `tools/research_spend_baseline.json` stands at **0** — lowered from the 35 this ticket
   was opened to pay down, never raised.
3. No grade moved and no placement was written; `tools/spend_land_sales.py --self-test`
   holds it.

**THE POINTER IN THE PARAGRAPH ABOVE IS A TRAP — DO NOT FOLLOW IT.** The tool on
`steward/salvage-t0635-mine` is the version written for pass 2, and
`tools/spend_land_sales.py` on `dev` SUPERSEDES it. They write different paragraphs about
the same register under different markers, so the older one does not overwrite the newer —
it appends beside it, and all thirty-one cards end up saying the tract sales twice in two
voices. This run did exactly that by following the pointer, and **`tools/check.sh` was
GREEN on the doubled tree**: `gaps()` asked only whether the paragraph was present and
`strays()` only whether an unruled card carried one, so neither could see a card that said
it twice.

That hole is what this ticket ships, and it is all it ships: `doubles()` in
`tools/spend_land_sales.py`, wired into `--check` and held by three new `--self-test`
assertions. It fires on both ways a card comes to say the register twice — this pass's own
paragraph written twice over, and a superseded pass's paragraph left standing beside it.
Demonstrated red on the doubled tree (31 faults, exit 1) and green on `dev` as it stands.
The other four spend passes carry no such rule; that is filed separately rather than
bundled here.
