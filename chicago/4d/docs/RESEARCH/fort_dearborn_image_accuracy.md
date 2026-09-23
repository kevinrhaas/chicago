# Fort Dearborn, against its two plates — the image-accuracy pass (T-0044)

> **HOW A ROW OF THE TABLE BELOW MAY BE ESTABLISHED, AND IT IS NOT BY LOOKING** (T-0197,
> 2026-08-28). Eight rows were written here by eye. **Three were struck as wrong within a
> week** — row 3 was backwards in both halves, row 4 mislocated the plate's most prominent
> structures by half a wall, row 5 described as missing a thing that had been built all
> along — and a fourth, row 8, had its compass word struck. Two of them had already become
> tickets, and both of those runs spent their whole budget establishing that the ticket was
> wrong rather than improving anything a visitor sees. So, from here on:
>
> 1. **A row states a measurement, names the tool that made it, and prints the number.** An
>    impression of a lithograph is not a reading of one. Rows 3, 4, 5, 8 and now 1, 2 and 6
>    each have a committed detector under `tools/measure_*_plate.py`, banked against a
>    baseline so a later edit to the detector cannot move the reading in silence.
> 2. **A row that has not been measured may not seed a ticket.** File the measurement first.
>    It is cheaper than the run that discovers the row was wrong.
> 3. **A row says which FORT its feature belongs to, or says that it cannot.** Both plates
>    are retrospective and both conflate the 1803 and 1816 forts; `data/exclusions.json`
>    already assigns one of `p4_0`'s features to the first. "Render versus plate, plate
>    wins" is the wrong question on a sheet like this one.
> 4. **A measurement that AGREES with the render is a finding too, and gets written down.**
>    Row 2 is the worked example: it is the first row of this table to survive measurement.
>
> The audit that produced this header is § "Rows 1, 2 and 6 measured" below.

**Run 2026-08-19.** The third and last piece of T-0006, the owner's K2 ask: *render each
landmark from its reference plate's viewpoint, compare, improve.* The Green Tree (T-0042)
and the Sauganash (T-0043) were the first two. The next two UNticketed plates in the
committed reference set are the **two Fort Dearborn views** in
`data/sources/assets/prefire_views_kevin_2026_08/` — `p4_0.png` and `p4_1.png` — and this
is their pass.

Both are **tier 5 pictorial**, retrospective, and bound by that directory's README in full:
they may drive massing, roof form, fenestration, materials, furniture and setting as
`inferred`, and they may never drive a coordinate or a footprint outline.

## The plates

**`p4_0.png` — the fort from across the river, coloured, plate "1."** The stockade on its
rising bank, seen from the north bank at about the height of a person standing. A picket
curtain under a ruled FLAT cap, drawn pale on the reach east of the gate work and brown on
the reach west of it — **this line said "Pale pointed pickets" until 2026-08-24 and was
wrong on both counts; see § "Row 3 was wrong"**; two works rising above the wall with
pyramidal roofs and small lanterns;
a log-faced blockhouse over the gate; ranges inside with dormers, chimneys and even bays;
**a flagstaff over the fort with the national flag flying**; **a track climbing the bank
from the water's edge to the gate**; a boat with rowers on the river; a two-storey frame
house among trees to the right, outside the walls.

**`p4_1.png` — the fort from the lake, the wider view.** The compound as a pale mass on
the low bank with the river running behind it; a small house group on the far bank; a long
fence line running east along the bank; scattered houses on the rise to the left; poplars
and trees around the buildings to the right. **It also depicts Native people, tipis and
canoes: the standing constraint (AGENTS.md § 1835 and Indigenous history, L1) applies —
they are reference for the SETTING only and nothing of them is drawn.**

## The render, before this pass

`docs/RESEARCH/fort_from_the_north_bank_2026-08-19.png` — shot at local `1145, 300`, yaw
180°, which is `p4_0`'s own stand. The fort reads: stockade, ranges, chimneys, the
lighthouse beyond. What is missing against the two plates, in the order a visitor would
notice it:

