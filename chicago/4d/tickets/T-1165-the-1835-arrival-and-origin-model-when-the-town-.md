---
id: T-1165
title: The 1835 arrival and origin model: when the town's people came, from where, and why — arrival-year cohorts, origin communities and reasons, from the attested biographies, the letter lists, the land sales and the season's press
state: withdrawn
epic: META
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: null
opened: 2026-09-16
closed: 2026-09-17
pr: null
claimed_by: null
blocked_on: folded into T-1293
needs_bake: false
closed_at: 2026-09-17T20:06:19.984Z
claimed_run: null
---

The owner asks for "arrival date and reason" on every person. The known layer records arrival
with a precision vocabulary (`day … not_later_than`) and no reason field; T-1160 adds the
reason vocabulary. This ticket derives the DISTRIBUTIONS reconstruction will draw from.

**Deliverable** — `data/reconstruction/1835_arrival_model.json`, built by
`tools/build_arrival_model_1835.py --build|--check|--self-test`:

1. **Arrival-year cohorts** — pre-1830 (the trading post and the fort), 1830–32 (plat and Black
   Hawk War), 1833 (harbour appropriation, the treaty, the first boom), 1834, spring–June 1835
   (the land sales) — as shares of the 1 July population, from the attested arrival dates in the
   layer plus the letter-list first appearances (a letter list dates a person's presence to a
   quarter), corrected by the growth curve of T-1161.
2. **Origin communities** — the pools of `1835_invented_name_pools.json` (yankee / New York,
   Ohio-Kentucky-southern, Irish, German, French-Canadian, free Black, British) with shares from
   the attested origins and the 1840 nativity where the sheet gives it; the Native, Métis and
   French-Canadian shares from the attested households and the treaty schedules, flagged
   `review_required` and read by T-1177; the free Black share from its bracket.
3. **Reasons for coming** — controlled vocabulary with shares BY COHORT AND TRADE: army posting;
   Indian Agency/treaty business; fur and Indian trade; forwarding/commission and lake trade;
   land speculation and the 1835 sales; canal survey and expectation; harbour works; building
   trades following the boom; keeping a tavern/store for the traffic; mission and church;
   following kin; farming the outskirts. Each share cites the biographies it counts.
4. **Family status on arrival** — came with family / sent for family later / single — by cohort
   and trade, from the biographies; feeds the household model.

**Acceptance:**

- Builds, re-derives, `--check` in `check.sh`; `docs/RESEARCH/1835_arrival_model.md` prints the
  tables with the biographies counted, by source id.
- The attested arrival/origin/reason facts are written to the persons who carry them at tier
  `attested`/`inferred` with their source (a spend, small, of what T-1157 will already have
  checked — no new source).
- Visible: the "The town's people" card shows arrival cohorts and origins, known vs implied.

**Stop condition:** T-1169 can fill every person's arrival, origin and reason from this
file with a seed and a basis.

**Links:** T-1160 · T-1161 · `data/research/old_settlers/` · `data/research/books/` ·
`1835_land_sales_by_tract.json`.
