# The 1812 shore, and the ten metres that made it adoptable

**Date:** 2026-09-17 · **Ticket:** T-1242 (piece 1 of T-0468) · **Subject:** filling
`shore_1812_pre_cut`, the shoreline state `docs/EPOCHS.md` has carried as `geometry: null`
since T-1152 · **Outcome:** the state has its own derived planform; the drafted piers and the
shore they caught are out of it; the natural mouth is set at Swearingen's half mile, and an
1834 instrument survey turns out to agree with a distance paced in 1803 to within 9.2 m.

## 1. The problem the state was reserved against

`data/terrain/shoreline_states.json` exists because a scene must not find a shoreline by
picking a convenient GeoJSON file. The 1812 and 1880s states were written as deliberately
empty addresses so that an 1812 scene could not quietly render the 1835 coast — the coast
with a 200-ft cut through the bar and two piers running into the lake, neither of which
existed in 1812. `tools/check_shoreline_states.py` has been failing on exactly that since
T-1152.

Filling the address has one hard obstacle: **there is no survey of the pre-cut mouth.** The
earliest instrument reading of this landform is Wright's of 1834, drawn after the cut and
showing the bar as an island because the cut had made it one.

## 2. What was decided, and what each departure rests on

The state is **derived rather than traced**, by `tools/derive_shore_1812.py`, from two
committed inputs and nothing else: `data/terrain/1812_mouth_readings.json` — which holds only
statements somebody made — and the Wright 1834 trace. Three departures from Wright, each
stated in the tool and gated:

| departure | rests on |
|---|---|
| the pier faces and the shore north of the pier head are dropped | the 1834 feature's own note ("between the piers this is not a natural shore") and the 1834 epoch's note that sand is *accreting* north of the north pier. The 1834 line there is recorded on the state as an **eastward bound** on the 1812 shore, not as it. |
| the bar runs to the mainland | the landform's behaviour: a baymouth spit is the reason the river was deflected south at all, and Swearingen describes the consequence in 1803 — the river stood "dead water, owing to its being stopped up at the mouth, by the washing of sand, from the lakes". The isthmus's *shape* is not claimed; see `docs/LIBERTIES.md` L240. |
| the mouth stands at the half mile below the fort | Swearingen, 17 August 1803, "a half mile above the mouth" — tier 1, written the day he arrived. |

## 3. The cross-check, and why it is stronger than the one in `swearingen_1803.md`

`docs/RESEARCH/swearingen_1803.md` § 7 measured the half mile against the committed trace in
2026-08-11 and reported that the 1834-mapped channel was "at least 560 m longer". That
comparison walked the **traced shoreline to the edge of the tracing window** — the memo said
plainly it was "a consistency, not a measurement" — and the window has since moved (T-0799).

This slice measures the thing the statement is actually about: **the tip of the bar**, which is
where the mouth was.

| station | reading | where it lands |
|---|---|---|
| Swearingen's half mile, 1803 | 804.672 m along the west bank from the fort anchor | local **E +1163.84, N −426.75** |
| Wright's bar tip, 1834 | read off the committed trace | local **E +1346.94, N −435.95** |
| "near present Madison Street" | Madison's platted centreline, `data/streets/1835.json` | local **N −519.05** |

Swearingen's station and Wright's bar tip are **9.2 m of northing apart** — inside the ±20 m
this trace claims for its own planform, and thirty-one years apart in time. A distance paced
by a lieutenant in 1803 and a surveyor's drawing of 1834 put the natural mouth in the same
place. That convergence is what makes the tier-1 reading adoptable rather than merely quotable.

The Madison Street reading is **94.9 m further south**, and it is a tier-2 compilation saying
*near*. It is kept beside the adopted station as the alternative, in the feature
`mouth_outlet_reading_band_1812`. **Nothing is averaged**, which is the rule the 1835 state's
Wright/Rees band already set for this dataset.

The fort anchor carries its own slack and reports it: the only committed coordinate the fort
parcel holds is the 1833-37 flagstaff, and the west-bank vertex nearest it stands **47.8 m**
away. Swearingen's distance is to the fort *site*, which both forts share, and it was travelled
along the water rather than across the reservation, so the anchor is the bank vertex and the
47.8 m is printed on the band rather than hidden in it.

