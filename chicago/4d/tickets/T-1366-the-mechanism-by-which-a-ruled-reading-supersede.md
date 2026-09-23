---
id: T-1366
title: The mechanism by which a ruled reading supersedes a mint's derived arrival bound, spent on the three spring-1833 arrivals of Botsford, Eli B Williams and Hibbard Porter
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-1350
opened: 2026-09-18
closed: 2026-09-19
pr: 1502
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-19T05:06:08.238Z
claimed_run: null
---

The mechanism by which a ruled reading supersedes a mint's derived arrival bound, spent on the three spring-1833 arrivals of Botsford, Eli B Williams and Hibbard Porter.

Piece 1 of 2 of **T-1350 — The four resident mints derive `arrival` from the registers they read and silently revert a reading pass that supersedes one: seven ruled book findings — the spring-1833 arrivals of Botsford, Williams and Hibbard Porter and the Baptist presence of 19 October 1833 for Willard Jones, Nathaniel Carpenter and Martin D. Harmon — cannot reach the cards the crosswalk has already joined them to**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:**

1. A RULED READING REACHES A CARD A MINT OWNS AND SURVIVES THE NEXT `--build`. A committed
   ledger, `data/research/residents/arrival_supersessions.json`, consulted by all four
   mints; proved by each mint's own byte-for-byte `--check` passing with the superseded
   values standing, and again by a merge of `dev` plus a 147-step `rederive.mjs --run`
   leaving them in place.
2. AND IT CANNOT BECOME A WAY TO WRITE ANY DATE ANYWHERE. Four refusals, gated in
   `check.sh` and each with its own firing self-test: no identity is made here (the merge
   must already be committed to a crosswalk), no reading is invented here (the claim id
   must exist in the claims file named, the sources in `data/sources/`), a supersession
   must be EARLIER than the bound it replaces, and the grade ceiling is the source's — a
   `transcription_mediated` claim may not be graded above `inferred`.
3. THE OLD FAILURE IS LOUD, NOT SILENT. Each entry banks the derived bound it was ruled
   against; a mint that later derives a different one stops the build and names the card
   and both dates.
4. THE THREE SPRING-1833 CARDS CARRY THEIR FINDING. J. K. Botsford, Eli B Williams and
   Hibbard Porter at 1833-03-01, season precision, claim bk_mose1_005, `inferred`.
5. THE DERIVED LAYER AGREES and nothing else moves: the reconstruction programme withdraws
   the three drawn `arrival_year` blocks the evidence retires, the town model, order book,
   transient cohort, tiers, sidecars, profile, audit and research reports all re-derive,
   the 909 re-admissions re-derive unchanged, and `./tools/check.sh` is green.
