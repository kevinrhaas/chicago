# The Sauganash, against its four views — the measured reading (T-0617)

> **HOW A ROW OF THIS TABLE MAY BE ESTABLISHED, AND IT IS NOT BY LOOKING.** This file
> is written under T-0197's rule, which the Fort Dearborn table earned the hard way:
> eight rows there were written by eye and three were struck as wrong inside a week,
> two of them after becoming tickets whose runs were spent proving the ticket wrong.
> So: **a row states a measurement, names the tool that made it, and prints the
> number.** Every figure below comes out of `tools/measure_sauganash_plate.py`, is
> banked in `tools/sauganash_plate_baseline.json`, and is re-checked by
> `tools/check.sh` on every run — a detector edit that moves a number cannot do it in
> silence. A row that could NOT be measured says so and is graded `unresolved`; it may
> not seed a ticket.

**Run 2026-09-04.** The owner deposited four views of the Sauganash on 2026-09-03 with
the report that the model is *"missing a fair amount of detail, like the door, the
windows, the roof, etc."* **T-0616** filed the brief and split; this is its first
piece, the reading. **T-0626** is the second piece, where the reading is spent on the
record and the geometry — and it is the only place the plan may be changed. Nothing
here changes a record.

## 1. The four views are one witness and three copies

| view | file | what it is |
|---|---|---|
| **Braunhold** | `chicago/reference/images/chicago/chicago_sauganash_hotel_1831.jpg` (2017 × 1296) | F. Braunhold's pen engraving, *"Copyright secured by A. T. Andreas, 1884"*. The sharpest and largest of the four. **This is the plate that was measured.** |
| Petford | `…/sauganash-hotel/sauganashhotel.jpg` (1200 × 847) | C. F. Petford's watercolour, lettered *"Sauganash Hotel. 1831."* Same composition, same station, same five bays; coloured. |
| Trowbridge | `…/sauganash-hotel/sauganash2.jpg` (860 × 508) | The wash already recorded at `data/sources/trowbridge_sauganash_hotel.json`, undated, its companion signed 1902. Same composition with figures added. |
| the thumbnail | `…/sauganash-hotel/images.jpeg` (192 × 135) | A watermarked stock-library thumbnail of a coloured version of the same composition. At 192 px it carries no measurable detail and is used for nothing. |

`docs/RESEARCH/sauganash_hotel.md` § 4 already treats the Andreas engraving and the
Kurz & Allison panel as **one witness and a copy**, and the Trowbridge source record
extends that to a third. The fourth view does not change it. **All four are the same
composition seen from the same station**, so agreement among them is evidence of
copying and not of corroboration, and the reading below is a reading of ONE sheet.
That is stated at the top because it is the single most important thing about this
material and the easiest to forget when four files sit in a folder.

## 2. What makes these numbers measurements

Nothing on the sheet can be read with a ruler laid on it: the building is drawn in
two-point perspective. Two things make the figures below real, and both are in the
tool.

**The wall's own horizontals are the ruler.** A clapboard wall and a log wall are each
a stack of world-horizontal lines at one pitch. The detector shears a patch of blank
wall through 201 candidate slopes and takes the one that stacks every line on itself
(maximum variance of the row projection); the pitch then falls out of that profile's
autocorrelation. Six patches of siding and three of logs are read this way, and each
box is a box drawn on **plain wall**, never round a feature.

**The scale datum is stated and it is a person.** A standing adult is taken at
**1.70 m**, hat included, because the hat is what the detector measures to. The two
men on the walk in front of bays 1 and 2 measure **145 px** (`walk_left` 147,
`walk_right` 143 — a 4 px spread on 145). They stand a pace forward of the wall and
the datum is generous, so **every metre below is a LOWER BOUND**. That bias is stated
rather than corrected: correcting it would mean claiming a depth the plate does not
give.

