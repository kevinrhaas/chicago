# T-2737 — what slowed dev's still frame on 1835 town_backyard

dev's still-frame gate (`chicago-4d-frame-time.yml`, desktop) went red on 529f58a61
(run 39057019019): full 15664 ms vs a ceiling of 13750, balanced 10659 vs 10500,
light 7015 vs 7000, on the AMD EPYC 7763 entry of `tools/still_frame_ceilings.json`.

## The gate's own record says it was a landing, not the machine

Every desktop still-frame job on a 7763 between the last green dev run and now
(`gh api …/actions/workflows/chicago-4d-frame-time.yml/runs`, job logs):

| when | commit | full | balanced | light |
|---|---|---|---|---|
| 10-16 17:10 – 18:50 (5 runs) | dev 48fa0caf8 and branches on it | 13126 – 13191 | 10241 – 10327 | 6742 – 6837 |
| 10-17 07:48 | main e2f67357f (old code) | 13084 | 10238 | 6742 |
| 10-17 17:48 – 20:19 (11 runs) | dev 529f58a61 and later | 15413 – 15778 | 10600 – 10731 | 6968 – 7037 |

The same host class read the old main at 13084 on the morning of the 17th, so the
machine had not changed. The triangles had not changed either: 3,287,381 → 3,287,408
at full, and 976,284 at light on both sides. The 9V74 entry moved the same way
(full 9839 → 11444 – 11476).

## Bisected on the steward runner (also an EPYC 7763, 4 cores)

`tools/measure_still_frame.mjs --only desktop --tiers full --stands town_backyard`,
published mirror at each commit. This runner reads about 16 % slower than the CI
host carrying the same CPU string (15271 vs 13185 at 48fa0caf8), so these numbers
are compared with each other, never with the ceiling.

| # | commit | full ms |
|---|---|---|
| 0 | 48fa0caf8 (last green) | 15271 |
| 28 | 95e372011 T-2692 | 15428 |
| 31 | bb9c3e902 T-2702 | 15316 |
| 32 | e1f2033ef T-2697 | 15270 |
| 33 | c9df69f71 T-2669 | 15368 |
| **34** | **be5fdccc1 T-2613** Navigator landing replaces Tap to enter | **18658** |
| 37 | 282e9e5c6 T-2704 | 18662 |
| 46 | 6d4324101 T-2709 | 18944 |
| 56 | c1228fad7 | 19257 |
| 83 | 529f58a61 (first red) | 19338 |

A layer attribution (`--attribute`) on 48fa0caf8 against dev 8dc1420ab: every layer
cost 16 – 35 % more for the same triangles (trees 6492 → 8172 ms at 993,644), and so
did the frame with every layer hidden (91 → 122 ms). Canvas, pixel ratio, render
passes and shadow map were the same (1280x800, 1, one pass, 4096²). It was something
over the canvas.

## The cause: the trip blur, frozen by the instrument

T-2613 gave the gate `backdrop-filter: blur(12px)` for the trip, up from the 2 px it
had always had, easing to `blur(0)` as Home turns over (`css/walk.css`). The tool
stopped the page's loop at `ready`, the first instant of the trip, so every stand was
timed under the 12 px blur, a moment a visitor sees for about a second and never at a
stand they walked to. The compositor re-reads that backdrop under the device on every
frame drawn.

A/B on dev 8dc1420ab, this runner, full, town_backyard:

| what was timed | full ms |
|---|---|
| as the tool read it (frozen at `ready`, gate at blur(12px)) | 19007 – 19280 |
| the gate's backdrop-filter forced to none | 15951 |
| **the tool waits for Home (welcome, transitions finished): backdrop none** | **15730** |
| the same wait with Home put back to `blur(0)` | 15737 |

So the 12 px trip blur was 3.1 – 3.6 s of the frame at full. `blur(0)` costs nothing
measurable (Chromium drops a zero blur), so Home's CSS is left as T-2613 wrote it.
Balanced and light hardly moved with the blur on this runner (12185 → 12268 and
7956 → 7935 ms). What they gained since the ceilings were set on 2026-10-04 is
content: balanced 2,472,178 → 2,563,150 triangles and light 976,284 → 998,964 since
48fa0caf8 alone.

## The fix

`measure_still_frame.mjs` now waits after stopping the loop, up to 60 s, for Home
(`welcome`) or the gate down, then up to 5 s for the gate's own animations to finish.
Every reading prints and records (`gate` in `--json`) the state it was timed under:
on this runner, `gate up, welcome welcome, backdrop none`, settled 884 ms after the loop
stopped. The `--arrival` read, which times the arrival screen with the loop running,
is unchanged.

## Not settled here

- The trip blur's own cost is real for the second or so that the trip is on screen,
  and on a phone GPU it is unmeasured. That is T-2613's design (§05) and not a
  still-frame question.
- This runner and the frame-time workflow's host both report "AMD EPYC 7763, 4 cores"
  and read 16 % apart, so a steward-runner `--gate` on a 7763 fails on code CI passes.
  The ceilings file keys machines by CPU string; it cannot tell the two apart.
