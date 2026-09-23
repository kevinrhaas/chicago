---
id: T-1028
title: The 619 town-lot sales the by-section sweep cannot see: Cook County's register describes a lot and block with no section, so 466 sales of 1836 — the town's own ground — are outside the land_sales deposit
state: split
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-11
closed: 2026-09-11
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-11T10:43:52.177Z
claimed_run: null
---

The 619 town-lot sales the by-section sweep cannot see: Cook County's register describes a lot and block with no section, so 466 sales of 1836 — the town's own ground — are outside the land_sales deposit.

**The finding, from T-0830 (2026-09-11).** `harvest_land_sales.py --sweep` asks the
Archives' search for a SECTION, thirty-six queries per township, each walked to its end.
A row the register gives no section answers no section query, ever — and the register
gives no section to a town lot: the tract is written `L2BL46CHIOT`, a lot and a block and
a town code, with Section, Township, Range and Meridian all empty.

T-0830 measured the size of that blind spot with the query that can see it —
`harvest_land_sales.py --county-list COOK`, county alone, walked to the end of the
results through the same More cursor. 83 pages, 12,444 rows, **2,785 dated on or before
31 December 1836**, committed as
`data/research/land_sales/text/isa_land_tract_sales_cook_county_list_through_1836.tsv`
and measured in `coverage.json § completeness_probe`:

| | rows | in the deposit |
|---|---|---|
| inside the seven declared townships | 953 | **953** — read whole, nothing missing |
| sectioned, outside the seven | 1,213 | 0 — outside what the deposits declare |
| **no section at all** | **619** | **0** |

**466 of the 619 are dated 1836**, 133 are 1830, 16 are 1831, and four carry a year the
register itself mis-prints (1000 ×3, 1483 ×1), carried unsmoothed. 618 end in a town code
— `CHIOT` 336, `CHIOTV` 107, `CHIV` 93, `CHI` 62, `CHIOTVO` 20 — and one is a bare
`L6BL17`. 255 distinct purchaser spellings. Every one of the five George Dalton
purchases T-0830 went looking for is among them, as a canal sale (`CN`) of June 1836.

**Why it is worth reading.** These are the town's OWN lots changing hands in the year the
land rush reached the plat, and the domain currently holds four sales for the whole of
1836. It is also the largest single block of unread ground this project knows the size of.

**Ask.** Harvest the 619 into the domain the way the sweep's rows are harvested —
detail page per row, appended as a new deposit under `DEPOSITS` so no committed id
renumbers — and make the parser, the tract resolver and the crosswalk honest about a row
with no section. Budget it before claiming: 619 detail pages at the reader's ~20/minute
pace is about half an hour of fetching ALONE, before the parser and the ground join, so
this is more than one run and should be `split` — the harvest and its deposit first, the
tract/ground join second.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- The 619 rows are read at their detail pages and committed as their own deposit, with
  record ids appended and nothing already cited by `data/structures/*.json` renumbered.
- `tract()` either resolves a lot-and-block-in-a-named-town or REFUSES it with a stated
  reason; it never guesses which plat a town code names, and it never invents a section.
- `coverage.json § completeness_probe` re-derives to `complete_for_1836_cook_county: true`,
  or says precisely what is still outside it.
- No resident is minted or regraded by the harvest. A purchase is a transaction.
- `tools/read_land_sales.py --check`, `tools/resolve_land_tracts.py --check` and
  `tools/research_domains.py --check` green.

**Links:** T-0830 (the measurement, and the five Dalton purchases that led to it) ·
T-0497 (the Dalton Data Bank reading) · T-0557, T-0675, T-0676 (the by-section sweep) ·
`data/research/land_sales/README.md` § the sweep is complete for every section it declares.
