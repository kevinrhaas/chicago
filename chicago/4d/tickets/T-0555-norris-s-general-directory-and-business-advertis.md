---
id: T-0555
title: Norris's General Directory and Business Advertiser of Chicago for 1844 (HathiTrust chi.56111136): parse residents, businesses and occupations, date-flag them as later evidence, and use them to validate and enrich the 1835 residences and businesses
state: split
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-03
closed: 2026-09-03
pr: null
claimed_by: run 9/3/2026, 10:45:06 AM CT
blocked_on: null
needs_bake: false
---

Norris's General Directory and Business Advertiser of Chicago for 1844 (HathiTrust chi.56111136): parse residents, businesses and occupations, date-flag them as later evidence, and use them to validate and enrich the 1835 residences and businesses.

**The owner's ask, verbatim (2026-09-03):** "Also the same with this business directory
https://babel.hathitrust.org/cgi/pt?id=chi.56111136&seq=15 for residents and businesses I know this directory is
later but parse what you can from it and include the businesses with date appropriate so it can be used to
improve the business's reference and validate enhance confirm residences and business".

**What the volume is.** HathiTrust `chi.56111136` (University of Chicago copy, full view, US public domain) is
J. W. Norris, *General Directory and Business Advertiser of the City of Chicago, for the Year 1844: together with a
Historical Sketch and Statistical Account, to the Present Time* (Chicago, 1844; the HathiTrust record dates the
copy 1933, a reprint). Three things are in it and all three are wanted: (1) the **directory** — every resident
listed with occupation and street or "boards at"; (2) the **business advertiser** — the advertisements, which are
businesses with proprietors, trades, addresses and often "established 18xx"; (3) the **historical sketch and
statistical account** — a founding-era narrative written nine years after the scene, with dates, early settlers,
buildings and institutions, which is town findings.

**How to read it.** HathiTrust serves page text: try `…/cgi/pt?id=chi.56111136&seq=N&view=plaintext` (and the
`ssd` reader) page by page from the owner's `seq=15`; if the text view is refused, the page images at
`/cgi/imgsrv/image?id=chi.56111136&seq=N&size=full` and `tesseract` (installed on the runner) are the fallback.
Be gentle — one page at a time, cache every page under `data/research/directory_1844/text/`, never re-fetch.
Do not commit the images.

**What to produce.** `data/research/directory_1844/` under the T-0492 shape: `entries.json` (one record per
directory line: name as printed, normalized, occupation, business, street/address, boards-at, page, line),
`businesses.json` (from the advertiser and the directory: firm, proprietors, trade, address, any "established"
year, page), `claims.json` (town findings from the sketch and statistics, `town_finding: true`, verbatim quote,
page), a source record `norris_directory_1844` with `describes_date: 1844`, and a README saying what was read and
what was not.

**Then use it as the owner said.** Everything is 1844 and flagged so. (a) VALIDATE: every 1835 resident whose
name and trade match an 1844 entry gets the entry as continuity evidence on the record. (b) ENHANCE: an attested
1835 resident with no trade, street or business gets them from 1844 where the sketch or the match makes the
carry-back arguable, stated as 1844 evidence, never silently as 1835 fact. (c) BUSINESSES: every 1844 business
whose founding the sketch, the ad or the 1843 Fergus directory (`data/sources/fergus_chicago_directory_1843.json`)
puts at or before 1835 is written to the businesses layer with `known_by` / `established` dates, so the 1835
business references improve. Under the ratified ladder an 1844 listing alone never makes an 1835 resident.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)
- Every page of the directory and the advertiser read (or the pages not read named in the README with why).
- `entries.json`, `businesses.json`, `claims.json`, the source record and the README present and validating.
- A crosswalk file naming every 1835 resident and business matched, with the match reason and what was carried.
- Counts in the PR: entries read, businesses read, residents validated, residents enriched, businesses added
  or dated.

**Effort.** An 1844 Chicago directory is thousands of lines: read the sketch and the advertiser first (they carry
the dated statements), then split the alphabet (`ticket.mjs split`) so the pieces keep this place in the queue.

**Links:** T-0492 (research-domain shape) · `data/sources/fergus_chicago_directory_1843.json` and
`resident_research_fergus_directory_1843.json` (the 1843 directory the repo already cites) · T-0508 (the
directory ticket in wave 2, which this feeds) · T-0513 (consolidation — waits on this).

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
