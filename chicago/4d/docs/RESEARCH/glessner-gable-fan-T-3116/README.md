# T-3116 — Glessner's 18th Street gable fan against the stack's crest

Piece 2 of 3 of T-3028 (found by T-3024 and T-3065). HABS photographs 14 and 01 both read the
stack's crest about 1.2-1.6 ft nearer the gable's fan than built. Sheet 6 prints the crest
(48.62 ft over the door), so the fan was the one to read.

**Acceptance, stated before the work:** the fan's height read against sheet 6 and both
photographs, ruled, built, Glessner rebaked, every Glessner view re-rendered, and HABS 17's
stack proportion above the coping re-read.

## Why camera-free

Sheet 6 is the Prairie Avenue elevation; it draws the 18th Street gable edge-on, so it gives
the crest, the stones and the coping's junction but not the fan. Neither camera can be trusted
up there either: both are solved on controls in the north wall below about 25 ft, and both
draw sheet 6's crest high (HABS 14 by about 15 px, HABS 01 by about 12). So each photograph is
read on its own vertical through the stack and the light, scaled by heights the photograph
does not set: sheet 6's crest and both stones (T-3024's record) and the north pairs' sill and
head (T-2850, solved on HABS 13 and 14 together). HABS 14 is inclined, so that vertical is a
1-D projective map (three parameters, seven anchors, residuals 0.14 ft at most); HABS 01 is
level, so it is linear. The same fit run on the render, with the render's own rows, returns
the built heights (HABS 14 within 0.25 ft, HABS 01 within 0.3), and that method error is
taken off the photograph's reading. `read_fan.py` holds the picks and re-derives
`readings.json` (`--check` compares).

## Readings (photograph over the build, ft)

| | HABS 14 | HABS 01 |
|---|---|---|
| fan's crown (built 39.15 ng) | +1.39 | +1.00 |
| light's round head (35.2) | +1.23 | +1.00 |
| transom (33.14-33.88) | +0.54 to +0.70 | not resolved |
| light's sill (29.0) | +0.78 | +0.52 |
| coping meets the stack (43.3) | -0.53 | -0.79 |

Both photographs show the fan's crown standing as far over the light's head as built (69 px
in both in HABS 14; within 3 px in HABS 01), so the ring's 4.7 ft stands and the light and fan
move together. HABS 14's pairs are read at the camera's rows (its solve fixes them; the print's
white frames and the render's dark ones are not the same edge); read at the print's frames
instead, the fan's crown still comes out +1.36 to +1.50.

## The ruling

The light and its fan are raised **1.0 ft**, the mean of the six fan, head and sill readings
(0.99), +/- 0.4 ft: sill 30.0, transom 34.14-34.88, spring 35.45, round head 36.2, the fan's
crown 40.15 ft ng. The light's width (1.5 ft) and the ring are not touched. Nothing about the
stack, the coping or the rakes moves.

## Result

- `habs14-photo-before-after.jpg`: the photograph, the render before, the render after. Through
  HABS 14 the crest now stands 147 px over the fan's crown against the photograph's 142 (162
  before); the same fit on the new render reads the fan's crown 39.91, head 36.05 and sill 29.94
  against the built 40.15, 36.2 and 30.0, the method's own offset.
- `habs17-photo-before-after.jpg`: HABS 17, which nobody had read for this, is the check. From
  the north-east it resolves the fan's crown 92 px under the crest; the render had 101 and has 91.
- Every Glessner view is re-rendered from the rebaked master, and every verdict kept: the renders
  differ from the old ones at the gable's light and fan and otherwise only in scattered shading
  noise.

## The coping's junction (T-3115's note)

T-3115's "about 13 px under the 1886 stone's foot" was a raw relative reading on a 3x crop.
Read on the photograph's own rows, the junction stands about 8 px (0.5 ft at 16 px/ft) under
the stone's foot, and the camera-free fit puts it at 42.6-43.0 ft ng (HABS 01: about 42.5),
where the build has 43.3 and sheet 6 draws 43.5-43.7. T-3024 ruled the junction at the middle
of sheet 6 and the photographs; these readings fall inside that spread, so it stands. It is
handed to the sign-off (T-3117) with the stack's proportion, not rebuilt here.

## HABS 17's stack proportion

Re-read with the fan raised: neither the stack nor the coping moved, so the proportion T-3024
and T-3065 carried (about 1.15 of the seen width above the junction in the photograph against
0.95 in the render) is what it was, and stays open on T-3117.

## Found

The light reads wider in both photographs than its built 1.5 ft: about 38 px against the
render's 27 in HABS 14 and about 10 against 7 in HABS 01, roughly 2.1 ft. Not built here (filed
as its own ticket).
