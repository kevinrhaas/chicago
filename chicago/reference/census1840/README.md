# `chicago/reference/census1840/` — the 1840 census deposit, and what has been made of it

This folder is a **read-only reference deposit**: the FamilySearch page images of the 1840
federal census of Chicago, plus the workbooks and crosswalks that have been derived from
them. Nothing here is loaded by the app, and nothing here is published — see
[§ Nothing in here reaches the site](#nothing-in-here-reaches-the-site).

The *reading* of these sheets lives one directory over, in
[`chicago/4d/data/research/census_1840/`](../../4d/data/research/census_1840/README.md),
which holds the per-page line readings, the coverage declaration, the crosswalks and the
domain's rules. **That file is the authority on how a sheet is read; this one is the
authority on what is in this folder and where each thing came from.**

## What 1840 may and may not assert about 1835

**This is LATER EVIDENCE.** The owner's ruling of 2026-09-03, ratified in
[`docs/RESEARCH/resident-grading-policy.md`](../../4d/docs/RESEARCH/resident-grading-policy.md),
is verbatim: *"1839/1840 alone is never a 1835 resident (later evidence only)."* That is
rung **G0** of the grading ladder, and it is absolute.

So, concretely:

- A name read off these sheets **may** be used as a *second* source beside an in-window
  record — an 1833/1834/1835 poll or tax list, the contemporary press, the parish
  register — under rungs G1a/G2b of the ladder.
- A name read off these sheets **may not**, on its own, mint an 1835 resident, place a
  household in the 1835 town, or raise anybody's grade.
- The 1840 **household composition** — sizes, age bands, industry columns — is used as a
  *calibration* for what a Chicago household looked like, never as a fact about a
  particular 1835 household. It is derived into
  `data/research/census_1840/composition_1840.json`, which carries counts and nothing else,
  and whose own self-test refuses the file if a name or an IPUMS serial ever reaches it.
- The bridge from an 1840 line to an 1835 person is a separate, adjudicated step (T-0505);
  minting and regrading are separate steps again (T-0514, T-0515).

## The page images — 75 files, 74 distinct

| group | files | read state |
|---|---:|---|
| images 1–25 (`33S7-9YYJ-24` … `33S7-9YYJ-C8`) | 25 | declared by **T-0494** and its successors; **25 of 25** carry a committed page file |
| images 26–50 (`33S7-9YYJ-DD` … `33SQ-GYYJ-9CZ`) | 25 | declared by **T-0495** and its successors; **14 of 25** carry a committed page file |
| images 51–74 (`33SQ-GYYJ-9J5` … `33SQ-GYYN-38YY`) | 24 | **undeclared and unread** — the open ticket is **T-0496** |
| `33S7-9YYJ-9WF (1).jpg` | 1 | a byte-identical second copy of `33S7-9YYJ-9WF.jpg` (1,349,156 bytes each, md5 `4cc1ca3ff88c213598c1cfe409938a35`) — **not a distinct page** |

Reproduce the file counts with `ls chicago/reference/census1840/*.jpg | wc -l` (75) and
`md5sum chicago/reference/census1840/*.jpg | awk '{print $1}' | sort -u | wc -l` (74); the
read counts with `ls chicago/4d/data/research/census_1840/pages/*.json | wc -l` (39). The
grouping is `ls *.jpg | sort` with the duplicate copy removed first, so the index runs 1–74;
`data/research/census_1840/coverage.json` states the boundary and every per-image finding.

- **Source:** `census_1840_chicago_familysearch_images` (tier 1) — 1840 U.S. Census,
  population schedules, Chicago, Cook County, Illinois; FamilySearch collection 1786457,
  division of S. W. Sherman. The collection page is login-walled, which is recorded in
  `coverage.json` as *inaccessible*, not as absent: the deposited JPEGs are the record.
- **Rights:** public domain; `asset_use: text_only`.
- **The deposit is read only.** No image, crop or render is ever committed — only derived
  text. A crop made to read a line is a working file and stays out of the tree.
- Sheets come in two kinds, numbered in one run of printed pages: a **left sheet** carrying
  the heads of families and the 26 free-white age bands, and a **right (continuation)**
  sheet carrying the slaves, the family total, the six industry columns, pensioners,
  deaf/dumb/blind and the schools-and-illiteracy block. One household is a single ruled
  line spanning both, so a name and its own figures sit on two different images.

## `validation/` — nine files, three provenances

| file | rows/shape | what it is | where it came from |
|---|---|---|---|
| `Chicago_1835_Best_Resident_Set_Research.xlsx` | 6 sheets (README · Best 1835 Resident Set · 1840 Census Detail · Ambiguities & Review · Early Lists Raw · Sources) | **v1** of the owner's adjudication workbook: a best-1835-resident set with poll/tax columns, an 1840 census detail sheet carrying page/row/SERIAL, and an explicit ambiguities sheet | deposited by the owner, 2026-09-02 (`Add updated 1835 resident research workbooks`) |
| `Chicago_1835_Best_Resident_Set_Research_v2.xlsx` | 8 sheets — v1's six plus *Pages 229-231 Research* and *229-231 Priority Adds* | **v2**, the same workbook extended over printed pages 229–231 | deposited by the owner, 2026-09-02, same commit |
| `Chicago_1840_IPUMS_Name_Crosswalk_Working.xlsx` | 3 sheets (Read Me · Validated Names 55 · All 964) | the working crosswalk behind the 55-name tranche: the validated rows, and all 964 IPUMS households with the 909 unnamed ones left explicitly unnamed | deposited by the owner, 2026-09-01 (`Add Chicago reference materials under GitHub size limit`) |
| `H_1840_chicago_name_crosswalk_README.txt` | prose | the method note for that tranche — the fingerprint method, the two serial blocks it resolved, and the separation of name confidence from serial-mapping confidence | deposited by the owner, 2026-09-01 |
| `H_1840_chicago_name_crosswalk_pages234_235.csv` | 55 rows | the 55 validated head-of-household names on printed pages 234 and 235, each with its IPUMS SERIAL and both confidences | deposited by the owner, 2026-09-01 |
| `H_1840_chicago_with_names_partial.csv` | 964 rows | the full IPUMS Chicago 1840 extract with names attached where they were validated and blank where they were not — the base table everything else here is measured against | deposited by the owner, 2026-09-01 |
| `T-0504_1840_name_serial_crosswalk.csv` | 636 rows | **the successor to the lost v3/v4 workbooks**, GENERATED: every line this project has read off the sheets, with its fingerprint verdict (`unique` / `ambiguous(n)` / `none`), the columns compared, the candidates, and the block-continuity argument | **T-0504**, PR **#724**, 2026-09-03 |
| `T-0504_1840_name_serial_crosswalk.xlsx` | 1 sheet, 636 rows | the same table as a workbook; written when `openpyxl` imports, the CSV is the gated artifact | T-0504, PR #724 |
| `T-0504_1840_name_serial_crosswalk_README.txt` | prose, generated | the generated method/counts note that ships with the package | T-0504, PR #724 |

**v3 and v4 do not exist here.** The owner ruled on them, 2026-09-03: *"They are lost;
rebuild."* What survives of v4 is the 210 named heads on printed pages 229–235 that PR
**#670** recovered, kept as the source record `census_1840_chicago_v4_research` and as the
calibration set `data/research/census_1840/crosswalk_670.json` compares every new reading
against. The T-0504 package is the rebuild, and it is named by ticket rather than by a
version number precisely so that nobody has to guess which version they are holding.

The three older files are the owner's own hand work and are **preserved as deposited**. The
T-0504 package is **generated** by `chicago/4d/tools/census_1840_fingerprint.py --build` and
gated by `--check` in `chicago/4d/tools/check.sh`, so a hand edit is refused and a stale
package fails the gate the moment a page reading moves under it.

## The fingerprint method, in one paragraph

The 1840 left sheet carries twenty-six free-white age-band columns, thirteen male and
thirteen female. A read line's twenty-six numbers are its **fingerprint**, and are compared
against the same twenty-six household variables in the IPUMS extract; a line whose pattern
exactly one household carries is `unique` and takes that household's SERIAL, a pattern
several households carry is `ambiguous(n)` and takes none, and a pattern nobody carries — or
a line with no band-level cells — is `none`. A column counts toward the comparison only where
the page's own reading **closes against the enumerator's printed foot total**, and a page
that closes fewer than twenty of its twenty-six is not fingerprinted at all; `columns_compared`
on every row says how many survived. A SERIAL is attached to at most one line, so where one
serial is the sole match for two lines neither keeps it and both read `none`, naming each
other. Block continuity — IPUMS numbers households in enumeration order, so an ambiguous
line's candidates can be ranked by which continues the run of its resolved neighbours — is
**recorded and never spent**: it is written into the row as a lead for a reader, and does not
change a confidence. And the ceiling is the first thing to understand about the method: **531
of the 964 households have a globally distinct fingerprint and the other 433 do not**, so no
reading of the age bands, however perfect, will ever separate them. Naming those needs a
second axis — the directories, the poll books, the church registers — not a better read of
the same columns.

## Nothing in here reaches the site

The deposit and its derivatives are repository-only. Two gates hold that:

- `tools/check.sh` → step **“the newspaper corpus resolves, and nothing under `data/research/`
  is published”** (`python3 tools/newspaper_corpus.py --check`) — the absolute assertion that
  no file under `chicago/4d/data/research/` appears in the published mirror.
- `tools/publish.sh` copies a named payload to `site/chicago/4d/`; neither
  `chicago/reference/` nor `chicago/4d/data/research/` is in it, and
  `tools/check_published.mjs` re-derives the mirror from its source, so an extra file in the
  mirror is a red gate rather than a silent publication.

## Related

- [`chicago/4d/data/research/census_1840/README.md`](../../4d/data/research/census_1840/README.md) — the reading rules, the per-page files, and the #670 reconciliation.
- [`chicago/4d/docs/RESEARCH/census-and-civic-evidence-2026-09.md`](../../4d/docs/RESEARCH/census-and-civic-evidence-2026-09.md) — the dossier over the whole census-and-civic sweep, of which this is one domain.
- [`chicago/4d/docs/RESEARCH/household-composition-1840-calibration.md`](../../4d/docs/RESEARCH/household-composition-1840-calibration.md) — what the 1840 composition may be used for.
- [`chicago/reference/resident-research/README.md`](../resident-research/README.md) — the cohort research packages and the programme audit.
