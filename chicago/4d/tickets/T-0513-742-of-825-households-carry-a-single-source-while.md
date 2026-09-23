---
id: T-0513
title: 742 of 825 households carry a single source while the crosswalks have ruled more: consolidate the closed rulings onto the cards, and again every few sources
state: done
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-02
closed: 2026-09-03
pr: 732
claimed_by: run 9/3/2026, 4:29:32 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-03T22:01:26.317Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33807940502
---

**The owner's ask, 2026-09-03, verbatim:** "And then create a final ticket that does a review and
consolidation of that research."

**REOPENED AS A REPEATING PASS — the owner's instruction of 2026-09-03 (evening), verbatim:**
"right as long as you are capturing the data and then you can have or make sure there is consolidation
tickets that build out the full cross source corroboration of these people, like if you have found and
matched philo carpenter from those multiple sources, you should have all of those in the resident data
for him eventually, dont land those tickets at the very end maybe every few you should do that
consolidation".

**Why the shape had to change, and it is the whole reason this ticket had not moved.** This ticket
carried a bar in QUEUE.md — *"do not take it while any sweep ticket is open"* — written when wave 1
looked finite. It is not: wave 1 is OPEN-ENDED, every source the owner adds lands at its top, and
31 tickets stood ahead of this one and climbing. A gate that opens only when no sweep is open never
opens, and T-0514/T-0515 — the tickets that actually WRITE the people — sat behind it. Consolidation
was permanently one sweep away.

**So the bar is lifted and the ticket is INCREMENTAL.** It consolidates what is CLOSED, and it runs
again. It does not wait for the corpus to be finished, because the corpus is never finished.

**THE SCALE OF IT, and it is not one man.** Counted across the whole residents layer:

| distinct sources cited | household records |
|---|---|
| 1 | **742** |
| 2 | 70 |
| 3 | 13 |
| **total** | **825** |

**Ninety per cent of the town's households rest on a single source, and no record anywhere cites more
than three.** That is the defect. It is not that one card is thin; it is that corroboration is
almost entirely absent from the layer a visitor reads, while the crosswalks that would supply it sit
in `data/research/` holding rulings nobody has spent. The second hop of
`tools/measure_research_spend.py` puts the other end of the same fact at 109 rulings reaching a town
person and 0 reaching that person's card.

**The case the owner named, as the worked example.** `hh_carpenter_philo.json` carries ONE source on
Philo Carpenter — `andreas_1884_v1`. The crosswalks have already ruled six or more for the same man:
`poll_1833_006`, `tax_1833_012`, `poll_1834_023`, the newspaper person `person_philo_carpenter`, and
two bridge-candidate tiers at "VERY LIKELY 1835". The slot exists (`persons[].sources`), the evidence
exists and is adjudicated, and the two have never been introduced. That is what a pass delivers: a
resident's card carrying every source the project has ruled for that person.

**The cadence.** A consolidation pass runs after every few source tickets, not at the end — see the
band this ticket sits in in QUEUE.md. Each pass takes the rulings closed since the last one and spends
them onto cards. A pass that finds nothing new closed says so and costs a run nothing.

**The finding.** By the time the sweep above lands, the same men and women will be named in up to ten
places — the residents layer (848), the newspaper gazetteer (2,630 persons), the four voter lists (346
entries), the 1830 schedule, the 1840 heads (up to 964), the baptismal register, Fergus 26–29, Hubbard,
the 1839 directory, and fifteen cohort findings ledgers — and every one of those domains declares its
own merges and refusals against the residents layer, not against each other. Nothing says, for one
identity, everything the project knows. The newspapers solved this for themselves with `identity.json`
("the ONLY place two differently-spelled names may become one person"); this ticket does it across
domains, and it is where the grading ladder is APPLIED as a proposal — not yet to the records.

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

**The ask.**

1. `tools/consolidate_resident_evidence.py --build | --check | --self-test` →
   `data/research/residents/identity_master.json`: one row per identity, listing every domain
   appearance (domain, record id, `as_read`, `normalized`, locator, describes_date), the declared
   cross-domain merges (rule id, discriminator, evidence) and refusals (rule id, why — surname-only
   is always a refusal; same surname different forename initial NEVER merges, the newspapers' rule),
   and the canonical person id where one exists. Rules carry ids so a later reader can count which
   fired.
2. `data/research/residents/source_coverage.json`: per domain — names read, matched, candidate,
   unmatched, negative searches recorded — and the overlap matrix between domains.
3. `docs/RESEARCH/resident-grading-policy.md`: the ratified ladder verbatim with its date, one rule id
   per rung (G1…), the evidence types each rung accepts, and worked examples from the master; the
   place a later run reads before grading anyone.
4. `data/research/residents/grading_proposal.json`: for every identity, the proposed `grade`,
   `resident_subtype`, the rule that fired and the evidence rows it fired on; for every existing person,
   the proposed change (or none) with the rule; conflicts (two rules disagreeing) listed for the owner
   rather than resolved silently. NOT applied — **T-0514** mints and **T-0515** regrades from this file.
5. A review section in the same doc: what each source turned out to be worth, which domains
   disagree with which, and the gaps that remain — the "review" half of the owner's ask.
6. `check.sh` steps for `--check` and `--self-test`.

**Dependencies:** this ticket consumes T-0493–T-0512. If any of them is still open, work that instead
— `blocked_on` carries one id, so CHECK THE LEDGER; a consolidation run before its inputs land is a
consolidation run twice.

**Runner notes (2026-09-03):** the improve runner's custom lane now installs `pdftotext` and
`pdftoppm` (poppler-utils), `tesseract`, `openpyxl` and `pypdf` before the run (polecat-platform
`steward-improve.yml`, on the owner's instruction the same day), and the gate installs `openpyxl` and
`pypdf` beside `jsonschema` and `pyproj`. Check with `command -v pdftotext tesseract` and
`python3 -c 'import openpyxl'` first — a failed install is a `::warning` in the step log, not a
surprise — and if one is missing, fall back to `pypdf` and page reads. Write CSV always and XLSX
when openpyxl imports. Never disable TLS or unset HTTPS_PROXY.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- Every named identity in every landed domain has exactly one master row or a recorded refusal; zero
  unresolved duplicates without a refusal.
- Proposed counts by grade and subtype stated against the #668 baseline (117 attested / 731 inferred /
  706 projected / 848 persons); conflicts listed.
- The policy doc carries the ladder verbatim with rule ids; `--self-test` fires on a surname-only
  merge, a rule with no evidence, an identity in two rows, and a grade above what its rule allows.
- No household file is changed here.

**Links:** `data/research/newspapers/identity.json` (the model) · `source_hierarchy.json` · T-0487
(the first adjudication) · T-0514 · T-0515 · T-0517.

**Inputs added 2026-09-03 (afternoon), on the owner's instruction:** T-0554 (the Old Settlers' receptions), T-0555 (Norris's 1844 directory), T-0556 (Genealogy Trails Cook County, and its split pieces) T-0557 (the Illinois land-sales database) and T-0562 (the Newberry Genealogical Index on the Internet Archive). Do not take this ticket while any of them, or their pieces, is open.
