# Arrival and jaunts acceptance — budgets and legacy surfaces, October 2026

T-2047 (piece 4 of 4 of T-1272, *Verify arrival, jaunts and source browsing on the
published mobile app*). Written 2026-10-04 against `dev` at `cb56e2e4`. Every number below
is read from a file or measured by a command named beside it, on one steward runner
(4 cores, headless Chromium, software WebGL). None is estimated.

The parent's other three pieces have their own PRs and reports. T-2044 (smoke part 14,
the whole path at both viewports) merged as #367. T-2045 (boot variants) and T-2046
(layouts) were in flight while this was measured, so their stills and verdicts belong to
them, and this report does not restate or anticipate them.

**The short version.** The arrival-and-jaunts section is within its own budgets: it adds
11.5 KB to a first visit and keeps the catalog, the jaunt files and the source index off
the boot path. Two of the town's budgets are NOT met on `dev`, and neither failure comes
from this section: the boot payload is 0.122 MB over its 13 MB, and the mobile flora
heartbeat is past its 250 ms. A third finding is that the boot slowed by more than the
10 % that calls for re-measuring `boot-weights.js`. Each one leaves as a named successor
(§ 5) carrying its measurement. No budget was raised.

## 1. Boot payload — 13.122 MB against 13 MB: OVER

`node tools/measure_boot_payload.mjs --check`, on the published mirror (`./tools/publish.sh`):

```
BOOT PAYLOAD — first visit stands in the 1835 street
  13.122 MB across 1306 request(s) (gzip on the wire, fresh context, ready + 3s settle)
BOOT PAYLOAD OVER BUDGET: 13.122 MB > 13.000 MB (docs/SITE-BUDGET.md §4)
```

**The method checks out.** The same tool, run on `49d0a226` (T-1973's merge, where the
budget was re-set to 13 MB) published by that tree's own `publish.sh`, reads **12.575 MB
across 1289 requests**. That is T-1973's own figure (SITE-BUDGET §4a), so the +0.547 MB is
growth, not a change in how it is counted. Where it came from, per path on the wire:

