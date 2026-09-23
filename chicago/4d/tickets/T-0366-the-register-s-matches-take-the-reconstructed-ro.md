---
id: T-0366
title: The register's matches take the reconstructed roofs, where the papers place the man nowhere
state: done
epic: PAPERS
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0264
opened: 2026-08-29
closed: 2026-08-29
pr: 518
claimed_by: null
blocked_on: null
needs_bake: false
---

Piece 1 of 3 of **T-0264 — Documented people replace the invented**, split because
the parent needed more than one run's demonstration to be done. The parent keeps the
full ask and its links; this ticket owns the REPLACEMENT half, and only the part of it
the evidence can carry without contradicting itself.

`data/research/newspapers/register_1835.json` lists, per trade, the documented people
the papers put in Chicago against the households the town INVENTED for want of one.
This piece spends that list where spending it is safe: on the men the papers name and
place NOWHERE IN PARTICULAR. For them a reconstructed dwelling is not a contradiction,
it is the only answer any source permits. A man the papers put at a street or a named
house is T-0367's, not this ticket's.

**Acceptance:** (one demonstration, never weakened to pass)

- A derivation, not a list: a tool re-derives the deal on every commit from the
  register and the committed town, and `check.sh` fails if the tree stops matching it.
- Every refusal is printed with its reason, so the ratio of taken to refused is
  auditable rather than asserted.
- Each replaced person's card carries the newspaper citation, the trade as the paper
  sets it, and a dated bound; the invented name and its `name_basis` are retired.
- The person's grade rises to `inferred` and NOT to `attested`: the man is documented,
  the dwelling is not, and the household says so in its own words.
- The other invented residents keep their names — retiring a roof must not re-deal
  anybody else's.
- The invented-person count falls, stated before → after; docs/LIBERTIES.md owns the
  placement; check.sh green; a changelog entry a visitor can check against a card.

**Done 2026-08-29.** Five roofs retired (cooper, joiner, physician, tailor, tavern
keeper), 66 candidates refused with reasons, `tools/replace_invented_residents.py` and
its gate. `data/residents/index.json` by_grade reconstructed 113 → 108, inferred
20 → 25. L205 records the liberty.
