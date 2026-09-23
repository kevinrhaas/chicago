---
id: T-1041
title: A house's agency reaches no card: the walkthrough shows trades and proprietors and has no place for a relation
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-11
closed: 2026-09-13
pr: 1299
claimed_by: run 9/13/2026, 7:49:06 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-14T01:42:27.410Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34793545676
---

A house's agency reaches no card: the walkthrough shows trades and proprietors and has no place for a relation.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Found by T-0410**, which built the relation and stopped at the data.

`identity.json`'s `agencies` now records that a house or a man HELD an agency for a named
principal, and the compiler writes `agencies_held` onto the holder's own record in
`gazetteer.json`. Two houses carry one today: `business_hubbard_co` and
`person_e_k_hubbard`, with `business_jones_king_co` carrying an `agencies_refused` line.

Nothing reads any of it. The walkthrough's card shows a trade, goods, proprietors, a
street and a placement, because those are the fields a business record had when the card
was written. A relation is none of those, which is the whole reason T-0410 exists — and a
reader of the town meets Hubbard & Co. today with no way to learn that it insured property
against loss by fire for the Howard of New-York for eleven months, nor that the agency
left it for one man three weeks before the scene date.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- A card for a house or a person that holds an agency says so, naming the principal and
  the window, and citing the printings the holding rests on exactly as every other line on
  that card cites its source.
- A REFUSED holding is legible too, or is deliberately not shown with the reason recorded
  here — the refusal is a judgement about that house and the card is where a reader would
  look for it.
- Nothing on the card implies the holder traded in the principal's line, held a roof for
  it, or was a partner in any house he signed for. A holding adds a line and nothing else,
  and the card must not be the place that quietly upgrades it.
- The smoke pins the rendered text, as it does for every other claim that carries one.

Links: T-0410 (the relation), T-0411 (the same shape, for a paper and its office).
