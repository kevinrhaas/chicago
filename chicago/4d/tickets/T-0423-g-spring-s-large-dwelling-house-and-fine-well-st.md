---
id: T-0423
title: G. Spring's large dwelling-house and fine well stands on lot 7 of block 16, where an anonymous roof stands now
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-29
closed: 2026-09-03
pr: 720
claimed_by: run 9/3/2026, 1:24:39 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-03T19:07:11.209Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33789733566
---

T-0358 committed the Thompson plat's block numbering for the South Water tier, which resolves the
only lot-and-block address in the whole newspaper corpus. G. Spring's For-Sale notice ran in the
*Chicago Democrat* six times between 1834-06-18 and 1834-11-19:

> For Sale, **LOT No. 7, in block No. 16, one lot east of Haddock's Tavern, on Lake street**, in
> the town of Chicago. There is on said lot a large **Dwelling-House and fine well**.

Block 16 is `blk_south_water_dearborn`, its Lake Street frontage is its south row, and lot 7 is the
third lot east of Dearborn — local **E +762.3 … +788.5, N −103.9 … −58.1**. Standing on it today is
`recon_1835_blk_south_water_dearborn_d3_03`, an anonymous reconstructed count-unit roof from the
665-roof programme, centred E +773.3, N −95.1. A documented dwelling-house is standing there under
an invented name.

**This is the visible half of T-0358.** It is also the first building in this town placed from a
LOT rather than from a street or a landmark, which is why the placement argument matters more than
the roof does.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- A visitor walking the north side of Lake Street east of Dearborn opens a card that names this
  house and cites the four legible printings, instead of an anonymous count-unit.
- The block-16 count is `inferred` and stays `inferred`; the placement inherits that grade and does
  not quietly rise above it. What is documented is the address; which reconstructed fabric stands
  under it is not.
- The anonymous roof that made way is accounted for the way the street-face adoptions account for
  theirs — the occupancy ledger balances, and nothing is dealt twice.
- The well is a documented feature of the lot. Either it is drawn, or the record says why not.
- Whether the house that stands there should also gain the Mansion House's one-lot correction
  (T-0358 § 7) is a SEPARATE question and must not ride along on this one.

**Links:** T-0358 · T-0324 · `docs/RESEARCH/thompson_block_numbering.md` §§ 6–7 ·
`data/traces/thompson_block_numbering.json` · `data/structures/mansion_house.json`
