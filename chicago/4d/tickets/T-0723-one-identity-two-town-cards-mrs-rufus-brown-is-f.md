---
id: T-0723
title: One identity, two town cards: Mrs Rufus Brown is folded onto her husband by the honorific strip, and N. R. Norton is Nelson R. Norton carried twice
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-06
pr: 998
claimed_by: run 9/6/2026, 12:56:09 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-06T18:42:04.090Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34049511702
---
**Found by T-0692's coverage pass, 2026-09-04.** Two identities in `identity_master.json`
absorb TWO town cards each, and `canonical_person_id` is `town[0]`, so the second card gets
no proposal row at all — the ladder ruled the identity and the ruling was never offered to
the card. T-0692 added `town_person_ids` so the absorption is visible; it did not resolve
either case, because they are two different faults with two different answers.

**`brown_mrs_rufus` — "Mrs Rufus Brown" — is folded onto `brown_rufus`, and she is not her
husband.** `Mrs` is stripped as an honorific, which leaves `Rufus Brown` on both readings,
so the merge is M1-identical and wrong. A woman whose only printed name is her husband's is
a real and common shape in this corpus, and the splitter has no way to hold her apart today.
The fix is a rule, not a one-off: a name whose forename tokens are entirely the husband's,
carrying a female honorific, is a DIFFERENT person and must never merge.

**`norton_n_r` and `norton_nelson_r` are two cards for one man.** Here the merge is right —
M2 attaches the initial-only reading to the one full forename of that surname — and the
defect is upstream: the town carries Nelson R. Norton twice. That is a reconciliation of two
household records, not a splitter change.

**Acceptance:** the honorific case is held apart by a stated rule with a self-test that
fires when it is broken, and `Mrs Rufus Brown` gets a ladder rung of her own; the Norton
duplicate is reconciled into one card or the two are shown to be two men with the evidence
that says so; `--coverage` reports no person in state `absorbed_by_another_card`; and no
person is deleted without the merge being recorded where a reader of either card can see it.
