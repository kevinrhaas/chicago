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
and Wells (T-2099). `--gate` read it on several CPUs the same evening: this steward runner and
the GitHub-hosted runners that `chicago-4d-frame-time.yml` happened to land on. Frame ms,
with the frame in bare screens after it:

| tier | EPYC 9V74 desktop | EPYC 7763 desktop | EPYC 9V74 phone | EPYC 7763 phone | Xeon 8573C phone |
|---|---:|---:|---:|---:|---:|
| full | 13919 · 168.7 | 12440 · 124.8 | 10028 · 144.3 | 8433 · 110.7 | 6492 · 106.8 |
| balanced | 10460 · 123.8 | 9479 · 95.6 | 7220 · 105.1 | 6141 · 79.5 | 4890 · 82.6 |
| light | 6650 · 78.5 | 6184 · 62.0 | 4262 · 61.8 | 3730 · 49.2 | 2884 · 48.8 |
| bare screen | 82.5–84.7 | 99.2–99.7 | 68.7–69.5 | 75.8–77.2 | 59.1–60.8 |

**The first design gated the ratio, and the third CPU refuted it.** The plan was to divide
the frame by a bare screen (every layer hidden: clear and sky, one call) timed in the same
page, so a faster or slower runner would cancel out. On the two GitHub-hosted CPUs it nearly
did: their milliseconds differ by up to 30 %, and their ratios agree within 4 %. The EPYC
9V74 draws the bare screen quickly and the town slowly, so it reads the ratio about a third
higher. A fourth CPU then turned up: the EPYC 9V45, whose phone frames read 4654 / 3393 / 1982 ms at
79.8 / 58.8 / 36.3 bare screens. Across the four CPUs the phone's `full` frame reads 80 to 144
bare screens. A unit that spread is not machine-free. The ratio is still printed, as
`bare screens`, and it is not gated.

Milliseconds on ONE CPU hold steady. The EPYC 7763's desktop `full` frame read 12331,
12440 and 12308 ms in three runs, `balanced` 9397–9479 and `light` 6162–6184, a spread of
1 % or less. A 10 % margin therefore catches a real regression without flaking.

So **the ceiling is in milliseconds, and it belongs to one machine.**
`tools/still_frame_ceilings.json` keeps ceilings per CPU model and core count. Each is set by
the rule *that machine's own reading plus 10 %, rounded up to 250 ms*:

| tier | 9V74 desktop | 9V74 phone | 7763 desktop | 7763 phone | 8573C phone | 9V45 phone |
|---|---:|---:|---:|---:|---:|---:|
| full | 15500 | 11250 | 13750 | 9500 | 7250 | 5250 |
| balanced | 11750 | 8000 | 10500 | 7000 | 5500 | 3750 |
| light | 7500 | 4750 | 7000 | 4250 | 3250 | 2250 |

A machine, or a viewport of one, with no number is read and warned about (`::warning`).
It is never failed on another machine's numbers, and `--strict` fails it. A red that only
meant "GitHub gave us a new CPU" would teach people to ignore the gate. The next reading on
an unlisted CPU adds its own numbers by the same rule.
`.github/workflows/chicago-4d-frame-time.yml` runs the gate nightly, on dispatch, and on any
push that changes the gate, its ceilings or the workflow, one job per viewport. It is not in
the smoke because one viewport's gate is about five minutes of software rasterising.

## What is left of T-2099

T-2109 (1904's glass, half of every 1904 frame) and T-2110 (the phone's default Image
sharpness, and the trees' and terrain's fragment cost in 1835) are the fixes. When either
lands, its PR brings the ceiling it beats down to its own reading, by the rule above.