| # | the gap | can this runner close it |
|---|---|---|
| 1 | **No road anywhere on the reservation.** ~~Both plates show a travelled way at the fort;~~ **HALF STRUCK — measured 2026-08-28 by T-0197.** The render's half was true and this pass closed it (`fort_road`). The plates' half is not: `p4_0` draws exactly ONE way and it is row 2's bank track, counted here a second time; `p4_1` draws NONE at the fort, on a detector that finds the way it draws elsewhere on the same bank. See below. | **shipped — and the road stands on the 1830 plan, not on these plates** |
| 2 | The track descending the bank from the north gate to the water (`p4_0`). **MEASURED AND CONFIRMED 2026-08-28 by T-0197 — the first row of this table to survive measurement.** One bare mass, 38,361 px, meeting the wall's foot at the gate and descending frame-right to the shore. | **closed 2026-08-27 by T-0099** — `fort_bank_track`, and the plate agrees on its direction |
| 3 | ~~Pickets are flat-topped and dark; the plate's are pointed and pale.~~ **This row was wrong in both halves — see below. Refuted and closed 2026-08-24 by T-0094.** The one thing about the pickets the plate DOES say — that it draws them three times coarser — was left open by that pass and is **settled 2026-08-28 by T-0185, see below.** | nothing to bake |
| 4 | ~~The corner works do not rise above the curtain with roofs and lanterns as the plate draws them.~~ **`p4_0` draws no work at either angle it shows. Refuted and closed 2026-08-24 by T-0095 — see below.** | nothing to bake |
| 5 | ~~No gate is drawn in either documented wall;~~ **a gate has been drawn in both since the archetype was written — but both stood a QUARTER OPEN, and that is now fixed. Closed 2026-08-24 by T-0095 — see below.** The plate's log-faced work over the gate is not built, and § "Row 4" says why. | **closed — one asset rebaked** |
| 6 | **A flagstaff and flag over the fort** — the most conspicuous single feature of `p4_0`. **MEASURED 2026-08-28 by T-0197: drawn, and it stands at 0.495 of the wall — over the GATE, between the two works at 0.435 and 0.521, and NOT in the parade where `data/exclusions.json` puts the first fort's.** | **CLOSED 2026-08-28 by T-0096 — and NOT on this plate.** A staff IS built, on Andreas vol. 1 p. 128 (*"a flagstaff at the fort, some fifty feet high"*, in his 1833–37 town description); the plate's over-the-gate position was refused with the towers it belongs to. See § "Row 6 is answered, and the plate did not answer it" |
| 7 | The ground round the walls is full prairie sward; both plates show it bare and trodden. | **closed 2026-08-23 by T-0097** — a 12 m band of trodden earth outside the palisade, derived from the stockade's own committed footprint (`data/enclosures/fort_dearborn_apron.json`, L174); before/after at `docs/evidence/t-0097-{before,after}.png` |
| 8 | No trees at the fort; `p4_0` puts a tree mass ~~east~~ **WEST** of the walls and `p4_1` trees round the buildings on both banks. **The compass word in this row was wrong — see "Row 8's east is west" below.** | **closed 2026-08-24 by T-0098** — the mass is WEST, measured; and the plate cannot DATE it, so 12 relict black willows stand there `reconstructed` rather than the plate's closed canopy (`data/flora/plantings/fort_dearborn_wood.json`, L188); before/after at `docs/evidence/t-0098-{before,after}.png` |

## The pitch: the plate is coarser because it could not be finer (T-0185, 2026-08-28)

T-0094 measured `p4_0` to refute the row above and turned up, on the way, **the one thing about
the pickets the plate positively asserts**: it resolves separate posts at a **10 px pitch on a
42.9 px curtain**, autocorrelating +0.70 on the east reach and +0.60 on the west. That is 0.23 of
the wall's height per post. The record builds `picket_spacing_m` 0.30 on a `picket_height_m` of
3.7 — **0.081**, nearly three times finer. The finding sat unactioned for four days and this is
its pass. **Nothing moved, and that is the finding rather than a refusal to act on it.**

**Neither number was ever evidence about 1816.** Both `picket_width_m` and `picket_spacing_m` are
`reconstructed` and say so; the plate is tier 5 and admissible for form as `inferred` at best. So
the question was never "adopt the plate's proportion" — 0.23 of a 3.7 m wall is an **0.86 m post**,
which is not a picket anybody split. The question was whether a rhythm this fine is the right
reconstruction, and whether the wall reads as posts or as a slab where a visitor actually stands.
Both halves are now measured.

### The plate could not have drawn this wall

`tools/measure_picket_plate.py` reads the plate's own drawn scale off the curtain it already
measures: 42.9 px for the record's 3.7 m wall is **11.59 px per metre**. At that scale this
stockade's rhythm is **3.48 px of pitch — 2.78 px of post and 0.70 px of gap.**

Then it measures what the plate actually holds, by run length along the same column profile the
rhythm is autocorrelated from:

| reach | posts drawn | dark strokes | pale gaps |
|---|---|---|---|
| east | 19 | 3–4 px | 3–6 px |
| west | 30 | 3–5 px | 2–5 px |

**The narrowest gap the plate carries anywhere on that curtain is 2 px, 2.9 times wider than the
0.70 px this wall would need.** A draughtsman cannot leave a two-thirds-of-a-pixel gap between
two-and-three-quarter-pixel posts, and neither can the stone. So the 10 px pitch is the **floor of
the medium**: he drew the finest picket line his plate could carry, which is what a draughtsman
does. It is a reading of the lithograph, not of the fort, and it cannot move the record.

### And the model reads as posts everywhere a visitor can stand

