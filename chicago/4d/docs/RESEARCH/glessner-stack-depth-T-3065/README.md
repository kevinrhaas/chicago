# T-3065 — Glessner's 18th Street stack: the width the obliques missed was the depth

T-3058 freed Taylor 2135's camera and checked the three stacks' widths against the photograph. The
south and middle stacks matched within 0.6 px. The north stack's record box (W 15.25-22.35, S 0-3.1)
came out 8.6 px wider: 82.6 px against the picks' 74. T-3058 read the north face about 6.2 ft wide
in the photograph, against T-2873's 7.1 from HABS 14, and HABS 01 had read about 6.3.

**Acceptance, stated before the work:** read the stack's width and depth through HABS 14 and Taylor
2135 together, and the device's projection; rule or rebuild until the north stack's width check
reads like the other two; rebake Glessner and re-render the four views that show the stack.

`read_depth.py` re-derives the sheet 6 reading and the Taylor projections below into
`readings.json` (`--check` compares).

## What each picture says, and which edge it is

| view | what it sees | box against the photograph |
|---|---|---|
| HABS 14 (1965), square to the face from 4.6 ft east of it | the face's two edges | x 913-1043 against 912-1040. The east rake, drawn through this camera from the Prairie corner, lies on the photograph's along its whole length to the stack's side, so the scale at the stack holds. **7.1 ft stands.** |
| Taylor 2135 (1887-1889), from the north-east | east face (left), north face (right) | the north-west corner and both stones' ends within about 1 px (the stones' shadows, under their proud bottoms, run x 1036-1061). **Only the left edge, the east face's back corner, was off: 987 against 991.5.** |
| HABS 17 (1965), from the north-east | the same two faces | at the cap's top edge the east face is 22 px against the box's 28, the north face 24 against 24; this camera stands about 8 px off the stack |
| HABS 01 (1963), from the north-west | north face (lit), west side (dark) | the dark west side within 2 px; the lit face's east edge 4-5 px in, against a white sky, on a level camera that reads this roof about 2 ft low |

T-3058's "corner" at x 1035 is the vertical joint at the stones' east ends. Through the camera those
ends stand at 1035.5 and the corner at 1028. So in both north-east views the north face is the
box's, and what is short is the east face. That face's width is the stack's depth.

## The depth

HABS sheet 6 is the east elevation. It draws the stack edge-on, so its drawn width is the depth.

| stack | sheet 6, between the outline strokes | recorded |
|---|---|---|
| north | **2.44 ft** (2.39-2.49 over six rows, x 7915-8097) | 3.1 |
| middle | 2.64 ft | 2.8 |
| south | 3.85 ft | 4.0 |

The record carried the north stack at S 0.5-3.1 (2.6 ft) from the Glessner bake (T-1732). T-2214 moved
its face to S 0, flush with the gable, and did not move the back. The stack grew half a foot deeper
with nothing behind it.

## The ruling

**2.6 ft deep (S 0-2.6), the face kept at 7.1 ft.** The strokes give 2.44. The same reading gives the
middle and south stacks 0.15 ft under their recorded depths, so on this record's own reading of the
sheet the north stack is about 2.6 ft. That is the depth it had before T-2214. Taylor's back corner
agrees: 2.45 ft would put it at x 993.7, 2.6 ft at 992.0, and the photograph's edge is at 991.5.
Liberty: `docs/LIBERTIES.md` § `L-glessner-stack-depth-3065`.

**The device's projection stands.** Through the refitted camera the stones fall inside the
photograph's edge: the render's right silhouette is at 1066.5-1067.5 against the photograph's
1067.5-1068.5. The west cross stands about 2 px past the face's edge on one row, which is within a
pixel of the photograph's edge. The crosses are dark quads drawn at the rock faces' furthest reach
(0.104 m), where the rock at those two places reaches 0.06-0.08 m (the GLB's 90th percentile). HABS 14
shows them incised. That is written onto T-3028 (Glessner's sign-off), with the crest's height
against the fan that T-3024 left on this ticket, because the queue is at its ceiling.

## Result

Glessner rebaked (masters, full and light derivatives, the v4 recovery package). Taylor 2135 refitted
by `tools/glessner_prairie_front.py --camera` on the new box:

| | T-3058 | T-3065 |
|---|---|---|
| principal point | 549.6, 712.0 | 564.5, 696.9 |
| focal | 2251 | 2256 |
| pitch / roll | 2.59 / 1.37 deg | 2.99 / 1.32 deg |
| controls + jambs rms | 2.08 px | 2.08 px |
| stacks' centres and tops | 1.6 px rms | 1.9 px rms |
| stack widths: south / middle / north | -0.1 / -0.6 / **+8.6** | -0.0 / -0.6 / **+1.5** px |
| plumb edges' lean rms | 0.0096 | 0.0104 |

`taylor-before-after.jpg` shows the photograph, the render before and the render after, same crop.
The carried proportion item (the stack above the coping's junction, 1.14 of its seen width in the
photograph against 1.03 in the render) was the same error: the seen width falls from 82.6 to about
76 px and the height is unchanged, so the render's proportion is about 1.12.

Left open: the pitch question T-3058 raised (the edges alone give 1.2 deg) still stands, in Taylor's
match record. On T-3028: the crest against the fan, HABS 17's proportion once its camera reaches the
stack, and the crosses.
