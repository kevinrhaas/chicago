---
id: T-0825
title: dev is red at desktop part 2: the town's wagons vary in type and in the way they stand — 23 farm_box, 17 cart, 23 covered, 6 distinct headings
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-09
pr: null
claimed_by: null
blocked_on: folded into T-0836: the same six-heading wagon red; T-0836 diagnoses why the rule caps at 6
needs_bake: false
closed_at: 2026-09-10T04:20:05.389Z
claimed_run: null
---

dev is red at desktop part 2: the town's wagons vary in type and in the way they stand — 23 farm_box, 17 cart, 23 covered, 6 distinct headings.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Measured 2026-09-05, on T-0693's run and NOT caused by it.**

`SMOKE_VIEWPORT=desktop SMOKE_STAGE=2 node tools/smoke_renderer.mjs --published`, run on a
detached worktree at plain `origin/dev` (2078f85dc) with no branch changes at all, fails with:

```
FAIL  desktop 1280x800: the town's wagons vary in type and in the way they stand
      — 23 farm_box, 17 cart, 23 covered; 6 distinct heading(s) to the nearest 5 degrees
```

The same assertion fails identically on the T-0693 branch, whose diff touches only resident
household records, `renderers/web/js/residents.js`, four tools and the changelog — no wagon
record, no furniture generator, no archetype. So the red is dev's, and it dates from after
`dev-smoke-state.json`'s last desktop part-2 reading (PASS, 2026-09-04T23:36Z); both readings
are filed in that record by this PR.

**What to find out:** the check wants more distinct headings than the placement rule is now
producing. Either the rule's heading spread narrowed under a recent change, or the threshold
moved; the type mix (23/17/23) looks healthy, so the heading term is the one to read first.
