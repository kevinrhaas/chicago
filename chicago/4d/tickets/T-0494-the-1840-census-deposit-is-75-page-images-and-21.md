---
id: T-0494
title: The 1840 census deposit is 75 page images and 210 heads on seven printed pages are the only names read from it: images 1-25
state: split
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-02
closed: 2026-09-03
pr: 684
claimed_by: run 9/3/2026, 2:59:15 AM CT
blocked_on: null
needs_bake: false
---

**The owner's ask, 2026-09-03, recorded verbatim:** "create tickets to do more resident research
transcription and analysis or extract find public sources or APIs to read and find data from the
following reference materials, you should see them all in GitHub — Voter Roll; Census 1830 and 1840;
Fergus; Swift walker; Hh porter. And then create a final ticket that does a review and consolidation of
that research." 

**The finding.** `chicago/reference/census1840/` holds **75 FamilySearch page images** of the 1840
federal census of Chicago (`33S7-9YYJ-*.jpg`, `33SQ-GYYJ-*.jpg`, `33S7-9YYN-*.jpg`, `33SQ-GYYN-*.jpg`;
`33S7-9YYJ-9WF` is committed twice). Names have been read from only seven printed pages, 229–235: PR
#670 recovered **210 named household heads** with IPUMS serials from the owner's v4 workbook into
`data/census/1840/household_heads.csv.gz` (index in `data/census/1840/index.json`, source images named
per row). The IPUMS extract holds **964** Chicago households, so **754 remain unnamed while every page
image carries the names**. The owner's ruling on the missing v3/v4 workbooks, 2026-09-03, verbatim:
"They are lost; rebuild" — so the page images are the record, and #670's 210 rows are the calibration
set this reading must reproduce before it extends.

**The ask — this ticket reads images 1-25** of the 75, taken in the sorted filename order
`ls chicago/reference/census1840/*.jpg | sort` (state the exact list in coverage; skip the duplicate
`9WF (1)` copy and say so).

1. For each image, `data/research/census_1840/pages/<familysearch_id>.json`: the printed page number
   read off the sheet (or `unknown`), whether it is a LEFT sheet (names + free-white age bands) or a
   RIGHT sheet (continuation columns), and one record per line: `line`, `as_read` (the head's name as
   written, with `[?]` for an unread letter — an unread letter is a POSITION, not an absence, T-0397),
   `normalized`, `name_confidence` (`high | medium | low`), the 13 free-white male and 13 free-white
   female age-band cells, free coloured and slave cells, the industry columns (agriculture, commerce,
   manufactures/trades, navigation of the ocean, canals/lakes/rivers, learned professions), pensioners,
   and the schools/illiteracy columns where the sheet carries them; blank or illegible lines recorded
   as `illegible`, never skipped; `reading: scan_verified`.
2. `data/research/census_1840/coverage.json` gains this group's image ids.
3. Where a page is one of the seven #670 already read (229–235), cross-check line by line and state
   the agreement count against its 210 rows — disagreements listed, none silently overwritten.
4. Keep enumeration order: the line sequence is the only spatial signal the 1840 census carries
   (neighbours were visited in walking order), and the later placement sweep will want it.
5. Do NOT attach IPUMS serials here — **T-0504** does that by the age-band fingerprint over all three
   groups; do not commit images or crops; the Read tool renders JPEGs directly.

The 1840 census is LATER EVIDENCE: nothing read here mints a 1835 resident (the owner's ratified ladder:
"1839/1840 alone is never a 1835 resident"). This ticket produces the named record; **T-0505**
crosswalks it.

