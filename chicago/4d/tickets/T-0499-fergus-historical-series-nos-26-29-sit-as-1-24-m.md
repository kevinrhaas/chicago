---
id: T-0499
title: Fergus' Historical Series Nos. 26-29 sit as 1.24 MB of raw OCR with no text, no register and no claim read out of them: first half by page index
state: done
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-02
closed: 2026-09-03
pr: 739
claimed_by: run 9/3/2026, 6:13:26 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-03T23:50:40.432Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33816329157
---

**The owner's ask, 2026-09-03, recorded verbatim:** "create tickets to do more resident research
transcription and analysis or extract find public sources or APIs to read and find data from the
following reference materials, you should see them all in GitHub — Voter Roll; Census 1830 and 1840;
Fergus; Swift walker; Hh porter. And then create a final ticket that does a review and consolidation of
that research." 

**The finding.** `chicago/reference/fergus/fergushistorical2629unse_hocr_searchtext` is 1.24 MB of raw
Internet Archive OCR of **Fergus' Historical Series Nos. 26–29** (IA item `fergushistorical2629unse`,
Allen County Public Library copy), with `_hocr_pageindex.json` mapping pages to character offsets. The
first pages are the library plate and Fergus Printing Company advertisements; "FERGUS' HISTORICAL
SERIES, No. 27" and "No. 29" title lines and a "CHICAGO ANTIQUITIES" heading are visible in the text.
Nothing in the project has read it: no derived text, no register, no claim, no source record for the
series (the Fergus *directories* of 1839/1843 are cited separately via web transcriptions — **T-0506**).
The Fergus numbers are where the settlers of the 1830s told their own stories thirty and forty years
on — names with arrival years, trades, where the buildings stood, what the prairie and the river looked
like — which is exactly the material the owner asked to be kept for the town.

**The ask — the FIRST half of the volume by page index.**

1. First, together with the other half (coordinate through the coverage file; whichever ticket lands
   first does this and the other reuses it): derive `data/research/books/text/fergus_26_29.txt` from the
   deposit OCR with `data/research/books/page_index/fergus_26_29.json` built from the hOCR page index;
   register it in `data/research/books/corpus.json`; write the volume's TABLE OF CONTENTS into
   `data/research/books/README.md` — which Fergus numbers and titles the item actually holds, with page
   ranges — because the deposit's filename says 26–29 and the text must say what that means. If the
   deposit OCR is too rough on a passage, fetch the item's `_djvu.txt` from archive.org and record which
   text each quote is checked against. Source record `data/sources/fergus_historical_series_26_29.json`
   (tier 3 as a series of reminiscences; a number that reprints a contemporary document is tier 2 for
   that piece — say so per piece in `what_it_supplies`).
2. Read the pages of the FIRST half of the volume by page index and author `data/research/books/extracted/fergus_26_29_first_half.json` —
   claims with verbatim quotes: `person` (name, year, role, where), `business`, `building`, `street`,
   `landscape`, `appearance`, `event`, `household`; `describes_date` on every claim (a reminiscence
   published in 1880 describing 1834 is 1834 evidence of tier 3, never 1880 evidence); `town_finding:
   true` where it is one.
3. Declare the page range in `data/research/books/coverage.json` with no hole.
4. Crosswalk every named person of the 1830–1836 window to residents, voters and letter-list names
   in `data/research/books/crosswalk.json` — merges and refusals with rules.

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

- The volume's contents table is written, and this half's page range is declared with no hole.
- Claim counts by kind stated; the number of town findings stated — and state your target N BEFORE
  reading, so the count is a measurement and not a rationalisation.
- Every 1830–1836 named person crosswalked with counted outcomes; every quote rebuilds from the
  committed text.
- `research_domains.py --check` green; nothing minted.

**Links:** `chicago/reference/fergus/` · T-0506 (the 1839 directory) · T-0501 (Hubbard — the same
book pattern) · T-0513.
