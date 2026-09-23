---
id: T-0598
title: 103 of 109 rulings that reach a town person cannot say what they rest on: every crosswalk states its source, so a ruling can be spent
state: done
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-03
closed: 2026-09-03
pr: 733
claimed_by: run 9/3/2026, 4:30:05 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-03T22:14:10.007Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33807947702
---

**The owner's ask, 2026-09-03 (evening), verbatim:** "yes do a ticket for that on the crosswalks and
put it relatively high in queue in an appropriate place."

**The finding, and it fell out of building the second hop of
`tools/measure_research_spend.py`.** That measure asks, of every ruling that reaches a person in the
town, whether that person's CARD carries any source the ruling rests on. It cannot ask the question
of most rulings, because most rulings never say what they rest on:

| domain | reach a town person | state a source | cannot be judged |
|---|---|---|---|
| civic | 99 | **0** | 99 |
| census_1840 | 10 | 6 | 4 |
| **total** | **109** | **6** | **103** |

`civic/voter_crosswalk.json` matches 99 voters to residents with a `record_id`, a
`matched_resident`, a `household_id`, a `discriminator` sentence and a `rule` — and no `source_id`
anywhere, on the entry or at the top of the file. The evidence it rests on is
`chicago_voter_lists_1833_1835_irad`; that string appears in the domain's `records/` file and
nowhere in the crosswalk that adjudicates against it.

**Why this is a real defect and not bookkeeping.** A ruling is only spendable if something can carry
it to a card. `persons[].sources` on a resident record is a list of SOURCE IDS. A ruling that names
a person but not a source cannot be spent by any tool, only by a human rereading the whole crosswalk
and inferring what it must have meant — which is exactly the manual step the owner has been asking
the project to stop relying on. It also means the second-hop gate is blind on those 103: it reports
them `unjudgeable` rather than counting them, deliberately, because a number that looks like a
finding and is really the instrument's blind spot is worse than no number (that mistake was made and
corrected the same evening — the whitelist bug, PR #715 follow-up).

**The ask.**

1. Every crosswalk file states the source or sources its rulings rest on. The narrow form is a
   top-level `source_id` (or `source_ids`) naming what the domain adjudicated FROM; the better form,
   where a ruling rests on something specific, is a per-entry `discriminators: [{source_id, …}]`
   like `census_1840/resident_crosswalk.json` already writes. Both are already in use in this repo —
   this ticket makes them universal, it does not invent a shape.
2. Backfill `civic/voter_crosswalk.json` and `civic/blackhawk_war_crosswalk.json` first: they are
   99 of the 103 and the source ids already exist in their own `records/` files.
3. Then the rest of the domains' crosswalks, and `census_1840/resident_crosswalk.json`'s four
   entries that carry `same_name_support` with no `source_id` on the support rows.
4. Extend `tools/measure_research_spend.py --self-test` with a case that a crosswalk stating no
   source at all is a FAULT rather than merely unjudgeable, and turn the gate on for it once the
   backfill lands — the ratchet shape, so it can never regrow.

**Done when** `measure_research_spend.py` reports `no source stated` at 0 for civic and in single
figures overall, and every ruling that reaches a town person can be checked against that person's
card by a tool rather than by a person.

**Do not** invent a source for a ruling whose basis is genuinely unrecorded. If a crosswalk cannot
say what it rested on, that ruling is not merely unlabelled, it is unreviewable, and it should be
re-derived or withdrawn rather than given a plausible-looking citation. A wrong `source_id` is worse
than a missing one: the gate would go green on it.