**The pattern this ticket follows** is the newspaper pipeline's (`data/research/newspapers/README.md`,
`tools/compile_gazetteer.py`), generalised by **T-0492** into `tools/research_domains.py` — read both
first, and if T-0492 is still open, WORK THAT INSTEAD: the deposit stays read-only; derived TEXT is
committed (never scans or renders); claims are hand-authored against the CLOSED kind vocabulary with a
REQUIRED `reading` (`transcription_mediated` | `scan_verified`), a verbatim `quote` the gate rebuilds
character for character, a `normalized` sibling, and a `locator`; `coverage.json` declares exactly what
was read so a hole fails and a swept-and-empty range is evidence; a `crosswalk.json` in the
`identity.json` shape declares every merge AND every refusal — a surname match is a clue, not an
identity, and is recorded as a refusal with its rule; every source cited gets a `data/sources/<id>.json`
with `tier`, `verified`, `what_it_supplies` and `what_it_does_not_supply`. **Town findings** — any
business, building, street, infrastructure, landscape or appearance fact the source yields — go in the
SAME claims file with `town_finding: true`, because the owner asked: "While you are parsing these
sources, if you have items that will help fill out any other part of the town, businesses, structures,
landscape, streets, appearance etc, please keep and include that in the research you do and we will use
that later for the structures when needed." Negative searches are recorded (source, query, date,
result). This ticket does NOT mint or regrade residents — **T-0514** and **T-0515** do that from the
consolidation. No model identifiers in any artifact; no hand edits under `site/` or `vendor/`.

**Runner notes (2026-09-03):** the improve runner's custom lane now installs `pdftotext` and
`pdftoppm` (poppler-utils), `tesseract`, `openpyxl` and `pypdf` before the run (polecat-platform
`steward-improve.yml`, on the owner's instruction the same day), and the gate installs `openpyxl` and
`pypdf` beside `jsonschema` and `pyproj`. Check with `command -v pdftotext tesseract` and
`python3 -c 'import openpyxl'` first — a failed install is a `::warning` in the step log, not a
surprise — and if one is missing, fall back to `pypdf` and page reads. Write CSV always and XLSX
when openpyxl imports. Network: archive.org's search API and `/download/<id>/<id>_djvu.txt` work; HathiTrust
page views return 403 (its catalog API works); FamilySearch and Ancestry are login-walled — record
them as inaccessible, never as absent; Google Books fails. Never disable TLS or unset HTTPS_PROXY.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- 25 of 25 images declared in coverage, each with a page file; the line count per page stated.
- Every line has a record (readable or `illegible`); the name-confidence distribution is stated.
- For every page in 229–235 inside this group: the agreement count with #670's rows, and the list of
  disagreements with the reading that decides each.
- `research_domains.py --check` green on the domain; no serial attached; no resident minted.

**Links:** PR #670 and `data/census/1840/index.json` (the 210-row calibration set) ·
`chicago/reference/census1840/validation/H_1840_chicago_name_crosswalk_README.txt` (the fingerprint
method) · T-0504 (serial mapping) · T-0505 (crosswalk) · T-0507 (composition calibration) ·
`data/sources/census_1840_chicago_name_crosswalk.json` and `census_1840_chicago_v4_research.json`.

---

**What the run of 2026-09-03 delivered before splitting this ticket.** All 25 images of group 1 are
declared in `data/research/census_1840/coverage.json` — sheet side, printed page, line count, and
what has and has not been read from each. The NAMES of the three pages PR #670 also read were
transcribed in full off the sheets (229 in `33S7-9YYJ-9M5`, 231 in `-38`, 234 in `-99F`: 92 lines,
3 high / 31 medium / 58 low) and crosswalked line by line against #670's rows in
`crosswalk_670.json`, which now also runs a row-offset test per page. Printed page 206
(`33S7-9YYJ-95F`) turned out to be the enumeration's certificate and recapitulation sheet and was
read in full; printed page 238 (`33S7-9YYJ-C8`) is printed, numbered and empty, and is declared as
such. The deposit count was corrected: 74 distinct images in 75 files, not 75 in 76, so the third
group is images 51-74.

It was split because the remaining work — nine unread left sheets, eleven continuation sheets, and
the 26 narrow age-band columns that only become committable once they are checked against the
enumerator's own printed totals — is several runs of reading, not one, and shipping a
self-invented "(1/2)" is not allowed. The five children carry it.

