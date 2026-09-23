---
id: T-0337
title: One man is two proprietors of Russell & Clift, and the gazetteer has no rule that can join them
state: done
epic: PAPERS
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-28
closed: 2026-08-29
pr: 543
claimed_by: run 8/29/2026, 9:51:31 AM CT
blocked_on: null
needs_bake: false
---
`business_russell_clift` in `data/research/newspapers/gazetteer.json` lists THREE
proprietors — `Aaron Russell`, `Benj. Clift` and `[H. H.] Clift` — and the last two are
the same man. The copartnership notice names him once and the deposit's OCR sets the
forename differently in every printing: `Hon). 1. Clift` (1834-09-03 page 3 column 3),
`nj. H. Clif` (1834-09-24 page 3 column 4), `HE Clint` (1834-11-12 page 3 column 4). The
1834-09-03 read supplied `Benj. [H.]` and the 1834-11-12 read supplied `[H. H.?]`, both
honestly bracketed, and the compiler unions the two strings.

`identity.json` is the declared merge rule for PERSONS and it cannot reach this: these
are `business.proprietors` strings on a business record, not gazetteer persons, so
nothing in the tool can join them and nothing in the gate can see that they need joining.
T-0304 records the same gap one level up, for firm names.

Found while closing T-0327, which resolved the December 1834 bookseller's heading to this
same firm.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- Either the forename is read off a printing that settles it, or the two strings are
  reduced to the one bracketed reading both witnesses support and the disagreement is
  recorded in the claim notes.
- Whatever the answer, the gate can tell: an assertion refuses a business whose
  `proprietors` carry two spellings of one surname with different forenames unless a
  declared rule says they are two people — the firm-side sibling of `identity.json`'s
  same-surname-different-initials rule.
- The assertion is proved to fire when broken, in `--self-test`.
