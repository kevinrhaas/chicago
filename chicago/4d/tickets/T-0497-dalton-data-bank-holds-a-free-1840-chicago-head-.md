---
id: T-0497
title: Dalton Data Bank holds a free 1840 Chicago head-of-household index by ward, and the repo cites it without reading it
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-02
closed: 2026-09-05
pr: 856
claimed_by: run 9/5/2026, 1:39:37 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T07:14:33.733Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33950206105
---

**The owner's ask, 2026-09-03, recorded verbatim:** "create tickets to do more resident research
transcription and analysis or extract find public sources or APIs to read and find data from the
following reference materials, you should see them all in GitHub — Voter Roll; Census 1830 and 1840;
Fergus; Swift walker; Hh porter. And then create a final ticket that does a review and consolidation of
that research." 

**The finding.** `data/sources/dalton_1840_chicago_census_index.json` cites the Dalton Data Bank's free
Illinois 1840 census index (daltondatabank.net, Chicago by ward) — and cites it for exactly one man,
Edward Dalton, as a later-Chicago identity candidate. The index is a bulk head-of-household name list
for the whole city, public, and text; the repo has never read it as a whole. It is the cheapest
second reading of the 1840 heads the project can get, and a spelling cross-check for the 75 page
images **T-0494**–**T-0496** are reading.

**The ask.**

1. Fetch every 1840 Chicago ward page of the index (`curl -L`, through the proxy); record the URL, the
   fetch date and the HTTP result per page in the source record's `access_notes`.
2. Parse into `data/research/census_1840/dalton_index.json` — records with `as_read`, `normalized`,
   `ward`, and page/line where the index gives them; store NAMES ONLY, never the page HTML (the site's
   rights are `check_required`; a name index of a public-domain census is fact, the page is theirs).
3. Update the source record: `what_it_supplies` (names by ward, an access path), `what_it_does_not_supply`
   (household composition, 1835 residency, the page image), fetch dates, and `verified: true` only if
   every ward page was actually retrieved.
4. Crosswalk the index against the residents layer, the voter lists (**T-0493** if landed) and #670's
   210 named heads: matched / candidate / refused, with rules. Surname alone is a refusal.
5. Town findings: the ward boundaries the index implies, if it states them.

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

- Every ward page fetched, or the failure recorded with the HTTP result — no silent gap.
- Row count stated; surname overlap with the residents layer, the voter lists and the 210 #670 heads
  stated with counts.
- `research_domains.py --check` green; names only committed; no resident minted.

**Links:** `dalton_1840_chicago_census_index.json` · T-0494–T-0496 · T-0504 (the fingerprint mapping
uses this as a spelling second reading) · T-0505.
