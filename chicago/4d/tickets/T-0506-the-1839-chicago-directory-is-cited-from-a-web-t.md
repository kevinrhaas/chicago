---
id: T-0506
title: The 1839 Chicago directory is cited from a web transcription and never extracted: every entry structured and crosswalked
state: done
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-02
closed: 2026-09-03
pr: 741
claimed_by: run 9/3/2026, 6:12:04 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-03T23:53:47.655Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33816339726
---

**The owner's ask, 2026-09-03, recorded verbatim:** "create tickets to do more resident research
transcription and analysis or extract find public sources or APIs to read and find data from the
following reference materials, you should see them all in GitHub — Voter Roll; Census 1830 and 1840;
Fergus; Swift walker; Hh porter. And then create a final ticket that does a review and consolidation of
that research." 

**The finding.** *Fergus' Directory of the City of Chicago, 1839* (Robert Fergus's 1876 reprint of the
first city directory) is the closest address list to 1835 the project can reach: a name, a trade and a
street for every head the compiler found, four years after the scene. The repo cites it FOUR times —
`fergus_chicago_directory_1839.json` (tier 4, a web transcription at ldsgenealogy.com),
`resident_research_fergus_directory_1839.json`, `rr_fergus_directory_1839.json`, plus the 1843 Norris
directory — and every cohort pass searched it by hand for one name at a time. It has never been
extracted as a whole, so no crosswalk can count what it says about the 848 residents or the 346 voters,
and no street ever learned which trades stood on it in 1839.

**The ask.**

1. Find the reprint on archive.org (advancedsearch: `fergus directory chicago 1839`; the Fergus
   Historical Series numbers are separate items), fetch its `_djvu.txt`, commit
   `data/research/directories/text/fergus_1839.txt` with a page index; do the same for the 1843 Norris
   directory if reachable, else record the search.
2. Extract EVERY entry into `data/research/directories/fergus_1839.json` — records: `as_read` (the
   printed line), `name_normalized`, `trade_as_printed`, `trade_normalized` (the residents vocabulary
   word where one exists; else the printed word, flagged — **T-0418** owns the vocabulary gap), `address_as_printed`,
   `street_normalized`, `locator` (page, line), `reading: transcription_mediated` (an OCR of a reprint).
   State the entry count against the book's own count.
3. Replace or upgrade the source record: the IA scan text is a tier-2 reprint of an 1839 primary, and
   it supersedes the web transcription for citation; say so in both records.
4. Crosswalk to residents, voters (**T-0493**), letter-list names and the 1840 heads (**T-0504**) in
   `data/research/directories/crosswalk.json` — `later_directory` evidence, never on its own a 1835
   residency claim (the ratified ladder: "1839/1840 alone is never a 1835 resident").
5. Town findings: every street name as printed, every business with an address, the trades per street
   — the 1839 street-face picture is the best proxy for 1835 the project will ever hold, and the street
   tickets (T-0444–T-0447, T-0451) will want it.

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

- Entry count stated against the book's own count; every entry structured; coverage declared by page.
- Crosswalk outcomes counted; the trades with no vocabulary word listed for T-0418.
- Street and business town findings counted; the source records say which text is senior.
- `research_domains.py --check` green; nothing minted or regraded.

**Links:** `fergus_chicago_directory_1839.json` and its two siblings · `norris_chicago_directory_1843.json`
· T-0418 · T-0493 · T-0504 · T-0513.
