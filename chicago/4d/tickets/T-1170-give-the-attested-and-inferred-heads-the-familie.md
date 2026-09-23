---
id: T-1170
title: Give the attested and inferred heads the families the sources name: spouses, children, kin and dependants from the baptism and marriage registers, the 1840 census rows of heads the layer carries, Andreas and old-settler biographies and the ruled kin ties — inferred where named, reconstructed where only counted
state: open
epic: META
requested_by: owner
seen: true
effort: M
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

20 households hold more than one person; 27 carry `kin` rows. The sources name far more: St
Mary's baptisms 1833–35 (57 entries, 45 at Chicago, parents and godparents), St Cyr marriages
(the 1834–35 entries), the 1840 census rows already bridged to 27 cards (`spend_census_1840_heads.py`)
with their sex × age bands, Andreas's biographies ("married in 18xx Miss …, by whom he had …"),
the old-settler reminiscences, `kin_rulings.json`. Stage `families_named` of T-1167.

**Rules:**

- A member a source NAMES with a relationship → `inferred` (or `attested` where the ladder
  allows), with the source, relationship, sex and birth bound the source gives; `kin[]` written
  both ways.
- A member a source COUNTS but does not name (an 1840 row's "1 male 5–10", "and family", a
  baptism naming the child but not the siblings) → `reconstructed`: a name from the pools by the
  head's community and surname, a birth year inside the counted band (1840 bands back-projected
  five years; a child under 5 in 1840 born after 1835-07-01 is NOT present), `basis` naming the
  counting row, `seed`.
- The 1840 row is used ONLY where the head is already an 1835 resident (the 27 bridged + any
  T-1159 class R4 the ticket admits); the T-0507 line stands for everyone else.
- A `touches_removal` household gains named members here and counted members through T-1177
  only; every member it gains inherits `review_required` + `touches_removal` with the sentence.

**Acceptance:**

- Every named family member in the four source groups is on a card or in a disposition row
  (`duplicate` / `contradicted` / `later_only` — born after the scene / `insufficient_identity`);
  counts printed; `survey_stated_kin.py --check` green with the new ties.
- Household size distribution before/after printed against the model; no attested/inferred
  member is displaced by a reconstructed one.
- Visible: family members appear on the household card with relationship, tier and the row that
  counted them.

**Stop condition:** no source-named or source-counted family member of an 1835 head is missing.

**Links:** T-1167 · T-1163 · T-1146 · T-0507 · `spend_census_1840_heads.py` ·
`data/research/church/` · `data/residents/kin_rulings.json`.
