---
id: T-0504
title: 754 of 964 IPUMS 1840 households are unnamed while every page image carries the names: fingerprint every read page to a serial
state: done
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-02
closed: 2026-09-03
pr: 724
claimed_by: run 9/3/2026, 2:33:14 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-03T20:09:23.623Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33796870672
---

**The owner's ask, 2026-09-03, recorded verbatim:** "create tickets to do more resident research
transcription and analysis or extract find public sources or APIs to read and find data from the
following reference materials, you should see them all in GitHub — Voter Roll; Census 1830 and 1840;
Fergus; Swift walker; Hh porter. And then create a final ticket that does a review and consolidation of
that research." 

**The finding.** IPUMS's 1840 extract for Chicago holds **964** households as age-band and industry
counts with no names (`chicago/reference/ipums/H_1840_chicago.csv`, the codebook `H_1800s.pdf`). The
owner's v1/v2 workbooks attached names to 55 of them from printed pages 234–235 by a **26-column
free-white age-band fingerprint**: each census line's male/female age-band cells, compared with the
IPUMS household variables, resolve the line to a SERIAL, and block continuity settles the few near
misses (`chicago/reference/census1840/validation/H_1840_chicago_name_crosswalk_README.txt` is the
method statement; name confidence and serial-mapping confidence are kept separate). PR #670 recovered
the v4 workbook's extension of that to **210 heads on pages 229–235** (`data/census/1840/household_heads.csv.gz`,
with `serial_confidence` per row). **754 households remain unnamed** while **T-0494**–**T-0496** are
reading every one of the 75 page images. The owner's ruling on the missing v3/v4 workbooks,
2026-09-03, verbatim: "They are lost; rebuild".

**The ask.**

1. `tools/census_1840_fingerprint.py --build | --check | --self-test` — pure python and `csv`, no
   network: for every page record the three reading tickets produced, compute the fingerprint from the
   age-band cells, match against the IPUMS rows, attach `serial` with `serial_mapping_confidence` ∈
   `unique | ambiguous(n) | none` and the block-continuity argument where it was used; write
   `data/research/census_1840/serial_crosswalk.json`.
2. **Reproduce first, then extend:** the 210 #670 mappings (and the 55 v1 mappings inside them) must
   come out of the tool with the agreement count stated and every disagreement listed with the
   reading that decides it — none silently overwritten. Only then attach serials to the newly read
   pages.
3. `--self-test` breaks the assertions: a fingerprint that matches two serials must read `ambiguous`,
   not pick one; a line with no match must read `none`; a serial may not be attached twice.
4. A reference package `chicago/reference/census1840/validation/T-0504_1840_name_serial_crosswalk.csv`
   (+ `.xlsx` if openpyxl imports) with a README in the shape of the existing crosswalk README — this
   is the successor to the lost v3/v4 workbooks and is named by ticket, not by a guessed version number.
5. Update `data/sources/census_1840_chicago_name_crosswalk.json`'s coverage and `what_it_supplies`.
6. One `check.sh` step for `--check`, paired with `--self-test`.

The result is a dated 1840 record. Nothing here mints a 1835 resident — **T-0505** crosswalks the
named heads to 1835 identities, and the ratified ladder says "1839/1840 alone is never a 1835 resident".

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

- Counts stated: rows read, names attached, serials `unique` / `ambiguous` / `none` — and they sum to
  the rows.
- The 210 #670 mappings reproduced with the agreement count and the list of disagreements.
- `census_1840_fingerprint.py --self-test` fires its assertions; the tool and its self-test are in
  `check.sh`; the package and README exist.
- Nothing minted.

**Links:** PR #670 · `H_1840_chicago_name_crosswalk_README.txt` · T-0494–T-0497 · T-0505 · T-0507.