The other half is a fact about the model, and it is why the fine rhythm is kept rather than merely
defended. `tools/measure_picket_reading.mjs` takes the SAME statistic — autocorrelation of the
curtain's column-mean darkness — off a render of the same wall, from `p4_0`'s own stand (local
1145, 300, yaw 180) and from outside the north gate, at both release viewports:

| stand | viewport | measured | expected | autocorr | 2× | reads as |
|---|---|---|---|---|---|---|
| p4_0, across the river | desktop | 4 px | 4.49 px | +0.93 | +0.85 | **posts** |
| p4_0, across the river | phone | 4 px | 1.62 px | +0.66 | +0.31 | **aliased** |
| north gate | desktop | 34 px | — | +0.66 | +0.50 | **posts** |
| north gate | phone | 16 px | — | +0.76 | +0.56 | **posts** |

`expected` is derived from the drawn extent of the whole 53 m curtain in that shot, so a measured
peak well above it is a moiré rather than a finer reading. Evidence:
`docs/evidence/t-0185-{p4_0,north_wall}-{desktop,phone}.png`.

**A drawing has one viewing distance and a walkable reconstruction has all of them.** The plate's
coarser rhythm is the correct answer to a problem this model does not have: its viewer cannot walk
up to the wall, and ours can. At the gate the wall resolves at 34 px on a desktop and 16 px on a
phone, where an 0.86 m post would read as a paddock rail. The one place the model hits the
draughtsman's own bind is a **phone at the river stand**, where a 1.62 px pitch falls under the
pixel grid and beats into a 4 px moiré — a fact about a 390 px screen at fifty metres, not about
the reconstruction. It is filed as its own ticket rather than answered by coarsening the wall.
**T-0266 settled that ticket on 2026-09-13, and narrowed this row: the phone reading above was
taken at `devicePixelRatio` 1, which is the renderer a phone gets only when the visitor has turned
Render quality down. At the shipped default the same stand resolves. See the section below.**

**What this changes:** nothing standing. `picket_width_m` 0.24 and `picket_spacing_m` 0.30 are
unmoved and still `reconstructed`, the 768 posts and the palisade's committed master are untouched
and unrebaked, and no confidence was upgraded. `docs/LIBERTIES.md` **L47** — which already owned
"the gap between the posts, which decides whether you can see through the wall" — carries the
disagreement and its resolution, and so do both attribute notes on the record, which is where a
visitor opening the stockade's card will read it.

### The phone's moiré is a SETTING, not a wall (T-0266, 2026-09-13)

The row above reads *aliased* on a phone, and it was filed as its own ticket to decide what the
renderer should do about a 1.62 px rhythm. The answer is that it should do nothing, and the reason
is that **the aliased row was never a reading of a phone.** It is a reading of a phone with
*Render quality* turned down.

`measure_picket_reading.mjs` booted every context at `deviceScaleFactor: 1`. That is not a detail
of the harness: `deviceScaleFactor` sets `window.devicePixelRatio` inside the page, and `main.js`
boot reads exactly that —

```js
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, hud.settings.quality));
```

— with `hud.js` `DEFAULTS.quality` **1.5 on both platforms**. So a context at dsf 1 asks the
renderer for `min(1, 1.5)` = **1.0**, and a real phone at dsf 2 asks for `min(2, 1.5)` = **1.5**:
three backing-store pixels for every two CSS pixels, against one. Every picket reading this project
had ever taken on a phone was at the lower of those two — which is what the renderer draws when the
visitor uses the escape hatch T-0157 shipped for frame rate. **The shipped default had not been
measured here at all.**

The file now reads the phone at both, in one pass. `phone-dpr2` is the same viewport, the same
stand and the same camera on a raster twice as wide, so its crop rectangle and its wall span are
the phone's multiplied by the ratio — a derivation, not a second constant read off by eye.

| stand | viewport | dpr | ratio | measured | expected | autocorr | 2× | reads as |
|---|---|---|---|---|---|---|---|---|
| p4_0, across the river | desktop | 1 | 1.0× | 4 px | 4.49 px | +0.93 | +0.85 | **posts** |
| north gate | desktop | 1 | 1.0× | 34 px | — | +0.67 | +0.50 | **posts** |
| p4_0, across the river | phone | 1 | 1.0× | 4 px | 1.62 px | +0.68 | +0.34 | **aliased** |
| north gate | phone | 1 | 1.0× | 16 px | — | +0.76 | +0.56 | **posts** |
| p4_0, across the river | phone | 2 | 1.5× | 4 px | **3.25 px** | **+0.84** | **+0.64** | **posts** |
| north gate | phone | 2 | 1.5× | 33 px | — | +0.80 | +0.61 | **posts** |

