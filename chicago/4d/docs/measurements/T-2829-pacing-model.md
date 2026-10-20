# T-2829 — why Adaptive made turning less steady on the owner's phone

**What this is.** A cause named from the code and checked with a deterministic model:
the frame governor (`renderers/web/js/frame-governor.js`) driven through a simulated rAF
loop fitted to the **Fixed** rows of the owner's reading (T-2733,
`t-2733-owner-phone-1835.txt`). The Adaptive rows are then *predicted* by the model, not
fitted. **It is a model, not a reading.** It shows how the governor's rules act on frames
distributed like his. It does not show how his phone will read. That re-reading is his to
take (below). The tool is `tools/model_governor_phone.mjs`. `tools/test_frame_governor.mjs`
holds its turn result in check.sh.

## The phone draws on a 120 Hz grid, and Fixed already turns faster than 30

The model draws on a vsync grid, holds the thread for a frame's cost (normal, seeded), and
times each draw as `pacing-read.js` does: the rAF time plus a dispatch delay. Fitting each
move's Fixed row (`--fit`) on 120 Hz and 60 Hz grids gives this (misfit is a weighted
squared error, lower is better):

```
walk   120 Hz: misfit  12.0  cost 25±5 jitter 3  ->  170  29.6   6.5  29.6  40.5  46.8   46  0.0
walk   60 Hz: misfit  50.7  cost 18.5±2 jitter 4  ->  165  30.4   7.4  32.6  39.4  45.9   58  0.0
turn   120 Hz: misfit   2.3  cost 23.5±2 jitter 3  ->  185  27.1   4.8  26.3  35.8  40.8   21  0.0
turn   60 Hz: misfit 100.3  cost 16.5±5 jitter 1  ->  199  25.1   8.4  27.2  35.1  37.0   46  0.0
flight 120 Hz: misfit   6.1  cost 25.5±2 jitter 2  ->  167  30.1   4.7  31.2  36.6  39.8   47  0.0
flight 60 Hz: misfit  35.8  cost 21±3 jitter 3  ->  156  32.2   5.1  33.3  38.3  42.9   66  0.0
```

A 27 ms median with a 4.7 ms sd needs a rung between 16.7 and 33.3 ms. A 60 Hz display
has no such rung, and its best fit reads an sd of 8.4. A 120 Hz display (ProMotion) has
one: every third vsync, 25 ms. The p95 of 41 ms in all three Adaptive rows is the next
rung up (5 × 8.33). So on a turn this phone draws mostly every 25 ms, about 37 fps.

## The cause, from the code

At the dev build the owner read, a moving window of 10 frames whose p80 is over 18.3 ms
triggers three things:

1. **Three scale steps, three resizes.** The scale steps 1 → 0.85 → 0.72 → 0.67, one step
   per window, because `stepDownMin` bounds each step. Each step is a `setPixelRatio`, so
   each one resizes the drawing buffer. On this phone the steps buy nothing: the window
   stays on its vsync rung at every scale. The frame is not fill-bound at Low (ratio 1,
   375 × 636).
2. **Then it paces to 30.** At the floor, with p80 ≤ 33.5 ms, `decide` sets pace 2 and
   `shouldDraw` waits 29.3 ms from the last draw. On a 120 Hz grid that is the fourth
   vsync, so every 25 ms frame is held back to 33.3 ms. This matches the owner's
   reading: median 27 → 32, draws 186 → 157.
3. **Each new move starts again.** After any rest of 3 still frames, the governor goes
   back to scale 1, pace 1. So the drive in his reading was about 1 s of unpaced 25 ms
   frames with three resizes, then 33 ms. It measured the transition as much as the
   paced state.

A turn regresses most because its Fixed frames are the fastest (median 27 against 29 and
31 for walk and flight). That leaves the largest gap between what the phone delivers and
the paced 33 ms.

## Model, before and after (5 s a drive, the reading's length; mean of 30 seeded drives)

`rzN` is a resize hitch of N ms added to the frame each scale switch lands on. **No phone
has measured that cost.** The walk and flight Adaptive rows (max 46 and 49 ms, none over
50, three switches each) bound it near 20 ms or less there. Only a 40 ms hitch on every
turn switch reproduces the turn's max 73 and its three frames over 50. However, Fixed
walk also had three frames over 50 ms with no switch at all. So these 5 s samples cannot
attribute those spikes, and the readout now does (below).

Before, with the governor as on `origin/dev`:

