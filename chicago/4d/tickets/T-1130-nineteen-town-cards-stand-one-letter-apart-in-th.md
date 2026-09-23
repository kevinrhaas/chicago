---
id: T-1130
title: Nineteen town cards stand one letter apart in the surname and identical in the forename, and the merge machinery has never been shown one of them
state: split
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-14
closed: 2026-09-14
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-15T01:46:40.834Z
claimed_run: null
---

**Found by T-0987 stretch 15, and found from the other side of the room.** The stretch
was reading Fergus 1843's initial-absent refusals — surname present in 1843, the printed
initial not — and asked what the exact-surname join cannot see. One of the sixteen
candidates it turned up was `Hiram Pearson`, refused because the volume prints
`Pearsons, Hiram, speculator, bds Tremont House`. The volume is not at fault: it sets
`Pearson` and `Pearsons` as two populated surnames and the printed volume's own OCR
agrees. **The town is.** It holds BOTH:

* `hh_pearsons_hiram` — Andreas's man, `attested`, came in the spring of 1833, treasurer
  of the city 1837-9 and an alderman from its first election, carried here as a
  speculator. The card's own note quotes Andreas's roster, and the roster prints
  **`Hiram Pearson, came in spring of 1833`**.
* `hh_pearson_hiram` — a civic-mint card off the 1833 poll list, `unplaced`,
  `occupation: none_recorded`, `present_on_scene_date: uncertain`.

One man, minted twice by two of this project's own passes, under the two spellings one
source sets.

## The class, measured rather than guessed

`tools/surname_one_letter_away.py` § `town_pairs` puts the one-letter test over the whole
resident layer and keeps only pairs whose FORENAME is identical:

```
  22  cards one letter apart in the surname, same forename
   3  already ruled by the merge machinery (Vanderbogart, Barre/Barry, Chark/Clark)
  19  never put to T-0839, T-0844, T-0993, T-1001 or T-1002 at all
```

The nineteen:

```
  Clark Anight / Clark Knight            Joseph Babeu / Joseph Babeue
  Reuben Beech / Reuben Bench            A O T Bread / A O T Breed
  John David / John Davis                John W Eldredge / John W Eldridge
  William Forsyth / William Forsythe     Wm. H. Fraser / Wm. H. Frazer
  Robert Hussey / Robert Hussy           Paul Kingston / Paul Kingstone
  Alonzo Murray / Alonzo Murry           William Paine / William Payne
  Hiram Pearson / Hiram Pearsons         Peter Pruyne / Peter Pryne
  Stephen M Salsbury / Stephen M. Salisbury
  Isaac Scarrett / Isaac Scarritt        E L Trall / E. L. Thrall
  John Vandine / John Vandino            Charles Wesencraft / Charles Wessencraft
```

**Why the machinery never saw them, and it is not an oversight.** `compatible()` in
`tools/consolidate_town_cards.py` buckets by the surname as ONE STRING, so two spellings
never meet — the same hole T-1002 found by hand for `beaubien-medard`, one bucket along.
And T-1001 ASKED the fold question and answered it NO: a blanket one-letter fold over the
land register's 427 purchaser spellings gathered a new rival for 200 of them and changed
24 named matches into losses. So the fold must stay off and each pair is a HAND ruling
under a named C-rule, exactly as T-1001's Kimberl(e)y pair and T-1002's three were.

## Acceptance

1. Every one of the nineteen carries a ruling in `data/residents/card_merge_rulings.json`
   — `merge` under a named C-rule, or a refusal that says what keeps the two apart. None
   is left silent, and none is ruled on the one-letter distance alone: C9's load-bearing
   clause is **a page that demonstrates the variation**, and a pair with no such page is
   refused and says so.
2. A merge takes the survivor the existing rules pick and states what each card knew, the
   way every cluster in that file already does. The town's person count moves by exactly
   the number merged and the PR says the number.
3. The directory crosswalks are re-derived afterwards: a merged card changes which
   residents the surname-plus-initial join reaches, and Fergus 1843's initial-absent pool
   should fall by one for Pearson alone.
4. `./tools/check.sh` green, the chain iterated to a fixed point behind the rulings.

**Not a fold.** Nothing here widens `compatible()`, and nothing here reopens T-1001's
measurement. Nineteen hand rulings, each with its own page or its own refusal.

**SIZE.** Nineteen pairs is more than one run's demonstrations. Split it before claiming,
or work it in stretches and say which pairs a run took.
