---
id: T-1183
title: The 1835 business staffing model: how many clerks, journeymen, apprentices, printers, bar-keepers, hostlers, cooks and teachers each kind of business employed, from the sources the project holds — the rule every business is staffed by
state: open
epic: META
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: null
opened: 2026-09-16
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: null
claimed_run: null
---

Zero of 196 businesses carry a staff member; the residents layer has 5 partners and no clerk,
apprentice, journeyman or servant, though the relationship vocabulary admits all of them. The
owner: *"there may be multiple people who staff a business like a store … or the newspapers and
you will … be reconstructing the staff of the store."* Before anybody is staffed, the RATIO has to
be written down with its evidence, so a reconstructed clerk is a claim about a kind of store and
not about a whim.

**Deliverable** — `data/reconstruction/1835_business_staffing_model.json`, built by
`tools/build_staffing_model_1835.py --build|--check|--self-test`, one row per business type
(the census classes plus the finer trades of the occupation model):

- `staff_roles[]` with `{ role, count_low, count_typical, count_high, sex_rule, age_band,
  lives_on_premises: share, basis, source_ids[] }` — e.g. a dry-goods store: 1–2 clerks (young
  men, often boarding with the merchant or upstairs); a forwarding house: clerks + warehousemen +
  a teamster; a printing office: an editor, 1–2 journeymen printers, an apprentice (the
  *Democrat*'s known hands — Calhoun, the partners, the apprentices Andreas names — are the
  fixture); a tavern/hotel: bar-keeper, hostler, cook, chambermaid(s), a boy; a smithy: the smith
  + a striker/apprentice; a tannery/packing house: hands by season; a school: the teacher
  (+ assistant at the larger); a law office: the attorney + a student-at-law; a physician: alone
  or with a student.
- Evidence: the attested cases in the layer (every business that names a second person), the
  1839 directory's clerks and their employers, the 1840 industry columns, Andreas's biographies
  ("came to Chicago as a clerk for …"), the apprentices the register prints. Where the project
  holds no figure, the row says `basis: period convention, reconstructed` and names the analogue.
- The **shop household rule** shared with T-1163: which staff live with the proprietor.

**Acceptance:**

- Builds, re-derives, `--check` in `check.sh`; `docs/RESEARCH/1835_business_staffing_model.md`
  prints every row with its evidence.
- A dry-run applies the model to the audited business records (T-1182) and prints the staff
  count the town implies, by role and sex, against the occupation model's employment rows — the
  two files must agree or the disagreement is stated and one is corrected.
- No person is written.

**Stop condition:** T-1189 can staff every business from this file and the order book alone.

**Links:** T-1162 · T-1163 · T-1182 · `docs/RESEARCH/chicago_democrat_office.md`.
