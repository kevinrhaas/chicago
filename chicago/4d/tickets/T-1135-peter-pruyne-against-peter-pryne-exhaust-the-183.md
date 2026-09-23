---
id: T-1135
title: Peter Pruyne against Peter Pryne: exhaust the 1833 tax roll, or leave the town two men of one stem
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-14
closed: 2026-09-15
pr: 1356
claimed_by: run 9/15/2026, 8:33:03 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-15T14:27:56.238Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34975284349
---

Peter Pruyne against Peter Pryne: exhaust the 1833 tax roll, or leave the town two men of one stem.

**Left undecided by T-1132**, which ruled the three one-letter town pairs an anchor
reaches and could take only two of them. The ruling is written in full at
`data/residents/card_merge_rulings.json` § cluster `pruyne-pryne`, state `undecided`,
rule U1 — read it first; both readings are stated there and neither is taken.

**The state of play.** `pruyne_peter` is Peter Pruyne the druggist: with E. S. Kimberly
he opened Chicago's second drug store early in 1833; he bought school-section lots on
24-25 October 1833; he married Rebecca Sherman on 20 August 1835; he polled in ward 1 on
2 May 1837; he died in November 1839. `pryne_peter` is a civic mint on the town's own
rolls and nothing else — `Pryne, Peter` at tax_1833_086, poll_1834_091 and poll_1835_060.
The corpus holds no other bearer of the stem.

**Why C9 cannot fire.** Its load-bearing clause is a page that demonstrates the
variation, and there is none: the IRAD rolls print Pryne three times and Pruyne never;
the ISA land register prints Pruyne eighteen times and Pryne never; the deposited
1833-1835 newspaper run prints the stem 239 times, all Pruyne. Genealogy Trails carries
both spellings, but in two transcriptions of two different originals, which is a
republisher's inconsistency and not a printer's.

## Acceptance

1. **Work the exhaustion, or say it fails.** C12's shape, moved from the forename to the
   surname: the 1833 tax list is a closed roll of 115 enumerated taxpayers; Pruyne owning
   ground inside the platted town in October 1833 is an independent non-name fact arguing
   he stood on it; if every other Pr-stem entry on that roll is accounted for by a card of
   its own that Pruyne is not, `Pryne, Peter` is the only entry left for him. The count is
   run over the WHOLE roll and PRINTED, never asserted — that is what makes it a count and
   not a resemblance.
2. **If it holds**, the rule it fires under is written first (C12 reaches a forename only,
   so this is a new clause with its own four conditions), then the merge lands under it
   with `survivor` the card that carries the trade, and the town's person count moves by
   one and the PR says so.
3. **If it fails** — the roll does not bound what it needs to, or another Pr-stem entry is
   unaccounted for — the cluster is re-ruled `distinct` with the count printed as the
   reason, and U1 stops being the answer. Either way the cluster stops being undecided.
4. `./tools/check.sh` green; `consolidate_town_cards.py --check` green behind the ruling.

**Not a fold.** Nothing here widens `compatible()`, and T-1001's measurement of a blanket
one-letter fold stands.
