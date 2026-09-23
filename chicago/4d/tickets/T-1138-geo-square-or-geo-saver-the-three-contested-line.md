---
id: T-1138
title: Geo. Square or Geo. Saver: the three contested lines of the 1 April 1834 return need the page image before any card on them can be ruled
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-15
closed: 2026-09-15
pr: 1351
claimed_by: run 9/15/2026, 6:01:35 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-15T12:18:38.431Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34960673645
---

Geo. Square or Geo. Saver: the three contested lines of the 1 April 1834 return need the
page image before any card on them can be ruled.

**Filed by T-1133**, which could rule six of its seven one-letter post-office pairs and had
to leave `square_geo` / `squire_george` undecided under U1 because one of the two printed
lines has two readings and nobody has arbitrated them.

## The three lines

`data/research/newspapers/extracted/chicago_democrat_1834_04_01.json` reads three
consecutive lines of the S run of the 1 April 1834 return as

```
  Benjamin Reed, the,
  Ira Raymore apy'
  3. Geo. Square t 3 first rate
```

— an advertisement's column bleeding across all three. The extraction of the impression of
16 April 1834 reads the SAME three positions as `Benjarnin Smith`, `Ira Saymoro` and
`Geo. Saver`, and its own note (T-0321) calls that impression "the best witness to the J-W
half of the 1 April 1834 list that the corpus holds", records that "the alphabetical
position is with this printing and against 1834-04-01's", and then declines to act:

> a minted name is not rewritten on a second transcription of equal rank — that is what
> the page images are for — so the three stand as minted and the disagreement is recorded
> here.

Three town cards rest on the losing side of that disagreement. 8 April 1834's own reading
of the block "is cut too far left to arbitrate".

## Acceptance

1. The page image of the 1 April 1834 return is read at those three lines, the way T-0424
   read the 1 January 1834 return — the reading committed with its crop, not asserted in
   prose — and each of the three is settled or explicitly left unreadable with the crop
   shown.
2. Every card the reading moves is moved in the same PR: a card minted on a name the image
   does not set is withdrawn under a named rule, not quietly renamed, and one minted on a
   name the image DOES set keeps it with the image cited.
3. The Square/Squire cluster in `data/residents/card_merge_rulings.json` stops being
   `undecided`: if the line reads SAVER the cluster dissolves, and if it reads SQUARE the
   pair is a two-return case and D6 rules it. Either way `referred_to: T-1138` goes.
4. `./tools/check.sh` green, the chain iterated to a fixed point behind whatever moved.

**Not this ticket:** the other 167 lines of the 1 April 1834 return. This is three lines
and the cards on them; a concordance of that whole return, in T-1010's shape, is a
different and larger piece of work and should be filed as one if it is wanted.