At the ratio a phone actually rasterises into, the river stand **resolves**. The measured 4 px
stands against a 3.25 px expectation — 1.23 of it, inside the 1.5 this instrument calls a beat —
where at ratio 1.0 the same 4 px stood against 1.62 and was 2.5 times the wall's own rhythm. The
reading is not merely re-labelled: the correlation rises +0.68 → +0.84 and its harmonic +0.34 →
+0.64, which is the difference between a rhythm inferred from a residual and one that is simply
there. Read in backing-store pixels rather than screen ones, the wall draws 2.43 px of pitch at the
default and 1.62 at the hatch, either side of the 2 px floor where a rhythm stops being separable
at all. The north gate resolves at every ratio, and the desktop is untouched.

Evidence: `docs/evidence/t-0185-{p4_0,north_wall}-phone-dpr2.png`, beside the dsf-1 pair already
here.

**What the alternatives would have cost, which is the thing the ticket asked to be decided
against.** Two were available and both are refused on a measured price rather than on taste:

* **Close the hatch** — floor the pixel ratio at 1.5 so no phone can fall under the rhythm. T-0157
  measured what that floor is worth: dropping the ratio to 1 *cuts the multisampled pixel count by
  56 %*, at 4 stations, which is the whole reason the control exists. Forcing it back up is 2.25×
  the shaded pixels, town-wide and at every stand, bought to settle one wall's rhythm at one stand
  across the river — and bought from precisely the visitor who asked for frame rate instead. The
  trade is the wrong way round.
* **Smooth the wall at range** — swap the picket rhythm for a slab beyond some distance. It needs a
  rebake of the palisade, it puts a different wall at `p4_0`'s own stand from the one the plate is
  compared against two sections above, and T-0185 already settled that the fine rhythm is right at
  every range a visitor can choose. This ticket refused it in advance and the measurement does not
  reopen it.

So nothing in the scene changes and nothing is rebaked. What changes is that the instrument can no
longer read a phone at a setting and report it as the phone: the ratio each row was drawn into is a
column in its own table.

**The honest limit.** These are SwiftShader renders at a `deviceScaleFactor` Playwright sets, not
frames off phone silicon, and the frame COST of either ratio on real hardware is still unmeasured —
T-0157 says so of its own figure and this does not improve on it. What is measured here is what is
drawn, which is the question the ticket asked.

## Row 3 was wrong, and the correction is the interesting part (T-0094, 2026-08-24)

This pass wrote *"Pale pointed pickets"* of `p4_0` in its own description of the plate, and then
*"Pickets are flat-topped and dark; the plate's are pointed and pale"* in the table. **It read the
plate by eye and it read the model by eye, and it got both wrong.** T-0094 was filed off this row
and closed refuted; `tools/measure_picket_plate.py` now holds the finding and prints it.

**The model was never flat-topped.** `generators/archetypes/palisade.py::_picket` has built every
post as a shaft plus a four-triangle sharpened head since the archetype was written, sized by
`PalisadeParams.picket_point_m`. The committed master says so independently:
`assets/gltf/fort_dearborn_palisade__picket_1816.glb` puts the picket surface's 21,504 positions on
exactly three heights — 6,144 feet at 0.000 m, 12,288 shoulders at 3.388 m, **3,072 apexes at
3.700 m**, four per post over 768 posts. That is **0.312 m of head, 8.4 % of the picket**, and the
sawtooth reads plainly at the wall and still reads from `p4_0`'s own stand across the river.
`docs/evidence/t-0094-plate-vs-model.png` is the three views side by side.

**And the plate draws a ruled flat cap.** Measured on the east reach of the north curtain, over the
195 px between the gate work and the east corner: the cap resolves in 138 columns and is straight
to **0.45 px rms**, peak-to-peak 2.0 px, stable across three detector thresholds. The same plate
**resolves individual pickets** — the curtain's column profile autocorrelates at **+0.70 at a 10 px
lag**, +0.60 on the west reach — and stands the curtain **43 px** tall, so a head of the model's own
proportion would have serrated that line by **3.6 px**, eight times the residual. `p4_1` rules the
same flat cap. The draughtsman had the resolution and drew no point.

That does not make the model's head wrong — a lithographer rules the top of a distant stockade, and
these are tier-5 retrospective plates. It makes the head **unattested and ours**, which is now
recorded in the record's own `construction` note and in **L179**, where it had never been written
down at all.

**"Pale" is a reading of half of one wall.** The plate paints this single continuous curtain across
a **1.85× range of tone** in one view — median sRGB (200, 191, 158), luminance 191, east of the gate
work; (117, 102, 76), luminance 103, west of it — against the fort's own frame range at 183, bare
bank earth at 115 and the paper at 218. The picket surface this project ships, `hewn_log`, is sRGB
(158, 141, 120), **luminance 143: inside the range the plate paints the same wall across.** A source
that draws half a stockade darker than the model and half paler cannot warrant moving it either
way. The whitewash trap the ticket named is separate and stands: Fergus's white-washed board fence
is the enclosure of 1850, after the pickets came down.

