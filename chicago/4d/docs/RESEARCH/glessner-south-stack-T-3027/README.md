# T-3027 — Glessner's south stack in Taylor 2135, read against HABS sheets 6 and 4

T-2858 refitted Taylor 2135's camera on the ten first-floor jambs and withheld the three stacks
as checks. Through that camera the south stack's north face read 14.6 px left of the
photograph, the middle stack's 7-8 px and the north stack's within 4 px. That gradient along the
roof does not show in the jambs below. This piece reads the south stack's plan place
(W 14.18-21.8, S 57.2-61.2) against the sheets.

**Ruling: the stack stands where it is built, and nothing is moved.** What is left belongs to
the camera, and T-3058 owns it.

`python3 read_stack.py` writes `readings.json` (about a minute; the refits dominate).

## The sheets

| | sheet 6 (front elevation, 1966, photogrammetric) | sheet 4 (Section A-A, 1963) | built |
|---|---|---|---|
| south shaft, S | **57.14-61.07** | 58.48-61.59 | 57.2-61.2 |
| middle shaft, S | 25.57-28.26 | 26.67-28.72 | 25.8-28.6 |
| east feet | south 41.32 ft, middle 42.62 ft over the door: the south **1.30 ft lower** | — | 1.36 ft lower (east faces W 14.18 and 15.55) |
| west feet | — | **level**, y 2150 and 2148 | both west faces W 21.8 |

- Sheet 6 is plotted from phototheodolite pairs. Its horizontal scale is T-2857's feet bar,
  75.4 px to the foot, measured from the north corner. Its vertical scale is the printed 0.00
  and 48.62 leaders, the pair T-2222's toe heights stand on. The shaft edges are the drawn lines.
  The feet were picked by eye on full-resolution crops, at the foot of each stack's flashing,
  +/- 3 px.
- Sheet 4 is hand-drafted, and T-2206 already gives it about +/- 1 ft. Its scale is T-2206's 74-ft
  wall-to-wall calibration. The rock-faced outline is read as the median over its rows. It draws
  both stacks narrower than sheet 6 and about 1 ft further south. Its feet are the useful
  reading here: both west aprons stop at the same height. Its south stack's south-west corner
  is behind the stair tower's roof line.

## What the photograph would need

- Through the refitted camera the south stack's top box is **95 px across, against the
  photograph's 96**. The photograph shows the same stack, displaced as a whole.
- Moving the stack alone to close its north face would take **1.5 ft north** or **2.05 ft west**.
  - 1.5 ft north: sheet 6 draws that face 0.06 ft from where it is built. Sheet 4 puts the stack
    south, not north.
  - 2.05 ft west on both faces: it would raise the east foot about 2 ft on sheet 6's 45° slope,
    where the reading agrees with the build to 0.06 ft relative to the middle stack. It would
    lower the west foot about 4 ft down the court slope, where sheet 4 draws both feet level.

So the stack's place cannot carry the offset.

## The camera

All refits use T-2858's solve: its controls, its ten jambs and its starting grid.

| refit | principal point | jambs + controls rms | south | middle | north |
|---|---|---|---|---|---|
| committed (T-2858) | held at T-2221's (415.5, 815.5) | 1.36 | -14.6 | -7.8 / -6.6 | +3.8 / +0.5 |
| stacks admitted as controls | held | 1.49 | -13.0 | -7.2 / -5.7 | +5.4 / +2.4 |
| freed, south withheld | (573.7, 760.9) | 1.97 | **-7.3** | -4.6 / -2.7 | +1.3 / -2.3 |
| freed, all three fitted | (591.4, 749.9) | 2.17 | -5.0 | -3.5 / -1.5 | +1.9 / -1.6 |

(px, render minus photograph, left / right edge; the south stack's left edge is not read on
the render.)

- With the principal point held, the camera cannot reach the stacks at all. Freed, it predicts
  the withheld south stack at -7.3 px instead of -14.6.
- So about half the gradient is the principal point. Taylor worked with a view camera whose lens
  shift is unknown, and the print is cropped. The other half is not explained.
- The freed solves have several minima. The first trial, on a coarser starting grid, landed at
  different numbers. So no camera is adopted here.
- T-3058 owns the camera: the principal point, the cap-overhang correction carried from T-2221's
  render, and the picks. Changing the camera also means re-rendering the side-by-side and
  re-reading T-3045's courses through it, which is more than this piece.

## On the match record

The south-stack item in `data/reference_views/glessner_house/taylor-2135-ne.match.json` is
closed as this ruling. A new open item, T-3058's, carries the camera, so the offset still shows
as open.