**The plate then tests itself, and it passes.** The south-east face's own horizontals
converge too weakly among themselves to fix a vanishing point — four patches of siding
600 px apart differ by 0.016 in slope, inside the detector's noise, and the crossing
lands *inside the wall it belongs to*, which is the arithmetic saying it has no answer.
The **ridge** fixes it: the same world direction, drawn 300 px higher, so its slope is
genuinely different. Three of the four siding patches autocorrelate well enough to be
admitted (+0.37, +0.30, +0.23; the fourth, `se_1`, reads +0.11 and is dropped), and
with the ridge in, those **four lines cross at x = 6462**, residual 45 px, on a horizon
at **y = 917.5**.

> **The horizon lands at the standing figures' eye level.** The two men's hats top out
> at y = 900 and y = 902 and their heels at y = 1047 and y = 1045; a horizon at 917.5 is 16 px below the hat on
> a 145 px figure — eye height on a standing man. Nothing in the construction knew
> about the figures and nothing about the figures knew about the ridge. **This is the
> strongest single result of the pass**: the sheet's geometry and its staffage agree,
> and the 1.70 m datum is not floating.

## 3. The table

Confidences are the project ladder. `documented` requires a source record; `inferred`
requires the reasoning to be stated; `unresolved` is a row the plate does not answer
and is not a licence to guess.

