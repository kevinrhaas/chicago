---
id: T-0745
title: dev's gate is still red, but not on T-0739's nine: the four that remain are the cross-street faces, blk_washington_clark's southern ground, the far-timber census, and a duplicate ticket id
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-05
pr: 867
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T10:27:17.078Z
claimed_run: null
---

dev's gate is still red, but not on T-0739's nine: the four that remain are the cross-street faces, blk_washington_clark's southern ground, the far-timber census, and a duplicate ticket id.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Measured, 2026-09-05, by T-0741's run.** `tools/check.sh` was run on a clean worktree of
`origin/dev` at `8ae7d0dec` and on this run's branch. Both exit 1, and their failure lines are
IDENTICAL — the branch introduces none of them. But they are NOT the nine T-0739 records: the
sidecar drift, the three cohort collisions and the two ladder re-derivations all pass now. Four
remain:

- `the seven cross streets have 34 platted faces — got 0`, and with it `both sides of every
  covered cross street are found` (2 checks failed in that step)
- `1 committed platted block(s) stand off the modelled ground: blk_washington_clark` →
  `SOUTHERN GROUND FAIL`, twice: `the programme's stated southern coverage is not what the
  ground measures`
- `the far-timber census disagrees with what is banked (ROADMAP R-BUG5)`, three times
- `ticket queue FAILED: T-0739-the-1830-division-s-recapitulation-counts-53-and.md: DUPLICATE id
  T-0739` — two branches each assigned T-0739 and both merged. The tool prints its own repair:
  `node tools/ticket.mjs restamp <file>` renumbers the younger one, which is the 1830
  recapitulation ticket (merged in #853, after #848 filed the other).

**Acceptance:** `tools/check.sh` exits 0 on `dev`, each of the four repaired rather than
silenced, and T-0739's body corrected or closed — it names nine failures that no longer fire,
which is worse than no record, because the next run to read it will look for the wrong red.

**Why this is filed rather than fixed here.** T-0741 was one unit of work about inventorying
census images. Three of these four are terrain and street geometry and the fourth is ticket
bookkeeping; none of them is that unit, and bundling them into its PR would make one
un-revertible commit out of four unrelated repairs.

---

**CLOSED 2026-09-05. The gate is green — and three of this ticket's four items were never
failures.** Measured on a clean worktree at `f3dfcc28f`: `./tools/check.sh` exits **0**,
with **zero** `^ <label> failed` lines. PR #863 (T-0739) repaired the cohort gate, ran the
derivation cascade and restamped the duplicate id to **T-0757** — which is the one item on
this list that was real, and this ticket is what found it.

**The other three are the self-tests working, and reading them as red is a trap the next
run would have fallen into.** `check.sh` marks a failing STEP, and only a failing step,
with `^ <label> failed`. Several steps are self-tests that deliberately break a derivation
and require its assertions to fire — and a fired assertion prints the same `FAIL <sentence>`
a real one does. On the green tree measured above, **10 lines still contain `FAIL`**:

- `FAIL the seven cross streets have 34 platted faces — got 0` and `FAIL both sides of every
  covered cross street are found`, inside `SELF-TEST: the cross-street faces are withheld;
  the counts must fire` — followed by `self-test OK`. The real step above them reports
  `frontage face enumeration OK — 36 east-west faces, 34 cross-street faces over 7 cross
  streets`;
- the two `SOUTHERN GROUND FAIL` blocks, inside `…and its own assertions still fire when
  broken`. The step above them prints `SOUTHERN GROUND PASS`;
- the three `FAIL — the far-timber census disagrees with what is banked`, each inside the
  far-timber self-test, whose step reports `PASS (ratchet)`.

Had this ticket been worked as filed, a run would have spent itself extending terrain and
chasing street geometry that is fine. The output that made three tickets describe dev's red
wrongly is now **T-0758**.
