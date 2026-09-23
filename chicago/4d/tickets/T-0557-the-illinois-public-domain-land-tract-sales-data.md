---
id: T-0557
title: The Illinois Public Domain Land Tract Sales database (Illinois State Archives): pull every federal land sale in the townships around Chicago through 1836 and crosswalk purchasers to residents, households and structures
state: done
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-03
closed: 2026-09-03
pr: 738
claimed_by: run 9/3/2026, 4:36:40 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-03T22:43:42.025Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33807954375
---

The Illinois Public Domain Land Tract Sales database (Illinois State Archives): pull every federal land sale in the townships around Chicago through 1836 and crosswalk purchasers to residents, households and structures.

**The owner's ask, verbatim (2026-09-03):** "And lastly add the land sales data ticket based on this , again to
improve all the data we have https://apps.ilsos.gov/isa/landSalesSearch.do".

**What the database is.** The Illinois State Archives' *Illinois Public Domain Land Tract Sales* database: every
sale of federal land in Illinois from the land offices, searchable by purchaser name and by legal description
(section, township, range, meridian) and county. Each entry carries the purchaser as written, the sale type and
date, acres, price, the tract (section or part, township, range, meridian), the county, the land-office volume
and page — and, where the register wrote it, **the purchaser's stated residence**, which for a sale of 1835 is a
contemporary statement of where the buyer lived. The Chicago land office opened in 1835 and its first years are
the great Chicago land sales; the sections granted to the Illinois and Michigan Canal were sold by the canal
commissioners and are NOT here, so their absence is not a hole in the reading.

**Scope.** Third Principal Meridian. The town first: T39N R14E (Chicago), then T40N R14E (the North Side and
north), then the ring — T39N R13E, T38N R14E, T38N R15E, T40N R13E, T41N R14E — every sale dated through
31 December 1836, and every sale to a purchaser whose stated residence is Chicago or Cook County whatever the
tract. The session that filed this could not reach the site (a WAF error to its proxy); the runner may, and if
the search form refuses automation, page through results by hand-shaped queries with polite pacing, or find the
Archives' downloadable dataset of the same records and say which you used.

**What to produce.** `data/research/land_sales/` under the T-0492 shape: `entries.json` with the database's
fields VERBATIM per sale (purchaser as written, normalized, residence as written, date, acres, price, section /
part, township, range, meridian, county, volume, page) plus a `tract` the map can use (the section and aliquot
part, so a quarter-quarter resolves to a footprint against the plat and the T-0444 sheet); a source record with
`describes_date` per entry; a README with counts by township and year.

**Then use it as the owner said — to improve all the data.** (a) RESIDENTS: a purchaser whose stated residence is
Chicago in 1835 is contemporary evidence of presence; crosswalk every purchaser name to the residents layer and
the voter lists and write the evidence on the record, graded under the ratified ladder (a purchase alone, with no
residence stated, is a land record, not a resident). (b) HOUSEHOLDS AND STRUCTURES: a structure standing on a
tract whose 1835 purchaser is known gets that owner as `land_owner` evidence with the sale date; a purchaser who
bought and is otherwise attested in town is a household with a place. (c) BUSINESSES: sales to firms, and to men
whose trade the town knows, date and place those businesses. (d) TOWN FINDINGS: the pattern of sales itself —
which sections were entered when, by whom, at what price — is the land rush the newspapers describe, and goes in
`claims.json`.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)
- Every sale in T39N R14E and T40N R14E through 1836 in `entries.json`, fields verbatim, none summarized; the
  ring townships either read or named as not yet read in the README.
- The crosswalk file: every purchaser matched to a resident, household, structure or business, with the match
  reason and the grade; and the ones not matched, listed.
- Counts in the PR: sales read, purchasers, matched residents, structures given an owner, businesses dated.

**Effort.** Two townships to the end of 1836 is one run; the ring is another. Split by township
(`ticket.mjs split`) so the pieces keep this place in the queue.

**Links:** T-0444 (the plat sheet and the owner's ruling on it) · T-0492 (shape) · T-0493 (voter lists) ·
T-0505 (the 1840 crosswalk, same matching discipline) · T-0513 (consolidation — waits on this) · the structures
layer's `land_owner` / provenance fields.

**This is overall expansion, not a residents-only pass.** The owner's words, 2026-09-03: "this is overall
expansion because while you are parsing for residents and household people you might as well improve the
business and structure and occupation and other surrounding data and attributes that will help us render the
most complete reconstruction possible of chicago 1835." So every person this source yields is read WITH the
trade, the business, the street or lot, the building and the year it carries — and each of those goes to the
layer it belongs to (residents, households, `businesses`, structures, `claims.json` town findings with
`town_finding: true`, verbatim quote and locator), under the research-domain shape T-0492 fixed. Later
evidence stays date-flagged (`describes_date`), and under the ratified ladder (quoted in T-0513) a later
source alone never makes an 1835 resident — it corroborates, enriches and dates. No IPUMS serial is minted
here; nothing here regrades a person without the ladder's test being stated on the record.