| # | what the plate says | the number, and the tool | grade |
|---|---|---|---|
| 1 | **The south-east front is five bays.** Five openings in the upper storey and five in the ground storey, detected as the only VERTICAL ink on a wall of horizontal siding. | `measure_sauganash_plate.py` → `se_face.bays_upper = 5`, `bays_lower = 5` | `inferred` — one plate, tier 5 |
| 2 | **The door is the MIDDLE bay**, not an end one. It is the darkest opening on the ground storey (an unlit room behind an open door; nothing else on the sheet is inked like that, `ink 0.494`). | `se_face.door_index_1based = 3` of 5 | `inferred` |
| 3 | **Those five bays are EQUAL on the ground.** The drawn gaps fall 169.2 → 161.1 → 153.0 → 137.5 px, a 20.4 % spread that reads as an irregular rhythm and is not one: rectified against the face's own vanishing point they are **0.997, 1.011, 1.020, 0.972** — equal to ±2.4 %. | `bay_rhythm.rectified_gaps` | `inferred`, and it is a **refutation of the impression** |
| 4 | **The sheet is a CONSTRUCTED perspective, not a free-hand impression.** Two orthogonal horizontal vanishing points of one real camera satisfy `f² = -(v1-p)·(v2-p) > 0`. Here `f² = 1.343 × 10⁷`, i.e. **f = 3665 px** on a 2017 px sheet — a plausible lens, not a contradiction. Independently, the station that would make the five bays equal (`x = 5814`) agrees with the station the building's own lines give (`x = 6462`) to **0.9×**. | `perspective_test`, `bay_rhythm.equal_bay_station` | **This is the row that licenses rows 3 and 8.** A retrospective view that passes this test may be read for PROPORTION; it still may not drive a coordinate. |
| 5 | **The doorcase is 2.39 m over its jambs and sidelights**, with an opening 1.92 m tall below the head. | `door_detail.doorcase_m`, `opening_m` (lower bounds) | `inferred` |
| 6 | **The door carries a glazed TRANSOM.** Below the solid doorcase cornice and above the head of the opening at row 808 there are 45 rows whose mean ink is **0.464** — ink with white in it, which is glazing, where the opening below runs 0.86. | `door_detail.transom` | `inferred` |
| 7 | **The clapboard is drawn at 15 px of exposure = 0.176 m** (about 7 inches) at the stated datum. Two patches of blank wall give 15 px outright (autocorrelating +0.30 and +0.23); a third locks onto the 8 px half-period, and the median of the three is the number taken. | `clapboard.median_px`, `exposure_m` | **`inferred`, and the number is a fact about the ENGRAVER.** 0.18 m is coarse for period weatherboard; a plate cannot resolve a 4-inch exposure at this scale, exactly as `p4_0` could not resolve the fort's pickets and drew them three times coarse (T-0185). Do not adopt it as a material dimension. |
| 8 | **The annex is a LOG wall and the block is not.** The annex's courses run **22 px = 0.258 m** against the block's 15 px, on three patches autocorrelating +0.48, +0.30 and +0.20. A log course half again the siding's course is the difference the plate is actually asserting. | `annex.median_px`, `annex.autocorr` | `inferred` |
| 9 | **Two chimneys stand clear of the roof**, at drawn x 652–705 (rising 69 px) and x 1358–1403 (rising 61 px). A third stack visible against the block's south-west wall behind the annex roof does NOT clear the roof line and is not counted here. | `chimneys.count = 2` | `inferred` — and it agrees with `docs/RESEARCH/sauganash_hotel.md` § 4, which read two chimneys off the same descent by eye |
| 10 | **The near gable's apex is at (648, 350)**; its left rake is drawn at slope **−0.318** and the RIDGE runs away to the right at **+0.095**. The right-hand line out of the apex is the ridge, not a rake — which is what puts the gable end at the left-front and the long eaves face to the right. | `roof.apex`, `left_rake_slope`, `right_rake_slope` | `inferred` for the arrangement |
| 11 | **The roof PITCH is not read here, and T-0626 found there is nothing on this apex to read it FROM.** This row expected the pitch to fall out of the left line by rectifying the gable-end plane. It does not, because that line is not a rake. Projected onto the vertical through the end face's own vanishing point, at the focal length row 4 recovered, it stands at **1.35 deg** in the world — and the right-hand line at **0.11 deg** — where a 38 deg rake in the same plane would have been DRAWN at image slope −1.99 against the −0.318 measured. **Both lines out of the apex are world-horizontals, so they are two RIDGES at one height meeting at a point, and the pitch is still unread.** `tools/sauganash_apex_lines.py` is the arithmetic, it needs no image library, and `tools/check.sh` gates on it. | `sauganash_apex_lines.py` → `left.world_deg`, `right.world_deg` | **`unresolved` for the pitch, and `inferred` for what the sum found instead** — see row 14 |
| 12 | **The sash heights are not read here.** Sash extents are taken by differencing a window against the same number of columns of blank wall beside it; four of the ground-storey bays have a doorway or a corner board where that blank wall should be, and the storey's five heights disagree by **1.44 of their own mean**. Widths are steady and are reported (upper 0.795 m, ground 0.912 m); heights are not. | `windows.lower.height_resolved = false` | **`unresolved`** |
| 13 | **Two storeys, 2.87 m head to head**, upper window heads to ground window heads. | `storeys.storey_pitch_m` | `inferred`, lower bound |
| 14 | **The second mass is on the sheet, and row 11 is how it was found.** Two ridges at one height meeting at one apex, the main block's running toward the five-bay face's vanishing point and the other away at right angles. Two gable ridges of one wall height and one pitch reach the same height only if they SPAN the same width, so the wing's span is the main block's own depth — which is what `data/structures/sauganash_hotel.json` carries and what the archetype refuses to build otherwise. The wing's LENGTH is not here and cannot be: it is behind the block from this station. | `sauganash_apex_lines.py`; `roof.apex`, `end_vanishing`, `se_vanishing`, `perspective_test.focal_px` | `inferred` — one plate, tier 5, and it may drive a PROPORTION and never a coordinate |

## 4. The fifth view is NOT spent here

T-0617 carries a fifth image the owner deposited the same day —
`chicago/reference/images/chicago/eliza-chappel-school/21617595_…_n.jpg`, captioned as
Eliza Chappell's school at Clark and Lake. It shows a one-storey LOG building with a
door and two windows on the near face, a woman in the doorway, a crowd of children,
canoes on a shore, and a white lighthouse tower in the middle distance. **If it is
Chappell's first school of September 1833 it is a fifth view of this very log annex,
nearly square-on, and the most informative one of the lot.** If it is some other log
schoolhouse it leaves this ticket entirely.

