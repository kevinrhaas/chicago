---
id: T-0503
title: Eleven images of the St Mary's baptismal register 1833-1835 are deposited and unread
state: done
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-02
closed: 2026-09-04
pr: 742
claimed_by: run 9/4/2026, 1:00:18 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-04T06:21:37.355Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33839205388
---

**The owner's ask, 2026-09-03, recorded verbatim:** "create tickets to do more resident research
transcription and analysis or extract find public sources or APIs to read and find data from the
following reference materials, you should see them all in GitHub — Voter Roll; Census 1830 and 1840;
Fergus; Swift walker; Hh porter. And then create a final ticket that does a review and consolidation of
that research." 

**The finding.** `chicago/reference/catholic-baptisms-1833-1835/` holds **11 FamilySearch page images**
(`S3HT-DHG9-*.jpg`) of the baptismal register Father John Mary Irenaeus St. Cyr kept at St Mary's from
1833 — the first Catholic parish in Chicago. `data/sources/catholic_chicago_st_cyr_1833.json` (tier 4,
an encyclopedia entry) bounds his ministry and says plainly it "is not used to infer unnamed people
from the repository baptism scans". The scans themselves are unread. They name the French, Métis and
Irish Catholic families — the Beaubiens, Laframboises, Ouilmettes, the canal Irish beginning to
arrive — who are under-represented in the newspapers and absent from a poll list that recorded only
men who voted. Each entry names a child, two parents and two godparents with a date: the only
KINSHIP evidence this project has ever been offered in a primary record.

**The ask.**

1. Read all 11 images (the Read tool renders JPEGs) and transcribe every entry into
   `data/research/church/st_marys_baptisms_1833_1835.json`: `date`, `child`, `parents[]`, `godparents[]`,
   `officiant`, `residence_or_notes`, each name `as_read` (French/Latin as written, `[?]` for an unread
   letter) and `normalized` (the English form the papers would print), `name_confidence`, `reading:
   scan_verified`, `locator` = image id + entry position. Illegible entries recorded as such.
2. `data/research/church/coverage.json` declares the 11 image ids.
3. Source record `data/sources/st_marys_baptismal_register_1833_1835.json`: `type: manuscript`, tier 1
   (a contemporary sacramental register), `rights_status: check_required` (FamilySearch's image terms),
   `repository`, `locator` = the image ids, `verified: true`, what it supplies (names, kinship, dates,
   sometimes residence) and does not (occupation, address as such, presence on 1 July 1835 for anyone
   not baptised that week).
4. Search archive.org for the *Illinois Catholic Historical Review* (1918–) transcription of St Cyr's
   register as a second reading; cite it if found, and record the search if not.
5. Crosswalk every adult (parents, godparents, officiant) to residents, the voter lists (**T-0493**)
   and letter-list names in `data/research/church/crosswalk.json` — merges and refusals with rules
   (a Beaubien is not THE Beaubien without a forename).
6. Town findings: any place named (the chapel, a house, "at the fort"), and the register's own
   description of where the parish met.

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

- 11 of 11 images declared; entry count stated; the number of distinct adult names stated.
- Every adult crosswalked with counted outcomes, and the count of adults present NOWHERE else in the
  residents layer stated — these are the community the owner's ask reaches that no other source does.
- The source record validates; the second-reading search is recorded either way.
- `research_domains.py --check` green; nothing minted.

**Links:** `catholic_chicago_st_cyr_1833.json` · T-0493 · T-0513 · the ratified ladder ("baptism
parent/godparent 1833–35 → inferred; attested if also in another source").
