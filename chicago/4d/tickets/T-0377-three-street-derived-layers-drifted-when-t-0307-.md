---
id: T-0377
title: Three street-derived layers drifted when T-0307 moved North Water Street, and dev's gate is red on all three
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-29
closed: 2026-09-09
pr: null
claimed_by: null
blocked_on: stale: the three layers were regenerated in #541 (T-0350) and verify on dev; twin of T-0388
needs_bake: false
closed_at: 2026-09-10T04:20:09.003Z
claimed_run: null
---
PR #530 (T-0307) changed `data/streets/1835.json` and nothing else. Three committed
layers are DERIVED from the street lines and were not regenerated with it, so
`tools/check.sh` on an unmodified `origin/dev` fails three steps:

```
the dooryard plantings re-derive from the rule that dealt their stems     FAIL
the planted poplar rows re-derive from the rule that chose their greens   FAIL
the yard goods re-derive from the rule that chose their frontages         FAIL
```

Found on 2026-08-29 by T-0376's branch, which is byte-identical to `dev` on
`data/flora/**`, `data/yard/**` and `data/streets/**` — so the drift is a function of
dev's tree alone. Not fixed there, because a PR is one revertible unit and moving
plantings is a visible change that owes its own entry.

**Acceptance:** (never weakened to pass)

- The three generators are re-run and their outputs committed, so `check.sh` is green on
  an unmodified `dev`.
- The move is stated: how many stems, rows and goods changed position, and by how much.
- Whether the three should be re-derived by the same gate that catches them, or whether a
  street edit should be refused until they are, is answered in the PR rather than left.
- A changelog entry if anything a visitor can see moves; none if nothing does, said plainly.

---

## THE RED IS GONE — measured 2026-08-29, verify and withdraw

`tools/check.sh` was run on an unmodified `origin/dev` at `9b6e3276`, clean worktree.
All three steps this ticket names now PASS:

```
the dooryard plantings re-derive …    verified 128 dooryard stems across 62 of 144 dwellings
the planted poplar rows re-derive …   verified 2 planted row(s), 8 stems, across 144 dwellings
the yard goods re-derive …            verified 148 object(s) on 26 trading frontage(s)
```

A later merge re-ran the three generators and committed their outputs. **Which merge did
it, and whether the visible consequence this ticket predicted actually happened — a poplar
row leaving the town — is NOT established here**, and that is what the withdrawing run
owes: name the commit, say whether a row left, and confirm a changelog entry was made if
one did. Withdraw with that evidence; do not withdraw on the green alone.

**AND THIS TICKET HAS A TWIN.** T-0377 and T-0388 describe the SAME three failures from
the same cause, filed hours apart by two different runs (T-0376's and T-0336's) that could
not see each other — the collision T-0238 records, this time in `new`, not `claim`. One
withdrawal should close both, and the pair is a second data point for T-0238's rate.
