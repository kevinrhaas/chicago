---
id: T-1134
title: The ten one-letter town pairs the town's own lists print with no anchor on either card
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-1130
opened: 2026-09-14
closed: 2026-09-15
pr: 1353
claimed_by: run 9/15/2026, 1:42:28 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-15T13:25:58.675Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34937778308
---

The ten one-letter town pairs the town's own lists print with no anchor on either card.

Piece 3 of 3 of **T-1130 — Nineteen town cards stand one letter apart in the surname and identical in the forename, and the merge machinery has never been shown one of them**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

## The ten, named before the work, on the repository's own test

`tools/surname_one_letter_away.py` § `town_pairs` joins the cards one letter apart in the
surname and identical in the forename. T-1132 drew the split's line with
`consolidate_town_cards.anchored()` — the three pairs a card DOCUMENTS went first — and the
seventeen left divide on the mint that put them there, which is the card's own
`source_pass`. Where BOTH cards are `letter_list`, the post office alone prints the pair:
those are T-1133's. Where the town's own rolls print one of them — a `civic` card, minted
off the IRAD poll and tax lists — the pair is this ticket's. Intersected with the nineteen
T-1130 counted, that is exactly ten:

```
  Clark Anight / Clark Knight            A O T Bread / A O T Breed
  John W Eldredge / John W Eldridge      William Forsyth / William Forsythe
  Paul Kingston / Paul Kingstone         William Paine / William Payne
  Stephen M Salsbury / Stephen M. Salisbury
  Isaac Scarrett / Isaac Scarritt        E L Trall / E. L. Thrall
  Charles Wesencraft / Charles Wessencraft
```

(The same test also joins `John L Wilton / John Wilson`, a pair T-1130 did not count
because the surnames are two letters apart at the stem it folds. It is not taken here.)

## Acceptance

1. Every one of the ten carries a written ruling in `data/residents/card_merge_rulings.json`
   — `merge` under a named C-rule, or a refusal that says what keeps the two apart. None is
   left silent, and **none is ruled on the one-letter distance alone**: C9's load-bearing
   clause is a page that demonstrates the variation, and a pair with no such page is refused
   and says so.
2. The page question is ASKED OF THE CORPUS AND NOT OF THE READER'S MEMORY: every deposited
   text this project holds — the IRAD poll and tax rolls, the 1833-1835 newspaper run, the
   land register, Fergus 1839 and 1843, Norris 1844, the books, the church and old-settler
   lists — is searched for both spellings of each stem, and the ruling quotes what that
   search returned, including when it returned nothing.
3. A merge takes the survivor the existing rules pick and states what each card knew. The
   town's person count moves by exactly the number merged and the PR says the number.
4. `./tools/check.sh` green, the chain iterated to a fixed point behind any merge.

## What was done

All ten are ruled, and every ruling is made at a page rather than at a distance.

**Four fold.** `eldredge_john_w` onto `eldridge_john_w` and `salsbury_stephen_m` onto
`salisbury_stephen_m` and `scarritt_isaac` onto `scarrett_isaac` under **C9** — in each case
one publication is caught setting the two spellings for one man: the Chicago Democrat made
Eldredge/Eldridge secretary of a public meeting twice in the summer of 1835 and spelled him
both ways, and printed the county's commissioner slate of August 1834 on the 6th and again on
the 13th with `plen M. Salsburg`/`Stephen M. Balsbury` and `Scaredi`/`Isaac Scarret`.
`anight_clark` onto `knight_clark` under **C13**, a new rule for this project's OWN extraction
losing a letter: the entry sits inside the K run of the letter list of 30 June 1835, between
`Kirne, E. Capt.` and `King, Neheminh`, with an ampersand where the capital belongs, and
`Anight` is a string the whole deposited corpus does not hold.

**Six stay two, under D7**, also new — one letter, both stems alive, and no title that sets
both. Bread/Breed, Forsyth/Forsythe, Kingston/Kingstone, Paine/Payne, Trall/Thrall,
Wesencraft/Wessencraft. Acceptance 2 is met in each: the corpus was searched for both
spellings of every stem and each refusal prints what the search returned, including when it
returned nothing, and the argument FOR the merge is kept verbatim so that a page reopens it.

**The town moves by exactly the four merged** — 1,305 persons to **1,301**, 1,281 households
to 1,277 — and a house comes off Randolph Street with the Eldridge fold, because the two
directories had put the one physician there twice.

**Two machinery faults were found underneath and fixed with it.** A letter-list card folded
onto a civic survivor lost its source silently, because the mint writes `letter_list_returns`
where every other pass writes a `record_id` and the crosswalk had nothing for
`declared_anchors()` to key on; three earlier folds carry the fault invisibly and Clark Knight
is the first whose survivor cites no paper of its own. And a conflict the research ledgers
record against a folded card had stopped being counted, which the audit's own assertion caught
at 95 against 96.

**T-1140** is filed for the shape five of the six refusals share.

**Shipped by a later run.** The run that did this work committed it and died before opening a
PR. This run merged `dev` into it (T-1133 and T-1139 had landed in the meantime), re-derived
the whole chain to a fixed point behind the joined tree, restored the two redirect rows that
the first dev merge had dropped from `index.json` — `frazer_wm_h` and `vandine_john`, T-1133's
own folds, whose loss is what made the audit's conflict count read 95 against 96 — restated
L214 from 738 to 736, and corrected the release note's town count from 1,303 to 1,301.
(The published mirror needs no commit: `site/chicago/4d/` has been untracked since T-0938 —
`check.sh` runs `publish.sh` and then asks `check_published.mjs` whether what it produced
matches its source, and `deploy.yml` publishes before the Pages upload.)
