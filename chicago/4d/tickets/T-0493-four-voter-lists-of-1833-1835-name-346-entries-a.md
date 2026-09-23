---
id: T-0493
title: Four voter lists of 1833-1835 name 346 entries, and the residents layer holds 99 of their 215 surnames
state: done
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-02
closed: 2026-09-03
pr: 692
claimed_by: run 9/3/2026, 5:36:32 AM CT
blocked_on: null
needs_bake: false
---

**The owner's ask, 2026-09-03, recorded verbatim:** "create tickets to do more resident research
transcription and analysis or extract find public sources or APIs to read and find data from the
following reference materials, you should see them all in GitHub — Voter Roll; Census 1830 and 1840;
Fergus; Swift walker; Hh porter. And then create a final ticket that does a review and consolidation of
that research." 

**The finding.** `chicago/reference/voter-roll/Early_Chicago_Voter_Lists_1833-1835_Transcription.txt`
(with its .docx and the source PDF beside it) carries four lists transcribed from the *Chicago
Genealogist* Summer 1993 (XXV/4) publication of Ingrid Latimer Schulz's IRAD transcription: the **poll
list of the first town election, 10 August 1833** (31 names), the **1833 town tax list** (115), the
**1834 poll list, filed 11 August 1834** (115), and the **1835 poll list** (85) — 346 entries, 215
distinct surnames. Measured against `data/residents/index.json` on `dev` (824 households): only **99 of
the 215 surnames** match any resident, and only **37 of the 85 men on the 1835 poll** do. A man who
voted at Chicago in 1835 is the strongest residence evidence this project holds short of a newspaper
naming him, and half of them are in no record at all — Bread, Pixby, Kennicott, Ulrich, Trowbridge,
Calhoun (Alvin), Cusick, Garland, Haighs, Markle, Panster… The v1/v2 workbooks under
`chicago/reference/census1840/validation/` tiered these men ("A — CONFIRMED 1835 VOTER") and
`data/research/residents/census_1835_bridge_candidates.json` holds 802 rows derived from them; nothing
ever turned that into structured evidence the residents layer can cite.

**The ask.**

1. `data/research/civic/voter_lists_1833_1835.json` — all 346 entries as records (`as_read` exactly as
   the transcription prints, including `S---?, Albert`; `normalized`; `list` ∈ `poll_1833 | tax_1833 |
   poll_1834 | poll_1835`; `locator` = list + line; `reading: transcription_mediated`), and
   `data/research/civic/coverage.json` declaring all four lists.
2. `data/research/civic/voter_crosswalk.json` — every entry crosswalked to the 848 residents and to the
   bridge-candidates file: `matched_resident` (with the discriminator that resolves it — a forename, a
   trade, a second list), `candidate`, or `unmatched`; every refusal declared with its rule.
3. Source records: `data/sources/chicago_voter_lists_1833_1835_irad.json` (the IRAD originals as
   transcribed — tier 2, `reading` mediated twice: Schulz then Genealogy Trails; `verified: true` only
   if the Genealogy Trails page is fetched and matched line for line, else say so) and
   `data/sources/chicago_genealogist_1993_voter_lists.json` (the publication).
4. **Settle the 1835 poll list's date** — which election it records (the town trustees' election, or
   the August county election) and how far from 1835-07-01 it falls; write the finding into the source
   record, because the grading ladder (below) treats an 1835 vote as presence on the scene date.
5. A second-source sweep for every unmatched 1835-poll name: Andreas vol. 1 (archive.org full text —
   the 1833 incorporation voters and the 1835 election are printed), the Illinois State Archives Public
   Domain Land Tract Sales database (a purchase in T39N R14E 1830–35 is a second civic record),
   earlychicago.com (tier-4 pointer only), Genealogy Trails Cook County. Every negative search recorded.
6. A reference package `chicago/reference/resident-research/T-0493/` per
   `chicago/reference/resident-research/README.md` (CSV always; XLSX if openpyxl imports).
7. Town findings: where each poll was held, who the trustees were, the tax list read as a ranked property
   list (it is the closest thing to a property roll the project has and feeds the later placement sweep).

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

**The ratified grading ladder** (the owner's ruling of 2026-09-03, recorded verbatim so this ticket
grades nothing on its own but records what the consolidation will apply): "attested = 1835 poll + any
second independent source, or a contemporary record naming the person in Chicago; inferred = 1835 poll
alone, or 1833/1834 lists with another source, or baptism parent/godparent 1833–35, or Hubbard/Fergus
naming a resident with trade or address; projected_resident = a single appearance with nothing else;
1839/1840 alone is never a 1835 resident (later evidence only)."

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

- 346 of 346 entries structured; the four lists declared in coverage; `research_domains.py --check`
  green on the domain.
- Every entry carries an outcome, and the PR states the counts: matched / candidate / unmatched per
  list, and how many of the 85 men on the 1835 poll have a second independent source.
- At least one recorded negative search per unmatched 1835-poll name.
- The 1835 poll's election date is stated in the source record with its evidence, or the failure to find
  it is recorded as a negative search.
- The reference package exists with Residents / Candidates / Sources / Search_Log.
- No resident is minted or regraded here.

**Links:** `census_1835_bridge_candidates.json` (802 rows from the v1 workbook) · T-0487–T-0490 (the
synthesis this feeds) · T-0513 (consolidation) · T-0514 (mint) · L214 (the letter-list scale liberty
this evidence will sit beside).
