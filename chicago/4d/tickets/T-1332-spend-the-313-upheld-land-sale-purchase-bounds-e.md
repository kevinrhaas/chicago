---
id: T-1332
title: Spend the 313 upheld land-sale purchase bounds: each tract entered on or before 1 July 1835 by a purchaser the crosswalk joined to a card this town holds, written onto that card as a dated appearance and never as a residence
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-1319
opened: 2026-09-18
closed: 2026-09-18
pr: 1472
claimed_by: run 9/18/2026, 2:41:33 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-18T20:29:21.865Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35386917968
---

Spend the 313 upheld land-sale purchase bounds: each tract entered on or before 1 July 1835 by a purchaser the crosswalk joined to a card this town holds, written onto that card as a dated appearance and never as a residence.

Piece 1 of 2 of **T-1319 — Spend the land-sale and enrichment units: the entered tracts whose purchaser join the adjudication upheld, and the corroborated_enrichment rows naming an arrival or origin no structured field carries**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (stated before working — one demonstration, never weakened to pass)

ONE DEMONSTRATION: the research-spend ledger closes all 313 of these units as `asserted`
off the cards, and the derived ruling register rules none of them. Before: `land_sales`
read `asserted 0 / unresolved 353`, 313 of them deferred to this ticket by name. After:
`asserted 313 / unresolved 40`, and T-1332 is gone from the ledger's owner table. That is
the whole of it, and it cannot be reached by writing prose, by moving a grade or by
declaring an assertion — `tools/research_spend_ledger.py` reads the CARD, and its
`ruling_coverage_faults` fails a ruling on a unit something else already closed, so the
register HAS to stop ruling them at the same commit.

AND FOUR THINGS IT MAY NOT DO TO GET THERE, each held by a gate rather than by this note:

  1. NOT ONE ROW CLAIMS A CHICAGO PRESENCE. `here_by` is null on all 313. A purchase is a
     transaction; the register's only residence column reads a county, a state or UNKNOWN,
     never a town. The eighteen rows the register states COOK for carry
     `bound_kind: "residence_in_cook"` and still no `here_by`, because Chicago is in Cook
     County and Cook County is not Chicago.
  2. NO ROW IS `attested`. Every identity here is the crosswalk's name adjudication and
     none of them is an identification a source makes. `date_confidence` is `documented`
     because the register prints the date; `confidence` is `inferred` because the subject
     rests on a name.
  3. NO SECOND SHAPE FOR ONE FACT. The bounds go into `persons[].dated_bounds[]`, the block
     T-1326 introduced — so the block gains a second owner, and `tools/dated_bounds_block.py`
     is the rule that stops the two passes wiping each other, with both `--check`s true at
     once in either run order.
  4. NO GRADE MOVES, NO IDENTITY REOPENS, NO PERSON IS MINTED, AND NO OTHER KEY IS TOUCHED.
     `--self-test` diffs a card through the applier and asserts the changed key set is
     `{"dated_bounds"}` alone.

**READ THIS BEFORE CLAIMING (T-1330, 2026-09-18).** A purchase bound is a DATED APPEARANCE,
and `persons[].dated_bounds[]` is the structured block a dated appearance belongs in. That
block is being introduced by **T-1326** (`tools/spend_civic_roll_bounds.py`, the town's own
rolls) and it is not on `dev` yet — check before you start:

    grep -rn 'dated_bounds' chicago/4d/tools/ | head

If it is there, write into it and do not invent a second shape for the same fact. If it is
not, T-1326 is still in flight and this ticket is not workable yet — say so and take the next
row rather than building a rival block, because two blocks carrying one fact is the
duplication this loop exists to avoid. The ticket was carried as `blocked-tech` for about an
hour on the day it was minted and then reopened, because a blocked ticket is not an open
owner and these 313 units have to defer to one (see below).

**The units.** `data/research/land_sales/spend_rulings.json`, rule
`the_purchase_bounds_a_held_residents_presence`, 313 rows — tracts entered on or before
1 July 1835 by a purchaser the crosswalk's T-0700 / T-0850 adjudication UPHELD against a card
this town holds. The rule's `ticket` was repointed from the split parent T-1319 to this
ticket by T-1330, because the parent stopped being `split_live` the moment its other child
closed and 313 units would otherwise have deferred to spent work (T-1237).

**The standing rule this whole domain was read under:** a purchase is a TRANSACTION and not a
RESIDENCE. The register's Residence column reads COOK, ILLINOIS, another county or UNKNOWN —
a county, a state, or nothing, and never a town. A row can bound a presence. It can never
assert one, and it may not move a grade or reopen an identity the crosswalk has ruled.


**RENUMBERED FROM T-1329 ON THE DAY IT WAS MINTED (2026-09-18).** Another branch split
T-1318 at the same hour and minted its own T-1329 for the 1830 schedule lines, the church
register sponsorships and the press notices. Two branches splitting at once each take the
local max and each get it right alone and wrong together — the same collision
`data/research/spend_rulings.json` records against T-1312/T-1313. That ticket merged first,
so this one moved; `tools/spend_land_sales_rulings.py` points the 313 rows here.
