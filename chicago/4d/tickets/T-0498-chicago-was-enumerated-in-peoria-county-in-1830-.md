---
id: T-0498
title: Chicago was enumerated in Peoria County in 1830 and the repo holds only county aggregates: find and transcribe the named schedule
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-02
closed: 2026-09-03
pr: 734
claimed_by: run 9/3/2026, 5:17:27 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-03T22:17:41.482Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33807961008
---

**The owner's ask, 2026-09-03, recorded verbatim:** "create tickets to do more resident research
transcription and analysis or extract find public sources or APIs to read and find data from the
following reference materials, you should see them all in GitHub — Voter Roll; Census 1830 and 1840;
Fergus; Swift walker; Hh porter. And then create a final ticket that does a review and consolidation of
that research." 

**The finding.** The owner listed "Census 1830" among the reference materials, and what the repo holds
for 1830 is aggregate only: `chicago/reference/ipums/nhgis0001_csv/nhgis0001_ds5_1830_county.csv` (NHGIS
total population by Illinois county, with its codebook and the 1830 county shapefile). No named 1830
schedule is anywhere in the tree. Chicago in 1830 was enumerated in **Peoria County** (Cook County was
created in 1831), and the named schedule — a few dozen households: Kinzie, Beaubien, Clybourne,
Laughton, Wolcott, Miller, Robinson, Hogan and the rest — is a public record that genealogy sites and
Andreas reprint. Many of those households were still here on 1 July 1835, and a household present in
1830 AND on an 1833–35 list is the strongest continuity evidence the ladder recognises ("1830 Peoria
County schedule household + any 1833–35 source → attested"). `docs/RESEARCH/chicago_1830_claims.md`
already warns that Andreas's "Map of Chicago in 1830" is a land-title map and a name on it is not a
house — this ticket is about the CENSUS, not the map, and must not confuse the two.

**The ask.**

1. Find a public transcription of the 1830 Peoria County schedule's Chicago households: ILGenWeb /
   USGenWeb Archives (Peoria County census transcriptions), Genealogy Trails (Peoria and Cook), Andreas
   vol. 1 on archive.org (advancedsearch for the identifier, then `_djvu.txt`), Hurlbut's *Chicago
   Antiquities* (archive.org), the Illinois State Archives. FamilySearch's images (NARA M19) are
   login-walled — record that as inaccessible.
2. Transcribe into `data/research/census_1830/schedule_chicago_1830.json` — one record per household:
   head `as_read`/`normalized`, the 1830 age-band cells as the transcription gives them, the
   transcription's own line order; `reading: transcription_mediated` (two transcriptions of the same
   schedule, agreeing, are worth recording as two readings).
3. Source record `data/sources/census_1830_peoria_county_chicago_precinct.json` with the tier the
   provenance earns (a genealogy transcription of a primary is tier 2 for the names, with the mediation
   stated), `verified`, `what_it_supplies` / `what_it_does_not_supply`.
4. Crosswalk to residents and to the voter lists (**T-0493**) in `data/research/census_1830/resident_crosswalk.json`;
   NHGIS's Peoria County total as a calibration check on the transcription's count.
5. If no named schedule is reachable from this runner, the finding is the negative-search log — every
   site tried, the query, the date, the result — and a `block --owner` naming the paywalled copies,
   not an empty file.
6. Town findings: anything the schedule's order or notes say about where households stood.

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

- Either N households transcribed with their source, coverage declared, and every household
  crosswalked (matched / candidate / refused, counted) — or at least four named public sources searched
  with each result recorded and the ticket blocked on the owner with the paywalled copies named.
- The source record states the mediation chain (original → transcriber → site) honestly.
- `research_domains.py --check` green; nothing minted.

**Links:** `docs/RESEARCH/chicago_1830_claims.md` · `data/sources/andreas_1884_chicago_1830_map.json` ·
T-0493 · T-0513.
