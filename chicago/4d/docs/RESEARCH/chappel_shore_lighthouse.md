# The Eliza Chappel shore drawing, read against the harbour light (T-0649)

> **HOW A ROW OF THIS FILE MAY BE ESTABLISHED, AND IT IS NOT BY LOOKING.** Written
> under T-0197's rule: **a row states a measurement, names the tool that made it, and
> prints the number.** Every figure below comes out of
> `tools/measure_chappel_shore_lighthouse.py`, is banked in
> `tools/chappel_shore_lighthouse_baseline.json`, and is re-checked by `tools/check.sh`
> on every run, so a detector edit that moves a number cannot do it in silence. A
> question that could NOT be measured says so and is graded `unresolved`; it may not
> seed a ticket and it may not move a record.

**Run 2026-09-04.** T-0617 read the four attested Sauganash views and deliberately did
not spend a fifth image the owner deposited on 2026-09-03. This is the ticket that was
filed to settle what that image depicts, and its answer is that **the lighthouse does
not settle it** — with the numbers that show why, which is the outcome the ticket's own
acceptance allowed for. Nothing here changes a record's confidence, and the successor
that would spend the view on the Sauganash's log annex is **not** filed, because the
reading below removes the grounds for filing it.

## 1. The fork, restated before the work

`data/sources/eliza_chappel_school_shore_view.json` holds the image: an unattributed,
undated drawing at tier 5, `asset_use: cross_check`, arriving with a social-media
filename and no artist, title, date or repository. Two readings were open:

* **(a)** it is Eliza Chappell's FIRST school of September 1833 — the *"small log house
  formerly used as a store"* the Beaubien material identifies as Mark Beaubien's own
  original cabin beside the Sauganash at Lake and Market — in which case it is a fifth,
  nearly square-on view of the **Sauganash's log annex**, and the most informative one
  the project holds; or
* **(b)** it is some other log schoolhouse, and it belongs to whatever record it does
  depict.

The ticket named the control: the tower's drawn position and proportions against
`chicago_harbor_lighthouse_1838.jpg`, the bank's bearing, and the log building's
orientation, read together, either say which corner of the town the view stands on **or
say, with the number that shows it, that they cannot.**

## 2. What makes these numbers measurements

The decisive test is **focal-free**, which is what makes it worth running on a sheet
640 px wide. For anything standing on one flat ground plane, seen from one station,

    r  =  drawn height / (base depression below the horizon)  =  H / h_eye

and the right-hand side knows nothing about the distance, the focal length or the size
of the sheet. So **r must be the same for every adult in the picture, wherever they
stand** — and for any two objects, `H_i / H_j = r_i / r_j`. Four adults at four depths
therefore test the drawing itself before any question about Chicago is asked.

The horizon is the one assumption, and it is stated rather than buried: on a prairie
running to infinity the drawn sky/ground boundary IS the eye-level horizon. It is
fitted across 63 open prairie columns in the window `x 220–432, y 195–245`, and comes
out at **y = 215**, straight to a residual of **2.47 px**. The ±3 px on it is carried
through everything below.

**The search windows.** Every one is a box drawn round a PART OF THE PICTURE, never
round the feature itself; the detector finds the feature inside it. They are quoted
here so a reader can lay them back on the sheet: tower `119–139 × 180–236`, horizon
`220–432 × 195–245`, the buildings that give the tower its ground `103–119 × 216–242`
and `140–153 × 216–244`, the water's edge `72–120 × 205–275`, the flanks that a fort
would have to be in `78–119` and `139–196 × 200–244`, the cabin's silhouette
`500–640 × 140–232`, the doorcase head `550–583 × 213–221`, and the four adults at
`562–578 × 222–282`, `372–386 × 232–296`, `318–340 × 288–360`, `386–420 × 288–356`.

## 3. The table

