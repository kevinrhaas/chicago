---
id: T-1326
title: Spend the town's own rolls onto the cards they name: the 1833-1835 poll lists, the 1833 tax list and the 1832 Black Hawk enrolment, each written onto the held resident as a dated, sourced bound the ledger can see
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-1318
opened: 2026-09-18
closed: 2026-09-18
pr: 1458
claimed_by: run 9/18/2026, 10:56:48 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-18T17:08:29.344Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35364663146
---

Spend the town's own rolls onto the cards they name: the 1833-1835 poll lists, the 1833 tax list and the 1832 Black Hawk enrolment, each written onto the held resident as a dated, sourced bound the ledger can see.

Piece 1 of 2 of **T-1318 — Spend the roll-and-appearance units: the 1830 schedule lines, the poll books, the 1833 tax roll, the 1832 Black Hawk enrolment, the church register sponsorships and the press notices, each as a bound on a held resident's presence and never more**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Why the parent was split here.** T-1318 owned 538 units across four corpora, and only 216 of
them sat on a card at all. The line between the two children is the line the evidence itself
draws: the town's own rolls are one corpus, adjudicated once in `voter_crosswalk.json`, already
written onto 236 cards in prose by T-0634's pass, and needing only to be made legible to the
research-spend ledger. The 1830 schedule, the church register and the press notices are three
other corpora whose cards mostly carry no block at all, and that is T-1329's run.

**Acceptance:** (stated before working — one demonstration, never weakened to pass)

1. Every one of the 292 matched entries of the 1833-1835 poll and tax lists is a structured,
   source-bearing field on the person `data/research/civic/voter_crosswalk.json` matched it to
   — `persons[].dated_bounds[]` — and `research_spend_ledger.natural_disposition` closes it
   `asserted` off that field rather than off prose.
2. No row reaches `attested`. Every matched identity in that crosswalk is a name agreement and
   none is an identification a source makes, so every bound is `inferred` and says why.
3. No row covers the scene date, the 1835 poll included: an earlier source corroborates and
   dates and never promotes, and that list's own reading gives its date as a bare year.
4. A tax row bounds PROPERTY and not presence (T-1117): `bounds: "property"`, `here_by: null`.
5. The eight corroborated 1832 Black Hawk enrolments get a written REFUSAL under a named rule
   rather than a fourth hand-off, and the refusal states what would reopen them.
6. The two rules that used to hand the 292 on are GONE from
   `tools/spend_name_on_a_roll_rulings.py` — a ruling on a unit something else closed reads as
   work done and is not — and that file's own self-test is what refuses a rule that never fires.
7. `measure_research_spend.py --check` green with **0** units owned by this ticket, and 0 owned
   by the split parent: what this run did not spend is repointed at T-1329, which holds it.
8. No grade moves, no identity is reopened, no person is minted, and the applier changes exactly
   one key — asserted by `tools/spend_civic_roll_bounds.py --self-test`.

**Verification:** `tools/spend_civic_roll_bounds.py --self-test` (17 checks) and `--check`;
`tools/spend_name_on_a_roll_rulings.py --self-test` and `--check`;
`tools/spend_remainder_rulings.py --self-test`; `tools/check.sh`; the smoke parts
`tools/smoke_budget.mjs --for-diff` names.