## 4. What is gated

`tools/check.sh` now refuses a commit in which:

* the 1812 state is not `traced`, or carries no geometry of its own;
* any 1812 feature holds an 1835 feature's own coordinates (aliasing, from the other side);
* the committed file is not what its readings and the 1834 trace derive (a hand edit);
* any 1812 line carries a drafted pier vertex;
* the mouth is resolved to a midpoint between the two readings, or the alternative is dropped;
* any 1812 feature claims `documented`.

Six self-tests break each of those in turn and require the refusal to fire.

## 5. What this leaves open

* **No elevation is claimed by any feature here.** This is planform only. The terrain spec,
  the heightfield and the ground and water meshes are **T-1243**, the second piece of T-0468,
  and that is also where the isthmus of L240 gets a surface or is written down as absent.
* **The river polygon and its banks for 1812 are not written.** They follow the spec.
* **The 1812 lake shore north of the pier root is not claimed** — only bounded. Anything that
  wants it needs a pre-1833 chart, and none has been reached.
* **A pre-cut chart or sounding would replace most of this file**, and should. The one pre-cut
  sheet held, Harrison 1830, has now been measured against it — section 6 — and disagrees down
  the old channel. What is written
  here is Wright's 1834 reading with the harbour works taken out of it and a stated distance
  laid on top; it is the best available reading of the 1812 mouth and is graded `inferred`
  throughout for exactly that reason.

## 6. A second reading: Harrison 1830, measured against this line (T-1286)

**Date:** 2026-10-02 · **Ticket:** T-1286 · **Outcome:** near the fort the only pre-cut sheet
held agrees with this line to within its own claimed tolerance; down the old southward channel
it does not, by about 120 m, and it puts the old mouth about 357 m further north. **No geometry
moved.** Wright carries the state by the owner's ruling of 2026-09-17; this section records how
far the one pre-cut reading sits from it.

**What was measured.** The closed PR's tracer is kept as `tools/trace_shoreline_1830.py`. It
fetches Andreas's 1884 re-engraving of Harrison's plate from the Internet Archive, asserts the
stockade's ink still falls where T-0883's transform puts it (**8.0 px**, inside its 12 px
tolerance), and writes `data/terrain/harrison_1830_pre_cut_reading.geojson` — outside
`epochs/`, so no scene can find it as a shoreline. Re-run on 2026-10-02 it reproduced the closed
PR's two lines byte for byte: `south_shore_pre_cut`, 688.8 m, and `north_shore_pre_cut`,
999.1 m. `tools/measure_shore_1812_harrison.py` then walks both every 2 m and measures each
station to the nearest point on this file's lines, weighting by length. The answer is
`data/terrain/1812_harrison_cross_check.json`; `check.sh` re-measures it, and refuses an
`evidence_limit` that no longer quotes it.

| distance from the fort anchor | Harrison line | median | 90th pct | greatest |
|---|---|---|---|---|
| 0–100 m | 484.7 m | **9.1 m** | 20.8 m | 30.8 m |
| 100–200 m | 839.3 m | 15.8 m | 36.9 m | 71.2 m |
| 200–300 m | 266.1 m | **118.2 m** | 148.0 m | **157.1 m** |
| 300–400 m | 97.7 m | **120.2 m** | 122.7 m | 123.7 m |
| **all 1,687.8 m** | | 17.0 m | 120.2 m | 157.1 m |

