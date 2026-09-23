---
id: T-0514
title: About half the voter-list men are in no resident record: mint residents from the consolidated civic, census, church and book evidence
state: done
epic: TOWN
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-02
closed: 2026-09-04
pr: 785
claimed_by: run 9/4/2026, 8:05:50 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-04T15:10:47.692Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33875889978
---

**The owner's ask, 2026-09-03, verbatim:** "Once complete i would like to begin to do and update of the
resident and household data based on all of your deep research, from the sources at hand and any
supporting or related sources you find and identifying as many residents of chicago circa 1835. look at
the tickets and completion of the research that was done for chicago and one research is done do an
update of the residents and households, if there are business and structure information from what you
have you can update that as well, but we will want a sweep through all of the residents you have
defined … and lastly if there is anything from the census records or other research that you think
should be included in terms of residents, please do that" 

**The ratified grading ladder** — the owner's ruling of 2026-09-03, recorded verbatim, binding on every
grade this programme assigns: "attested = 1835 poll + any second independent source, or a contemporary
record naming the person in Chicago; inferred = 1835 poll alone, or 1833/1834 lists with another source,
or baptism parent/godparent 1833–35, or Hubbard/Fergus naming a resident with trade or address;
projected_resident = a single appearance with nothing else; 1839/1840 alone is never a 1835 resident
(later evidence only)." And the owner's tier definitions from the ask, verbatim: "for ones that you are
confident, those will be attested, the ones corroborated, those who you have a source or some potential
sources that you think you are reasonably sure, include all those unasserted as inferred. the balance of
people who you have seen in at least one source, they are documented, but you have some names of and
you dont have much else, you can put those in a sub category of inferred as a projected resident, under
the inferred category so we can filter by attested or inferred." 

**The finding.** Measured on `dev` before the sweep: only 37 of the 85 men on the 1835 poll list have
even a surname in the residents layer; half the voter-list men — Bread, Pixby, Kennicott, Ulrich,
Trowbridge, Alvin Calhoun and the rest — are in no record. The 1830 schedule's households, the
baptismal register's parents and godparents, and the people Hubbard and the Fergus reminiscences put in
Chicago with a trade or an address will be in the same position. **T-0513**'s `grading_proposal.json`
says, per identity, what the ratified ladder makes of them; this ticket writes the people.

**The ask.**

1. `tools/mint_civic_residents.py --build | --check | --self-test`, in the mint precedence AFTER
   `mint_documented_residents` and `mint_placed_residents` and BEFORE `mint_letter_list_residents`
   (each pass skips its own output and every pass below it — `docs/LIBERTIES.md` L213 and the
   docstring of `mint_documented_residents.py` state the rule), reading `grading_proposal.json` and
   minting a household + person for every identity with NO existing record whose proposed grade is
   attested or inferred (projected included): the household's fixed 15 keys, `division: unplaced`,
   `lives_at` / `works_at` null with the note saying why ("the placement sweep assigns homes and
   workplaces once the ~3,600-resident list is complete" — the owner's own sequencing), `arrival` as
   a `not_later_than` bound from the earliest record, `present_on_scene_date` argued per rung; the
   person carrying `grade`, `resident_subtype` where the rule says so, `sources[]`, and evidence
   blocks `civic_evidence[]` (list, as_read, locator), `census_evidence[]` (1830), `church_evidence[]`,
   `book_evidence[]` — each with the rule id that fired.
2. `tools/validate.py check_residents` extended for the new person keys; `index.json` vocabulary and
   counts regenerated; `tools/town_census.py`; a new `docs/LIBERTIES.md` L-number for the civic-evidence
   scale (what is and is not invented — a household container around a name is the same liberty L214
   records for the letter lists); `tools/publish.sh`; a changelog entry (`v: null`, `ts: ''`, `date: ''`,
   then `node tools/stamp-changelog.mjs`); `check.sh` steps for `--check`/`--self-test`.
3. Every refusal printed by `--report`: an identity the proposal grades but the ladder's evidence does
   not reach, an arrival after 1835-07-01, a merge the consolidation refused.
4. Payload: report `du -sh site/chicago/4d/data/residents` before and after (T-0438 already found the
   letter-list cohort is 2.54 MiB of the published tree).

Nothing is minted from an 1839 directory or an 1840 census appearance alone; no reconstructed person is
created (the count stays zero); no figure is drawn (L1).

**Dependency:** T-0513 must be `done`. If it is open, work it instead.

**Runner notes (2026-09-03):** the improve runner's custom lane now installs `pdftotext` and
`pdftoppm` (poppler-utils), `tesseract`, `openpyxl` and `pypdf` before the run (polecat-platform
`steward-improve.yml`, on the owner's instruction the same day), and the gate installs `openpyxl` and
`pypdf` beside `jsonschema` and `pyproj`. Check with `command -v pdftotext tesseract` and
`python3 -c 'import openpyxl'` first — a failed install is a `::warning` in the step log, not a
surprise — and if one is missing, fall back to `pypdf` and page reads. Write CSV always and XLSX
when openpyxl imports. Never disable TLS or unset HTTPS_PROXY.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- Minted counts by source domain and by grade/subtype, before/after against the #668 baseline, in the
  PR; zero arrivals after 1835-07-01; zero persons minted from 1839/1840 alone.
- `--self-test` fires on: a mint with no evidence block, a mint the ladder does not reach, a duplicate
  of an existing person, a later-only source used as a residency source.
- `check.sh` green; `validate.py` green; mirror published; changelog stamped; the liberty recorded;
  the payload delta stated.

**Links:** T-0513 · `tools/mint_letter_list_residents.py` (the precedence and the refusal style) ·
L214 · T-0438 · T-0515 · T-0517.
