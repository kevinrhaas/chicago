---
id: T-0690
title: dev is red at mobile part 8: the road-legibility aid moves the frame by 3 cells where the gate wants 4
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-13
pr: 1256
claimed_by: run 9/13/2026, 10:26:47 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-13T16:06:04.955Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34765103447
---

dev is red at mobile part 8: the road-legibility aid moves the frame by 3 cells where the gate wants 4.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Found by T-0446's run on 2026-09-04, and **proved inherited before it was filed**.

`tools/smoke_renderer.mjs` part 8 asserts that turning the road-legibility aid
full on moves the rendered frame:

    FAIL  mobile 390x780: raising the road-legibility aid reaches the render
          — set to 1, reads back 1: cell delta mean 0.36, worst 3
            (need worst>=4, mean>=0.15)

The mean clears its floor comfortably. It is the **worst-cell** half of the
requirement that misses, by one cell.

**It is dev's, not any branch's.** Run on a clean `origin/dev` worktree at
`a6d8909d`, `SMOKE_VIEWPORT=mobile SMOKE_STAGE=8`, the same assertion fails with
`mean 0.35, worst 3` — the same worst cell, one hundredth apart in the mean. The
T-0446 branch, which adds two streets, reads `0.36 / 3`: it moved the number the
RIGHT way and did not move the verdict.

Worth noting beside it, from the same log and not yet accounted for: the road-band
report in part 7 says **9 bands moved against the bank**, four of them `rose` by
1.3 to 4.4 ΔL* and six of them `ungated` — "was gated when banked and is not gated
now — either the probes stopped projecting or the station moved". A town whose
roads have become markedly more legible on their own is exactly the state in which
an aid that adds legibility would have less left to add, so the two readings may
be one fault. That is a hypothesis and this ticket does not assert it.

Desktop is not measured here — only mobile part 8 was read.

**Acceptance:** either the aid moves the frame by the four cells the gate asks
for, or the gate's worst-cell floor is re-derived from what the aid can actually
do at 390x780 and the reasoning is written down. Whichever it is, `origin/dev`
comes back green at mobile part 8, and the nine moved road bands are explained or
re-banked.

---

**ACCEPTANCE AS WORKED, 2026-09-13 — the first branch, and neither floor moved.**

Stated before working: the aid must move the frame by the four cells the gate
asks for, on BOTH viewports, with the floors left where they are; the movement
report's ten entries must each be accounted for; `check.sh` green.

It is the first branch, and the finding is that the aid was never weak. The
instrument was. `tools/measure_road_aid.mjs` - new here - holds the clock and
takes aid-off / aid-full-on / aid-off-again at five grid sizes. On the published
mirror at `lake_market`, worst reach cell / worst residual cell:

    grid    390x780      1280x800
    12s      2 / 0        2 / 0
    24s      3 / 0        4 / 0
    48s      3 / 0        7 / 0     <- was here
    96s      7 / 0       11 / 0     <- here
   144s      9 / 0       15 / 0

The signature averages luma per cell, so a roadway covering about a tenth of the
frame is diluted inside every cell it only partly covers. R-A1 had already seen
the effect on 2026-08-16 - worst 2 at 12s against worst 6 at 48s, nothing in the
scene changed between the readings - and set its floor from the 48s desktop
reading alone. The residual is 0 at every grid on both viewports, so this is
dilution and not noise.

So `ROAD_AID_REACH_GRID = 96` is read by R-A1's three captures and by nothing
else. `ROAD_AID_MIN_WORST` stays 4 and `ROAD_AID_MIN_MEAN` stays 0.15, each now
about half the weaker viewport's reading - the rule `SHADOW_REACH_MIN_WORST`
beside it was set by. `ROAD_AID_GRID` keeps its 48 and its three other users:
the roughness merge, the facade tone and the shadow reach each derived a floor
against that grid alone, and handing all three a finer instrument would have
slackened three assertions while repairing one.

**THE TEN MOVED BANDS, ACCOUNTED FOR - six of them were this gate lying.** The
report filters the bank by VIEWPORT and compares it against what the invocation
measured. That was honest while all three road stations sat in one part; T-0173
then cut them across parts 7 and 8 and nothing here noticed. So a part-filtered
run compared the bank's whole viewport against the one station it had visited
and reported every band it had not been to as `ungated - either the probes
stopped projecting or the station moved`. Neither had: `SMOKE_STAGE=8` never
goes to `south_water` or `from_above`, which are part 7's, and those six bands
are six of the ten. The filter now takes the stations the invocation actually
read.

The other four are real, they are all `lake_market`, and all four ROSE - mobile
250-600 m by 3.9 dL*, 40-100 by 1.7, 100-250 by 1.5, and 2-40 m from 60 % to
80 % perceptible; desktop the same four bands by 1.9, 1.5, 1.3 and 0.8 dL*. The
roads are more legible than when they were banked, which is the direction this
report exists to notice, and mobile part 7's own gated station checks pass on
dev. They are NOT re-banked here: T-0016's rule is to re-bank in the commit that
moved the numbers on purpose, and this commit did not move them - re-banking
numbers somebody else moved would erase the only evidence that they did.

**Verification, foreground, on the published mirror:**

- `SMOKE_VIEWPORT=mobile SMOKE_STAGE=8` - 17 passed, 0 failed. The aid reads
  `mean 0.26 / worst 6 at 96s`, restored residual `0.00 / 0`. This is the red
  the ticket was filed over, green.
- `SMOKE_VIEWPORT=desktop SMOKE_STAGE=8` - 17 passed, 0 failed, `mean 0.28 /
  worst 11 at 96s`. The other viewport did not pay for it.
- `tools/check.sh` green.

**One thing for the runner and not for the repo:** `check.sh` came up red on an
untouched `dev` at *...and the strip still reads the same off the sheet* with
`ModuleNotFoundError: No module named 'PIL'`. The custom lane pre-installs
`pdftotext`, `tesseract`, `openpyxl` and `pypdf`, and
`read_kinzie_addition_water_lots.py --check-sheet` needs Pillow, which is not in
that list. `pip install pillow` and the step passes. Worth adding to the lane's
install step.

STILL REPRODUCES, 2026-09-13, measured by T-1081's mobile stage-8 leg against the
published mirror on a green `check.sh`: `set to 1, reads back 1: cell delta mean 0.24,
worst 3 (need worst>=4, mean>=0.15)` — byte-identical to the reading dev's standing record
has carried since 2026-09-13T01:14. The mean clears its threshold and only the worst cell
falls short, by one. With T-1081 landed this is the LAST standing red on dev's smoke, and
mobile part 8 is the only part it holds.
