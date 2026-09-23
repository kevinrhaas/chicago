---
id: T-0374
title: letter_list_only reaches the visitor's card, and the 1,536 names known only from the post office
state: split
epic: PAPERS
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0368
opened: 2026-08-29
closed: 2026-08-29
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
---
Piece 3 of 3 of **T-0368 — The letter lists mint new residents**.

The owner's ruling of 2026-08-28: a name in the post office's list of uncalled-for
letters is enough to make somebody a resident. 1,536 of the register's `new_resident`
people are known ONLY that way, and the parent is emphatic that the two evidence
strengths must stay distinguishable forever — a letter-list name and a man who
advertised his shop are not the same claim.

`letter_list_only` today reaches `gazetteer.json` and `register_1835.json` and stops
there. Nothing in `data/residents/`, `tools/measure_layer_reads.py` or
`renderers/web/js/residents.js` has ever seen the field.

**1,536 people against a town of 209 is a change of scale and probably not one run.**
Size it before claiming; the flag reaching the card is separable from the cohort and
may be the piece worth doing first.

**Acceptance:** (state it before working — never weakened to pass)

- `letter_list_only: true` reaches the visitor's card, declared in
  `tools/measure_layer_reads.py` and rendered, so a letter-list name and a documented
  tradesman never read as the same evidence.
- No minted resident carries an occupation the papers do not give them.
- `town_census.json` totals move additively; no household silently loses a member.
- Before → after on the person count, with the instrument named.
