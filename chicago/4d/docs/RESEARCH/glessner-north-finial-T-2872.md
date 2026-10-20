# T-2872 — Glessner's north tower finial, ruled against HABS 01 and 14

**Ruling: the plan is kept** (centre W 41 / S 7.35, drum radius 7.35 ft, eave
radius 9.35 ft, tip 44.9 ft above north grade). HABS 14's miss at the finial is
that camera's depth, not the tower's plan. Nothing in the model moved.

The reading is `data/comparisons/glessner/north-finial.json`, written and checked
by `tools/glessner_north_finial_read.py` (a `check.sh` step). No new archival
source was used: the photographs are HABS IL-1015 photographs 1 and 14, the
cameras are the committed ones, and HABS 14's re-solves use
`tools/glessner_north_pairs.py`'s own picks and solve.

## The question

On HABS 14's re-solved camera (T-2850/T-2855) the built finial tip lands at
x 1329, y 343 against the photograph's 1302, 354 — about 29 px, image-right
and high. HABS 01 holds the same tip within 3 px. Triangulated from the two
photographs' tips alone, the tip sits at about W 39.7 / S 8.8, height 44.9 ft
(both tips then within about 3 px). A drum still tangent to 18th Street and
still ending at W 48.3 would carry that tip with a radius of about 8.8 ft. The
ticket asked for that plan to be built or argued.

## Three readings

| | built (W 41 / S 7.35, r 7.35) | tips-only plan (W 39.7 / S 8.6, r 8.6) |
|---|---:|---:|
| HABS 01 tip | 3.0 px | 3.2 px |
| HABS 14 tip | 29.4 px | 2.7 px |
| HABS 01 cone width growth, model / photograph | 1.12 | 1.30 |
| HABS 01 silhouette fit, worse than the best size by | 0.45 px | 1.44 px |

1. **The tips.** Each photograph's tip is read by rule: the topmost row darker
   than grey 110 in a fixed window, the centroid of its dark pixels over three
   rows (HABS 14's window sits right of the utility pole). They agree with the
   picks earlier work used (HABS 01 428/460, HABS 14 1302-1304/353-355).

2. **The cone's size, from its silhouette.** A wider drum carries a wider cone,
   so the cone's outline is a reading of its radius that the tip alone cannot
   give. HABS 01's camera was fitted with the tower left out, so it can measure
   the tower without having been bent to it. There the cone stands against open
   sky for 12-34 px below the tip, clear of the stack to its right and the roofs
   to its left; both edges are read row by row at the sky/slate midpoint. In
   HABS 14 the pole covers the left edge, so only the right edge is read, 14-104
   px below the tip. For each size of the upper cone (rise, centre and height
   kept) the model's edges are slid freely in the image onto the photograph's,
   so the camera's offset and the finial's length drop out, and only the
   outline's shape is compared. HABS 01 fits best at **0.9** of the built size
   (0.8-1.0 within half a pixel); HABS 14 at **0.82**. The wider cone the
   tips-only plan needs (1.15 of the built at the cone's base) fits HABS 01 1.4
   px worse than the best, and is outside both.

3. **HABS 14's own depth.** Every control in that camera lies in the north
   wall's plane except two: the north stack's crest and a "tower depth"
   control, both model-derived, which it misses by about 15 px each, and its
   eye sits on the 2.5 m height bound. A plane alone cannot separate distance
   from focal length. Re-solved with the stack crest only it takes a focal
   length of 944 px (from 1476) and puts the built tip at 1307, 401; with the
   tower-depth control only, 1689 px and 1336, 341. The built tip moves
   **28.5 px** across those solves, the size of the miss; all three fit the
   wall's controls at 6.4-8.8 px RMS.

## Why the plan is kept

The tips-only plan rests on HABS 14 placing an off-plane point to within a few
pixels, which that camera cannot do: its own two off-plane controls disagree with
it by 15 px, and dropping either moves the tip by as much as the miss. HABS 01,
the one camera fitted independently of the tower, already holds the built tip,
and its view of the cone refuses the wider drum the tips-only plan needs. Moving
the centre to W 39.7 / S 8.8 without widening the drum is not available either:
the drum would then stand about 1.45 ft back from the 18th Street wall, against
HABS 01, 13 and 14, which show the flat north face turning straight into the
curve (T-2470).

Both silhouettes lean narrower than built (0.9 and 0.82). HABS 01's half-pixel
band still includes the built size, and HABS 14's reading depends on that camera's
pitch, so this run does not change the cone. If later work narrows it, HABS 01's
band (0.8-1.0) is the evidence, and the `check.sh` step holds the record inside
it.

## What the gate holds

`python3 tools/glessner_north_finial_read.py --check` fails if the reading is stale
(any committed camera, photograph or tower value moved; numbers compared to 0.5),
if the record's tower puts HABS 01's tip more than 5 px off, or if its cone fits
HABS 01's silhouette more than 1 px worse than the best size. The tips-only plan
fails the third test (1.45 px).

## Limits

The silhouette is read over the cone's top two to six feet; a cone whose slope
changes lower down would not show here. HABS 14's reading of the cone's size depends
on its camera's pitch. The finial's own length (the model's 1.5 ft) is not read
reliably by this method (the two photographs give 0.3-1.1 ft) and is not ruled.
