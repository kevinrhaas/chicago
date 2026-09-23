---
id: T-1158
title: Per-attribute tiers on every person, household and business field — attested, inferred or reconstructed, each with its reason — so a profile can be filled at the lowest honest tier and replaced later
state: done
epic: META
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-09-16
closed: 2026-09-17
pr: 1426
claimed_by: run 9/17/2026, 7:44:21 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-18T01:36:27.093Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35292169604
---

The owner, 2026-09-17: *"note for each attribute of each person what is attested, inferred or
reconstructed and reasons why."* Today the grade is carried per PERSON (`grade`, ladder rung) and
per structure attribute (`confidence` blocks on structures), but a person's sex, birth year,
arrival, origin, relationship and roles do not each say which tier THEY stand on. T-1146 adds
per-value provenance for asserted facts; this ticket makes the third tier — `reconstructed` —
a first-class per-attribute value with a required `basis`, so the analysis and reconstruction
bands can fill every attribute honestly and a later source can replace one value without
touching the rest.

**One collision to resolve first.** Household claim blocks (`arrival`, `origin`,
`reason_for_coming`, `lives_at`, `works_at`, `party_size_on_arrival`, `occupation`) already use
`confidence: "reconstructed"` — 7,383 times — to mean *not attested*, almost always with `value:
null` ("Not attested."). That is the opposite of what the tier will mean once a value is actually
invented. The migration below reads a null-valued `reconstructed` block as `tier: unknown` (a new
value that means "nothing is asserted yet") and reserves `reconstructed` for a non-null value
carrying `basis` and `seed`; `audit_confidence.py --strict` and `validate.py` refuse the old
ambiguity after the migration, and the renderer prints "not recorded" for `unknown`.

**The model (additive — no existing field moves; validators accept the old shape until the
migration below runs):**

- Every scalar person attribute that reconstruction will touch — `sex`, `birth_year` (with
  `precision`), `arrival` (date + precision + `reason`), `origin`, `relationship`,
  `presence`, `division`, `community` (the vocabulary T-1177 defines), each `roles[]` entry, `lives_at[]`/`works_at[]` entries, `name` (for
  a reconstructed name) — becomes `{ value, tier: attested|inferred|reconstructed, basis,
  source_id?, claim_id?, model_id?, seed? }`. `attested` requires `source_id`; `inferred`
  requires a `basis` naming the evidence about THIS person; `reconstructed` requires `basis`
  naming the MODEL row it was drawn from (`data/reconstruction/1835_population_model.json` etc.
  once T-1161 lands — until then a stated rule) and the deterministic `seed`.
- Household and business records take the same shape on `composition`, `type`, `capacity`,
  `staff[]`, `proprietors[]`, `location`.
- A record-level `grade` stays, derived: the HIGHEST tier of its identity (name + presence)
  assertions, never above `reconstructed` when the name is invented (`tools/validate.py` already
  refuses an invented name above the bottom tier — keep that rule and extend it).
- `replaceable_by: { kind: person|household|business, match: <rule> }` on every reconstructed
  record and attribute: what evidence would retire it (the owner: *"so if we get new research …
  we can replace the reconstructed person or business with an inferred or attested one later"*).

**Acceptance:**

- Schema (`data/residents/`, the business schema, `data/structures.schema.json` occupant links)
  extended; `tools/validate.py` refuses a tier without its required fields and a `reconstructed`
  value with no `basis`/`seed`; a mutation self-test in `check.sh` breaks each rule.
- Migration tool `tools/migrate_attribute_tiers.py --build|--check` lifts every existing value
  into the shape at the tier its current provenance supports (attested source → attested;
  `inferred` note → inferred), with a report of counts per attribute per tier. Zero value changes
  tier upward; the check is wired.
- The evidence panel (`renderers/web/js/` people card) prints the tier beside each attribute and
  the basis on hover/expand, and the People view gains a filter `attested / inferred /
  reconstructed` that reads the derived record grade. This is the visible half of the ticket.
- `summarize_residents.py` (and the town census) gain a per-attribute tier section.
- `docs/PROVENANCE.md` documents the per-attribute shape and the replaceability rule.

**Stop condition:** every person/household/business attribute the reconstruction bands will
write has a place to say its tier and why, and a reconstructed value cannot be written without
a basis and a seed.

**Links:** T-1145 · T-1146 · T-1147 · AGENTS.md § RECONSTRUCTED IS A TIER · `docs/PROVENANCE.md`.

## WHAT SHIPPED, AND THE ONE CLAUSE THAT DID NOT (2026-09-18)

The tier vocabulary, the collision's resolution, the contract, the gate, the report, the
card and the docs all landed. **The clause that did not is "written into the card", and
the reason is worth keeping.**

Writing `tier` into all 1,258 household records was tried first and measured: ten of
`check.sh`'s steps go red the moment a tier lands in a card, because those bytes are
owned by NINE derivations that each rebuild a card from its sources and compare the
result — `synthesize_resident_research.py --drift`, the four mints, both
back-projections, `qualify_later_trades.py`, `survey_stated_kin.py` and the four
directory crosswalks. None of them knows the field exists, so every one of them drops
it on the next pass. A field nine writers silently drop is a field that lies.

So the EXISTING layer's tiers are derived — in `tools/migrate_attribute_tiers.py` for
the gate and the published table, in `renderers/web/js/attribute-tiers.js` for the card
a visitor opens, with `tools/check_attribute_tiers.mjs` holding the two to one answer.
What a RECORD may carry is the full shape, enforced by `validate.py` wherever it appears,
so the reconstruction bands from T-1167 write tiers on the records they mint from day one
and are refused if they write one wrong. **Teaching the nine writers to emit the tier
belongs with T-1144**, which already owns that layer's drift and has to re-run all three
writers anyway; doing it here would have meant landing nine writer changes and 1,258
rewritten cards inside a ticket about a vocabulary.

Clause by clause:

- Schema + `validate.py` refusals + a mutation self-test breaking each rule — **done**
  (`check_tier_block`, 29 self-test cases, wired into `check.sh` twice).
- The migration tool with a report of counts per attribute per tier, and zero value
  changing tier upward — **done**; the tier is derived from the block's own confidence,
  so it cannot exceed it, and `validate.py` refuses a written tier that disagrees.
- Tier beside each attribute on the card, and the basis on expand — **done**. The forty
  reconstructed values' basis and replacement rule are published in the derived table and
  rendered structurally by `basisHtml` on any record that carries them; on today's forty
  the basis is also the block's own note, which the card already prints in full.
- The People view's `attested / inferred / reconstructed` filter on the derived record
  grade — **already existed** (`people.js`, the `grade` pill row). What it lacked was the
  per-attribute reading, which is what shipped.
- `summarize_residents.py` per-attribute tier section — **done** (`tiers`).
- `docs/PROVENANCE.md` — **done**, including the disambiguation the project now needs:
  a SOURCE carries a numbered tier (the 1-6 evidence ladder), an ATTRIBUTE carries a
  named one, and nothing reads both off the same field.

The town census gained no tier section: it counts people and roofs, not attributes, and
the per-attribute table is a research artefact. Stated rather than quietly skipped.