**What the render's darkness at this stand actually is.** From `p4_0`'s stand a visitor looks south
at the fort's NORTH face, which on 1 July is the shaded one; the log ranges behind the wall read
(52, 55, 57) and the brick range (59, 44, 46) in the same frame. The wall is not painted black, it
is lit from behind — and the plate, being a picture, lit it anyway.

**What the plate does say about the pickets, and nobody has acted on:** it draws them at a 10 px
pitch on a 43 px wall — about **0.23 of the wall's height per post**, where the model builds 0.30 m
centres on a 3.7 m picket, **0.081**. The plate's rhythm is nearly three times as coarse. Filed as
its own ticket rather than acted on here: it is a `picket_width_m`/`picket_spacing_m` question, both
`reconstructed`, and moving either needs the bake.

## The flagstaff is a documented trap, and this pass refuses it

`p4_0` plainly draws a flagstaff. **`data/exclusions.json` already excludes one**: the
flagstaff in the parade belongs to Captain Whistler's 1808 FIRST fort, in the passage that
ends *"Such was the old Fort previous to 1812"*, and the entry closes *"none of it may be
borrowed for the second fort's records"*. Retrospective plates conflate the two forts —
that is why the courthouse plate in the same directory is filed as a negative reference —
so a tier-5 view is exactly the evidence that cannot settle this one. Raising it on this
plate alone would be the commonest error in the popular literature, committed on purpose.

It is a real question with a real answer somewhere: a garrison return, a quartermaster's
account, Andreas on the 1816 fort, or an identification of this plate against chicagology's
numbering. Filed as a ticket rather than built or forgotten.

**It was the second of those, and T-0096 found it on 2026-08-28** — Andreas vol. 1 p. 128,
inside his own *Chicago from 1833 to 1837*. The staff is now built. **This section's refusal
stands exactly as written**: the plate did not warrant it then and does not warrant it now, and
the position the plate draws was refused a second time when the staff was placed. See § "Row 6
is answered, and the plate did not answer it" below.

## What this pass shipped

**The fort road** — `data/streets/1835.json`, id `fort_road`. Before and after from the
same stand, at local `1000, 30`, yaw 70°:
`fort_road_before_2026-08-19.png` → `fort_road_after_2026-08-19.png`.

`fort_road_published_2026-08-19.png` is the same stand on the PUBLISHED mirror, which is the
run that matters here — the source tree loads uncompressed masters and the site loads the
derivatives, and this project has shipped bugs in that gap twice. Zero page errors either way.

It leaves the east end of South Water Street, crosses the reservation east of the garrison
garden and past the Beaubien buildings, and arrives at the fort's south gate. The reasoning,
and the line between what is documented and what is invented, is in the record's own note and
in **L140**. In one sentence: the gates are attested three times over, the 1830 Harrison plan
puts the garrison garden *west of a road*, and the western reach — the connection to the town
— is this project's reconstruction, because South Water Street stops at the United States
Reservation by the 1833 order and nothing reached draws what carried on.

## What was filed instead of built

Rows 2–8 above became tickets at the bottom of `tickets/QUEUE.md`, where the owner can rank
them. Rows 3–5 are one bake apart; rows 6–8 are not.

## Rows 4 and 5 were wrong too, and the gate was open (T-0095, 2026-08-24)

The full working is in **`docs/RESEARCH/fort_dearborn_gate_and_corner_works.md`**; this is the
part that belongs to this table. Measured by `tools/measure_fort_works_plate.py` and
`tools/measure_fort_gates.py`, both of which run in `tools/check.sh`.

**Row 4 — `p4_0` raises no work at either angle it draws.** The plate raises exactly two
roofed, lanterned, log-faced works and **both stand over the middle of the wall**, at
**0.435 and 0.521** of the drawn run — over the gate, which is where row 5 already put one
of them. A corner work stands at 0.000 or 1.000. The one angle the plate shows unoccluded is
the north-east, and it is drawn **plain**: the picket crest is the skyline from column 319,
rising 0.04 curtain heights over its first twenty columns — which is what the record says of
that angle. The north-west angle, the one the record does put a work at, is behind the tree
outside the walls: the crest is last legible at column 1181 and the material past it is green
by 12.1 against 8.0 over the fort. **The plate has nothing to say about it, and no height was
read out of leaves.**

This row and row 3 are the same mistake made twice on the same sheet, one day apart: the plate
read by eye, and a feature of the record joined to a feature of the drawing that was somewhere
else.

**Row 5 — the gate was drawn, and it was open.** `palisade.py::_gate` has built a gateway in
both documented walls since the archetype was written — jamb posts, a lintel, two leaves —
and it was in the committed GLB when this table was written. What was wrong is something this
table did not claim: **one leaf of each pair was placed from a midpoint that collapsed onto
its own jamb**, so 0.90 m of the 3.6 m gateway stood open with daylight straight through the
wall, and 0.90 m of leaf lay across the pickets outside the frame. Both gates. In the bytes a
visitor downloaded. Fixed and rebaked; before and after from this plate's own stand at
`docs/evidence/t-0095-{before,after}.png`, with the gate itself at 5x in
`t-0095-close-{before,after}.png`.

