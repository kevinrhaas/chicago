# What the Thompson plat actually draws of the water, read at 5×

**Investigated:** 2026-09-04 · **Ticket:** T-0452 · **Epoch:** `e1834_harbor_cut` ·
**Record:** none — this is a memo about a *reading* ·
**Source:** `thompson_plat_1830`, through the sheet held in this repository at
`chicago/pre_fire_v1/maps/images/1830_thompson_plat.png` (2728 × 1944) ·
**Data touched:** `data/terrain/epochs/e1834_harbor_cut/hydrology.geojson` (its `note`),
`tools/trace_river.py` (where that note is authored), `data/sources/thompson_plat_1830.json` ·
**Owner's ask:** *"the water north of the river"* — marked on the dev preview, 2026-08-31 ·
**Gate:** `tools/check.sh`

---

## 1. The sentence this ticket was opened against

`hydrology.geojson` held one feature, and its own note ended:

> *"…so a traced boundary would be a fiction. **Probably one of the three sloughs off the
> Main Branch shown on the 1830 Thompson plat.** Depth is conjectural: no source gives one."*

T-0452 read that as the file admitting the plat draws three and the reconstruction holds
one. Both halves of that reading are wrong, and the sentence is why.

## 2. The plat draws ONE watercourse, and it is not the source of the count

The whole sheet was read: North Division (x 1000–2728), West Division (x 60–1000,
y 300–1944), South Division (x 1080–2728, y 760–1944), and the east margin out to the
*Due North line*. Crops were taken at 1.8× to 5× and vertical strokes were located by
column scan rather than by eye.

**One watercourse is drawn, and only one.** It runs north out of the main stem across
**North Division block 6** — the fifth block west of the plat's east boundary in the tier
that fronts North Water Street — and it is drawn **as two banks**, not as a line:

| where, on the sheet | west bank (px) | east bank (px) | drawn width |
|---|---:|---:|---|
| block 6's north line | 1321.5 | 1377.0 | 55.5 px |
| block 6's lower lot row | 1346.5 | 1393.0 | 46.5 px |
| at North Water Street | ≈ 1378 | ≈ 1428 | ≈ 50 px |
| south of the street, at the mouth | 1333.5 | 1389.5 | 56 px, flaring |

The pair wanders 16–21 px across one lot row while the block's lot lines hold to ±1 px over
the same span, so they are not lot lines drawn badly. They never cross. South of North
Water Street they turn away from each other — west bank west, east bank east — and each
runs into the heavy line of the main stem's north bank. That is a mouth, and the plat draws
it open.

**Nowhere else on the sheet is any watercourse drawn.** The West Division carries the North
Branch's east bank and nothing else; the diagonal through block 22 that reads like one at
low magnification is the lot line bearing *North 26° W / North 51° W*, lettered along
itself. The South Division carries the main stem's two banks and nothing else — no La Salle
slough, no State Street slough, and no re-entrant in any block face between Market and
State.

**So the plat is not the source of "three sloughs off the Main Branch."** It never was:
`main_branch_sloughs_1833.md` § 1 established in 2026-08-20 that the phrase is a caption on
a *Conley/Stelzer 1933* figure reproduced in Chicago Architecture History, and that
Conley/Stelzer is the operative source for all three. What survived that correction was a
sentence inside the committed data crediting the count to Thompson, and it is corrected here.

## 3. Where block 6 is, and what the plat's channel corroborates

The sheet's east–west axis was fitted to the committed grid on **five South Division street
corridors**, whose centres were read as the midpoint of the gap between two block faces:

| corridor | sheet px | fit → local E | committed E | residual |
|---|---:|---:|---:|---:|
| Wells | 1735.50 | +327.9 | +329.3 | −1.4 m |
| La Salle | 1964.75 | +451.7 | +451.3 | +0.4 m |
| Clark | 2194.00 | +575.6 | +574.7 | +0.9 m |
| Dearborn | 2425.00 | +700.3 | +697.7 | +2.6 m |
| State | 2652.50 | +823.2 | +825.8 | −2.5 m |

`E = 0.540168 · px − 609.567`, **0.5402 m/px**, residuals ≤ 2.6 m over 500 m. The
independent check is the platted street itself: an 80-ft corridor measures 46.5 px on this
sheet, which the fit returns as **25.1 m against the platted 24.384 m** — 3 % high, which is
paper and pen and not a wider street.

Applied to block 6, entirely across the sheet's centre fold and therefore worth less than
the residuals above:

| feature | local E |
|---|---|
| block 6, west face | +90.1 |
| block 6, east face | +189.9 |
| plat channel, west bank | +104.3 (north line) … +110.7 (mouth) |
| plat channel, east bank | +134.2 (north line) … +141.0 (mouth) |
| **committed `north_side_slough` centreline** | **+133.0 … +189.5**, mouth at (189.5, 152.5) |

The committed slough — traced from Wright 1834, a different sheet by a different hand — runs
**inside block 6 and only inside block 6**, and its western extent (+133.0) sits on the
plat's east bank (+134.2). The two sheets agree on the block. They disagree on where in the
block by about **half a block face, 48–55 m**: Thompson puts the channel in the west half,
Wright in the east.

**That is the whole of the corroboration and it is graded as such.** `thompson_plat_1830` is
a parameter source — a Canal Commissioners' working copy, no high-resolution scan, never
traced for geometry — and nothing here is committed from it. What it now supports, which it
did not before, is that Wright's watercourse existed on an 1830 sheet too, in the same block.

