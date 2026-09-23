---
id: T-0502
title: H. H. Porter's Short Autobiography is a 66 MB scan with a garbled text layer, and nothing says whether it carries 1835 Chicago at all
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-02
closed: 2026-09-05
pr: 849
claimed_by: run 9/4/2026, 11:59:08 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T06:18:37.326Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33945828328
---

**The owner's ask, 2026-09-03, recorded verbatim:** "create tickets to do more resident research
transcription and analysis or extract find public sources or APIs to read and find data from the
following reference materials, you should see them all in GitHub — Voter Roll; Census 1830 and 1840;
Fergus; Swift walker; Hh porter. And then create a final ticket that does a review and consolidation of
that research." 

**The finding.** `chicago/reference/hh-porter-a-short-autobiography/4582673.pdf` is a 66 MB, 70-page
scan (Kansas City Public Library reference copy; `/Title` is just the item number) of Henry H. Porter's
*A Short Autobiography* (1915). Its text layer uses subset encodings that come out as garbage on naive
extraction. No transcription, no source record, no mention anywhere in the project. **Two traps before
any reading:** (1) Henry Hobart Porter was born in 1835 and came to Chicago in the 1850s — the book is
expected to carry family memory of the 1830s at best, not residency evidence; the owner listed it, so
it is read and RULED ON, not assumed. (2) "Porter, H." on the 1835 poll list (`chicago/reference/voter-roll/`)
is a different man to resolve through **T-0493**, and Jeremiah Porter the Presbyterian chaplain
(`hh_porter_jeremiah`, `presbyterian_history_jeremiah_porter.json`) is a third — do not conflate any
two of the three.

**The ask.**

1. Extract the text: `pypdf` first; if garbled, render pages into the scratchpad (never commit renders)
   and read them with the Read tool; search archive.org for a clean copy of the title and use its
   `_djvu.txt` if it exists (record which). Commit `data/research/books/text/porter_hh_short_autobiography_1915.txt`
   with a page index; register in `books/corpus.json`.
2. **Rule on relevance first**, with the pages that decide it: does the book carry anything about
   Chicago 1830–1836 — a parent, a relative, a house, a business, a scene? If yes, author
   `data/research/books/extracted/porter_hh_1915.json` claims with `describes_date` and town findings.
   If no, the deliverable is a **carries-no-document finding**: the source record says so in
   `what_it_does_not_supply`, and `books/coverage.json` declares all 70 pages read with nothing extracted
   — an absence a pass has looked for is evidence; an absence nobody looked for is a hole.
3. Source record `data/sources/porter_hh_short_autobiography_1915.json` (`type: book`, tier per what it
   turns out to be, `describes_date` honest, `verified: true`).
4. Record the "Porter, H." refusal in `books/crosswalk.json` — H. H. Porter is NOT the 1835 voter — with
   the birth-year evidence.

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

- All 70 pages declared read (text or page-read), no hole.
- The relevance ruling stated with the pages that decide it; either a claims file with counts or a
  carries-no-document finding in the source record.
- The "Porter, H." refusal and the Jeremiah Porter distinction recorded in the crosswalk.
- `research_domains.py --check` green; nothing minted.

**Links:** `hh_porter_jeremiah` · T-0493 · T-0501 (the book pattern) · T-0513.
