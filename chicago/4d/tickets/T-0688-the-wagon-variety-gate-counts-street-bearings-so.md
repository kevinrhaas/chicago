---
id: T-0688
title: The wagon-variety gate counts street bearings, so re-deriving a street took it from 9 buckets to 7 and it is at its floor of 8
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-11
pr: 1126
claimed_by: run 9/11/2026, 7:33:04 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-11T12:42:36.492Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34596674770
---

The wagon-variety gate counts street bearings, so re-deriving a street took it from 9 buckets to 7 and it is at its floor of 8.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Found by T-0447 (PR on `steward/t-0447-north-water-east-end`), which is parked on this
and on nothing else.

## The assertion

`tools/smoke_renderer.mjs:3762`, part 2, both viewports:

```js
check(`${label}: the town's wagons vary in type and in the way they stand`,
  kinds.size >= 3 && kinds.has('covered') && kinds.has('cart')
    && kinds.has('farm_box')
    && commonest <= townWagons.length * 0.75 && bearings.size >= 8, …
```

where `bearings = new Set(townWagons.map((w) => Math.round(w.bearing / 5)))`.

## What it actually measures

A town wagon drawn up "along the road" takes the bearing of the street segment it stands
on, so this clause counts **distinct street bearings that happen to have a wagon on
them**. It is a property of the street network, not of the wagon rule, and the comment
above it justifies only the three `kinds` clauses — the floor of 8 is unexplained.

## Measured, on `dev` and on the T-0447 branch

| bucket | dev | branch |
|---|---|---|
| 0° | 5 | 5 |
| **90°** | 14 | **15** |
| **95°** | **1** (`town_wagon_north_water_7`) | — |
| 175° | 1 | 1 |
| 180° | 9 | 9 |
| **225°** | **1** (`town_wagon_north_water_8`) | — |
| 270° | 33 | 33 |
| 355° | 1 | 1 |
| 360° | 1 | 1 |
| **buckets** | **9** | **7** |

Both lost buckets were single wagons on North Water Street's **hand-drawn** east tail —
the two vertices T-0447 removed as unsourced. `north_water_7` moved 0.9 m and its street
segment's bearing went 96.2° → 90.2°, merging it into the 90° group; `north_water_8` was
refused outright, with the rule's own reason: *"on the left verge, it reaches into the
North Water Street travelled track, which is where a visitor walks."*

So **the gate was passing with one bucket of margin, and both of the buckets carrying that
margin were artifacts of a line nobody derived.** It is also weaker than 9 makes it look:
0° and 360° are the same heading, and 175° and 180° differ by five degrees, so the town's
66 wagons stand in about four real directions.

## The question, and it is a judgement, not arithmetic

Two answers are defensible and T-0447 declined to pick one inside its own PR, because
either is a change to a gate made by the change the gate refused:

1. **The proxy is wrong.** Re-cut the clause to measure what the comment says it measures
   — the wagon rule's own variety, `drawn_up` mix and kind mix — and stop counting street
   bearings, which no wagon rule controls.
2. **The town is genuinely thin.** 65 wagons in four real directions is what this town
   has; keep a bearing measure, but set its floor from something derived rather than from
   whatever the last measurement happened to read.

**Acceptance:**

1. The clause either measures the wagon rule or measures the street network, and says
   which in its own comment.
2. Its floor is derived from something, not from the last green reading.
3. The T-0447 branch's diff is green under the re-cut gate, or T-0447 is told why not.

---

## THE RULING — answer 1, the proxy was wrong (2026-09-11)

**What it measured was never the wagon rule.** A town wagon drawn up along a road takes
that road's bearing, so `new Set(townWagons.map((w) => Math.round(w.bearing / 5)))`
counted distinct STREET headings that happened to carry a wagon. The floor of 8 was the
last green reading written down, which is why re-deriving one centreline could fail it.

**T-0836 landed between the survey and this ruling, and it changes the numbers without
changing the argument.** Every derived wagon is now slewed off its square bearing by an
angle dealt from its own id, so the bearing buckets on dev today read **14**, not 9 —
the clause passes with six buckets of margin, and passes on the JITTER rather than on
anything about the town. A measure that failed for the wrong reason in August now passes
for the wrong reason in September. `town_wagon_north_water_8`, one of the two buckets the
survey named, no longer exists on dev at all: T-0836's own setback refused its stand.

**The re-cut.** The old clause is split in two. The kind clause keeps its floors, which
were always properties of the wagon rule. The standing clause now asks the SLEW about
itself, and reads every number off the record rather than restating it:

- `generate_yard_goods.py` now writes `slew_envelope_deg` and `slew_steps` onto each
  dealt wagon. Nothing in the smoke repeats 6/12/15/9, so the two files cannot drift.
- **Every slew inside its own envelope** — the exact clause, not a floor. A wagon outside
  it is a deal that escaped the rule, and `_lateral_reach` set its stand back for an angle
  it no longer stands at.
- **All three envelopes standing** (6 along a road, 12 backed square, 15 in a yard), or
  the grading of the manoeuvre is untested. Measured: 3.
- **The deal is dealing**: the along-the-road class must use at least `slew_steps - 1` of
  the deal's own steps, and no step may carry more than a quarter of the dealt wagons.
  Derivation, stated so the floor is not a reading: the slew is `sha1(id) mod steps`
  walked end to end, a uniform deal into 9 buckets; 58 wagons over 9 steps is about seven
  apiece, and a uniform deal leaving even one bucket empty is well under a percent — so
  the expectation is 9 and the floor is 9 minus one step of slack for the town gaining or
  losing a wagon. A quarter is more than double the uniform share of 11 %.
- Two wagons may stand undealt, and only two: the attested Western Hotel yard wagon and
  the Randolph Street water cart, which the record holds by hand rather than deriving.

**Measured on dev at 9642c607f, after regeneration:** 64 dealt and 2 held by hand; 0
outside their own envelope; envelopes 6/12/15; 9 of 9 steps used along the road;
commonest step 9 of 64.

**Acceptance 3 — T-0447 is green under the re-cut, and here is why.** The re-cut clause
never reads a street bearing, so the reading T-0447 broke is gone. Its two wagons: 
`town_wagon_north_water_8` is already refused on dev and cannot be removed twice;
`town_wagon_north_water_7` sits at the +1.5 degree step, which carries two wagons, so
removing it leaves that step occupied and the along-the-road class still uses all 9 steps
— two above the floor of 8. **T-0447 may unpark.**

