---
id: T-0509
title: 237 named residents have no research row: cohort 14 of 79
state: done
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-02
closed: 2026-09-05
pr: 901
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T17:02:25.796Z
claimed_run: null
---

**The owner's ask, 2026-09-03, verbatim:** "Once complete i would like to begin to do and update of the
resident and household data based on all of your deep research, from the sources at hand and any
supporting or related sources you find and identifying as many residents of chicago circa 1835."

**The finding.** After twelve cohorts (T-0442, T-0462, T-0463, T-0478–T-0486) and the September 2
synthesis, **611 of the 848 named people** in `data/residents/` have a research row and **237 do not**:
`tools/synthesize_resident_research.py` lists roughly 150 `ll_*` ids under `letter_list_missing_research_row`,
and the rest of the 848 were never in a cohort. `chicago/reference/resident-research/README.md`'s
completion rule — "A cohort ticket is not complete while any manifest person remains `pending`" — has
never been applied to the population as a whole. **T-0492** froze the 237 into three deterministic
cohorts of 79; this ticket is **cohort 14** (`data/research/residents/pass_14_79_cohort.json`).

**The ask.** The existing method, unchanged — read `docs/RESEARCH/resident-research-pass-12.md` and
the T-0486 package as the model:

1. For every one of the 79: a dated review with a targeted exact-name and justified-variant sweep
   across the repository newspapers and identity ledger, the voter lists (**T-0493** if landed), the
   1839 directory (**T-0506** if landed), the 1840 heads (**T-0504**/**T-0505** if landed), Andreas,
   earlychicago.com, the Illinois Public Domain Land Tract Sales database, the Illinois Statewide
   Marriage Index, the Dalton 1840 index, county histories on archive.org, and the archive.org
   full-text search API; outcome `corroborated | corroborated_enrichment | candidate_identity |
   no_corroboration` with the discriminator or its absence written down.
2. `data/research/residents/pass_14_findings.json` completed (`pending_person_ids: []`), a source record
   per source cited, and the durable package `chicago/reference/resident-research/T-0509/`
   (`_resident_research.csv` always, `_working.xlsx` if openpyxl imports, `README.md` with method, scope,
   date, confidence rules, unresolved issues, candidate/no-find counts).
3. Candidate identities stay unasserted; surname similarity is a clue; negative searches are recorded.
   Nothing here changes a grade — **T-0513** consolidates and **T-0514**/**T-0515** apply.

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

- 79 of 79 rows carry an outcome; `pending_person_ids` is empty; every `source_id` resolves.
- Search_Log rows ≥ people reviewed; counts by outcome stated in the PR.
- `tools/synthesize_resident_research.py --check` green with `letter_list_missing_research_row`
  reduced by this cohort's share; `check.sh` green.

**Links:** T-0486 (the model package) · T-0487–T-0490 · `chicago/reference/resident-research/README.md`
· T-0492 (the frozen cohort) · T-0513.
