---
id: T-0492
title: The research pattern exists for the newspapers only, and six new source domains have nowhere to land
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-02
closed: 2026-09-03
pr: 685
claimed_by: run 9/3/2026, 3:00:56 AM CT
blocked_on: null
needs_bake: false
---

**The owner's ask, 2026-09-03, recorded verbatim:** "create tickets to do more resident research
transcription and analysis or extract find public sources or APIs to read and find data from the
following reference materials, you should see them all in GitHub — Voter Roll; Census 1830 and 1840;
Fergus; Swift walker; Hh porter. And then create a final ticket that does a review and consolidation of
that research." 

**The finding.** The project has exactly one research pipeline — the newspapers' — and it is good:
a register that says where a passage IS, hand-authored claims that say what was read out of it, a closed
kind vocabulary, a required reading grade, verbatim quotes the gate rebuilds, a coverage declaration, an
identity layer that declares refusals as carefully as merges, and a `--check`/`--self-test` pair per
layer in `tools/check.sh`. Six new source domains are about to be read in parallel — civic lists, the
1830 census, the 1840 census, a church register, books and directories — and if each of the ten runs
invents its own file shape, the consolidation (**T-0513**) will spend its run re-reading ten dialects.
This ticket gives the domains one home and one gate BEFORE the sweep starts.

**The ask.**

1. `data/research/{civic,census_1830,census_1840,church,books,directories}/README.md` — each a page,
   in the voice of `data/research/newspapers/README.md`: what lives here, what is generated, what is
   hand-authored, and "this is research, not payload".
2. `tools/research_domains.py --build | --check | --self-test` — the shared schema and gate:
   - **records files** (`records[]`: `id`, `as_read`, `normalized`, `locator`, `reading`, `confidence`,
     `notes`) for list-shaped sources (voter lists, census lines, baptism entries, directory entries);
   - **claims files** (`claims[]`: `id`, `kind`, `reading`, `quote`, `normalized`, `locator`,
     `describes_date`, `entities[]`, `town_finding: bool`, `notes`) for prose sources (books);
   - `KINDS` = the newspaper kinds (`person, business, building, street, infrastructure, event, shipping,
     price, notice`) plus `landscape`, `appearance`, `household`, `civic` — CLOSED, with the same comment
     `compile_gazetteer.py` carries about why an open vocabulary becomes a synonym list within a week;
   - `READINGS` = `transcription_mediated | scan_verified`, REQUIRED;
   - a verbatim-quote gate for `books`/`directories` that reassembles every `quote` from the domain's
     committed `text/` file and fails on a one-character difference;
   - `coverage.json` per domain (declared list names, image ids or page ranges; an undeclared item is not
     read yet and is not a fault; a declared range with a hole IS);
   - `crosswalk.json` per domain in the `identity.json` shape — `merges[]` and `refusals[]`, each with
     `rule`, `evidence[]`, both names verbatim; surname-only is always a refusal;
   - `--self-test` breaks each assertion and proves it fires.
3. One `step` in `tools/check.sh` beside the synthesis step, with its prose comment, plus the
   `…and its own assertions still fire when broken` pair.
4. **Cohorts 13–15 fixed now**, so **T-0508**–**T-0510** do not all edit `check.sh` at once:
   `tools/select_resident_research_pass_13.py`, `_14.py`, `_15.py` with `--gate`, following
   `select_resident_research_pass_5.py`, selecting deterministically from the 237 named people with no
   research row (the `letter_list_missing_research_row` list `tools/synthesize_resident_research.py`
   emits plus the unresearched remainder of the 848) into three non-overlapping cohorts of 79 (79/79/79),
   written to `data/research/residents/pass_13_79_cohort.json` etc., each with a pending findings ledger
   and a `docs/RESEARCH/resident-research-pass-1N.md` note in the shape of pass 12's; three `check.sh`
   steps beside the existing cohort gates.

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

- Six domain READMEs exist and say what is hand-authored and what is generated.
- `python3 tools/research_domains.py --self-test` fires at least eight assertions when broken: an unknown
  kind, a missing reading, a quote that differs by one character, a coverage hole, a merge with no rule,
  a refusal naming only one spelling, a surname-only merge, a claim citing a source id that does not
  resolve.
- The three cohort files sum to 237 person ids with zero overlap among themselves and zero overlap with
  passes 1–12; each `--gate` is green and wired into `check.sh`.
- `bash tools/check.sh` is green (after **T-0491**; if dev is still red on T-0491's three faults, work
  T-0491 first).
- No claim data is authored here — the scaffold is empty on purpose.

**Links:** T-0257 (the extraction schema) · T-0299 / T-0397 (identity passes and refusals) · T-0262 (the
coverage declaration) · T-0486 / T-0487 (the research-row contract) · `chicago/reference/resident-research/README.md`
(the package contract) · T-0493–T-0507 (the sweep this unblocks).

---

**LANDED 2026-09-03.** Built and verified on `steward/t-0492-research-domains-scaffold`
(PR #680), which parked on `hold` because `dev` was red on T-0491's faults at the time and
a run does not launder an inherited red into `dev`. T-0491 merged (#682); this branch is
that work rebased onto the green `dev`, with two integration corrections the rebase forced:

- `data/research/census_1840/` is no longer empty — T-0495's read landed on `dev` in the
  meantime with its own `README.md` and a `coverage.json` in an `images[]` shape. Both of
  `dev`'s files are kept verbatim; the scaffold contributes only the domain's missing
  `crosswalk.json` and its `claims/`, `records/` and `text/` homes. That domain's coverage
  therefore declares nothing to the shared gate yet, which the ratified contract permits
  ("an undeclared item is not read yet and is not a fault") — migrating it is **T-0536**.
- the `T-0523` ticket file the parked branch carried reached `dev` on its own, so it is not
  duplicated here.

**Two measured corrections to the ask, carried in the code, the manifests and
`docs/RESEARCH/resident-research-pass-13.md`:**

- the frame is **228** named residents with no research row, not 237 (238 records
  carry no research block, less 5 unnamed placeholders and 5 real named people in
  `inf_*`/`hh_inf_*` records), so the cohorts are **76/76/76** and the files are
  named for what they hold;
- **225 of the 228 are the pilot, pass 2 and pass 3 cohorts** — reserved and never
  researched (T-0511 from the other side). "Zero overlap with passes 1-12" is
  therefore unmeetable as written: the population satisfying it is three people.
  The selector enforces zero overlap among 13/14/15 and zero overlap with the 611
  people who already hold a research row, which is the non-overlap that carries
  the meaning.

The five `inf_*` people are **T-0523**.
