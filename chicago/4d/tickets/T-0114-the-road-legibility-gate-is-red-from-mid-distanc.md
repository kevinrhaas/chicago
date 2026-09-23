---
id: T-0114
title: The road-legibility gate is red from mid-distance, and no run had reached it since it turned
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-20
closed: 2026-08-23
pr: 347
claimed_by: run 8/23/2026, 9:10:58 PM CT
blocked_on: null
needs_bake: false
---

The road-legibility gate is red from mid-distance, and no run had reached it since it turned.

Found by T-0060's staged smoke, 2026-08-20, on the published mirror at 390x780 — and
corroborated three ways: the same two checks fail with the T-0060 machinery, without it
(a pre-split filtered run), and the 2026-08-18 full-run kill already reported "208
passed / 2 failed" without ever printing which two. The suite simply died before the
road bands for long enough that nobody saw them turn.

The failing pair, with R-BUG2's own numbers:

- **from the walker's eye, down an open street** — the 100-250 m band reads ΔL* 1.8 of
  the 3.2 its opacity earns, 33 % perceptible of 42 bare probes, weber 0.0795 over
  ground L* 49.8. The near bands pass (2-40 m: 90 % perceptible; 40-100 m: 80 %).
- **from the air, at the aerial anchor** — the 250-600 m band reads ΔL* 2.1 of 4.6,
  49-51 % perceptible of 182 bare, weber 0.093 over ground L* 49.5.

Desktop confirms both (unfiltered reference run 32346862982, 2026-08-20): the walker's-eye
check reads ΔL* 3.4 of 4.5 opaque, 70 % perceptible in its near band, and the aerial
check fails its gated bands the same way. This is the town, on both widths.

The recent ground work is the suspect pool (the bands that fail are exactly the
mid-distance reaches the bank regrades and road-panel splitting touched: T-0110's
curved-bank panel subdivision, T-0046/T-0004's approach earthworks and fort-mound
regrade) — but R-BUG2's own history warns that "measure before choosing" refuted its
prime suspect once already. Read its box in docs/ROADMAP.md before deciding anything.

**Acceptance:** the failing bands are diagnosed with the R-BUG2 measurement (which
build turned them, and why), the repair restores every gated band over its bar without
touching the bars themselves, and both road checks pass in the affected stages
(`SMOKE_STAGE=3`, both viewports) and in the unfiltered workflow run.

**Re-measured by T-0074, 2026-08-20:** both checks fail with the same numbers on the
dooryard-plantings branch — walker 100-250 m band ΔL* 1.8 of 3.2, 33 % of 42 bare,
weber 0.0795; aerial 250-600 m ΔL* 2.1 of 4.6, 53 % of 182, weber 0.0922. The dooryard
stems change neither count nor contrast (probes under flora are excluded by the gate
itself), so this stands exactly as found.

---

## DIAGNOSED 2026-08-24 — a gap between two remedies, not a regression; and the prime suspect was refuted first

**Reproduced unchanged**, four days on, at `SMOKE_VIEWPORT=mobile SMOKE_STAGE=5` (the road checks
moved from stage 3 of 4 to **part 5 of 8** when T-0166 re-cut the body — worth knowing before
anyone re-runs the stage this ticket names):

| check | band | reading | bar |
|---|---|---|---|
| walker's eye | **100–250 m** | ΔL\* 1.8 of 3.2 opaque, **33 %** of 42 bare, weber 0.0795 | 55 % |
| aerial | **250–600 m** | ΔL\* 2.0 of 4.6 opaque, **54 %** of 182 bare, weber 0.0922 | 55 % |

Identical to the 2026-08-20 figures. Banked: `mobile/south_water/100-250` 0.3333,
`desktop/south_water/100-250` 0.5116, `mobile/from_above/250-600` 0.5440.

### The profile is non-monotonic, and that is the whole clue

Walker's eye, by band: **90 % · 87 % · 33 % · 97 %**. Contrast that simply degraded with distance
would fall off smoothly. This is a **hole in the middle**, and `streets.js` says why:

```glsl
float thin = clamp(2.0 / trackPx, 1.0, 6.0);        // binds only when the ribbon is < 2 px
float near = 1.0 - smoothstep(15.0, 40.0, eyeM);    // dies at 40 m
float gain = mix(1.0, 2.4, near);
```

**The near field is lifted by R-BUG3's `NEAR_GAIN` to 40 m. The far field is lifted by the
thin-pixel floor. Between them — roughly 40 m to wherever the ribbon narrows past 2 screen pixels —
the alpha is boosted by nothing at all.** Two remedies, each correct for its own end, with a gap
neither ever measured across. Nothing "turned" the band: **the trough was created the day the near
field was fixed and the middle was left where it had always been.**

### The prime suspect was refuted, exactly as this ticket warned

The obvious reading is that the thin-pixel floor should reach further in, so `MIN_TRACK_PX` was
doubled **2.0 → 4.0** and the band re-measured: **ΔL\* 1.8 of 3.2, 33 % — identical to the digit.**
At 100–250 m the ribbon is still many pixels wide, so `clamp(4.0/trackPx, 1, 6)` is still 1.0. That
path cannot reach the trough at all, and the ticket's own warning — *"measure before choosing
refuted its prime suspect once already"* — landed on this run too.