| this file's line, nearest | Harrison line | median | greatest |
|---|---|---|---|
| north bank to the pier root | 418.1 m | 14.8 m | 34.7 m |
| west bank of the channel (main stem's south bank included) | 1,108.3 m | 19.6 m | 157.1 m |
| where the spit met the mainland (L240) | 157.0 m | **7.3 m** | 27.9 m |

**What agrees.** Both banks of the main stem, past the fort and west of it, agree to a median
of 9 m within 100 m of the anchor and 16 m to 200 m — inside the ±20 m this planform claims for
itself, and the main stem's banks still agree at 200 m west of the fort (17–24 m). Two
independent readings, one surveyed after the cut and one drawn before it, put the river past the
fort in the same place. Everything over 40 m inside 200 m is one stretch: the old channel's west
bank where it leaves the bend, 150–200 m south-east of the fort, which is where the disagreement
below begins.

**One thing it strengthens.** Harrison's lake shore north of the old mouth runs a median
**7.3 m** from the line this file draws where the bar met the mainland — the attachment that
`docs/LIBERTIES.md` L240 declared from the landform's behaviour because Wright draws the bar as
an island. Harrison, three years before the cut, draws the bar attached there.

**What does not agree.** The old southward channel behind the bar. Where Harrison's west bank
leaves the bend it is 40 m west of Wright's at 150 m from the fort and 71 m at 200 m; beyond
that it sits **120 m west** at the median and **157 m** at worst, down to the foot of his sheet.
It is a divergence that grows down one bank, not a scatter across both. Harrison's bar is short. He letters **"Old Mouth of River very shallow"** at its foot,
local **E +1229, N −69** by the transform; the adopted station (Swearingen's half mile) is at
**N −427** and Wright's bar tip at **N −436** — **357 m and 367 m** further south. His sheet
stops at **N −174**, so it cannot test the adopted station directly; what it says instead is
that the mouth it drew was a third of a kilometre north of it.

**What this does not settle, and why it is filed rather than resolved.** The transform is one
anchor, one scale off the commandant's quarters and one rotation off the sheet's north arrow,
so its errors grow with distance from the fort — a rotation a few degrees out moves a point
400 m away by tens of metres, but 120 m at 250 m would take a rotation of more than 25°, and a
rotation that large would throw the main stem 200 m west of the fort out by about 85 m, where
it agrees to about 20.
The plate admits memory additions and has no scale bar. And the landform moved: Harrison's own
face letters a channel the soldiers cut in 1828 and calls the mouth below the bar the *old* one,
so the outlet of February 1830 need not be the outlet of August 1812, and the cut of 1833 had
four years to work on the bar before Wright drew it. Each of those is a reason the two could
disagree; this ticket does not choose between them, and it does not move the line. The question
is filed on **T-1243**, the ticket that lays the 1812 ground along this channel, which has to
say which of them it is before it grades that ground (the queue was over its ceiling, so the
finding went to the ticket that owns the question rather than to a new one).


## T-2171 — remove the lake-facing notch (2026-10-08)

The owner identified a V-shaped inlet at the north attachment of the sand spit.
It is not a digitised feature: T-2003 joined a 100 ft ribbon to a straight chord
from the river-bank root to the carried north shore. That construction made the notch.

Images inspected: Whistler's 1808 draught (the Quaife 1913 reproduction,
`whistler_1808_fort_dearborn_draught`); the retrospective **Chicago in 1812** map
in Andreas 1884 (`pre_fire_v1/media/images/buildings/chicago_1812_map_andreas.png`,
MEDIA-MAP-CHICAGO-1812-ANDREAS); Harrison's 1830 mouth plan as reengraved in Andreas
(`harrison_1830_river_mouth`); and the Wright 1834 map (`wright_1834`). The first
three support a continuous outer shore rather than this large angular inlet.
Whistler's landscape outside the garrison is not uniformly scaled; Andreas's 1812
map is retrospective, and Harrison depicts a later channel cut by soldiers in 1828.
Wright postdates the harbor cut and piers. None establishes a precise 1812 curve.

The adopted correction is **reconstructed**, not an upgraded historical reading.
A monotone cubic E(N) joins carried bar vertex 3 (E1449.35 N192.99) to carried
north-shore vertex 39 (E1372.66 N405.91), with slopes taken from adjacent retained
segments and clamped to prevent overshoot. Its 24 segments replace only the lake
face. The river-side offset, lower spit, southward channel and outlet stay fixed.
The wider attachment fills the previous artificial indentation without introducing
an 1828 or 1834 opening. Existing uncertainty about the longer carried 1834 shore
and the west-bank comparison remains. L403 records the superseded construction
and what evidence would replace this curve.
