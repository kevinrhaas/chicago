---
id: T-1375
title: The community attribute across the resident layer: the closed vocabulary, a tiered community on every person and household derived from the evidence the layer already holds, the People view's community filter, and the shares table printed against the town model
state: done
epic: META
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1177
opened: 2026-09-19
closed: 2026-09-19
pr: 1507
claimed_by: run 9/19/2026, 1:51:01 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-19T08:27:31.589Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35427481265
---

The community attribute across the resident layer: the closed vocabulary, a tiered community on every person and household derived from the evidence the layer already holds, the People view's community filter, and the shares table printed against the town model.

Piece 1 of 4 of **T-1177 — Reconstruct the under-documented cohorts within their evidence: the Native and Métis people, households and businesses in and around the town, the free Black residents, families and Black-owned businesses, and the Irish and German Catholic town the register implies — every one identified, tiered and reviewable**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance**, stated before working:

- A closed community vocabulary — `potawatomi | ottawa | ojibwe | metis | french_canadian |
  free_black | yankee | new_york | irish | german | british | southern | other | unknown`,
  the parent's own list — committed with a label and a note per value.
- A `community` on EVERY person in the layer and on every household, each carrying the tier
  it stands at and the rule that read it. `unknown` is a value, not an absence: where the
  layer holds no evidence the answer is `unknown` and the count of them is printed.
- Derived and never hand-edited, off fields ALREADY COMMITTED — a household's `origin`
  block, a reconstructed person's own name-pool community — with the tier capped by the
  rule that read it: a place is not a community, so a region reading may not beat
  `inferred` however attested the origin is.
- No source read, nobody minted, no confidence upgraded, no citation invented. The pass's
  own self-test REFUSES to write `potawatomi`, `ottawa`, `ojibwe`, `free_black` or
  `german` — those are readings, and they belong to T-1376, T-1377 and T-1378.
- Coverage is gated: every distinct `origin.value` in `data/residents/` accounted for
  exactly once in the rules file — stated community, region, or explicitly unreadable — so
  a new origin string cannot fall silently into `unknown`. `tools/check.sh` goes red if one
  does.
- Visible: the People view has a Community filter whose pills are the vocabulary's own
  order with their counts, and each list row prints the community it knows.
- The shares table printed against `data/reconstruction/1835_town_model.json` § Arrival and
  origin, saying plainly which part of the distribution is the reconstruction programme's
  own assumptions handed back and which part is evidence.

**Stop condition:** every person in the town answers the question "which community?", at a
tier that says how well, on a filter a visitor can use — and the five empty rows of the
vocabulary are a measured number rather than an absence nobody had counted.

**What shipped.** `data/residents/community_rules.json` (the vocabulary and all 54 origin
strings decided), `tools/derive_person_community.py` (`--check`, `--report`, `--self-test`),
`data/residents/community.json` (2,626 people, 1,864 households), the community row and
counts in `tools/compile_scene.py`'s `people.json`, the Community filter and list-row label
in `renderers/web/js/people.js`, `docs/RESEARCH/community_shares_1835.md`, two gate steps in
`tools/check.sh` and the derivation in `tools/derived_manifest.json`.

**What it measured, for the three tickets that follow.** 2,436 of 2,626 people carry a
community and 190 read `unknown`. `potawatomi`, `ottawa`, `ojibwe`, `free_black` and
`german` stand at zero; `metis` stands at two — Billy Caldwell and Alexander Robinson, and
only because each card's origin sentence states a parentage. Six of the eight
`touches_removal` households read `french_canadian`, `british`, `southern`, `new_york` or
`unknown`. Madore Benjamin Beaubien reads `unknown` on "Chicago — born at the settlement":
the literature gives him a Potawatomi mother and THIS LAYER DOES NOT SAY SO, so the pass
refused to inherit a community down a parentage the record has not written. T-1376 is the
ticket that writes it.
