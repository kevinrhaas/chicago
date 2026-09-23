---
id: T-0772
title: Twelve dooryard gardens went with the retired households: should a garden follow the house or the household?
state: blocked-owner
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-04
closed: null
pr: null
claimed_by: null
blocked_on: Does a dooryard garden follow the HOUSEHOLD or the HOUSE? Clause 4 of generate_dooryard_pickets.py asks for a household recorded as living on the lot, and since T-0516 withdrew the stale occupants prose that leaves the town ONE garden (Elijah Harmon's, blk_randolph_franklin_lot2) where it drew eighteen on 2026-08-18 and thirteen on 2026-09-02. The HOUSE reading — one dwelling standing alone on a platted lot, by archetype and by function — would keep thirteen or more on a weaker but still true claim: houses of this kind had kitchen gardens behind them. Household = fewer gardens, each resting on a named household; house = more gardens, resting on the archetype. If the HOUSE rule wins, the same question is asked of the lot-line fences, which run off the same occupancy test. docs/LIBERTIES.md L129 now states the count in force and the drift either way.
needs_bake: false
closed_at: null
claimed_run: null
---

Twelve dooryard gardens went with the retired households: should a garden follow the house or the household?.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Filed by T-0516, which caused it and refused to decide it.**

`tools/generate_dooryard_pickets.py` admits a lot to the garden layer on four clauses, and
clause 4 is *"a household recorded as living in it"* — read off the structure record's
`occupants` prose naming an `hh_` id. T-0516 withdrew that prose from the 104 anonymous
roofs the retired inferred-household layer had adopted, because the households it named
were removed on 2026-09-02 under the owner's ruling. The rule then did exactly what it
says: **thirteen dooryard gardens became one.** The survivor is Elijah Harmon's, the only
lot this record reaches where the committed household index carries a real `lives_at`.

The generator's own comment anticipated this and named the ticket: *"the stale-prose
problem is T-0516's"*. So the collapse is the rule working, not the rule breaking — twelve
gardens were resting on the prose of households that no longer exist, and a garden behind a
house nobody lives in claims a gardener who does not exist.

**But the question underneath it is the owner's, not the loop's.** A dooryard garden could
just as defensibly follow the HOUSE — one dwelling alone on a platted lot, by archetype and
by function — as follow a recorded household. That reading would keep all thirteen and
would say something weaker but still true: houses of this kind had kitchen gardens behind
them. It is a claim about what the town looked like, and the owner has ruled on exactly
this kind of trade before ("lots of nothing happened in the city which is bad").

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- The owner is asked, in these terms, which rule the garden layer runs on: the household
  (today, thirteen → one) or the house (thirteen or more, on a weaker claim). Use
  `ticket.mjs block --owner --on "..."` rather than choosing for him.
- Whichever he rules, clause 4 is rewritten to say it, `docs/LIBERTIES.md` L129's entry is
  brought into line with the rule actually in force, and the count before and after is
  stated.
- If the house rule wins, the same question is asked of the lot-line fences, which run off
  the same occupancy test.

**Links:** T-0516 (the withdrawal) · T-0637 (`belongs_to` on every run) · T-0514 (the
address work the real `lives_at` count is waiting on) · `docs/LIBERTIES.md` L129.
