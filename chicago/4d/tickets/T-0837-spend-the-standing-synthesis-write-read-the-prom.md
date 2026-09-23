---
id: T-0837
title: Spend the standing synthesis write: read the promotions it proposes and land them deliberately
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-0814
opened: 2026-09-05
closed: 2026-09-06
pr: 970
claimed_by: run 9/6/2026, 1:34:27 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-06T07:23:19.897Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34016717936
---

Spend the standing synthesis write: read the promotions it proposes and land them deliberately.

Piece 2 of 2 of **T-0814 — The synthesizer's write has drifted hundreds of household cards away from the repository and --check cannot see it, so T-0509's eight corroborations never reach a card**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

The 271 files the writer stands from the tree are landed or refused, each promotion named
and drawn from a source that says it, and `synthesis_drift_baseline.json` shrinks by
exactly what lands, in the same commit.

## The reading T-0838 did, and why it did not land the spend

T-0838 built the gate and then read what the standing write proposes. **It should not be
run and committed as it stands.** Three findings, all measured on `dev` at 4ab5b39cf:

**1. A promotion contradicts its own cited source.** The ledger row for `chapman_chas_h`
(`data/research/residents/synthesis_2026_09_02.json`) reads `occupation=printer` with
`source_ids: ["fergus_chicago_directory_1839"]`. Fergus 1839 prints
`"Chapman, Charles II., real estate dealer, Randolph street"` —
`data/research/directories/fergus_1839_crosswalk_1835.json`, and the card's own
`directories.people[].occupation_later` already carries that value from that source.
"printer" occurs in the **1843** crosswalk, not the 1839 one. Running the write lands
`occupation.value: "printer"`, `confidence: "attested"`, cited to a volume that says
something else. **Fix the ledger row before any spend; nothing else here is safe to land
around it.**

**2. Two of the three promotions back-project a later trade into the 1835 field.** All
three canonical promotions in the whole 271 are occupations, and each moves
`none_recorded` / `reconstructed` to a trade at `attested`:

| person | to | drawn from |
|---|---|---|
| `bailey_bennet` | carpenter | Fergus 1839, Norris 1843 |
| `chapman_chas_h` | printer *(see 1)* | "Fergus 1839" |
| `tuller_elam` | farmer | Whiteside County biography |

`bailey_bennet` and `chapman_chas_h` are the exact case T-0693 wrote a `later_occupation`
pointer for, and the write **deletes that pointer**, along with the note that says why:
"the 1835 occupation above still reads `none_recorded` … because a directory of 1839 is
evidence about 1839". The parent's ask 3 is the same rule from the other side. A trade
printed in 1839, 1843 or a county history is not an 1835 occupation at `attested`.

**3. The spend is a net DEMOTION, and an unruled one.** Across the 132 authored cards the
write moves 18 grades: **3 up (inferred → attested) and 15 down (attested → inferred)**.
The fifteen are people the ratified ladder graded, so running this tool reverts rulings
that T-0515 and T-0699 made — which is [[T-0822]]'s finding at a different count (it says
seventeen), reached independently here. **T-0822 has to settle before this spends**, or
the spend silently overrules the ladder.

Everything else in the 271 is `resident_research` block content — `summary`, `source_ids`,
`resident_subtype`, `reviewed_on`, and the note prefixes — which is the cohort work that
is genuinely standing and genuinely wants landing, once 1–3 are settled.

**Links:** T-0814 (parent) · T-0838 (the gate) · T-0822 (the demotions) · T-0693 (the
later-trade pointer this would delete) · T-0509 · T-0513 · T-0515 · T-0699.
