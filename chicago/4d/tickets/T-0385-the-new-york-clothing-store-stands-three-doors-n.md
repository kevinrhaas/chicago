---
id: T-0385
title: The New York Clothing Store stands three doors north of the Tremont House in Dearborn Street
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: T-0306
opened: 2026-08-29
closed: 2026-09-11
pr: 1134
claimed_by: run 9/11/2026, 9:51:33 AM CT
blocked_on: null
needs_bake: true
closed_at: 2026-09-11T15:53:15.393Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34612162594
---

The New York Clothing Store stands three doors north of the Tremont House in Dearborn Street.

Piece 3 of 5 of **T-0306 — The American names six Chicago storefronts with usable placements and none of them is standing in the model yet**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance** (stated 2026-09-11, before working, and met unweakened):

1. `compile_register.resolve_anchor` resolves this business's live anchor to
   `structure tremont_house_1`, and its register row reads `new_building` against it
   rather than `street_only` on `dearborn`.
2. The rule that gets it there is stated in prose beside the other placement rules in
   `compile_gazetteer.py`, and is bounded so that it can never prefer one printed
   ANCHOR to another — that is `anchor_changes`' to declare.
3. Its own self-test cases fire when the pass is broken, proved by breaking it.
4. `tools/check.sh` green, and the smoke parts `smoke_budget.mjs --for-diff` names.

**Found on the way, and it changes the ticket.** The `match_landmarks` blocker this
ticket is written around **is already fixed on `dev`**: `tremont_house_1` carries the
plain aka `Tremont House`, so `{tremont, house}` resolves to it and no relaxation by
shape is needed. The live blocker was the SECOND one, which the prior attempt found and
this ticket does not name — the gazetteer minting a house's placement from its earliest
printing, here an impression whose anchor the reading pass could not read at all.

**`needs_bake: true` was wrong.** No geometry moves: `new_building` is a finding and
nothing in this project builds from one. `validate.py --stale` reports 380 assets
matching their inputs, 0 stale. The roof three doors north of the Tremont House is still
owed, and T-0306's remaining pieces carry it.


**What it needs first.** The anchor is *"three doors north of the Tremont House, in
Dearborn Street"*, and `tools/compile_register.py`'s `match_landmark` cannot see the
Tremont: it compares whole word-sets, and every one of `tremont_house_1`'s three names
carries a disambiguator this project added — *(the first)*, *I*, *old* — so
`{tremont, house}` matches none of them. Four businesses fail on that one anchor. The
register calls this one `street_only` on `dearborn` today.

**Prior attempt: PR [#562](https://github.com/kevinrhaas/custom/pull/562), closed unmerged 2026-09-05 under T-0803.**
Opened 2026-08-29; **559 commits behind `dev`** with 55 changed files and a bake when it
was read. **Read its PR body before starting** — it solved the `match_landmark` blocker
this ticket names, and the shape of the fix is the part worth keeping: the relaxation is
**by shape, not by word list** (only a trailing parenthetical, a trailing roman numeral and
a leading `old` are stripped, only after exact matching fails, and only when what remains
resolves to exactly one building), because a word-list cut immediately produced two false
anchors — *"the First Baptist meeting house"* → the Temple Building and *"Chicago's first
post office"* → Hogan's store. It also found the second, more general blocker the ticket
does not name: the gazetteer placed a business on its EARLIEST printing, so King's shop sat
on a segmenter loss for as long as it ran. Files **T-0413** and **T-0414**.

Its branch could NOT be deleted from the session that closed it — this environment's proxy refuses a ref delete over both git and the REST API (HTTP 403) — so `ticket.mjs claim` **will see it as a rival branch and refuse**. That refusal is a false stop: the PR is closed and the branch is abandoned. `claim T-0385 --force` is correct here. `ticket.mjs inflight` reads it as COLD, which is the honest signal.
