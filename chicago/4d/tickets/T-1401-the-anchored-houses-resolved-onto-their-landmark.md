---
id: T-1401
title: The anchored houses resolved onto their landmark, and the register's double-printed partners folded: every anchored location carries the id of the structure or firm it stands against, and a partner the register styles two ways is one partner on the firm's own card
state: done
epic: META
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1182
opened: 2026-09-19
closed: 2026-09-19
pr: 1528
claimed_by: run 9/19/2026, 11:07:55 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-19T17:22:13.998Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35453633099
---

The anchored houses resolved onto their landmark, and the register's double-printed partners folded: every anchored location carries the id of the structure or firm it stands against, and a partner the register styles two ways is one partner on the firm's own card.

Piece 1 of 5 of **T-1182 — Audit every attested and inferred business against the research: proprietors, partners, dates, primary and secondary premises, the Dec 1835 State census classes and the August 1835 American count — and raise an inferred business for every in-window trade that has none**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

1. Every `anchored` location in `data/businesses/` carries an `anchor` block — `kind`
   (`structure` | `business` | `corner`), the `id` it resolves to, a `title` a card can
   print, and for a corner the two street ids — DERIVED in `tools/compile_businesses.py`
   from the register's own `action_target`, never by parsing `limit_reason`'s sentence.
   All 26 resolve: 15 against a committed structure, 7 against another business in this
   layer, 4 against a crossing of two platted streets.
2. A structure id the town does not hold, or a business id this layer does not carry, is
   a REFUSAL in the compiler, not a silent null — the same discipline every other id in
   this layer is held to.
3. `structure_id` stays null on an anchored location. The anchor is the landmark, not
   the house's own roof, and nothing downstream may read it as premises.
4. The building card says which houses stand against it: `firmCrosswalk().byStructure`
   carries the anchored firms as well as the premises ones, each marked with its
   relation, and the Use row prints them as a second group in its own words. The
   Tremont House names its four.
5. The twelve person-firm pairs the register prints under two styles are ONE entry on
   the record, with the styles it was printed under kept on `also_printed_as[]` — the
   typography is evidence and is not deleted. Thirteen printings fold onto twelve pairs
   (Giles Spring was printed three ways), `named_people` falls 209 -> 196 and linked
   157 -> 144, and every piece of prose that quotes those counts moves with them. The
   directory's search still answers a query typed off the paper: "James H. Collins" is
   on no record's `name` any more and must still find Collins & Caton.
6. `compile_businesses.py --check` re-derives both and refuses a hand-edit; `check.sh`
   runs it, and the smoke parts that cover the two cards are green.

