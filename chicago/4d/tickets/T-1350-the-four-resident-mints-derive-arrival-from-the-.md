---
id: T-1350
title: The four resident mints derive `arrival` from the registers they read and silently revert a reading pass that supersedes one: seven ruled book findings — the spring-1833 arrivals of Botsford, Williams and Hibbard Porter and the Baptist presence of 19 October 1833 for Willard Jones, Nathaniel Carpenter and Martin D. Harmon — cannot reach the cards the crosswalk has already joined them to
state: split
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-18
closed: 2026-09-18
pr: null
claimed_by: run 9/18/2026, 9:40:43 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-19T04:31:45.591Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35416184380
---

The four resident mints derive `arrival` from the registers they read and silently revert a reading pass that supersedes one: seven ruled book findings — the spring-1833 arrivals of Botsford, Williams and Hibbard Porter and the Baptist presence of 19 October 1833 for Willard Jones, Nathaniel Carpenter and Martin D. Harmon — cannot reach the cards the crosswalk has already joined them to.

**Acceptance:**

1. A RULED READING CAN REACH A CARD A MINT OWNS, and survives the next `--build`. The
   mechanism is a committed ledger, `data/research/residents/arrival_supersessions.json`,
   consulted by all four mints; the proof is that each mint's own byte-for-byte `--check`
   passes with the six superseded values standing.
2. AND IT CANNOT BECOME A WAY TO WRITE ANY DATE ANYWHERE. Four refusals, each gated and
   each with its own firing self-test: no identity is made here (an entry must name a
   merge a crosswalk already committed, in that crosswalk's words), no reading is invented
   here (the claim id must exist in the claims file named, the sources in `data/sources/`),
   a supersession must be EARLIER than the bound it replaces, and the grade ceiling is the
   source's — a `transcription_mediated` claim may not be graded above `inferred`.
3. THE OLD FAILURE IS LOUD, NOT SILENT. Each entry banks the derived bound it was ruled
   against. A mint that later derives a different one stops the build and names the card
   and both dates, rather than writing a stale ruling over evidence that has moved.
4. THE SIX CARDS CARRY THEIR FINDINGS. J. K. Botsford, Eli B Williams and Hibbard Porter
   at the spring of 1833 (season precision, 1833-03-01, claim bk_mose1_005); Willard Jones,
   Nathaniel Carpenter and M D Harmon bounded at 1833-10-19 by the Baptist catalogue
   (claim bk_mose2_010). T-1340's seventh finding, J. H. Collins, needs no entry: the
   compiler prints his coming undated and there was never a value to move.
5. THE DERIVED LAYER AGREES. The reconstruction programme withdraws the three guessed
   `arrival_year` blocks the new evidence retires, and the sidecars, population profile,
   resident audit, remainder rulings and research-spend ledger all re-derive.
6. NOTHING ELSE MOVES. `present_on_scene_date` is untouched — Willard Jones goes on
   reading `uncertain` for 1 July 1835, because a presence in October 1833 is an answer to
   a different question. `./tools/check.sh` green.