**It is not spent, because it is not settled, and it arrived with a social-media
filename and no artist, title, date or repository.** Provenance first: it is filed at
`data/sources/eliza_chappel_school_shore_view.json` as an unattributed, undated
retrospective at the tier that supports, `asset_use: cross_check`, and it may not move
an attributed plate on any axis where the two disagree. Settling it is a measurement —
the lighthouse is the control, and the tree already holds
`chicago_harbor_lighthouse_1838.jpg` to compare the tower against — and it is filed as
its own ticket, **T-0649**, rather than smuggled into this one.

> **T-0649 ran on 2026-09-04 and the answer is that the lighthouse CANNOT settle it.**
> The reading is `docs/RESEARCH/chappel_shore_lighthouse.md`, measured by
> `tools/measure_chappel_shore_lighthouse.py`. Three adults on the same bank, at
> depressions of 80, 140 and 144 px below the fitted horizon, are drawn 55, 61 and 65 px
> tall: one station demands the nearest be drawn **1.80×** the furthest and it is drawn
> **1.18×**, short by **1.523×**. **The sheet is composed, not constructed**, so no drawn
> position on it can be inverted to a station. The tower's foot is not drawn either, so
> its height is only bounded to **4.65–23.41 m**; and Fort Dearborn, which the committed
> coordinates put 35 m from the light and would draw **209 px** wide beside a 48 px
> tower, is not there — the widest mass flanking it is **7 px**. **The fifth view stays
> unspent, and the successor that would have spent it on the annex is not filed.**

## 5. What this pass did NOT do

* **No record changed.** `data/structures/sauganash_hotel.json` still carries its one
  12 × 8 m placeholder rectangle and still says so. Retiring it is T-0626.
* **No geometry was baked.** T-0617 is `needs_bake: false` and stayed that way.
* **No confidence was promoted.** Everything above is `inferred` or `unresolved`. A
  tier-5 retrospective that passes the perspective test earns the right to be read for
  PROPORTION; it does not earn a coordinate, a footprint outline, or a `documented`.

## 6. What T-0626 then spent, on 2026-09-04

Recorded here because this file is where the reading lives, and a reading nobody can
follow to a record is a reading nobody can check.

* **Row 11 was answered by refusing it**, which is the finding above: the left apex line
  is a ridge and not a rake, so the pitch remains unread and `roof_pitch_deg` keeps its
  typological 38°. Nothing was fitted to make a number appear.
* **The frontage.** Five equal bays at the 1.984 m the scale datum gives are 9.92 m, and
  the 12 × 8 m placeholder is retired for 9.92 × 8. The datum's stated bias was BOUNDED
  rather than left as "a lower bound": the plate's own focal length puts the two men
  43.0 m from the station, so standing a pace forward of the wall makes them under 3 %
  large, and 12 m is refuted rather than merely unsupported. **The depth is untouched and
  still a reconstruction** — nothing here measured it.
* **The second mass** (row 14) is built, its span forced by the shared apex and its length
  admitted as an invention at `docs/LIBERTIES.md` **L217**.
* **The log annex left this record.** `drloih_beaubien` captions the same engraving "The
  log cabin on the left was Chicago's first drugstore", which is
  `data/structures/philo_carpenter_log_shop.json` — already standing at that end of the
  hotel. The hotel's `log_wing` was drawing a second copy of it in front of its own
  street face; it is `false` from that date.
* **What was NOT spent.** The sash widths of row 12 (upper 0.795 m, ground 0.912 m) are
  measured and are still not in the record: the heights they belong with are `unresolved`,
  and a width without a height would let the archetype's own sash proportion pass as a
  reading. The clapboard exposure of row 7 stays out for the reason row 7 gives — it is a
  fact about the engraver. Row 5's doorcase and row 6's transom are readings of the door
  and no record carries them yet.

**Links:** T-0616 (the brief) · T-0626 (where the reading is spent) · T-0197 (the rule
this file is written under) · T-0185 (a plate coarser than the thing it draws) ·
`docs/RESEARCH/sauganash_hotel.md` · `data/sources/trowbridge_sauganash_hotel.json` ·
`tools/measure_sauganash_plate.py` · `tools/sauganash_plate_baseline.json`.
