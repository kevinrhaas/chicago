---
id: T-0830
title: The Dalton Data Bank prints two Cook County land purchases of June 1836 that the tract-sales sweep does not hold
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-11
pr: 1117
claimed_by: run 9/11/2026, 3:11:02 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-11T08:44:26.736Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34577554986
---

The Dalton Data Bank prints two Cook County land purchases of June 1836 that the tract-sales sweep does not hold.

**The finding, from T-0497's reading (2026-09-05).** `daltondatabank.net/Illinois_Page_2.html`, in its
ILLINOIS LAND SALES section and sourced to the Illinois Archives, prints under COOK COUNTY:

> George Dalton, price $1055, 6/25/1836; same date three other purchases at $687.50 and $343.75.
> George Dalton, price $875, 6/27/1836  Acreages not listed for this entry and three above.

Those dates fall inside the window `data/research/land_sales/` declares it read — the Illinois State
Archives' Public Domain Land Tract Sales database, through 1836 — and the surname is not in it (0 hits
across `data/research/land_sales/records/`). **The two registers do not contradict each other**: the
committed sweep is BY SECTION over seven townships around the town (T38N–T41N, R13E–R15E, third
principal meridian), and Cook County is far larger than those seven. So the likeliest reading is that
George Dalton bought outside the ring — which is worth knowing, because it says what the ring's edge
costs in coverage.

**The ask.** Query the Illinois State Archives database for the purchaser surname DALTON in Cook County
and settle which sections those five 1836 purchases sit in; if any falls inside the seven declared
townships, the sweep has a hole and `coverage.json` is wrong about it; if none does, record the negative
so the next reader does not do this again. A purchase is a TRANSACTION and never a residence — the
register's own Residence column is the only thing that speaks to where a purchaser lived, and it says
COOK, not Chicago. Nothing here mints or grades a resident.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- Each of the five 1836 Cook County purchases is placed in a section, or the query that could not place
  it is recorded with its result.
- `land_sales/coverage.json` states whether the seven-township declaration is complete for 1836 Cook
  County, in the terms it already uses.
- `tools/read_land_sales.py --check` and `tools/research_domains.py --check` green; no resident minted.

**Links:** T-0497 (the reading that found it) · `data/research/census_1840/records/dalton_index.json`
§ `dalton_index_land_sales_note` · `data/research/land_sales/` · T-0557, T-0675 (the sweep).