| what | 49d0a226 | cb56e2e4 | Δ |
|---|---|---|---|
| `data/sidecars/1835/` (the per-structure sidecars) | 3.339 MB | 3.601 MB | +0.263 |
| `walk/fonts/` (T-2036's skins, `css/skins.css`) | 0.012 | 0.083 | +0.071 |
| `data/enclosures/` (`town_entrance_aprons.json`, new) | 0.090 | 0.140 | +0.050 |
| `walk/js/` | 0.737 | 0.785 | +0.048 |
| `data/liberties.json` | 0.559 | 0.594 | +0.035 |
| `data/yard/` (`town_woodpiles.json`, new) | 0.052 | 0.076 | +0.024 |
| `data/frontage/`, `data/residents/`, `data/gltf/` | | | +0.058 |

**What the section itself costs a first visit:** `walk/js/arrival.js` 3.3 KB,
`walk/js/welcome.js` 2.1 KB, `walk/js/loading-early.js` 0.9 KB and
`data/loading/statuses.json` 5.2 KB, so 11.5 KB in all. The statuses are fetched during
boot by design (T-1275: `main.js` starts the load and does not await it). Its failure is
one of T-2045's variants. **Lazy, as the parent requires:** no URL containing `catalog`,
`jaunt` or `sources/` is in the 1306 requests. The catalog, the 26 jaunt files and the
source index are fetched only when a visitor opens them.

**Not in any gate's verdict yet.** The nightly bake enforces this check
(`chicago-4d-bake.yml`, T-1156), but every dev bake since 2026-10-03 was cancelled by a
newer push. → **T-2058** takes `liberties.json` (0.594 MB) off the boot path, the cut
SITE-BUDGET §4b names first.

## 2. Boot phases — the boot moved more than 10 %, and not because of the arrival

`node tools/measure_boot_phases.mjs --published --json`, all 12 cells, on `dev` and with
`--root` on `c2dd2ea1` (the tree before T-1247 started the arrival section, published by
its own `publish.sh`). Both were measured on the same runner within twenty minutes of
each other. Seconds to ready:

| cell | before (c2dd2ea1) | after (cb56e2e4) | Δ | flora gap after (ms) | longest task after (ms) |
|---|---|---|---|---|---|
| mobile/light/cold | 12.06 | 17.89 | +48 % | 320 | 4850 |
| mobile/light/warm | 12.34 | 18.92 | +53 % | 356 | 5472 |
| mobile/balanced/cold | 13.72 | 21.94 | +60 % | 396 | 6981 |
| mobile/balanced/warm | 13.27 | 22.22 | +67 % | 378 | 6289 |
| mobile/full/cold | 15.56 | 25.00 | +61 % | 422 | 7854 |
| mobile/full/warm | 15.04 | 25.51 | +70 % | 348 | 7796 |
| desktop/light/cold | 16.95 | 22.01 | +30 % | 380 | 8051 |
| desktop/light/warm | 17.33 | 25.64 | +48 % | 338 | 8050 |
| desktop/balanced/cold | 18.55 | 24.66 | +33 % | 338 | 10365 |
| desktop/balanced/warm | 19.38 | 29.48 | +52 % | 372 | 10448 |
| desktop/full/cold | 21.71 | 27.17 | +25 % | 427 | 11943 |
| desktop/full/warm | 20.67 | 34.24 | +66 % | 418 | 12028 |

These are a software-WebGL runner's seconds, about 4-8× the Apple M5 Max that
`boot-weights.js` was read on. Compare the two columns with each other, not with that file.
The town between them grew from 419 standing structures to 544.

**Where the time went** (mobile light cold, per phase, before → after): scene 1.24 → 1.54 s,
**terrain 0.72 → 3.71 s**, buildings 0.43 → 0.72, ground 0.73 → 2.31, flora 7.11 → 7.04,
people 0.36 → 0.49, interaction 1.60 → 2.33. The terrain phase now opens with one
~2.9 s long task. It was already there on `49d0a226` (2026-10-02, `--quick`: terrain
3.72 s), and the arrival section was complete by then. So it came in with that week's
ground and terrain work (T-1797, T-1812, T-1819, T-1825), not with the arrival.

**The heartbeat.** `--check` holds mobile light's flora paint gap to ≤ 250 ms. Bisected
with `--quick` on this runner:

| tree | gap, cold / warm |
|---|---|
| `c2dd2ea1` (before the arrival) | 140 / — ms (12-cell run) |
| `49d0a226` (arrival in, 2026-10-02) | 124 / 162 |
| `b06a063a^` (before T-2014) | 136 / 167 |
| `d90c7ed2^` (T-2014 in, before T-2015) | 143 / 137 |
| `d90c7ed2` (T-2015, #333, leaf-scale trees) | **339 / 388** |
| `cb56e2e4` (dev) | 320 / 356 |

→ **T-2059** (T-2015's trees and the heartbeat). → **T-2060** (`boot-weights.js`). The
parent asks for the weights to be re-measured when the boot moves more than 10 %, and it
moved. This piece did not rewrite them. They pace the arrival's progress for every first
visit with no timing history, and the only machine a run can reach is this runner, whose
seconds describe software WebGL. Choosing the machine is T-2060's first question.

## 3. Frame cost — inside every ceiling that was read

`node tools/measure_detail_ceilings.mjs` (desktop 1280×800, the gate's six stands,
`__chicago4d.stats()`), against `DETAIL` in `renderers/web/js/main.js`
(full 2,475,000 · balanced 1,880,000 · light 910,000 triangles; 295 draw calls):

| level | stand | triangles | of ceiling | calls |
|---|---|---|---|---|
| full | lake_at_canal (reference) | 2,310,985 | 93.4 % | 263 |
| full | the_forks | 2,263,320 | 91.4 % | 224 |
| full | from_above | 2,292,968 | 92.6 % | 178 |
| full | lake_and_market | 2,004,893 | 81.0 % | 236 |
| full | prairie_west | 2,424,791 | 98.0 % | 279 |
| full | sauganash_26 | 1,716,410 | 69.3 % | 169 |
| balanced | lake_at_canal (reference) | 1,861,014 | 99.0 % | 241 |
| balanced | the_forks | 1,824,834 | 97.1 % | 205 |
| balanced | from_above | 1,752,012 | 93.2 % | 174 |
| balanced | lake_and_market | 1,719,811 | 91.5 % | 234 |
| balanced | prairie_west | 1,866,709 | 99.3 % | 245 |
| balanced | sauganash_26 | 1,421,576 | 75.6 % | 169 |

**Not read here, said plainly:** the `light` level and the mobile viewport. The sweep was
cut off by the 580 s cap during desktop `light`. A second attempt, `measure_stand_budget.mjs
--stand lake_at_canal --tiers light --only both`, was cut off the same way. The smoke's
part 4 holds all three levels at both viewports. Its last recorded pass on dev is CI's, on
`a8fac67b` (2026-10-01, `tools/dev-smoke-state.json`). The arrival section draws nothing
in the scene, so it cannot move these numbers, but the room left is thin: balanced is at
99.0-99.3 % at two stands.

## 4. Legacy surfaces — the existing smoke parts, run on this branch

The parent lists every Evidence topic, Go to, Travel settings, People, framing and the
popup. In `tools/smoke_budget.mjs`'s map the popup is part 3, the Evidence hub part 12,
and the People directory and Evidence panel part 13. Each was run in the foreground on
the published mirror of this branch, which differs from `dev` only in documentation and
the release note:

SMOKE_RESULTS

## 5. Named successors

| ticket | what is left | placed |
|---|---|---|
| T-2058 | boot payload 13.122 MB over 13 MB, so take `liberties.json` off the boot path | foot of band 9 |
| T-2059 | mobile flora heartbeat 320-390 ms after T-2015, against the 250 ms check | foot of band 9 |
| T-2060 | `boot-weights.js` re-measure, once its machine is decided | foot of band 9 |

The tool placed all three at the foot of band 9, as it does for any follow-up that is
not the owner's. None of them is a defect in the arrival-and-jaunts section, so none was
fixed inside this piece. Nothing in § 1-3 is relabelled as met.
