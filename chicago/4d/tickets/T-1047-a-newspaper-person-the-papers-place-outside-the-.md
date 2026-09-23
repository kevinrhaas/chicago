---
id: T-1047
title: A newspaper person the papers place OUTSIDE the town still enters the resident pool as a Chicago appearance: 132 households carry one today, and the consolidation has no place test at all
state: split
epic: META
requested_by: loop
seen: false
effort: L
legacy_id: null
parent: T-1040
opened: 2026-09-11
closed: 2026-09-11
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-12T01:59:05.930Z
claimed_run: null
---

A newspaper person the papers place OUTSIDE the town still enters the resident pool as a Chicago appearance: 132 households carry one today, and the consolidation has no place test at all.

Piece 2 of 2 of **T-1040 — Two readings the newspapers gazetteer gives a Chicago person belong to somebody else**. Piece 1 (T-1046) repaired the READINGS; this one owns the CARD.

## THE FINDING, MEASURED

`tools/consolidate_resident_evidence.py`'s `read_newspapers()` hands EVERY gazetteer person to the resident identity pool with evidence class `newspaper_1833_1835`, and reads nothing but the name and the first mention. It never looks at `associated_places`. So a man the papers place at Michigan City, Green Bay, Detroit, Hennepin or Juliet is offered to the clustering as a Chicago appearance, and merge rule M1 — identical normalised name — puts him on whatever Chicago card shares his name.

`hh_miller_samuel` is the worked example T-1040 was filed on. After T-1046 the card cites ONE press reading, `person_col_samuel_miller`, whose gazetteer record now correctly reads `occupations: [agent]`, `associated_places: [Michigan City]` — and the card's own note still says "A CONTEMPORARY CHICAGO PAPER OF 1833-1835 PRINTS THIS PERSON BY NAME IN THE TOWN", and the rung G1b is spent partly on it. The sentence is false of that reading. Strip it and the card is the 1832 muster and the 1833 tax list, which is what it should have rested on all along.

**The scale, measured on dev at the time of filing:** 193 of 2,665 gazetteer persons carry `associated_places` of which NONE resolves inside `in_town_places()`, and 132 of those reach a household card. So this is not a one-line guard — it moves evidence, and therefore rungs, across a ninth of the town.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- the place test is DERIVED, not a list of cities, and it resolves against the committed dataset the way `in_town_places()` already does (the bare town, every committed 1835 street, every committed structure name and aka), so a street renamed or a building added moves the test with it;
- IT MUST FIRST SURVIVE ITS OWN FALSE POSITIVES, which the filing measurement already found and did not resolve: `Fort Dearborn`, `Water Street`, `the Mansion House`, `Chicago, Illinois`, `a farm two miles from Chicago`, `the market square, Chicago` and `the corner of Water and Franklin streets, Chicago` are all INSIDE the town and all fail the naive test. A rule that refuses those is worse than no rule. Resolve the place vocabulary before applying the guard;
- an out-of-town appearance is RECORDED and not dropped — its own class, named, so the count is visible and a reader can argue with it, the way the letter-list class already is;
- every card that loses a press reading is re-derived in the same pass, and any rung that moves is stated with its count rather than left to be discovered;
- `bash tools/check.sh` is green.

## SIZE

Filed at L on the measurement above: the place-vocabulary resolution is its own demonstration before the guard is a second one. Whoever takes it should expect to `split` it again rather than force both into one run.
