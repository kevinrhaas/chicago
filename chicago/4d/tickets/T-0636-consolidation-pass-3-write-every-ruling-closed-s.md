---
id: T-0636
title: Consolidation pass 3: write every ruling closed since consolidation pass 2 onto the card it names, and report the delta on both hops
state: done
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-03
closed: 2026-09-04
pr: 833
claimed_by: run 9/4/2026, 8:20:10 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T02:12:38.596Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33935468156
---

Consolidation pass 3: write every ruling closed since consolidation pass 2 onto the card it names, and report the delta on both hops.

This is **pass 3**, and its window opens where T-0635 closed. It is placed before the summary tickets (T-0517, T-0518) so the summary the owner asked for describes a town whose cards have been brought up to date, not one whose evidence is still in the crosswalks. If a fourth pass is wanted, file it — the series is meant to grow.

**Filed on the owner's instruction of 2026-09-04**: *"if possible do some periodic
consolidations along the way tk turn the research created into actual data household et al
not just research, I want to get the core research and people and household and business
dataset together"*. And on 2026-09-03, the rule this series exists to enforce: *"dont land
those tickets at the very end maybe every few you should do that consolidation."*

T-0513 established the pass and ran it once. It is `done`, and a done ticket cannot be
re-claimed, which is why this is a numbered series rather than one recurring ticket: three
slots placed at intervals in the queue, so a consolidation is never more than a few source
tickets away. **This is not a source ticket. Do not read anything new in it.**

## What a pass is

1. Run `tools/measure_research_spend.py` and record BOTH hops — read vs ruled, and ruled
   vs on a card — as the pass's opening state.
2. Run `tools/consolidate_resident_evidence.py` over every crosswalk **closed since the
   previous pass**, and write what it finds onto the cards it names.
3. Re-run the measurement and state the delta as a table.

The measurement at the time this series was filed, on dev at 2e1a972d:

```
domain            holds      read    spent  unspent  id pairs
civic            records      492      479       13        90
census_1830      records       71       71        0         5
census_1840      records      593      508       85       139
church           records      531      531        0         8
books            claims       152       26      126         3
directories      claims      6684      288     6396         0
land_sales       records      375        0      375       226
newberry_index   records     7165     2087     5078         5
TOTAL                       16063     3990    12073       476

ruled onto a town person, and whether their CARD learned it:
civic                 99 reached, 99 judgeable,  0 on a card, 99 unwritten
census_1840           10 reached, 10 judgeable,  4 on a card,  6 unwritten
TOTAL                109 reached,               4 on a card, 105 unwritten
```

**105 of 109 rulings that name a town person have never reached that person's card.** That
number, and the 12,073 unspent, are what this series moves.

## A pass that finds nothing says so

A pass over a window in which nothing closed costs a run almost nothing and must report
"nothing newly closed since <pass>" rather than inventing work. That is the design, not a
failure — it is what makes the cadence safe to schedule.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

1. The before/after table for both hops is in the PR, quoted from the tool, not retyped.
2. Every ruling written names its source id. A ruling that cannot say what it rests on is
   NOT written — it is listed as blocked, with the crosswalk that owes the anchor.
3. No grade rises except where the ratified ladder's clause admits it, and the clause is
   named per grade change.
4. Nothing is read that was not already read. If the pass wants a source, it files a
   ticket for it and does not take it.
5. The pass states which crosswalks it consumed and which it skipped as already spent, so
   the next pass in the series knows its own starting line.