**The north–south axis was deliberately not fitted.** Block depths on this sheet are not one
module (the plat letters both 150 and 180 ft), and the one anchor checked — block 6's north
line — lands about a street width off the committed Kinzie corridor. Whether the plat's
*East and West line* is Kinzie's north side or its south side, and whether the North
Division carries one tier of blocks here or two, is **T-0451's question**, and this reading
hands it over rather than settling it in passing.

## 4. The crossings (T-0452 acceptance 2, the fact T-0451 asked for)

Read off the sheet, as topology, which is what the sheet can carry:

- **The channel crosses block 6's lots.** Both banks run from the block's north line to its
  south line. The lot lines are drawn straight *through* the channel and the lot numbers
  5 · 6 · 7 · 8 and 4 · 3 · 2 · 1 are lettered on both sides of it. At the block's north
  line the west bank stands 0.14 of the face east of the west corner (≈ 45 ft of a 320-ft
  face) and the east bank 0.44 (≈ 141 ft) — so the channel occupies most of lot 6 and part
  of lot 7 in the north row, and the answering lots 3 and 2 in the south row.
- **The channel crosses the block's 18-ft alley**, at the block-number circle.
- **The channel crosses North Water Street**, and flares below it into the main stem.
- **The channel does NOT cross Kinzie Street on this sheet.** Both banks stop dead at the
  block's north line. The plat draws the water to its own boundary and no further, so it
  says nothing at all about the ground north of that tier. Wright 1834 is what carries the
  course on across Kinzie to Michigan Street, and it is what the committed trace is from.

**Thompson platted lots across his own water.** That is the load-bearing finding for
T-0451: laying the North Division grid over the slough is not this project inventing a
fault, it is the plat. A grid laid there is faithful; a grid laid there *silently* is not.

## 5. The reconstruction holds three sloughs, not one

T-0452's premise — *"the plat draws three and this holds one"* — read
`hydrology.geojson` alone. The other two are held in `terrain_spec.json`, and have been
since T-0005:

| # | slough | where it is held | form |
|---|---|---|---|
| 1 | north-side | `hydrology.geojson` `north_side_slough`, carved via `terrain_spec.json` `watercourses[0]` | traced centreline, `bed_ft −1.0`, `e_fold_m 1.2` |
| 2 | La Salle Street | `terrain_spec.json` `swales[2]` `lasalle_slough_lower`, `swales[3]` `lasalle_slough_upper` | authored centreline + half-width swales |
| 3 | State Street | `terrain_spec.json` `swales[4]` `state_slough_course`, `swales[5]` `state_slough_mouth` | authored centreline + half-width swales |

All three are also bridged: `slough_log_bridge`, `lasalle_slough_crossing` and
`north_water_slough_crossing` are committed structures with approaches in the same spec.
Nothing is missing. What was missing was a sentence saying so, in the file a reader opens
first.

## 6. Is a centreline enough? (T-0452 acceptance 3 — decided)

**It already is, and no width is invented.** The acceptance test is conditional — *"if lots
or buildings are to be kept out of the slough, it needs a width the ground can test"* — and
the condition is answered by measurement rather than by argument.

- **The ground already tests a width.** The centreline is not bare: `drafted_width_m 7.1`
  carries into `terrain_spec.json` `watercourses[0]`, which cuts a bed at −1.0 ft with a
  1.2 m e-fold. There is a channel in the heightfield, not just a line in a file.
- **Nothing committed stands in it.** Every placed phase in `data/structures/` was measured
  against the centreline. The nearest is `north_water_slough_crossing` at **6.0 m** — the
  bridge over it, which is meant to be there. The nearest that is not a crossing is
  `inf_boatman_cabin_north` at **65.8 m**. Against Wright's 3.55 m half-width that is 18×;
  against the plat's much wider drawn band (half-width ≈ 15 m) it is still 4.4×.
- **So a bank polygon would keep nothing out that is not already out**, and it would have to
  choose between two drawn widths that disagree by 3.5× — Wright's 7.1 m and Thompson's
  25–30 m. Choosing one of those and calling it the bank is exactly the fiction the note
  already refuses. **No `docs/LIBERTIES.md` entry is added, because no invention is made.**

The recorded consequence: `width_confidence` stays `inferred`, the width stays Wright's, and
the plat's disagreeing figure is on the record here so that the next reader does not have to
re-measure the sheet to find out it was looked at.

*Caveat, found while this was written and already filed: `tools/trace_river.py` would write
`width_confidence: reconstructed` and `depth_confidence: conjectural` on its next run, against
the committed `inferred` / `reconstructed`. Two runs found that on the same day — it is
**T-0687**, which proves with `trace_river.py --check` that the geometry is byte-identical and
only the two strings differ. This memo argues from the committed grades, and T-0687 is where
they get decided.*

## 7. What this reading refuses

- **It does not commit a course from the plat.** Not the channel, not its banks, not its
  mouth. `thompson_plat_1830` keeps `asset_use: inventory` and the source note's standing
  rule; the E-axis fit in § 3 exists to *place a corroboration*, and its output is a
  sentence, not geometry.
- **It does not rule on the North Division's grid, its tiers, or its cross streets.** § 3's
  last paragraph is a handoff to T-0451, not a finding.
- **It does not regrade the north-side slough.** `confidence: attested` for existence and
  course was already right on Wright alone; a second sheet agreeing at block resolution does
  not move a grade that was not resting on the count.
