# Does a dooryard garden follow the HOUSE or the HOUSEHOLD?

**The question is T-0772's, and it is the owner's to answer.** This file is the evidence
he was promised: the two readings of the rule, counted against the tree in front of them,
so the ruling is made on numbers rather than on a recollection of how many gardens the
town used to have.

DERIVED, NOT WRITTEN. Every count below comes from
`python3 tools/generate_dooryard_pickets.py --compare-rules`, which is the same generator
that writes the committed record, run with clause 4 dropped and every other clause left
alone. It writes nothing, and no writing path can reach the clause-4-less pool, so reading
this cannot move the record.

## How this came about

`tools/generate_dooryard_pickets.py` admits a lot to the garden layer on five clauses, and
clause 4 is *"a household is recorded as living there. A garden is a HOUSEHOLD'S."* — read
off the structure record's `occupants` prose naming an `hh_` id.

T-0516 withdrew that prose from the 104 anonymous roofs the retired inferred-household
layer had adopted, because the households it named were removed on 2026-09-02 under the
owner's own ruling. Clause 4 then did exactly what it says, and **thirteen dooryard gardens
became one**. The survivor is Elijah Harmon's log cabin on `blk_randolph_franklin_lot2`,
the only lot this record reaches where the committed household index carries a real
`lives_at`.

That collapse is the rule working. Twelve gardens were resting on the prose of households
that no longer exist, and a garden behind a house nobody lives in claims a gardener who
does not exist. The question underneath it is a different one, and it is not the loop's:
**a dooryard garden could as defensibly follow the HOUSE** — one dwelling alone on a
platted lot, by archetype and by function — as follow a recorded household.

## The two readings, over the same tree

Clause 5 (room at the back for a plot that hits nothing) is applied to both, so these are
gardens actually drawable and not pools:

| | lots admitted | gardens drawn | refused for want of room |
|---|---|---|---|
| **the HOUSEHOLD rule** — clause 4 as written, in force today | 1 | **1** | 0 |
| **the HOUSE rule** — clause 4 dropped, clauses 1, 2, 3, 5 unchanged | 34 | **29** | 5 |

The house rule adds **28** gardens. Where the ticket guessed "thirteen or more", the town
has grown since: the platted grid now holds 62 lots with exactly one building on them, 36
of those buildings are dwellings by archetype and 34 by function too.

## What the 28 added gardens would stand behind

Graded by the project's own confidence on what the building IS — `function.confidence` on
the structure record:

| the house's function grade | added gardens |
|---|---|
| `attested` | 3 |
| `reconstructed` | 25 |

**That table is the cost of the house rule, and it is the part worth ruling on.** Twenty-five
of the 28 would stand behind a reconstructed cottage — a building this project placed to fill
a block it knows was built up, not one a source puts on that lot. A garden behind one of those
is an invention resting on an invention. It is not therefore wrong: L129 already claims the
garden treatment as `reconstructed` on the plate's authority, and the same tier hides both
together. But it is a different claim from the one the record makes today.

And of the three `attested` houses, **two are John Wright's buildings to let**
(`wright_building_to_let_a`, `wright_building_to_let_b`) — which clause 4's own docstring
names as the thing it excludes, because their records say in as many words that *"the honest
reading of 'to let' is a building whose tenant this project cannot name"*. The house rule
brings them back and puts a kitchen garden behind a building that may have stood empty.

That leaves exactly **one** added garden behind an attested dwelling the town can name:
`lasalle_lake_house`, the house at the corner of LaSalle and Lake.

## The lot-line fences already answer it the other way

T-0772's third acceptance bullet asks that the same question be put to the lot-line fences,
*"which run off the same occupancy test"*. **They do not.** `tools/generate_lot_line_fences.py`
admits a lot on clause 2, IMPROVEMENT — *"at least one committed building centre stands in
it"* — and never looks at `occupants` at all; `enclosure_owners.household_links()` is read
there only to attribute a run in `belongs_to`, never to admit one. Today that record fences
**118 of the town's 127 improved platted lots in 291 runs**.

So the enclosure layer already holds both answers at once: **the yard fence follows the
house, and the garden inside that yard follows the household.** Whichever way the owner
rules, one of the two is currently out of step with the other, and that inconsistency —
not the count — is the strongest argument that the question has to be settled rather than
left.

## What the ruling has to move

Named here so the run that spends the ruling has no room to interpret it:

1. **Clause 4** of `tools/generate_dooryard_pickets.py`'s docstring and its code, rewritten
   to say the rule that won.
2. **`docs/LIBERTIES.md` L129**, which is stale in a way this measurement makes plain: it
   claims *"Eighteen garden fences"* on *"eighteen house lots"*, and the committed record
   holds **one**. It has been out of step since T-0516's withdrawal and nothing gates it.
   It must be brought into line with the rule actually in force — which is why this entry is
   not corrected here: the number to write into it depends on the ruling.
3. **The count before and after**, itemised against the tables above.
4. If the house rule wins, the note on every run and the `research_note` on the record,
   both of which currently argue the household reading in prose.

**Links:** T-0772 (this question) · T-0516 (the withdrawal that caused it) · T-0637
(`belongs_to`) · T-0514 (the address work a real `lives_at` count waits on) ·
`docs/LIBERTIES.md` L129 · `tools/generate_lot_line_fences.py` (the other answer).
