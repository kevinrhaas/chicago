---
id: T-0507
title: 964 IPUMS 1840 households carry age-band and industry composition, and no calibration summary exists for the household reconstruction
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-02
closed: 2026-09-04
pr: 811
claimed_by: run 9/4/2026, 4:00:36 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-04T21:35:20.218Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33918546773
---

**The owner's ask, 2026-09-03, recorded verbatim:** "create tickets to do more resident research
transcription and analysis or extract find public sources or APIs to read and find data from the
following reference materials, you should see them all in GitHub — Voter Roll; Census 1830 and 1840;
Fergus; Swift walker; Hh porter. And then create a final ticket that does a review and consolidation of
that research." 

**The finding.** `chicago/reference/ipums/H_1840_chicago.csv` holds 964 Chicago households of 1840 as
IPUMS variables — thirteen male and thirteen female free-white age bands, free coloured and slave
bands, the industry columns (agriculture, commerce, manufactures and trades, navigation, learned
professions), foreigners not naturalised, illiteracy — and `nhgis0001_ds5_1830_county.csv` holds the
1830 county totals. The occupation census the retired reconstructed-household programme was built on
(`data/reconstruction/1835_inferred_household_programme.json`) was calibrated on five in-dataset
figures because, as STATUS.md says, "no period trade table for a comparable western town exists in
`data/sources/`". One now does: five years late and for the same town. The owner's later sweep —
"assign these residents a place to live and work once we complete the full 3600ish resident list" —
will need a household-composition model, and this is its calibration.

**The ask.**

1. `tools/census_1840_composition.py --build | --check` (pure python, `csv`) → `data/research/census_1840/composition_1840.json`:
   household-size distribution (count, mean, median, percentiles), persons per household by sex and
   age band, the share of households by industry column, foreigners and illiteracy shares, and — where
   **T-0504** has attached wards or pages — the same by ward; the 1835 town census (3,265 people / 398
   dwellings, `data/town_census.json`) and the 1830 county totals placed beside it with the growth
   arithmetic; the IPUMS totals reproduced exactly (964 households; the person total the file implies).
2. `docs/RESEARCH/household-composition-1840-calibration.md`: what the distributions are, what they may
   calibrate for 1835 (household size, sex ratio, child share, trade split) and what they may NOT
   (any named person, any specific household's members), with the caveat that 1840 Chicago had
   doubled since the scene.
3. Source record for the IPUMS extract if none exists (`data/sources/ipums_1840_chicago_households.json`,
   `type: dataset`, tier 1 for the counts, the IPUMS citation as their terms require) and for NHGIS.
4. One `check.sh` step for `--check`.

No person is minted from a count, ever (the owner's own synthesis rule: "1840 household members are
never minted into 1835 solely from census counts").

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

- The summary reproduces the IPUMS household total (964) and states the person total; percentiles and
  shares stated; the doc names what each figure may and may not calibrate.
- Source records validate; the tool re-derives under `check.sh`.
- Nothing minted.

**Links:** `data/reconstruction/1835_inferred_household_programme.json` (the retired occupation census
this replaces as calibration) · `docs/RESEARCH/residents_1835_inferred.md` § 2 · T-0504 · T-0516 ·
the future placement sweep.
