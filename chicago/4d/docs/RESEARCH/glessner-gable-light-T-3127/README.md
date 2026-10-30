# T-3127 — the width of Glessner's 18th Street gable light

Found by T-3116: the light high in the 18th Street gable reads wider in both photographs
than its built 1.5 ft, about 38 px against the render's 27 in HABS 14 and about 10 against 7
in HABS 01.

**Acceptance, stated before the work:** the light's jambs read against the north pairs and
the fan's ring read on both prints; the width ruled; the light rebuilt; Glessner rebaked and
every Glessner view re-rendered.

## How it was read

Both cameras are solved on the north wall's pair jambs (T-2850; HABS 01 is level, by yaw), so
they carry a column across the wall well even where T-3116 found them high up it. Each
jamb is picked as the half-way crossing of a column-mean profile across the dark opening,
carried to the north face's plane through the view's camera (`face_w`, the north pairs' own
jamb reader) and named by its plan W. The same picks on the render of the build return the
built 1.5 ft as 1.43-1.45 (HABS 14) and 1.61 (HABS 01), and that error is taken off the
photograph's reading. The fan is read the same way at the lower ends of its outer ring,
where it meets the courses beside the spring, and scaled by the render's own span. 
`read_light.py` holds the picks and re-derives `readings.json` (`--check` compares).

## Readings

| | HABS 14 sash | HABS 14 head | HABS 01 sash | HABS 01 head |
|---|---|---|---|---|
| light's width, photograph less the method (ft) | 2.08 | 2.12 | 1.90 | 2.10 |
| photograph's centre against the render's (ft, + west) | -0.19 | -0.20 | +0.20 | +0.10 |

The fan's outer ring spans 9.8 ft on HABS 14 and 10.0 on HABS 01 against the built 9.4.

HABS 14 is the finer print here (about 18 px to the foot against HABS 01's 5) and reads the
light 2.08-2.12 ft; HABS 01 agrees within its pixel. The two disagree on the centre, by about
0.2 ft each way, so the centre is not moved.

## The ruling

- The light is **2.1 ft wide**, W 17.75-19.85, on its old centre (W 18.8).
- Its round head stays at T-3116's **36.2 ft** ng: both photographs showed the fan's crown as
  far over the head as built. A semicircle 2.1 ft across rises 1.05 ft, so the spring comes
  down from 35.45 to **35.15**. Sill (30.0) and transom (34.14-34.88) are unchanged.
- The fan's outer radius is measured from the spring, so it goes from 4.7 to **5.0 ft**. That keeps
  its crown at T-3116's **40.15 ft** and makes it 10.0 ft across, which is what both prints read
  (9.8 and 10.0).

## Result

`habs14-photo-before-after.jpg` and `habs01-photo-before-after.jpg` show the photograph, the
render before and the render after. On the rebaked render the light reads 39 px across in
HABS 14 against the photograph's 38 (27 before), and 11 px in HABS 01 against 10.5 (8 before).
Every Glessner view is re-rendered from the rebaked master and keeps its verdict. Only this
light and its fan changed, and every view that shows them was looked at again.

## Still open, handed to the sign-off (T-3117)

- HABS 14 shows the round head standing higher over the transom than built: T-3116 read the
  head 1.2 ft and the transom's top only 0.5-0.7 ft over the old build. That leaves the
  transom about 0.3-0.5 ft low against the current build in that one print. HABS 01 does not
  resolve the transom, so it is not moved on one reading.
- The fan in both prints shows fewer, broader stones than the 11 voussoirs built. Neither
  print resolves every joint, so they are not counted here.