| # | question | measured | grade |
|---|---|---|---|
| 1 | Do the drawn adults share one ground plane? | **No.** The three who stand on ground give r = 0.6875, 0.4514, 0.4357 — a spread of **1.578×** where one station demands 1.000× | `refuted` |
| 2 | Does figure scale fall off with depth the way one station demands? | **No.** `shore_man_left` stands **1.80×** deeper than `bank_hatted_man` and is drawn only **1.182×** larger — **short by 1.523×** | `refuted` |
| 3 | Is the tower's foot drawn? | **No.** The lit shaft ends at y = 221, the buildings either side of it stand at y = 233, the water's edge crosses its column at y = 249 | `not drawn` |
| 4 | How tall is the drawn tower, in metres? | **4.65 – 23.41 m (15 – 77 ft)**, over the three admissible feet and the three adults. Andreas's forty feet (12.19 m) is inside the band, and so is nearly everything else | `unresolved` |
| 5 | Does the tower carry the 1832 tower's signature? | **Yes, and only that.** Tapered shaft, railed gallery, domed lantern, finial. Gallery overhang **1.25** against the 1838 plate's **1.208** — but ±1 px on a **12 px** shaft is ±0.08, so the agreement excludes no conical harbour light of the period | `type match only` |
| 6 | Can the tower's taper be compared? | **No.** 12 px of width over 20 px of visible shaft on the drawing; on the control sheet the tower's right edge runs into foliage below the gallery | `not measurable` |
| 7 | Is the log building drawn square-on? | **Yes.** The doorcase head — the one long unambiguous world-horizontal on the face — has slope **−0.0102** over a 33 px run, residual **0.358 px** | `measured` |
| 8 | What does the cabin's roof do? | Ridge slope **−0.1005** (residual 0.52 px), left rake **−1.1064**, apex at **(561, 158)** | `measured` |
| 9 | Is Fort Dearborn drawn beside the tower? | **No.** The committed palisade is **53.0 m** square and stands **35.1 m** from the light, so beside a 48 px tower it would be **209 px** wide — **a third of the sheet**. The widest unbroken mass actually flanking the tower is **7 px**, **3.4 %** of a palisade | `absent` |
| 10 | What focal length would the Sauganash corner require? | The corner is **1001.2 m** from the light, bearing **72.4°**, on the committed coordinates. It needs **f = 4,619 – 7,288 px** on a 640 px sheet — a horizontal field of **5.0° – 7.9°** — and puts the nearest drawn adult **125 – 225 m** from the artist | `refuting, see § 5` |
| 11 | Which corner of the town is this? | **Unresolved, and not resolvable from this sheet.** See § 4 | `unresolved` |

## 4. The reading

**Row 1 and row 2 are the finding, and they are the reason for all the rest.** Three
adults standing on the same bank, at depressions of 80, 140 and 144 px below the
horizon, are drawn 55, 61 and 65 px tall. A single-station perspective demands that the
nearest be drawn 1.80× the size of the furthest; it is drawn 1.18×. **The picture is
not a construction.** It is a retrospective composition, put together by eye, in which
each part is drawn at the size that makes it legible. That is what a retrospective
illustration usually is, and there is nothing wrong with it as a picture — but it means
**no drawn position on this sheet can be inverted to a station**, and the error is a
factor of 1.5, which is larger than the difference between the candidate stations.

**Rows 3 and 4 are the tower's own share of the same trouble.** Its foot is not drawn:
the shaft's lit masonry ends at y = 221 and the bank takes the window over. The two
buildings that stand on the tower's own ground DO have drawn feet, at y = 233, and that
is the estimate; the water's edge at y = 249 is the lowest the foot can be, since the
tower stands on land. Depression is the denominator of every metric inversion, and it
runs from **6 px to 34 px** — so the drawn tower is anywhere between a 15-foot tower
and a 77-foot one. Forty feet sits comfortably inside that, which is worth exactly
nothing: the band would accommodate almost any tower ever built.

**Row 5 is a type match and is reported as one.** The drawn tower has the tapered shaft,
the railed gallery wider than the shaft, the domed lantern and the finial that the 1838
plate's tower has. The two gallery overhangs agree — 1.25 against 1.208 — but a 12 px
shaft carries ±0.08 on that ratio from edge quantisation alone, so the agreement
distinguishes the Chicago harbour light from no other conical harbour light of the
period. It says the artist drew *a lighthouse of the right kind*. It does not say which.

**Row 9 is the one negative worth having, and it needs no horizon and no focal length**
— two things at the same distance are drawn in the ratio of their real sizes, and the
fort and the light are 35 m apart on the committed coordinates, which is nothing beside
any station up the river. Fort Dearborn's palisade is 53 m square. Beside a 48 px tower
it would be **209 px** wide: a third of this sheet, unmissable, and drawn at better than
half the tower's height. What is drawn instead is a small gabled shed either hand, the
widest unbroken mass flanking the tower being **7 px**. **This drawing does not show
Fort Dearborn next to its lighthouse.** Either the artist left out the fort — a large
omission next to the very landmark he did draw — or the tower is not the Chicago harbour
light. The reading does not choose between those, and it does not need to: either way
the tower stops being usable as a control.

