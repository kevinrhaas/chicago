---
id: T-0358
title: The Thompson plat's block NUMBERING is uncommitted, so the corpus's only lot-and-block address cannot be placed
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-29
closed: 2026-08-29
pr: 571
claimed_by: run 8/29/2026, 4:28:55 PM CT
blocked_on: null
needs_bake: false
---

G. Spring's For-Sale notice ran in the *Chicago Democrat* six times between 1834-06-18 and
1834-11-19 and is the **only lot-and-block address in the whole newspaper corpus**:

> For Sale, **LOT No. 7, in block No. 16, one lot east of Haddock's Tavern, on Lake street**, in
> the town of Chicago. There is on said lot a large Dwelling-House and fine well. For terms
> enquire of G. SPRING.

(`chicago_democrat_1834_06_18` c006, `1834_09_03` c005, `1834_10_15` c006, `1834_11_19` c010 —
four legible settings; `1834_07_02` c053 cuts the tavern's name away and `1834_07_09` c024 sets
it "Maddock's".)

Three readings of the same claim have now recorded that it is the most placeable statement the
corpus makes and that placing it is somebody else's job — the June reading ("a claim a
reconstruction can put on the ground without a liberty"), the October one ("that is enough to
place a building on the plat AND to place Haddock's Tavern one lot west of it — but placing
either is a separate piece of work with the plat in front of it"), and T-0324, which established
that Haddock's Tavern **is** the Mansion House and then could not use the address either.

**Why it cannot be used.** Nothing in `data/` carries the Thompson plat's block NUMBERING.
`data/traces/vectors/thompson_lots.json` keys its nineteen committed blocks on their bounding
streets — `blk_south_water_dearborn`, `blk_lake_clark` and so on — and no committed source in
`data/sources/` numbers a block. So "block No. 16" resolves to nothing, and neither does the lot
number inside it: the module deals four lots per face by derivation, not by the plat's own
numbering, so "Lot No. 7" has no seat even once the block is found.

This is a dependency, not a nicety. Two documented buildings are waiting on it — the large
dwelling-house and well of Lot 7, and the Mansion House one lot west of it, whose committed
position is currently derived from Andreas's "on Lake near Dearborn" and carries an explicit
along-street uncertainty of at least a lot's width because of it. The *Chicago American* of
1835-07-11 (c002) prints more of the same kind ("Lots 11 and 19 in Block 16", "Lot 4 in Block
9[3]", "Block [8]4"), so the numbering unlocks a class of claims and not one address.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- A committed source establishes the Thompson plat's block numbering for at least the blocks this
  reconstruction holds, cited the way every other source record is, with its confidence stated.
  If no such source can be had, that is the answer and it is written down as one — the numbering
  is then `conjectural` or refused, never quietly inferred from a modern street guide.
- Block 16 is identified or explicitly refused. If identified, the lot numbering inside it is
  handled as its own question and not assumed to run the way the derived module deals lots.
- Nothing is renumbered on the strength of a modern plat reprint without saying so, and any
  invention lands in `docs/LIBERTIES.md`.

**Links:** T-0324 (found this and could not use it) · `data/traces/vectors/thompson_lots.json` ·
`data/structures/mansion_house.json` position note · `docs/RESEARCH/botsford_graves_1834.md`
