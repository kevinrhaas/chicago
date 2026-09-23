---
id: T-0729
title: dev's gate is red on an untouched dev again: 0 platted cross-street faces, blk_washington_clark off the ground, the southern coverage claim and the far-timber census
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-09
pr: null
claimed_by: null
blocked_on: stale: the four lines are check.sh's own negative-control self-tests, which T-0763 is about; the real gates (frontage faces 34, southern --gate PASS, far-timber --gate PASS) are green
needs_bake: false
closed_at: 2026-09-10T04:20:08.663Z
claimed_run: null
---

dev's gate is red on an untouched dev again: 0 platted cross-street faces, blk_washington_clark off the ground, the southern coverage claim and the far-timber census.

**Acceptance:** `./tools/check.sh` exits 0 on a clean checkout of `origin/dev` with no
branch applied, and the `chicago-4d-check.yml` run on `dev` is green. Each of the four
failures below is either fixed or, if the claim it checks is the thing that is wrong,
withdrawn with the reasoning written down — never by loosening the assertion to pass.

**Found by T-0722 (2026-09-05), which is not what it is about.** It is filed here rather
than fixed there because a red gate and a full byte budget are two different faults and one
PR should not carry both.

**The evidence, and it is not one branch's.** `./tools/check.sh` on a `git worktree` of
`origin/dev` at 06a0a9ec, with nothing applied, exits 1 with:

```
FAIL the seven cross streets have 34 platted faces — got 0
FAIL both sides of every covered cross street are found — Market and State are the
     town's outer edges and front on one side only
FAIL 1 committed platted block(s) stand off the modelled ground: blk_washington_clark
SOUTHERN GROUND FAIL — the programme's stated southern coverage is not what the ground
     measures
FAIL — the far-timber census disagrees with what is banked (ROADMAP R-BUG5)
```

CI says the same thing about the same tree: the `gate` run on 3c814565 (T-0636,
consolidation pass 3) is `failure` with **exactly this set** —
https://github.com/kevinrhaas/custom/actions/runs/33939107624 — while the run before it,
6decede8 at 02:22 UTC, was green. So the red arrived with 3c814565 and dev has carried it
since.

**Why it matters more than the failures do.** The dev gate is the only gate this app
merges on. While it is red on dev itself, no branch can go green, so every finished unit
of work parks on `hold` and the queue stops moving — which is what the open PR list
already looks like. T-0491 and T-0544 are the same fault class, twice before, and the
second was withdrawn rather than answered.

**A note for whoever takes it.** The four are probably not four. `0 platted cross-street
faces` and `blk_washington_clark stands off the modelled ground` are both about the plat
against the terrain, and the southern-coverage claim is about the same ground; start by
asking whether 3c814565 moved data any of those three derive from, rather than by fixing
them one at a time.
