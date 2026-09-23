---
id: T-1399
title: One liberty entry per reconstruction stage, with the counts the compiler agrees with, and the research doc's final tables by tier
state: done
epic: META
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1394
opened: 2026-09-19
closed: 2026-09-19
pr: 1546
claimed_by: run 9/19/2026, 10:09:32 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-20T03:49:56.674Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35485578847
---

One liberty entry per reconstruction stage, with the counts the compiler agrees with, and the research doc's final tables by tier.

Piece 2 of 3 of **T-1394 — The resident layer's closeout: the rebuild order made executable and gated as a fixed point over every reader of the layer, one liberty entry per stage with its counts, the People view's tier filter and reconstructed pills, and the research doc's final tables by tier**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

1. **The binding is declared, not prose.** Every stage of
   `data/reconstruction/1835_resident_reconstruction_programme.json` names the entries in
   `docs/LIBERTIES.md` that admit its inventions, and says in `mints` what it writes that an
   entry has to account for. A stage that mints nobody says why in `owes_no_person_scope`.
2. **The counts are the compiler's.** Every person-minting stage has an enumeration
   `residents.persons[<key>]` in `compile_liberties.SCOPE_SOURCES`, derived FROM the
   programme's own stage list so a new stage cannot be forgotten, counted off the cards over
   the whole of `data/residents/` — and each stage's liberty carries a `Scope:` naming it,
   whose declared count the compiler re-derives.
3. **The gate holds it in both directions**, through `compile_liberties.py --check`, which
   `check.sh` already runs: a stage no entry claims, a stage whose entry admits it only in
   prose, a named entry that does not exist, an entry claiming a stage the programme did not
   name it on, and a `mints` word that disagrees with what the layer actually holds.
4. **The dossier closes with the tables.** `docs/RESEARCH/1835_resident_reconstruction.md`
   prints what each stage wrote and the layer and its attributes by tier, and every figure in
   the stage table is re-derived by the same gate rather than typed once.
5. Each of those assertions has a self-test that breaks it and requires it to fire.

**Stop condition:** a reader can ask which entry admits a given stage, and how many people
that stage invented, and get one answer that a gate keeps true.
