---
id: T-0512
title: T-0490 promised chicago/reference/resident-research/final/audit/ and closed without it
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-02
closed: 2026-09-04
pr: 842
claimed_by: run 9/4/2026, 10:36:33 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T04:23:57.860Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33941756242
---

**The owner's concern, 2026-09-03, verbatim:** "I am concerned that there are only adjudicated mappings
through v4 and none other and we did at least 11 slices of residents to get to households but most of
your census work needs to be published, I think. Add any other tickets to queue for this also." Asked
what "published" should deliver, the owner chose (2026-09-03): **"Reference packages + final audit"** —
"Fill the missing chicago/reference/resident-research/ packages for the pilot and passes 2–3, and
deliver the final/audit master XLSX/CSV/README that T-0490 promised and never produced." Not the site
Evidence panel.

**The finding.** T-0490's acceptance clause promised "`chicago/reference/resident-research/final/audit/`
containing a master XLSX, CSV and README/coverage report with at least: canonical person ID, household
ID, evidence class, research-ticket provenance, source coverage by category, unresolved flags, and audit
result", plus "coverage metrics for identities, occupations, household membership, kinship,
property/address, voter/civic evidence and census linkage" and "follow-up tickets for material
unresolved gaps". T-0490 is `done` (PR #668) and none of that exists on `dev`: no `final/` folder, no
metrics table, no follow-up tickets (the ledger ends at T-0490). This is the second half of the publish
ask — the audit that lets the owner read, in one file, what the 848 residents rest on.

**The ask.**

1. `tools/export_resident_audit.py --build | --check` → `chicago/reference/resident-research/final/audit/`
   with `resident_audit_master.csv` (always), `resident_audit_master.xlsx` (when openpyxl imports) and
   `README.md`. One row per person in `data/residents/`: canonical person id, household id, name,
   grade, `resident_subtype`, `letter_list_only`, letter-list returns, research ticket and outcome,
   `resident_research.asserted_identity`, source ids by category (newspaper / civic / census /
   church / book / directory / secondary), `later_census` serial if any, scene-date presence, division,
   `lives_at`/`works_at`, unresolved flags (candidate identity open, conflicting evidence, no research
   row), and an audit result.
2. The README carries the coverage metrics table T-0490 named — identities, occupations, household
   membership, kinship, property/address, voter/civic, census linkage — each as "N of 848 with at least
   one source", plus the named list of remaining research gaps.
3. Baseline this run on `dev` as it stands; **T-0517** re-runs the export after the update tickets
   land so the two audits bracket the programme.
4. A `check.sh` step: the committed audit matches the residents layer (regenerable, hand edits refused).

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

- 848 rows (or the current person count, stated); the metrics table in the README; the gaps list.
- `export_resident_audit.py --check` green in `check.sh`; the package is regenerable by the tool.
- No research outcome is altered; no person minted.

**Links:** T-0490 (the promise) · PR #668 · T-0511 · T-0517 · T-0518.
