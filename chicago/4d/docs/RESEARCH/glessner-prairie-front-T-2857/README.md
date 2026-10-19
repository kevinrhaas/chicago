# Glessner's Prairie front, read against HABS sheet 6 and its three street photographs (T-2857)

T-2851 asked for the Prairie front's street openings and entry alignment, roof framing and
the main roof and stack heights to be read and built against Taylor 2135, HABS 16 and HABS 17.
It was split: this is the reading; **T-2858** builds what it found. Nothing in the scene
changed in this piece.

`read_front.py` (in this folder) re-derives every number below from the picks written in it.

## How it was read

The three cameras are weak instruments for this question. Taylor 2135 is fitted on five
controls for seven unknowns; HABS 16 and HABS 17 are T-2200's frozen cameras, whose
residuals refer to an older mesh (HABS 17's withheld checks were 33.7 px rms). A difference
read through one of them can be the camera's.

So the openings were read **without a camera**. Along one course of a plane wall, a
photograph is a one-dimensional projective map of the wall: three numbers fit it, and every
further point is a check (the cross-ratio is the same in the photograph and on the wall,
whatever the camera). The first-floor jambs and the front door were picked on each
photograph and fitted against the model's own opening schedule (`form.openings_prairie`).

HABS sheet 6 — the 1965 front elevation, plotted photogrammetrically from a phototheodolite
survey and the source the schedule cites — was re-measured at full resolution off its feet
scale bar (75.37 px/ft). Its Prairie front measures 73.98 ft between its corners against the
printed 74'-0", so the sheet reads true at that scale.

## What it found

**1. The openings are right relative to each other.** Ten jambs fit the model's spacing to
1.50 px rms on Taylor 2135 and 1.62 px on HABS 17; fourteen fit to 3.30 px on HABS 16. No
opening on the front is out of step with the others by as much as a picking error.

**2. Sheet 6 puts the north-end openings further north than the model does.** Centre
shifts, sheet minus model, positive toward 18th Street:

| opening | model (ft from N) | sheet 6 | shift |
|---|---|---|---|
| first-floor A (northmost) | 8.1–12.0 | 7.19–11.65 | **+0.63** |
| first-floor B | 16.9–20.8 | 16.28–20.67 | **+0.38** |
| front door (fan centre) | 32.9 | 32.53 | +0.37 |
| second-floor north group of three | 9.3–19.4 | 8.98–19.12 | +0.30 |
| second-floor group of four | 26.2–40.0 | 25.95–39.88 | +0.18 |
| first-floor D, C; the south three, the single, the pair | | | -0.02 to +0.20 |

The schedule's note gives its own tolerance as ±0.3 ft. A, B and the door are outside it.
The sheet also draws every first-floor light 4.3–4.45 ft between its outer lines, where the
model builds 3.9 ft; the second-floor groups agree with the sheet's outer lines to 0.1 ft.

**3. The NE corner stays within the evidence.** Fitted on the openings alone, both NE
photographs put the NE corner nearer window A than the model does, by 2.0 ft (HABS 17) and
2.6 ft (Taylor). HABS 16 puts the south corner 0.9 ft nearer the south openings. Against sheet 6's
positions those become 1.3–1.9 ft. But each figure is an extrapolation 8 ft past the last
fitted jamb, and the picks stand on the downspouts: sheet 6 draws them 0.90 ft (north) and
0.82 ft (south) in from the corners. The corner is not a finding against the sheet. T-2858
rules it once the openings are moved.

**4. Taylor 2135's misfit is the camera.** Its two Prairie-corner controls are the
downspouts, not the corners. Through it, every first-floor jamb lands 20.5 px left of the
photograph (21.6 px rms), and the three stacks land 15–22 px left too. Openings and stacks
are independent elements and they shift together, which is a registration error, not a
building error. Moving the two controls onto the sheet's downspout positions alone does not
cure it (18 px), because five controls are too few. T-2858 refits it on the openings and
keeps the stacks as withheld checks.

**5. The main roof and stacks agree.** On Taylor 2135 the three stack tops are within 2 px of
the photograph (south +2, middle −1, north +1; about 0.05 m at the stacks), and the ridge is
within 4–8 px. HABS 16's plate cuts the roof about 1.5 m above the eave and shows the eave
line and the south leader head where the model has them. HABS 17's north stack reads about
16 px high, but that is within its camera's 33.7 px check residual and is not a finding.

## Where each pick was read

- Taylor 2135 and HABS 16/17: off the committed side-by-sides in
  `docs/RESEARCH/photo-match/glessner_house/`. The photograph is the left panel; the render
  starts at x 1624 (Taylor) and 1824 (HABS). First-floor jambs were read at mid-window. The
  door's jambs are the outer reveal.
- Sheet 6: `prairie_1904_v1/research/public/glessner-habs-sheet-6.png`, at the outer heavy line
  of each window. The door was read at its fan's centre, because the fan is drawn and the
  reveal is hatched.

## For T-2858

Move first-floor A, B and the door and the second-floor north group to sheet 6's positions,
and widen the first-floor lights to the sheet's outer lines, or say why the model's 3.9 ft is
the sash and not the opening. Refit Taylor 2135 on the opening jambs with the stacks withheld.
Then re-render the three front views and read the NE corner again.