**And the log-faced work over the gate is still not built.** Not because the plate is unclear
— it is perfectly clear — but because of § "The flagstaff is a documented trap" above,
applied consistently. This sheet already carries one feature `data/exclusions.json` assigns to
the FIRST fort, and two roofed lanterned log towers is that fort's own signature in everything
but position. A tier-5 view that conflates the two forts cannot add a tower to the second one
at an angle **or** over a gate.

## Row 8's "east" is west — measured 2026-08-24 (T-0098)

This pass wrote row 8 by eye, and the compass word in it is wrong. The correction matters more
than the word does. Every row of the table above was written the same way — looked at, not
measured — and row 3's own reading of the pickets is under measurement on its own ticket
(T-0094) at the time of writing. **An impression of a lithograph standing in for a reading of one
is the fault this section exists to name**, and it is worth assuming the rest of the table
carries it until each row has been measured too.

`tools/measure_fort_trees_plate.py` measures it. Segmented for foliage — greener than red and
darker than the sky, then a 7×7 majority filter to kill the stipple — and split at the two ends
of the drawn stockade, `p4_0` carries:

| | foliage px | largest connected component |
|---|---|---|
| frame-LEFT of the stockade | 2 322 | **924 px** at x 27–87, y 534–557 — bank grass on the viewer's own side of the river, below the waterline |
| frame-RIGHT of the stockade | 35 714 | **33 334 px** at x 1189–1537, y 293–490 — a canopy, running clean off the right edge of the plate |

There is no mass on the frame-left at all.

**And frame-right is WEST.** That is settled off the stand rather than off the picture. This
document already fixes `p4_0`'s viewpoint as the north bank at local `1145, 300` looking south,
and `fort_from_the_north_bank_2026-08-19.png` is the render from it with the HUD compass reading
**S 180°**. A stand facing south has east on its LEFT. The witness is the committed
`chicago_lighthouse_1832`: it stands at local E 1105.2 against the fort's centre at E 1152.0 —
**46.8 m WEST** — and in that very shot it draws to the **frame-right** of the fort. Two
independent readings, the same answer.

Two other numbers the same measurement fixes, and they bound what T-0098 built:

* **the crown height.** The canopy tops stand 127 px above the wall foot — **8.8 m** scaled on
  the fort's committed 53 m footprint (whose apparent width from due north is 59.86 m, the walls
  being 8° off the grid) and **10.9 m** scaled on its committed 3.7 m picket height. The two
  scales differ by 24 %, which is the ±20 % the palisade's own placement note already carries on
  every dimension derived from the Harrison plate; both are printed and neither is averaged into
  the other. The crowns reach the fort's own range ridgeline, and the trees stand on ground that
  falls away from the wall, so the true crown is the higher of the two readings plus that fall.
* **the west end — which the plate does not give.** The mass reaches column 1537 of 1538: it is
  cut off by the frame. How far the wood runs is therefore this project's invention and is
  recorded as one (L179), not a reading of the picture.

The evidence overlay — the segmentation tinted over the plate, with the stockade's two ends, the
picket band and the measured mass drawn on it — is `docs/evidence/t-0098-plate-measured.png`.

### …and it cannot date them (T-0098, the same run)

Measuring which SIDE the mass is on does not establish WHEN it stood, and this row's other half
had never been asked. `data/exclusions.json` assigns `p4_0`'s flagstaff to **Whistler's first fort
of 1803**; T-0095 measured the plate's two roofed, lanterned works at 0.435 and 0.521 of the wall —
over the gate, not at the angles — and reads two such works as first-fort signature. Everything
struck so far is the fort's FABRIC, and both forts stood on the same ground. **But a draughtsman
working decades later off first-fort descriptions was drawing a scene, and there is no reason his
trees are better dated than his blockhouses.**

The dataset does not rescue it either. `docs/research/02-flora.md`, on Andreas, ends the South
Division's river timber belt **east at Wells Street** — some 900 m west of this reservation — and
`renderers/web/js/trees.js` enforces that limit in `timberEastLimits`, so the dealt timber layer
stops far short of the fort for a documented reason. **A belt at the fort would contradict the
dataset.** A few relict boles on ground people had used east of a belt's end would not, and that
is precisely what `z10_settled_town` records its black willow as: *"Left along the bank where the
landing was cut."*

So T-0098 built at the `reconstructed` tier with EMPTY sources, and built a **twelve-stem open
stand rather than the plate's closed canopy** — the record states the difference rather than
letting a visitor infer that the plate's mass was reproduced. For T-0197's audit: **row 8's
compass word is struck, and row 8's implicit date is struck with it.** What is left standing of
the row is that a draughtsman drawing this fort put trees outside its walls, on the west side.

