---
id: T-0511
title: The pilot, pass 2 and pass 3 cohorts have no reference package while T-0478 to T-0486 do
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-02
closed: 2026-09-04
pr: 837
claimed_by: run 9/4/2026, 10:28:34 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T03:54:43.338Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33941770781
---

**The owner's concern, 2026-09-03, verbatim:** "I am concerned that there are only adjudicated mappings
through v4 and none other and we did at least 11 slices of residents to get to households but most of
your census work needs to be published, I think. Add any other tickets to queue for this also." Asked
what "published" should deliver, the owner chose (2026-09-03): **"Reference packages + final audit"** —
"Fill the missing chicago/reference/resident-research/ packages for the pilot and passes 2–3, and
deliver the final/audit master XLSX/CSV/README that T-0490 promised and never produced." Not the site
Evidence panel.

**The finding.** `chicago/reference/resident-research/README.md` defines the durable package every
cohort ticket must leave — a working XLSX, a machine-readable CSV and a method README, in one folder
per ticket — and says "A cohort ticket is not complete … while its XLSX/CSV/README package exists only
locally." On `dev` the folders exist for **T-0478 through T-0486** only. The **pilot (T-0442), pass 2
(T-0462) and pass 3 (T-0463)** — 225 people, the first three "slices" the owner is counting — have
findings JSON under `data/research/residents/` (`pilot_75_cohort.json`, `pass_02_*`, `pass_03_*`) and
dossiers under `docs/RESEARCH/` but no package a reader can open. This is the first half of the
publish ask.

**The ask.**

1. Find the tool the later cohorts used to write their packages (search `tools/` and the T-0478–T-0486
   PRs for the XLSX/CSV writer); if there is none, write `tools/export_resident_research_package.py
   <ticket> --build | --check` from the findings JSON + cohort JSON, producing the four sheets
   (Residents / Candidates / Sources / Search_Log) as CSVs always and one XLSX when openpyxl imports,
   with `--check` proving a package matches its JSON.
2. Generate `chicago/reference/resident-research/T-0442/`, `T-0462/`, `T-0463/` with README.md each
   (method, source scope, date researched, confidence rules, unresolved, counts, links to the JSON).
3. Add an index table to `chicago/reference/resident-research/README.md`: every package folder, its
   ticket, its cohort size, its outcome counts, its date — so the "11 slices" are visible in one place.
4. A `check.sh` step: every completed cohort has a package and the package matches its findings.

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

- Three packages present with the contract's sheets; their row counts equal the findings JSON.
- The README index lists every package folder with counts; `export … --check` green in `check.sh`.
- No research outcome is altered; no person minted.

**Links:** T-0442, T-0462, T-0463 · `docs/RESEARCH/resident_identity_pilot_75.md`, `_pass_02_75.md`,
`_pass_03_75.md` · T-0512 (the second half of the publish ask) · T-0518.