*The one caveat, stated because it is real:* at a station within roughly 150 m of the
light the fort could fall outside the frame. But no station that near the mouth is
compatible with reading (a), which is what the row was run to test.

**Row 7 is the only positive the sheet gives, and it is the one that made the image
tempting in the first place.** The log building IS drawn square-on: its doorcase head is
horizontal to a hundredth of a slope over a 33 px run. That is exactly what a
draughtsman composing by eye does, and it is exactly what would make the picture
valuable if it were a construction. It is not, so the squareness buys nothing metric.

## 5. Why the station cannot be recovered, in one number

Take the reading at its most favourable: assume for the sake of argument that the
picture IS a construction, and ask what the Sauganash corner would then require. The
corner is 1001.2 m from the light on the committed coordinates of
`data/structures/sauganash_hotel.json` (the 1831 frame phase — the 1829 log phase still
carries a null point) and `data/structures/chicago_lighthouse_1832.json`, bearing 72.4°
— which is, for what it is worth, the right composition: the river running away
east-north-east, the north bank to the left, the town to the right.

The tower's base sits 18 px below the horizon. A station at 1001 m therefore needs a
focal length of **4,619 to 7,288 px on a 640 px sheet**, depending on which adult
supplies the eye height: a horizontal field of view of **5.0° to 7.9°**. At that field
the nearest drawn adult stands **125 to 225 m** from the artist — an adult drawn with a
hat brim, a coat and a hand on a canoe.

*Those five numbers moved on 2026-09-12 and the conclusion did not (T-1083).* The
range was **1066.3 m** when this note was written, and it is 1001.2 m now because
T-1065 (#1189) seated the lighthouse on Wright's own glyph — 49.6 m west and 56.7 m
south of where it had stood. The baseline the gate compares against was not re-derived
with it, and the dev gate could not see the difference because it installs no image
library and the step therefore stood on its own banked copy of the arithmetic. Both
are fixed; the reading of the RASTER never moved at all, which is the reason the
verdict is untouched. **1.5× is still 1.5× at either range**, and that is the whole
argument of this section.

That is not a refutation of reading (a). It is a demonstration that **the arithmetic
that would test reading (a) is being asked to work on a sheet whose own perspective is
wrong by 1.5×**, and 1.5× is far more than the difference between the stations on offer.
The question the ticket asked cannot be answered by this sheet.

## 6. What this changes, and what it does not

* **`data/sources/eliza_chappel_school_shore_view.json`.** `describes_date` and `note`
  now carry what the lighthouse establishes and what it does not. `verified` stays
  **false**: the subject is not settled.
* **`verified` did not move, no confidence was promoted, and no record gained an
  attribute.** The image supplies nothing it did not supply before.
* **The successor that would spend the view on the Sauganash's annex is NOT filed.**
  T-0649's acceptance made it conditional on (a) holding, and (a) does not hold on this
  evidence. What is filed instead is the one route left open: find the original.
* **`docs/RESEARCH/sauganash_image_accuracy.md` § 4** is corrected to point here.
* **Nothing about an attributed plate moved.** Braunhold, Petford and Trowbridge are
  untouched, as § 4 of that file already required.

## 7. What this pass did NOT do

* **It did not read the log building.** Course count, opening sizes, roof pitch and
  corner notching are all legible on this sheet and all were left alone, because the
  ticket's own terms were that it does not spend the view. Only the building's
  ORIENTATION was measured, and only because the ticket named it as one of the three
  things read together.
* **It did not grade the drawing as a forgery, a copy or a fabrication.** It is a
  retrospective illustration that was composed rather than constructed, which is what
  most retrospective illustrations are.
* **It did not bake.** T-0649 is `needs_bake: false` and stayed that way.

## 8. The route this pass left open, and what came of it (T-0663, 2026-09-04)

§ 6 filed one successor: **find the original.** It was run, and it did **not** find it.
`docs/RESEARCH/chappel_shore_origin_search.md` is that record — four publications a
reader would assume this sheet came from are eliminated by their own lists of
illustrations (Andreas 1884, the Porter memoir 1892, Kirkland 1892, Quaife 1933), one
untested candidate is named and quarantined (William Mark Young, *Chicago's First School
House*, ca. 1925, which **nobody has seen**), and six blocked routes are written down so
the next run does not walk into them.

Nothing measured above changes. `verified` is still **false**, the tower is still not a
control, and the sheet is still spent on nothing.
