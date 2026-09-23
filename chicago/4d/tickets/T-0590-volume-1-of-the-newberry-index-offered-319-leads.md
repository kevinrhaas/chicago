---
id: T-0590
title: Volume 1 of the Newberry index offered 319 leads and made 0 merges: rule on every lead before volumes 2-4 add more
state: done
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-03
closed: 2026-09-03
pr: 723
claimed_by: run 9/3/2026, 2:37:17 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-03T19:58:29.178Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33796903261
---

**The owner's ask, 2026-09-03 (evening), recorded verbatim:** "and yes create a newberry spend
ticket" — answering the finding below, which he had already put in his own words earlier the same
evening: "i see lots of research being done and some apparent findings from parsing but there are
not outputs or updates to the household and resident data it seems, should i be concerned?"

**The finding, measured by `tools/measure_research_spend.py`.** The `newberry_index` domain is the
project's largest unspent read: **2,619 units read, 0 ruled on.** No ticket anywhere in the 541
spent it — this is the first. The measure is not a complaint about T-0570, which did exactly what it
was asked and did it well; it is that nothing was ever asked next.

What volume 1 (A-C) actually holds, from its own `counts` block:

| | |
|---|---|
| cards read | 2,579 (plus a 40-card precision sample) |
| Chicago or Cook County cards | 581 — of which 420 Chicago, 161 Cook |
| **leads offered** | **319** — residents 156, census_1840 81, voters 64, structures 18 |
| merges made | **0** |
| Chicago/Cook cards matching no known work | 166 |

`crosswalk.json` holds one `pass` (T-0570's own summary of the sweep) and five `refusals`, all of
them name-pair rulings anchored to nothing. Under the spend measure that is zero: a ruling that
names neither a read card nor a person in the town has not moved anybody into the town.

**Why this outranks reading volumes 2-4.** T-0578, T-0579 and T-0580 read volumes 2, 3 and 4 — on
volume 1's rate, roughly 8,000 more cards and ~950 more leads. Reading them first triples an
unspent pile that nothing has yet drawn from once. The 319 leads already on disk are the cheapest
evidence in the project: they were computed against the residents layer, the civic lists, the 1840
heads and the structures, and every one of them is a question already framed.

**The ask.**

1. `data/research/newberry_index/lead_crosswalk.json` — every one of the 319 leads ruled on, one
   entry each, ANCHORED: each carries the card's `record_id` and, where it resolves, the
   `person_id` it reaches. Outcome `matched` (an independent discriminator beyond the surname — a
   forename, a trade, a locality, a date), `candidate` (plausible, insufficient) or `refused`, with
   the reason written out. A surname-only merge is a refusal, per the domain's own rule.
2. **A refusal is an output.** `census_1840/crosswalk.json` states the standard this project holds
   itself to: "A refusal is declared as explicitly as a merge — the absence of one reads like a pair
   nobody has looked at yet." 319 refusals, honestly reasoned, closes this ticket. A ruling is the
   deliverable; a merge is not the quota.
3. The 166 Chicago/Cook cards matching no known work are a SEPARATE finding — they point at works
   the project does not hold. Do not force them into a lead. Record them as an acquisition list and
   say so; T-0581/T-0582/T-0583 already exist for three of the works they name.
4. Lower `newberry_index` in `tools/research_spend_baseline.json` by what this ticket spends, and
   say the new figure in the PR. Lowering a ceiling is free and is exactly what spending a domain
   does.

**Do not** back-project. A Newberry card is an index entry pointing at a printed work; it is
evidence that a work mentions a name, not evidence that the person stood in Chicago in 1835. The
ratified grading ladder binds here as everywhere: a card alone never mints a resident.

**Done when** every one of the 319 leads carries an anchored ruling, `measure_research_spend.py`
reports `newberry_index` spent at 319 or better, and the baseline is lowered to match.
