# T-2111 — the arrival screen, a jaunt view, and a still-frame ceiling per tier

Read 2026-10-04 on dev @ 29fa96f2, published mirror, with `tools/measure_still_frame.mjs`
(T-2099's tool, extended). Raw rows: `t-2111-still-frame-arrival-jaunt.json`. Same method
and caveats as `T-2099-still-frame.md`: SwiftShader, clock held, frames driven by `step()`
and fenced by a one-pixel `readPixels`, medians of 2 timed frames. Desktop is 1280x800;
the phone stand-in is 390x780 at dpr 3, Image sharpness Medium (1.5), CPU throttled 4x.

## 1. The arrival screen draws the same picture over and over

The arrival and the welcome are a menu over the town, and the town under them is the
landing view, so the `landing` row below IS the arrival screen's frame (read with the gate
up). What that row cannot say is how often the frame is drawn. `--arrival 15` leaves the
loop running with the welcome up and nothing touched:

| | frames drawn | in | picture changed? |
|---|---:|---:|---|
| desktop | 3 | 23.5 s | no |
| phone | 6 | 19.5 s | no |

`tick()` holds the walk while the gate is open but still renders every frame, under a
translucent gate whose `backdrop-filter` blur the compositor redraws on top. On this
runner that is a few frames; on a phone it is every display refresh, each one a whole
town frame, for as long as a visitor reads the welcome. **Filed as T-2113**, not fixed
here.

## 2. The arrival screen and a jaunt view, every tier: frame ms (triangles, calls)

The jaunt view is `fort-dearborn-errand`, started for real and read at its first stop (the
fort's south gate), with its panel up; later tiers return to the same pose.

| tier | desktop arrival | desktop jaunt | phone arrival | phone jaunt |
|---|---:|---:|---:|---:|
| full | 7727 (1.90 M, 188) | 6895 (964 k, 62) | 5714 (1.79 M, 166) | 3445 (805 k, 62) |
| balanced | 7984 (1.56 M, 129) | 3468 (996 k, 95) | 5106 (1.44 M, 125) | 2076 (696 k, 55) |
| light | 4589 (783 k, 75) | 2815 (556 k, 40) | 3240 (740 k, 69) | 1802 (452 k, 32) |

Neither is the worst view. The jaunt stop is the cheapest view read so far at every tier on
the phone. Two cells are out of order and are reported as read, not smoothed. Desktop
`full` arrival is below `balanced`, though T-2099 read it above. Desktop `full` jaunt is
twice `balanced` on fewer triangles, and it was the first frame read after the outing
started. Take both `full` cells as one reading each, not a ranking.

## 3. The ceiling: the worst stand, every tier, in milliseconds per machine

The worst 1835 stand at every tier and viewport is still T-2084's back yard on Washington
and Wells (T-2099). Read with `--gate` on two machines the same evening:

| tier | steward runner desktop | phone | GitHub-hosted desktop | phone |
|---|---:|---:|---:|---:|
| full | 13919 | 10028 | 12331 | 8433 |
| balanced | 10460 | 7220 | 9397 | 6141 |
| light | 6650 | 4262 | 6175 | 3730 |
| bare screen | 82.5–84.7 | 68.7–69.5 | 99.0–99.3 | 75.8–77.2 |

**The first design gated a ratio, and the second machine refuted it.** The plan was to
divide the frame by a bare screen (every layer hidden: clear and sky, one call) timed in the
same page, so a faster or slower runner would cancel out. It did not. The GitHub-hosted
runner drew the frame 7–16 % faster and the bare screen 15–20 % SLOWER, so the ratio
differed by about a quarter (desktop `full` 168.7 against 124.3 screens). The milliseconds
differed by only a tenth. The ratio is still printed, as `bare screens`, and is not gated.

So **the ceiling is in milliseconds, and it belongs to one machine.**
`tools/still_frame_ceilings.json` keeps ceilings per CPU model and core count, each set by
the rule *that machine's reading plus 10 %, rounded up to 250 ms*. The steward runner (AMD
EPYC 9V74, 4 cores):

| tier | desktop | phone |
|---|---:|---:|
| full | 15500 | 11250 |
| balanced | 11750 | 8000 |
| light | 7500 | 4750 |

The GitHub-hosted runner's ceilings are set by the same rule, from its own reading, once it
has named its CPU (see the file). A machine the file does not list is read and warned
about, never failed on another machine's numbers; `--strict` fails it.
`.github/workflows/chicago-4d-frame-time.yml` runs the gate nightly, on dispatch, and on
any push that changes the gate, its ceilings or the workflow, one job per viewport. It is
not in the smoke because one viewport's gate is about five minutes of software rasterising.

## What is left of T-2099

T-2109 (1904's glass, half of every 1904 frame) and T-2110 (the phone's default Image
sharpness, and the trees' and terrain's fragment cost in 1835) are the fixes. When either
lands, its PR brings the ceiling it beats down to its own reading, by the rule above.
