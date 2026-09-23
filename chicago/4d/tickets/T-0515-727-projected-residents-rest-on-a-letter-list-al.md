---
id: T-0515
title: 727 projected residents rest on a letter list alone: regrade every one a second source corroborates and attach its evidence
state: done
epic: TOWN
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-02
closed: 2026-09-04
pr: 797
claimed_by: run 9/4/2026, 11:55:31 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-04T17:59:44.559Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33897541903
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

**The finding.** 727 of the 848 residents carry `letter_list_only: true` and 706 are `projected_resident`
— a name the post office printed once, and nothing else. The sweep changes that for many of them: a
voter-list appearance, a baptism, a directory line, an 1840 head, a Hubbard sentence. Under the ladder
a letter-list name with one of those leaves `projected_resident` (grade stays `inferred`) and with two
contemporary sources becomes `attested`. Conversely, nothing may be graded DOWN without a recorded
refusal. **T-0513**'s `grading_proposal.json` lists every proposed change with its rule; this ticket
applies them to the people who already exist.

**The ask.**

1. `tools/mint_civic_residents.py --regrade` (the same tool as **T-0514**, second mode): for every
   existing person with a proposed change — set `grade` / `resident_subtype` per the rule, attach the
   evidence blocks (`civic_evidence[]`, `census_evidence[]`, `church_evidence[]`, `book_evidence[]`,
   `directory_evidence[]`), extend `sources[]`, and write the rule id and date into
   `resident_research` (`regraded_on`, `rule`, `refusals[]`).
2. 1840 links: extend `data/research/residents/census_1840_identity_bridges.csv` from **T-0505**'s
   proposed `later_census` blocks and apply them through `tools/apply_census_1840_bridges.py`, keeping
   its rule — a bridge needs an adjudicated discriminator; composition is never back-projected.
3. Regenerate `index.json` counts, `town_census.json`, the mirror; a changelog entry; `check.sh`
   green.
4. `--report` prints every regrade with its rule and every refusal (a proposal the evidence rows do not
   support, a downgrade with no refusal recorded, a common-name bridge).

**Dependency:** T-0514 must be `done` (it owns the tool and the validator changes). If it is open,
work it instead.

**Runner notes (2026-09-03):** the improve runner's custom lane now installs `pdftotext` and
`pdftoppm` (poppler-utils), `tesseract`, `openpyxl` and `pypdf` before the run (polecat-platform
`steward-improve.yml`, on the owner's instruction the same day), and the gate installs `openpyxl` and
`pypdf` beside `jsonschema` and `pyproj`. Check with `command -v pdftotext tesseract` and
`python3 -c 'import openpyxl'` first — a failed install is a `::warning` in the step log, not a
surprise — and if one is missing, fall back to `pypdf` and page reads. Write CSV always and XLSX
when openpyxl imports. Never disable TLS or unset HTTPS_PROXY.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- Regraded count with the rule that fired for each; projected / inferred / attested counts before and
  after; `census_1840_linked` before and after.
- No grade lowered without a refusal recorded on the person; no `later_census` block without a bridge
  row; `apply_census_1840_bridges.py --check` green.
- `check.sh` green; mirror published; changelog stamped.

**Links:** T-0513 · T-0514 · T-0505 · PR #670 · L214 · T-0517.