```
move    row                 draws  mean    sd   med   p95   max  >33  >50  resizes paced
turn    owner fixed          186  27.1   4.7  27.0  37.0  44.0   16  0.0
turn    owner adaptive       157  32.0   6.5  32.0  41.0  73.0   56  3.0
turn    model fixed          186  26.9   4.8  26.1  35.9  40.9   20  0.0
turn    model adaptive rz0   158  31.7   4.7  32.5  38.8  42.4   58  0.0     3.0   74 %
turn    model adaptive rz20  156  32.1   5.1  32.7  39.6  50.7   60  0.6     3.0   74 %
turn    model adaptive rz40  155  32.5   6.7  32.6  39.6  70.7   59  3.0     3.0   73 %
walk    model fixed          171  29.3   6.4  29.3  39.9  46.2   45  0.1
walk    model adaptive rz0   156  32.3   5.2  33.0  40.4  46.0   64  0.0     3.0   66 %
flight  model fixed          167  30.1   4.7  31.0  36.8  39.7   47  0.0
flight  model adaptive rz0   154  32.5   3.5  33.0  37.4  39.9   65  0.0     3.0   73 %
```

The model predicts the owner's Adaptive turn mean, median and draws from his Fixed turn
alone, with pacing as the only cause. With no hitch, the turn's sd is unchanged and its
p95 rises by 3 ms.

After (this branch):

```
move    row                 draws  mean    sd   med   p95   max  >33  >50  resizes paced
turn    model fixed          186  26.9   4.8  26.1  35.9  40.9   20  0.0
turn    model adaptive rz0   186  27.1   4.8  26.4  35.9  40.9   21  0.0     1.1    2 %
turn    model adaptive rz20  185  27.2   5.0  26.4  36.2  46.7   22  0.1     1.1    2 %
turn    model adaptive rz40  184  27.3   5.7  26.4  36.2  66.7   22  1.1     1.1    2 %
walk    model fixed          171  29.3   6.4  29.3  39.9  46.2   45  0.1
walk    model adaptive rz0   163  30.9   5.8  31.4  40.1  46.1   55  0.1     1.1   34 %
flight  model fixed          167  30.1   4.7  31.0  36.8  39.7   47  0.0
flight  model adaptive rz0   155  32.3   3.7  32.9  37.4  39.8   64  0.0     1.0   67 %
```

At 15 s a mode (the readout's default now), with no hitch: turn 4.8 → 4.9 sd, 36.0 → 36.1
p95; walk 6.5 → 5.8, 39.6 → 40.0; flight 4.8 → 3.1, 36.8 → 37.4.

**What did not change in the model.** Flight's p95 still rises 0.6 ms (37.4 against
36.8), as it did before. Flight's frames already come at 31 ms, so it is still paced, and
pacing moves its p95 from a mix of 25 and 33 ms frames to 33 ms plus dispatch jitter. One
resize remains in each drive of the reading, because each drive starts from the setting
change that clears the mark. In use, the governor steps down once on the first move and
comes back up at the first rest. That first step down is how it learns that scaling does
not pay.

## The fix

- **No pace below the phone's own rate (`ownRateMin`).** If a window's median lies
  between 21 ms and the paced interval, the device has a rate of its own between 60
  and 30, and the governor does not pace it. On a 60 Hz display a median is 16.7 or
  33.3 ms, never in that band, so the 60/30 alternation T-2555 paces is paced exactly as
  before. A test holds this.
- **A pace is earned over 3 windows in a row (`paceAfter`).** This mirrors `upAfter`.
  One 10-frame window whose median lands on 33 ms no longer paces a device for 8 s. A
  probe re-paces on its first window, as before.
- **The ladder stops when a step buys nothing (`stepPaidMs`).** If the window after a
  step down does not lower its p80, the scale steps no lower. This is kept across rests,
  so later moves do not resize at all. It is cleared when the detail tier or the setting
  changes.
- **The readout attributes spikes.** Each row of Read frame pacing now also prints its
  ratio switches, how many of its draws over 50 ms came on a switch (or the draw after
  it), and the share of its draws paced to 30.

## The default

**Adaptive stays the default.** On the owner's numbers:

- Adaptive improved the walk (sd 6.0 → 5.0, p95 43 → 41, frames over 50 ms 3 → 0).
- The turn regression has a mechanism that the model reproduces from his own Fixed row,
  and this change removes it.
- The flight change is small (p95 +3 ms in his reading, +0.6 in the model).

A change of default would be a decision card for him (T-2829's acceptance), not a run's
change. The case for one would be this: his repeat on this build still shows Adaptive's
turn sd or p95 above Fixed's, with switches that are not the cause.

## The re-reading to ask for

Once this is on the dev preview:

1. On the same iPhone, open `https://chicago.polecat.live/4d/dev/1835/`.
2. Enter the town, then go to Settings → Performance → **Read frame pacing**.
3. Leave the length at **15 s a mode** (the default), and leave Sharpness as it is. The
   readout prints it, and the tool sets Light itself.
4. Copy the result and send it back.

It passes T-2829 if the **turn** row reads Adaptive sd ≤ Fixed sd and Adaptive p95 ≤
Fixed p95. The turn row should also show at most one switch and a paced share near 0 %.
If any frame over 50 ms comes "on one", the resize is a hitch on this phone.
