---
id: T-0505
title: Three of 210 named 1840 heads are bridged to 1835 residents: crosswalk every named head to residents, voters and letter-list names
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-02
closed: 2026-09-03
pr: 722
claimed_by: run 9/3/2026, 2:33:51 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-03T19:55:49.360Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33796879498
---

**The owner's ask, 2026-09-03, recorded verbatim:** "create tickets to do more resident research
transcription and analysis or extract find public sources or APIs to read and find data from the
following reference materials, you should see them all in GitHub — Voter Roll; Census 1830 and 1840;
Fergus; Swift walker; Hh porter. And then create a final ticket that does a review and consolidation of
that research." 

**The finding.** After PR #668 the synthesis reported "0 one-to-one resident links" to named 1840
heads (it matched the 55-name partial CSV by exact name only); PR #670 corrected that to **three
adjudicated bridges** — John Murphy (validated), William Hanford Adams (validated, and restored to the
residents layer as `hh_adams_william_h`), John Miller (provisional) — out of 210 named heads, with the
rule that a link requires an explicitly adjudicated identity bridge and that 1840 household composition
is never back-projected to 1835 (`data/research/residents/census_1840_identity_bridges_README.md`).
Once **T-0504** names most of the 964 households, the question is the same for every one of them, and
the answer must be written down per head: matched, candidate, or refused, with the reason.

**The ask.**

1. `data/research/census_1840/resident_crosswalk.json` — every named 1840 head from
   `serial_crosswalk.json` matched against: the residents layer (848 persons), the voter lists
   (**T-0493**), the letter-list names (`data/research/newspapers/gazetteer.json`), the 1839 directory
   (**T-0506**, if landed) and `census_1835_bridge_candidates.json`; outcome `matched` (an independent
   discriminator beyond the name — a forename AND a trade, a list appearance, a directory address),
   `candidate`, or `refused` with the rule. Common names (John Miller, William Smith) are refused
   unless a discriminator exists, and the refusal says so.
2. For each `matched` head, a proposed `later_census` block in the exact shape #670 wrote
   (`year`, `source_id`, `serial`, names, confidences, page/row, image, `household` counts,
   `bridge_basis`, the "LATER EVIDENCE, NOT A BACK-PROJECTION" note) — PROPOSED, in the crosswalk
   file, not applied to any household; **T-0515** applies them through `tools/apply_census_1840_bridges.py`
   by extending `census_1840_identity_bridges.csv`.
3. Re-adjudicate the 29 heads the September 2 legacy matcher listed as unmatched, with reasons.
4. Town findings: the enumeration order of matched heads against known addresses — where two known
   neighbours are adjacent in the census, say so; it is the only 1840 spatial signal.

The ratified ladder binds: "1839/1840 alone is never a 1835 resident (later evidence only)".

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

- Every named head has an outcome; counts by outcome stated; the 29 legacy heads re-adjudicated with
  reasons.
- Every `matched` head carries a proposed `later_census` block with a `bridge_basis` naming the
  discriminator; no household file is changed here.
- `research_domains.py --check` green; nothing minted or regraded.

**Links:** PR #670 · `census_1840_identity_bridges*.csv` and README · `tools/apply_census_1840_bridges.py`
· T-0504 · T-0513 · T-0515.
