---
id: T-0279
title: 2,526 of 18,911 drawn flower heads stand over open ground with no plant under their own stalk, on an unmodified dev
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-28
closed: 2026-09-13
pr: 1244
claimed_by: run 9/13/2026, 4:28:36 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-13T10:27:39.758Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34749474099
---

2,526 of 18,911 drawn flower heads stand over open ground with no plant under their own stalk, on an unmodified dev.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Acceptance:** the R-BUG7 head-support gate is green at desktop 1280x800 on an unmodified
`dev`, or the 13.4 % of heads it names are shown to be correctly placed and the gate is
corrected to say so — with the reason the figure moved recorded either way. Never the bar
lowered to fit.

**What was seen.** `tools/smoke_renderer.mjs` stage 7, desktop 1280x800, twice on the same
tree, on `dev` at `5b69f17c` with no renderer or data change:

```
FAIL  [5:54] desktop 1280x800: every drawn flower head has a plant under its own stalk
      — 2526 of 18911 drawn heads over 40 poses had nothing under the foot of
      their own stalk; worst flora-head-corymb at from_above 270deg, foot 1.61 m,
      0.61 m over its base over open ground
```

**13.4 % of drawn heads**, and the worst case is `over open ground` rather than over a gap —
an ORPHAN, a flower head with no plant beneath it at all. The mobile half of the same stage
does not reach this check's failing case, so it is a desktop-only reading today.

**It is new, and it is not a branch's.** `tools/dev-smoke-state.json` records `dev`'s standing
desktop part 7 as of 2026-08-28T00:55 with two failures — the tree-station gate (T-0243) and
the suite body killed at the per-command ceiling — and this is not among them. It was found
while measuring stage 7 for T-0225, whose diff is confined to the seam block BELOW this check
and reads no flora module, so it cannot be that either.

**Where to start.** The two flora changes that landed on `dev` immediately before, both of
which move which heads are drawn: T-0209 (the prairie's flowers carried out past the near
ring to 119.9 m, on the far band's aggregate clumps) and T-0214 (the nine flower-head ceilings
split by measured demand, `HEAD_SHARE`). The far band's `minPx` reach rule and `headRingAt`
are the two places a head can be drawn where its plant is not.

**Why it matters, and why the two readings are different findings.** R-BUG7's invariant is
that a head can only be drawn where its own plant is, because its ring is DERIVED from that
plant's (`headRingAt`). A red here says either

  * the invariant is broken in the drawing — a visitor sees flowers hanging in the air, which
    is the T-0035 defect in a new place and is visible; or
  * the gate has stopped being able to find the plant it should match, which is exactly the
    shape T-0243 and T-0244 describe for the timber gates since T-0223's lattice landed, and
    is a gate defect rather than a scene one.

Both are worth knowing and they are not the same thing. Whichever it is, say which.

**Links:** `tools/smoke_renderer.mjs` (stage 7, `headSupport`) ·
`renderers/web/js/flora.js` (`headRingAt`, `HEAD_FADE_AT`, `HEAD_SHARE`, `far.minPx`) ·
`tools/measure_head_support.mjs` · `tools/dev-smoke-state.json` ·
T-0209 · T-0214 · T-0035 · T-0243 · T-0244 · T-0225.

## MEASURED, 2026-09-13 — the heads were never floating; the reading was

The acceptance offered two endings: the gate green on an unmodified `dev`, or the heads
shown to be correctly placed with the reason the figure moved recorded. **It is the
second, and the gate is green as well.** Both halves were run in the foreground on this
branch, whose only code change is to a diagnostic tool no renderer reads.

**The gate — R-BUG7 itself, `tools/smoke_renderer.mjs`, desktop 1280x800, published:**

```
SMOKE_VIEWPORT=desktop SMOKE_STAGE=10 node tools/smoke_renderer.mjs --published
  pass  desktop 1280x800: every drawn flower head has a plant under its own stalk
32 passed, 0 failed        6 m 05 s
```

Run twice — once on `1ced9343e` and again after rebasing onto `4e43f4f90`, because `dev`
moved underneath this branch and a reading is about the tree it was taken on. Same verdict
both times; the second is the one filed in `tools/dev-smoke-state.json`, under the hash it
was actually taken at.

The check is in **part 10**, not part 7 — this ticket was written before T-0346/T-0173/
T-0170 re-cut the parts, and a run that trusted the number here spent a leg on part 7 and
read nothing about flowers. Part 7 at desktop is red on `dev` today for an unrelated
reason (the speed label is in miles per hour), which is `tools/dev-smoke-state.json`'s
standing reading of 2026-09-12 and not this.

**Why the figure moved: T-0448, 2026-08-31.** That ticket is this one, re-found three days
later at 2,693 of 18,893, and it MEASURED the mechanism rather than guessing at it: every
one of the 2,693 orphans stood on a `flora-far` card at 0.000 m whose top reached the foot
of its stalk. Since T-0209 the far band deals the whole community, so a flowering forb's
far card carries its own flower — `rebuildFar` calls `maybeHead` on it and puts the head at
the card's own `e,n`. The support set was the pre-T-0209 one and did not list `flora-far`,
so it looked for a stem beside a head that is carried by a card. The scene was right and
the assertion was wrong; `fd91f2a1b` corrected the assertion and the gate has been green
since. This ticket is therefore **superseded by T-0448** on the finding, and the work left
in it was the part T-0448 did not touch.

**The part T-0448 did not touch, which this branch repairs.** `tools/measure_head_support.mjs`
is the standalone reader of the same invariant, and its header promises the arithmetic is
"all of it copied from `flora.js` so the two cannot drift". They drifted. Two faults, both
fixed here:

1. **It could not run at all on a failure.** `headY_m: Number((p.y - drop)…)` referenced a
   `drop` that T-0035 deleted with the world-space head descent, so the file threw
   `ReferenceError: drop is not defined` the instant it found an unsupported head — the one
   case it exists to describe. It has been unusable for the whole of this ticket's life,
   which is a fair part of why the question went three weeks without an independent answer.
2. **It carried the pre-T-0209 support set**, a fortnight after `smoke_renderer.mjs` fixed
   its own. So it went on reporting the retracted figure to anyone who reached for it.

Measured here on the source tree, 44 poses across 11 anchors at four bearings, desktop
1280x800, on a `flora.js` this branch does not touch:

| support set | drawn heads | unsupported | |
|---|---|---|---|
| before — `flora-far` excluded, as this ticket found it | 19,682 | **2,893 (14.70 %)** | exit 1 |
| after — `flora-far` counted, as the gate counts it | 19,682 | **0 (0.00 %)** | exit 0 |

The same 19,682 heads, the same frame, the same scene: only the question changed. And the
after-run's `footToNearestStem_m` reads **0.000 m at every percentile including the max** —
every head foot sits exactly on its carrier, which is T-0448's finding reproduced
independently two weeks later.

A far card's `spread` is a billboard HALF-WIDTH, metres wide, so the repair counts a card as
supporting at its own foot and nowhere else (reach 0, floored at 5 cm) — the same rule the
gate uses, and not the free pass that would have made any head within a card's width pass.
