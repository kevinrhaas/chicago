---
id: T-1335
title: Spend the kin the church registers, the papers' family columns and the completed resident enrichments state — the 166 units T-1320's book pass was never scoped for, plus the two book relatives it left unruled: ties written onto held cards, nobody minted
state: open
epic: META
requested_by: steward
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-18
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: null
claimed_run: null
---

Spend the kin the church registers, the papers' family columns and the completed resident enrichments state — the 166 units T-1320's book pass was never scoped for, plus the two book relatives it left unruled: ties written onto held cards, nobody minted.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

1. Every one of the 168 units that deferred to T-1320 on this ticket's opening day has a
   ruling of its own: spent onto a card, or refused with the reason named, or handed on to
   a ticket that is OPEN. Measured, not asserted: `measure_research_spend.py --ledger-build`
   reports zero `unresolved ticket ... is missing or not open` for T-1335.
2. The three domains T-1320 never covered are read on their own terms, not by running the
   book pass over them. `the_register_entry_names_kin` (church, 147), `the_family_column_
   names_kin` (newspapers, 12) and `the_enrichment_names_kin_no_field_carries` (residents, 7)
   each name a different KIND of statement, and their rules' own prose still describes the
   T-1170 field they were written for.
3. **No person is minted by this pass, and no household gains a member.** A marriage names
   a spouse and creates nobody. A tie is written onto cards this town already holds, on
   both ends, or it is not written. This is the standing constraint T-1312 and T-1320 both
   worked under and it is not relaxed here.
4. A relative who is nobody here is RULED, the way T-1312 and T-1320 ruled theirs, and is
   not minted into the layer to give the tie somewhere to land.
5. The two book units T-1320's own pass left unruled — `bk_fer_024` (Min-ne-mung's sister,
   wife of Billy Caldwell) and `bk_mose1_012` — are ruled here rather than left as the
   residue of a closed ticket.


## WHY THIS TICKET EXISTS: A HANDOFF POINTED AT A TICKET THAT DID NOT COVER IT

`handed_to_the_family_pass` was T-1170's. When T-1170's split closed (T-1312/T-1313/T-1314),
the line was retargeted to T-1320 — in ALL FOUR domain `spend_rulings.json` files, when
T-1320's title scopes it to the BOOK corpus alone: "the ties whose relative is ALSO a held
resident ... and the book-corpus relatives who are nobody here". That retarget is mine and
the error is mine.

T-1320's pass (`spend_book_kin.py`, PR #1464) then did its book job and the ticket closed,
and 168 units read as deferring to spent work:

```
  church        147   the register's own cells.role — the child, father, mother,
                      groom, bride, spouse or decedent of a dated sacrament
  newspapers     12   the paper's MARRIED and DIED columns
  residents       7   corroborated_enrichment naming a kinship no field carries
  books           2   in T-1320's scope, and its pass did not rule them
```

Nothing dangled while T-1320 was open, which is why no gate complained until the close.
That is the same shape as the T-1237 rule — a unit cannot defer to spent work — reached
from the other side: not a split parent going quiet, but a handoff aimed at a ticket whose
scope was narrower than the line that pointed at it.
