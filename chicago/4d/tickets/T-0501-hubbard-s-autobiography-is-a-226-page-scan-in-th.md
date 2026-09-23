---
id: T-0501
title: Hubbard's autobiography is a 226-page scan in the deposit with no text, no source record and no mention anywhere in the project
state: done
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-02
closed: 2026-09-03
pr: 737
claimed_by: run 9/3/2026, 4:29:07 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-03T22:30:47.083Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33807967575
---

**The owner's ask, 2026-09-03, recorded verbatim:** "create tickets to do more resident research
transcription and analysis or extract find public sources or APIs to read and find data from the
following reference materials, you should see them all in GitHub — Voter Roll; Census 1830 and 1840;
Fergus; Swift walker; Hh porter. And then create a final ticket that does a review and consolidation of
that research." 

**The finding.** `chicago/reference/swift-walker-autobiography/autobiographyofg00hubb.pdf` is the
Internet Archive scan (item `autobiographyofg00hubb`, 226 pages, 7.8 MB) of *The Autobiography of
Gurdon Saltonstall Hubbard, Pa-pa-ma-ta-be, "The Swift Walker"* (Chicago, 1911; written in the 1880s
about 1818 onward). It carries a good embedded OCR layer — the Green Tree Tavern passage and the
1836 Kinzie Street warehouse material read cleanly straight out of it. `git grep` across `docs/`,
`data/sources/` and `tickets/` on dev returns ZERO hits for "swift walker" or the item id: dropped in,
never transcribed, never cited, never graded. Hubbard was a resident — trader, packer, warehouse owner,
the man who walked the Vincennes trace — and his book names the people, the buildings, the sandbar,
the prairie and the fort of the exact decade this scene reconstructs.

**The ask.**

1. Fetch `https://archive.org/download/autobiographyofg00hubb/autobiographyofg00hubb_djvu.txt`
   (verify the identifier with the advancedsearch API first; `curl -L`; fall back to `pypdf` text
   extraction from the deposited PDF if the download fails, and say which text the quotes are checked
   against). Commit `data/research/books/text/hubbard_autobiography_1911.txt` with
   `data/research/books/page_index/hubbard_autobiography_1911.json`; register in `books/corpus.json`.
2. Source record `data/sources/hubbard_autobiography_1911.json`: `type: book`, tier 3 (a participant's
   recollection written five decades on and edited posthumously — near-primary for what he did, tier 3
   for dates and for other men's affairs), `date: 1911`, `describes_date: 1818-1836`, `verified: true`,
   `what_it_supplies` / `what_it_does_not_supply` (no plat positions; his own warehouse's date is
   1836, after the scene).
3. Read every chapter that touches Chicago before 1836 and author
   `data/research/books/extracted/hubbard_autobiography_1911.json`: `person` (name, year, role — the
   Kinzies, the Beaubiens, Wolcott, the fort's officers, his partners and clerks), `business`
   (his trading and packing, Hubbard & Co., the Eagle Line), `building`, `street`, `landscape` (river
   mouth, sandbar, the prairie, Wolf Point, the portage), `appearance` (houses, the fort, dress),
   `event`; `describes_date` per claim; `town_finding: true` where it is one.
4. Declare the page range read in `books/coverage.json`; crosswalk every 1830–1836 named person in
   `books/crosswalk.json` (merges and refusals with rules); note where Hubbard contradicts Andreas or
   the papers — a disagreement is recorded, never resolved away (`docs/RESEARCH/<id>.md` if it needs a
   page).

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

- Every chapter touching Chicago before 1836 is declared read, by page range, with no hole.
- Claim counts by kind; town findings counted against an N stated before reading.
- Every 1830–1836 named person crosswalked with counted outcomes; every quote rebuilds from the
  committed text; the source record exists and validates.
- `research_domains.py --check` green; nothing minted.

**Links:** `docs/RESEARCH/green_tree_tavern.md` (already leans on Hubbard by way of Andreas) ·
`docs/RESEARCH/jh_kinzie_forwarding_store.md` · T-0499/T-0500 · T-0513.
