---
id: T-0668
title: The 531 civic residents ship a reading a browser never shows: put the evidence blocks on the resident card
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-04
pr: 809
claimed_by: run 9/4/2026, 3:59:08 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-04T21:43:37.383Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33918554084
---

The 531 civic residents ship a reading a browser never shows: put the evidence blocks on the resident card.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)


**THE MEASUREMENT, read out of `tools/measure_layer_reads.py` on dev before any change.**
`residents/household` declares 161 figures and 61 of them reach nothing. Forty-four of those
61 are the consolidation's own reading — the ladder rung it graded a person on and the
appearances it spent to get there:

| banked unread | records |
|---|---|
| `persons[].civic_mint` | 531 |
| `persons[].ladder_rule` | 531 |
| `persons[].press_evidence[]` — 7 leaves | 384 |
| `persons[].civic_evidence[]` — 7 leaves | 221 |
| `persons[].book_evidence[]` — 7 leaves | 167 |
| `persons[].church_evidence[]` — 7 leaves | 37 |
| `persons[].census_evidence[]` — 7 leaves | 20 |
| `persons[].biographical_evidence.*` — 3 leaves | 2 |

Each evidence entry is `{list, as_read, locator, record_id, describes_date, source, rule}` —
a transcribed name, the domain it stands in, where on the page, and the rung that accepted
it. That is an ARGUMENT, and the project's own rule for an argument (T-0491, on the 1840
bridge) is that it is shown whole or it is an assertion. `civic_mint` and `ladder_rule` are
the verdict that argument produced. A reader can only disagree with a grade if they can see
the rung and the lines it was awarded on.

**THE RUNG'S TEXT IS IN PYTHON AND THE READER IS JAVASCRIPT.** `GRADE_RULES` in
`tools/consolidate_resident_evidence.py` is the ratified ladder; nothing under `data/`
carries it, so a card printing `G2c` would print a code with no meaning anywhere a visitor
can reach. The rung text moves into `data/residents/index.json` under
`vocabulary.ladder_rules`, written from `GRADE_RULES` and held equal to it by that tool's
own gated `--check` — one source of truth, not two.

**Acceptance:** (stated before working — the definition of done, never weakened to pass)

- `vocabulary.ladder_rules` in `data/residents/index.json` carries every rung of `GRADE_RULES`
  with its grade and its text, is written by `consolidate_resident_evidence.py
  --write-vocabulary`, and `--check` FAILS if the two ever disagree. The check's own
  `--self-test` proves that failure fires.
- The person card renders, for every person that carries them: the rung and what it says, the
  `civic_mint` fact, and each evidence domain's entries whole — the quoted reading, the list,
  the locator, the record id, the date the line describes, and the source as a citation.
  `biographical_evidence` renders as graded claim rows like every other claim on the card.
- Prose on the card says what the section is and what it is NOT: an appearance is evidence
  about a person, and a later appearance is not an 1835 fact. The `describes_date` is on every
  line for that reason.
- `python3 tools/measure_layer_reads.py --gate` is green with those 44 entries UN-BANKED from
  `tools/layer_reads_baseline.json` in this same commit — the gate holds the bank exact in
  both directions, so this is the demonstration rather than a claim about it.
- `./tools/check.sh` green; the smoke legs `tools/smoke_budget.mjs --for-diff` names, green.
- `tools/publish.sh` run in the same commit, and a changelog entry.
