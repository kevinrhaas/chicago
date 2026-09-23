---
id: T-1161
title: The 1835 population model: how many people Chicago held on 1 July 1835, by sex, age band and division, derived from the November 1835 town census, the 1830 and 1840 schedules, the 1834 return and the growth curve — every figure sourced or labelled reconstructed
state: withdrawn
epic: META
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-09-16
closed: 2026-09-17
pr: null
claimed_by: null
blocked_on: folded into T-1293
needs_bake: false
closed_at: 2026-09-17T20:06:16.925Z
claimed_run: null
---

The owner, 2026-09-17: *"do your research on what the composition of the town should be based on
all of your existing research."* The reconstruction bands need a TARGET, and today the project
holds the pieces of one without the sum: the November 1835 town census (3,265 people, 398
dwellings — `andreas_1884_v1` p. 180, quoted in `data/town_census.json`), the 1840 IPUMS
composition (`data/research/census_1840/composition_1840.json`, T-0507: 4,834 people, 964
households, thirteen male and thirteen female age bands, 53 free coloured), the 1830 schedule
(`data/research/census_1830/`), the 1 April 1834 return (T-1153 and the continuation leaves),
Andreas's 1833 roster (~350 people), and the growth arithmetic the retired programme used
(`data/reconstruction/1835_inferred_household_programme.json`, ×9.3 from 1833).

**Deliverable** — `data/reconstruction/1835_population_model.json`, built by
`tools/build_population_model_1835.py --build|--check|--self-test`, holding:

1. **The 1 July 1835 headcount** as a bracket (low / point / high) interpolated between the last
   pre-scene count and the November census, with the interpolation rule stated (summer arrivals
   were heavy — the June 1835 land sales and the season's lake traffic — so the point is not the
   midpoint; say what it is and why, citing what the newspapers and Andreas say about the 1835
   season). Tier `reconstructed`, basis stated.
2. **Sex × age bands** for the town, by applying the 1840 band shares to the 1835 headcount and
   then correcting for what is KNOWN to differ (the garrison — male, 20–40; the 1835 building
   boom's labour — male, 20–30; fewer families than 1840). Every correction is a named row with a
   reason. Bands are the 1840 enumerator's bands so the numbers can be checked against the sheet.
3. **By division** — south / north / west / fort / outside-the-plat, using the roof programme's
   district split (370/135/150/10 + the fort) and the census's 8.2 per dwelling, corrected for
   where the hotels and boarding houses stand.
4. **Household count and size distribution** — from the 1840 distribution (mean 5.02, median 4,
   p99 21) shifted toward the 1835 dwelling ratio, with the rule that a dwelling held more than
   one household stated as a number.
5. **Free Black residents** — a bracket bounded above by 1840's 53 free coloured and below by
   the attested individuals; the Native and Métis population in and around the town on 1 July 1835 is
   modelled as its own rows — resident households, the traders' establishments, and families in
   town to trade or awaiting the annuity — bracketed from the treaty schedules, the registers
   and the traders' lists (T-1177 reads them), `review_required` on the row.
6. **The garrison** — companies of the 5th Infantry at Fort Dearborn on 1 July 1835 under
   Maj. John Greene (`docs/RESEARCH/fort_dearborn.md`): strength from the sources the dossier
   cites (Army returns if held; otherwise the company establishment, labelled reconstructed).
7. **The transient bracket** — people in town on 1 July who were not "residents": land-sale
   visitors, immigrants awaiting lots, vessel crews in port, harbour-works and canal-survey hands —
   as a separate bracket so the resident model is not inflated by it.

Every number carries `{ value, tier, basis, source_ids[] }` and the file is refused by
`--self-test` if any row lacks a basis or names a source not in `data/sources/`.

**Acceptance:**

- The model builds and re-derives; `--check` in `check.sh`; a `docs/RESEARCH/1835_population_model.md`
  page prints every table with its derivation in prose a historian could dispute line by line.
- The known profile (T-1160) is subtracted from the model in a **gap table** per bucket —
  this is the raw material of T-1166, which owns the final order book.
- Visible: the "The town's people" card (T-1160) gains a second column, "the town the
  sources imply", from this file, with the tier legend.

**Stop condition:** a reconstruction ticket can read, for any bucket (e.g. "women 20–29, South
Division"), how many the model wants, how many the known layer has, and what bounds the number.

**Links:** T-0507 · T-1153 · T-1160 · `docs/RESEARCH/household-composition-1840-calibration.md` ·
`docs/RESEARCH/residents_1835_inferred.md` § 2 (the retired arithmetic, to be superseded).
