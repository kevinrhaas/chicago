---
id: T-0836
title: The town's wagons stand on 6 distinct headings and the smoke asks for 8, so dev is red at both viewports on a layer no branch has touched
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-11
pr: 1118
claimed_by: run 9/11/2026, 3:25:02 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-11T09:03:02.370Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34578744716
---

The town's wagons stand on 6 distinct headings and the smoke asks for 8, so dev is red at both viewports on a layer no branch has touched.

Found by T-0431, which ran the smoke over its own diff and got the same single red at both
viewports.

**The reading.** `smoke_renderer.mjs` part 4, *"the town's wagons vary in type and in the way
they stand"*, requires `bearings.size >= 8` — distinct headings bucketed to the nearest 5°.
The town has **6**: buckets `[0, 18, 35, 36, 54, 72]`, i.e. 0°, ~90°, ~175°, ~180°, ~270°,
~360°. Kinds and share pass (23 farm_box, 23 covered, 18 cart of 64 town wagons); it is the
headings alone that fail.

**It is not any branch's doing.** `data/yard/town_trade_goods.json` is byte-identical between
`origin/dev` and T-0431's branch, and `townWagons` is `wagons.filter(w => w.stands_on ||
w.in_enclosure)` — so the assertion is a pure function of a file no recent branch has
touched. Reproduced from the committed data directly, without a browser:

    town wagons 64; farm_box 23, covered 23, cart 18; bearing buckets 6

**Why six.** `generate_yard_goods.py` stands a wagon square to the frontage it serves, and
the town's streets run on two bearings — so every wagon lands on one of four cardinal
headings plus the two the off-grid frontages give. The assertion asks for eight, which the
rule as written cannot produce however many wagons are dealt.

So one of the two is wrong: either the rule should draw wagons up at angles to the kerb (they
were not all squared in 1835 — a wagon backed to a door stands askew), or the assertion's
eight is a number nobody can meet and should be restated against what the rule can produce.
Not this ticket's call to make quietly: it is a claim about how the town looked.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- Either the wagon rule produces headings the assertion can pass and the reason is a claim
  about 1835 (with its LIBERTIES entry), or the assertion is restated against the rule with
  the measured ceiling written into it. Never both, and never the assertion weakened alone to
  make the red go away.
- Both viewports go green on part 4 and the reading is filed in `tools/dev-smoke-state.json`.

**Links:** T-0431 (found it) · `tools/generate_yard_goods.py` ·
`tools/smoke_renderer.mjs` (the assertion, near the `townWagons` block) ·
`data/yard/town_trade_goods.json`.

## Folded in from T-0825 (2026-09-10) — the same six-heading wagon red; T-0836 diagnoses why the rule caps at 6

*T-0825: dev is red at desktop part 2: the town's wagons vary in type and in the way they stand — 23 farm_box, 17 cart, 23 covered, 6 distinct headings*

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