### The mechanism, confirmed by moving the other lever

`NEAR_FADE_M` **40 → 260**, carrying the near gain across the trough:

| band | before | after |
|---|---|---|
| 2–40 m | 3.8 of 4.5, 90 % | 4.0 of 4.5, 90 % |
| 40–100 m | 3.1 of 5.4, 87 % | **4.9 of 5.4, 100 %** |
| **100–250 m** | 1.8 of 3.2, **33 %** ✗ | **2.1 of 3.2, 67 %** ✓ |
| 250–600 m | 7.0 of 4.5, 97 % | 7.0 of 4.5, 97 % |

`the roads reach the screen from the walker's eye` **passes**. The band is alpha-limited and
unboosted; give it a boost and it clears.

### NOT SHIPPED, and why

`NEAR_FADE_M = 260` is a **six-fold stretch of a constant calibrated for a near-field fault**, and
it makes every road materially more opaque through the whole near-and-mid field. It proves the
mechanism; it is not obviously the right repair, and it has had no visual check. The principled
version is a mid-distance term of its own rather than a near-field fix pulled out of shape — which
is a judgement about how the town should look, not a number that makes a gate go green.

**And it does not finish the ticket either.** The aerial band is **completely unmoved** — 2.0 of
4.6, 54 % — because from the air every probe is beyond any near-fade distance, so `eyeM` never
enters the ramp. The aerial needs its own answer, and it is failing by **one point**: 98 probes
perceptible where 100.1 are needed, out of 182. Two probes.

**Left at HEAD unchanged**; the constants are restored. The acceptance asks for both checks green at
both viewports, and only one of the two has an answer.

### Why this now blocks more than itself

Since T-0165 split the smoke into its own job, the nightly bake finally reaches the published smoke
— and `bake.sh` runs under `set -euo pipefail`, so **these two failures now fail the nightly.** They
have been red since 2026-08-20 and cost nothing, because no bake ever got far enough to run them.
**T-0114 is now the last thing between the pipeline and a green end-to-end run.**

---

## FIXED 2026-08-24 — the middle of the road gets a remedy of its own

`streets.js` gains a **mid-distance term** beside the two that already existed, on the one quantity
that is neither a pixel count nor a near-field ramp — distance from the eye, sustained across the
gap and released where the thin-pixel floor takes over:

```glsl
float near = 1.0 - smoothstep(15.0, 40.0, eyeM);
float mid  = 1.0 - smoothstep(40.0, 700.0, eyeM);     // MID_GAIN 1.7
float gain = max(mix(1.0, 2.4, near), mix(1.0, 1.7, mid));
```

**`max()`, not a product**, and that is load-bearing: the ramps overlap between 15 and 40 m and
multiplying would stack to **4.1×** there, re-breaking the near field R-BUG3 tuned. Taking the
larger leaves every metre under 40 m reading exactly what it read before.

`MID_GAIN` is 1.7 against `NEAR_GAIN`'s 2.4 on purpose — the middle was never invisible, only under
its bar. This lifts a band; it does not repaint the town.

### Measured, mobile, published mirror

| station · band | before | after |
|---|---|---|
| walker 2–40 m | 3.8 of 4.5, 90 % | 4.0 of 4.5, 90 % |
| walker 40–100 m | 3.1 of 5.4, 87 % | 4.9 of 5.4, **100 %** |
| **walker 100–250 m** | 1.8 of 3.2, **33 %** ✗ | 2.6 of 3.2, **98 %** ✓ |
| walker 250–600 m | 7.0 of 4.5, 97 % | 9.2 of 4.5, 98 % |
| aerial 100–250 m | 2.6 of 7.9, 85 % | 4.0 of 7.9, **95 %** |
| **aerial 250–600 m** | 2.0 of 4.6, **54 %** ✗ | 2.9 of 4.6, **69 %** ✓ |
| crossing 2–40 m | 2.5 of 2.5, 70 % | 2.5 of 2.5, **70 %** |

**Both viewports: 28 passed, 0 failed.** All three road checks green at 390×780 and 1280×800.

**The near field did not move**, which is the point of the `max()`: 2–40 m reads 90 % before and
after, and the crossing station — the one R-BUG3 added because neither gated station stood on a road
— reads 2.5 of 2.5 opaque at 70 % both times, identical.

**No bar was touched.** `ROAD_MIN_DELTA_L`, `ROAD_MIN_PERCEPTIBLE` and `ROAD_MIN_PROBES` are
unchanged; `git diff` on `smoke_renderer.mjs` is empty. The bands cleared the bars that were already
there.

### Why the aerial needed this and not the other lever

The rejected experiment — `NEAR_FADE_M` 40 → 260 — lifted the walker's band to 67 % and left the
aerial **completely unmoved at 54 %**, because from the air every probe is beyond any near-fade
distance. A ramp that reaches 700 m catches both: the aerial's 250–600 m band sits inside it once
camera altitude is counted into `eyeM`. One term, both checks, rather than a near-field constant
stretched six-fold to cover a fault it was never shaped for.

### What a visitor sees

Down an open street, the road no longer fades out between about forty metres and the middle
distance and then reappear further off. It runs continuously to where it should. From the air the
street grid reads across the town instead of dissolving in the 250–600 m ring.
