---
id: T-0772
title: Twelve dooryard gardens went with the retired households: should a garden follow the house or the household?
state: open
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
blocked_on: null
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

## THE OWNER'S RULING, 2026-09-21: the garden follows THE HOUSE

A dooryard garden is GROUND, not a family's possession. It belongs to the lot and the
structure standing on it, and it stays there when the household that worked it is
retired — inherited by whoever the roof is next dealt to, or standing unworked if it is
dealt to nobody.

What this settles for clause 4 of `generate_dooryard_pickets.py`: the clause asks for a
household recorded as living on the lot, and that is the wrong subject. It should ask
about the LOT — is this a dwelling lot of a kind that carried a dooryard — and not about
who was living on it on 1 July 1835. Retiring the stale occupants prose (T-0516) took the
town from eighteen gardens to one; under this ruling that withdrawal has no bearing on the
count, because the gardens were never the households' to take with them.

What it does NOT settle, and what the run must still argue: which lots carried a dooryard.
This ruling says a garden does not leave with a family; it does not say a garden may be
invented for a lot that never evidenced one. Every garden still needs its own basis, and a
garden restored under this ruling carries the household that evidenced it as the source of
the reading, with a note that the household has since been retired and the ground has not.