## Rows 1, 2 and 6 measured — and the audit of what is left (T-0197, 2026-08-28)

Rows 3, 4, 5 and 8 had each been measured by the run that struck them. **Rows 1, 2 and 6
never had been**, and between them they had already put two built ways on the reservation —
`fort_road` (row 1, this pass) and `fort_bank_track` (row 2, T-0099, merged the day before
this audit). This section measures all three, off the plates, with `tools/
measure_fort_ways_plate.py`. It runs in `tools/check.sh`, banks its reading in
`tools/fort_ways_plate_baseline.json` so a later edit to the detector cannot move it in
silence, and carries three assertions that ask the TOWN about the plates rather than the
other way round. The overlay is `docs/evidence/t-0197-ways-measured.png` — the segmented
corridor tinted on the sheet, with the wall's ends, the picket band, the flagstaff and the
two works of T-0095 drawn on it.

### Row 2 is CONFIRMED, and it is the first row of this table to survive measurement

`p4_0`'s bank is segmented for bare trodden ground — warmer than the sward (red over green
by 6) and paler than it (luminance 150 against the sward's 108–124), then the same 7×7
majority filter the trees tool uses to kill the stipple. The river fails the warmth clause
outright (R−G 0.5) and so does the sky (−5.3).

**One connected mass carries the whole thing: 38,361 px, rows 421–621, columns 751–1199.**

* It **meets the wall at the gate.** Its head touches the picket foot at column 752 — 10 px
  from the gate work `p4_0` raises at 0.521 of the drawn wall run (T-0095's own reading), so
  0.509 of that run. It does not begin at an angle, at a corner, or anywhere else on the
  wall.
* It **runs west.** Its per-row centre travels 840 → 1193 as it descends, drifting **+1.219
  columns a row** — frame-RIGHT, which on this plate's settled stand (§ "Row 8's east is
  west") is **WEST**.
* It **reaches the shore.** At its closest the mass's foot comes within **37 px** of the
  drawn waterline, at column 1140 — 2.6 m on the footprint scale and 3.2 m on the picket
  scale, both read at the FORT's depth, and the foot is nearer the viewer than the fort, so
  both are upper bounds. What lies between is the plate's own dark shore rule.
* **There is no second way.** The next bare mass anywhere on this bank is 151 px.

`fort_bank_track` as T-0099 built it runs **23.23 m west** over a 23.92 m chord out of the
north gate. The plate agrees on the direction and on the gate, and **cannot** agree or
disagree on the length: a line running away from a monocular viewer has none, and no
arithmetic on a lithograph recovers it. Which is why the record still reads
`geometry_confidence: reconstructed`, and why this file's second assertion fires the day
somebody promotes it on the strength of this section.

### Row 1 is HALF STRUCK: it counted one drawn way twice, and cited a plate that draws none

Row 1 reads *"No road anywhere on the reservation. Both plates show a travelled way at the
fort."* Two claims, and they do not stand together.

**The render's half was true**, and this pass closed it by shipping `fort_road`.

**"Both plates" is not.**

* On `p4_0`, the travelled way is the one measured above — row 2's bank track, descending
  from the NORTH gate to the water. **It is the same feature row 2 names.** The table
  counted it twice and read the second count as independent support for a road approaching
  the fort from the town, which is a different thing on the far side of the compound and is
  not drawn on this sheet at all. (It could not be: from `p4_0`'s stand the south side is
  behind the fort.)
* On `p4_1`, there is **no way at the fort.** Measured with a detector normalised to each
  window's own quartiles, so the two plates' very different palettes are comparable: a 9 px
  box mean to kill the stipple, then anything standing above the window's own third quartile
  by half its own interquartile range. Over the fort's ground — the bank between the drawn
  stockade's two ends, columns 378–755, below the wall foot — the largest pale mass is
  **340 px at +0.5 IQR and 0 px at +2.0 IQR**: it does not survive the stiffer threshold at
  all. Run unchanged over the house-group bank at frame-left, where the draughtsman DID draw
  a trodden way, the same detector finds **563 px at +0.5 IQR and 97 px at +2.0 IQR** — an
  elongated streak at rows 285–291, columns 145–186, still there at four times the margin.
  **The same detector, the same settings, the same sheet: it finds the way `p4_1` draws and
  finds nothing at the fort.** A null with a positive control beside it.

What this does NOT do is unbuild the fort road. That road never rested on these plates:
its own record and **L140** put it on the 1830 Harrison plan — which places the garrison
garden *west of a road* — with the western reach stated as this project's reconstruction
because South Water Street stops at the United States Reservation by the 1833 order. The
plate sentence in row 1 was decoration on a documented argument. It is struck so that the
next reader does not mistake it for the argument.

### Row 6 is CONFIRMED as drawn — and the measurement moves the first-fort question

`p4_0` does draw a flagstaff, and the row is right that it is conspicuous. Measured as the
tallest thin dark vertical standing in the sky over the fort (darker than the sky's own 80th
percentile by 45): **column 740, truck at row 158, 112 px of staff before the roofline takes
it**, rising **219 px over the picket head — 15.24 m on the footprint scale, 18.84 m on the
picket scale**, printed side by side and never averaged. The flag is there too: **378
red-dominant pixels at rows 195–220, columns 715–734**, flying frame-left of the truck.

The number the row never asked for is WHERE ALONG THE WALL it stands, and it is the one that
matters:

**0.495 of the drawn wall run** — between T-0095's two roofed, lanterned works at **0.435**
and **0.521**, over the GATE.

`data/exclusions.json` excludes a flagstaff and locates the excluded one **in the parade**,
in the passage that ends *"Such was the old Fort previous to 1812"*. The staff `p4_0` draws
is not in the parade. It rises from the gate work's own roofline, wedged exactly between the
two works that T-0095 read as first-fort signature (two blockhouses), so **the plate's
flagstaff and the plate's two towers are one composition standing over one gate** — either
all of it is the second fort or none of it is, and this sheet cannot say which. That is a
sharper form of the same trap the pass refused, not a way past it: **T-0096's question is
unchanged and still needs a source that reaches the 1816 post.** What is now recorded is
that the excluded first-fort staff and the drawn staff are not in the same place, so
"`exclusions.json` already covers it" is not an answer either.

### The tickets descending from these rows, re-read

| ticket | from row | verdict against the measurement |
|---|---|---|
| **T-0099** (done, PR #431) | 2 | **CONFIRMED.** The plate draws the track it built, out of the gate it built from, running the direction it swung. The length it chose is its own and is labelled `reconstructed`; the plate neither warrants nor refutes it. |
| **T-0096** (done) | 6 | **CONFIRMED, sharpened, then CLOSED ON A DIFFERENT SOURCE.** The staff is drawn on the plate and where it stands is measured — and neither fact built anything. What built it is Andreas vol. 1 p. 128. The plate's own position was refused for the second time, because the staff and the two towers there are one composition. |
| **T-0098** (done) | 8 | **CONFIRMED as measured** by its own run: the compass word struck, the date struck, twelve `reconstructed` relict stems built rather than the plate's closed canopy. No new work. |
| **T-0094** (refuted), **T-0095** (refuted), **T-0097** (done) | 3, 4, 5, 7 | already closed by measurement; not re-opened here. |
| `fort_road` (built by this pass, row 1) | 1 | **STANDS, on a different warrant than the row claimed.** The 1830 Harrison plan and L140, not the plates. No record changes; the row's plate sentence is struck. |

Nothing in this section moves a coordinate, a confidence or a mesh. **That is the point of
it**: the table is now eight rows of which seven have been measured, and the eighth — row 7 —
was closed by construction. There is nothing left in it that a future run can build to on the
strength of somebody's impression.


## Row 6 is answered, and the plate did not answer it (T-0096, 2026-08-28)

The row asked whether the second Fort Dearborn carried a flagstaff. **It did, and the evidence
is a text and not a view**: Andreas, *History of Chicago* vol. 1 **p. 128**, in the section
headed *Chicago from 1833 to 1837* — *"It did not show a single steeple nor a chimney four feet
above any roof. A flagstaff at the fort, some fifty feet high, flaunted, in pleasant weather and
on holidays — a weather-beaten flag …"*, and, of the approach from the south, *"the flag over the
fort, if perchance it was flying."* That is the fort standing in the years the scene date sits
in, described by a writer who in the same breath calls its buildings *"low posted, and none of
them exceeding two low stories"* — which is this fort and not Whistler's galleried one.

**What this does NOT do is rehabilitate `p4_0`.** The plate's staff was measured at 0.495 of the
drawn wall run, over the gate, between the two roofed lanterned works T-0095 read as first-fort
signature; that composition is refused whole, and the built staff takes its position from the
model (the parade's centre) under **L204**, not from the sheet. Nor is Whistler's parade-centre
staff the warrant — that fort is excluded, and the coincidence of two rectangles is not
corroboration.

Three other texts were searched for the same word and none attests a staff at the 1816 post:
Quaife's only flagstaff is Whistler's, Wau-Bun has none, Wentworth's 1881 address has none. The
full search table, the record, and the reasoning for building the spar bare — Andreas dates the
flag to *"pleasant weather and … holidays"*, and 1835-07-01 is a Wednesday — are in
`docs/RESEARCH/fort_dearborn.md` § 10.

**The table is now eight rows of which seven have been measured and one was closed by
construction, and row 6 is the only one that a measurement pointed AWAY from and a document
then settled.**
