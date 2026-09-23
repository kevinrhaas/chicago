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
* **A pre-cut chart or sounding would replace most of this file**, and should. What is written
  here is Wright's 1834 reading with the harbour works taken out of it and a stated distance
  laid on top; it is the best available reading of the 1812 mouth and is graded `inferred`
  throughout for exactly that reason.
