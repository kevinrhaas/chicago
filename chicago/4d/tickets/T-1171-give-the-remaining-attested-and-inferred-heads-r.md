---
id: T-1171
title: Give the remaining attested and inferred heads reconstructed families from the household model: wives, children, servants and apprentices drawn by the head's age, trade and household type, seeded, named from the pools, every member marked reconstructed
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

After T-1170, most of the 1,263 heads still stand alone — a letter-list name with a
sex and an age band and nothing else. The owner: *"make sure that family compositions included
children are complete."* Stage `families_model` of T-1167: the household model
(T-1163) is applied to every head that has no source-named family, deterministically.

**Rules:** the head's bucket (age band, trade, division, presence) → household type drawn from
the model's shares; married → a wife (age from the spacing rule, a pool forename, the head's
surname), children by marriage duration and the spacing rule (none born after 1835-07-01), a
servant/domestic where the type has one, an apprentice/journeyman where the trade's shop
household has one (agreed with T-1183); single → alone, or boarding (the type says which,
and T-1175 seats him). `presence` of members follows the head's. Every member: `grade:
reconstructed`, `name_basis`, `basis` (the model row), `seed`, `replaceable_by` ("a source naming
this head's family").

**Order-book discipline:** the tool fills the order book's person buckets (sex × age × division)
as it draws and refuses to overfill one — so the drawn town matches the population model in the
aggregate, not just per household.

**Acceptance:**

- Every head has a household type and the members it implies; the resulting person count,
  sex ratio (target ~147 men per 100 women aged 20+, from 1840, corrected by the model), age
  pyramid and household-size distribution printed against the model, all within the model's
  brackets; the order book buckets read filled to their `to_reconstruct` and not beyond.
- Deterministic: two builds are byte-identical; `--check` in `check.sh`.
- LIBERTIES entry for the whole reconstructed population, `Scope:` counted.
- Visible: the People view's reconstructed filter shows them; the household card shows the family
  with each member's tier and the rule that drew them; the "Reconstructing the town" card's
  person bars move.

**Stop condition:** the town's households look like the model's town in every printed table.

**Links:** T-1167 · T-1163 · T-1161 · T-1166 · T-1170.
