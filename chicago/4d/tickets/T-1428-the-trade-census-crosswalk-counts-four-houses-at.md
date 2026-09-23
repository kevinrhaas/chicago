---
id: T-1428
title: The trade-census crosswalk counts four houses at the scene date that the register says had not opened: read present_at_scene_date, not the gazetteer's built_at_scene_date — and teach the order book that a shortfall the evidence explains is not a quota
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-20
closed: 2026-09-20
pr: 1560
claimed_by: run 9/20/2026, 3:36:53 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-20T09:56:01.068Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35499767240
---

The trade-census crosswalk counts four houses at the scene date that the register says had not opened: read present_at_scene_date, not the gazetteer's built_at_scene_date — and teach the order book that a shortfall the evidence explains is not a quota.

**Found by T-1422, which stepped over it deliberately.** `tools/trade_census_1835.py`
classifies register rows with `built_at_scene_date` taken off the GAZETTEER, and that flag
means one thing only — `compile_gazetteer.py`: "a documented business stands in the 1835 town
unless a claim contradicts it", false *only* on a dissolution, removal or replacement notice.
It says nothing at all about a house whose OPENING is announced after the scene date. The
register carries that judgement in its own field, `present_at_scene_date: false` with
`exclusion: opening_announced_after_scene_date`, the compiled business records carry it, and
the crosswalk's own AUTHORED branch reads the right field two lines below the wrong one.

Four records diverge today, and the measurement is one loop:

| record | class | opened |
|---|---|---|
| `business_charles_hunt_high_school_for_young_ladies` | school | 17 August 1835 |
| `business_hiram_everts_high_school_for_young_gentlemen` | school | 10 August 1835 |
| `business_cromelien_brothers_co` | store | after the scene date |
| `business_william_f_lyon_wholesale_grocery_store` | store | after the scene date |

So the crosswalk prints `school 7 — town_matches_census` for a class that on 1 July 1835
holds **five**, and `store 67` where it holds 65. The December count was taken between
1 September and December and both schools had opened by then, so the census is not wrong and
neither is the register; only the join is.

**AND THIS IS WHY IT IS A TICKET AND NOT A LINE IN T-1422.** Fixing the field alone makes
the order book order **two reconstructed schools**: `business_buckets` cuts every bucket as
`max(0, census_count - town_records_at_scene_date)`, and school would go from 7−7 to 7−5. The
book would be commissioning an invention to fill a gap the evidence has already explained,
name by name and date by date — the exact move `does_not_follow` forbids: "where the town
holds fewer than the census counted, that gap is T-1007's to spend … and only where a source
NAMES the business." A shortfall a dated opening accounts for is not a quota, and the order
book has no word for that today. Both halves move together or neither does.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

1. `tools/trade_census_1835.py` reads the register's own `present_at_scene_date` for register
   rows, the same judgement its authored branch already reads, and a self-test fires on a
   record the register excludes for an opening after the scene date.
2. The order book does not order a reconstruction against a shortfall whose records are named
   and dated after the scene date. Whatever that mechanism is called, the school bucket's
   `to_reconstruct` is 0 and the row SAYS why rather than arriving at nought by luck.
3. Every figure the change moves — the crosswalk, `1835_town_model.md`, the order book, the
   spend — is rebuilt in the same commit, and the PR prints the before and after of each.
4. `./tools/check.sh` green and the smoke parts `smoke_budget.mjs --for-diff` names green.
