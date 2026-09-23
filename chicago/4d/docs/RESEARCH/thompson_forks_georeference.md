# The Thompson 1830 plat at the forks, measured against the Wright 1834 line

**Record:** none — this memo is about a *measurement*, not about a building ·
**Data:** `data/traces/gcp/thompson_1830_gcps.json`,
`data/traces/vectors/thompson_1830_forks_banks.json` ·
**Compared against:** `data/terrain/epochs/e1834_harbor_cut/river.geojson` ·
**Ticket:** T-0685, piece 2 of T-0453 · **Read on:** 2026-09-05

---

## 0. The question, and the answer in one paragraph

T-0453 records the owner reading the Thompson plat differently from this project at Wolf
Point. Nothing could settle it, because the plat had never been fitted to the frame the
Wright line lives in: `data/sources/thompson_plat_1830.json` is a PARAMETER SOURCE, read for
its stated figures and never traced, and `data/traces/gcp/` held control for Wright and
Hathaway and for nothing else. This memo fits it, traces its river at the forks, and measures
the two sheets against each other.

**They disagree, and the disagreement is on the BRANCH, not the stem.** Along the main stem
the two north banks are within 13 m of each other from local E +200 eastward and within 18 m
from the point to E +125 — inside the ±20 m the Wright georeference already declares.
On the North Branch they are not close: Thompson draws its **east** bank 27–43 m west of the
Wright line and its **west** bank 35–60 m west, over the whole reach from the point up to
local N +240. He also draws the branch **wider** — 88–93 m against 66–83 m at the same
northings. **The owner is right that the sheets differ at Wolf Point, and by more than the
declared tolerance.** Nothing has been moved: which line is the planform of record is his
ruling, and § 6 says what each choice costs.

## 1. The georeference

Ground control is **modern**, and deliberately the same kind and the same source as
`wright_1834_gcps.json`: street intersections from OpenStreetMap via the Overpass API,
reduced to EPSG:26916. Four of the twenty-two are intersections the Wright file itself
carries, and they reproduce its committed coordinates. Fitting both sheets against one
external frame is what makes the difference between them a difference between the SHEETS.

Twenty-two control points: Lake, Randolph and Washington against Franklin, Wells, La Salle,
Clark and Dearborn in the South Division; Fulton, Lake, Randolph and Washington against
Clinton and Canal in the West Division. Each plat pixel is the **midpoint of the two block-edge
lines that bound the street corridor**, found by an ink-density peak in a band taken from the
neighbouring block face — 46 px of corridor at this raster's scale, so a well-conditioned
reading. Picked to about ±2.6 m, which is the spread observed when the same street is picked
in three different tiers.

What is deliberately **excluded**: Market Street and South Water Street, because their modern
successor is Wacker Drive and it moved; and all four of the sheet's boundary lines — Kinzie,
Madison, State and the Des Plaines line — because a boundary drawn as a single stroke does not
say whether it is the street's centre or the block face, and half a corridor is 12.2 m of
unforced ambiguity.

| | Thompson 1830 | Wright 1834 | Hathaway 1834 |
|---|---|---|---|
| fit | similarity | affine | affine |
| RMS | **4.9 m** | 17.5 m | 17.7 m |
| max residual | 7.8 m | 32.7 m | 25.9 m |
| control points | 22 | 8 | 5 |
| scale | 0.5247 m/px | 0.698 / 0.725 | 0.641 / 0.670 |
| rotation | 0.78° | 1.18° | −0.26° |
| axis scale difference | 0.56 % | 3.7 % | — |

**That is not a claim that the 1830 survey is better than the 1834 one**, and the table would
mislead read that way. Thompson's town is a rectilinear grid whose modern successor streets
still run on its lines, so its control points are corners of the very figure being fitted; the
1834 sheets are drawn surveys of a landscape. And this raster is a modern photographic
reproduction, not the warped original — its 0.56 % of differential scale, against Wright's
3.7 % of real paper stretch, is why the conformal fit is the honest one here. It **is** a
claim that the sheet can be positioned to a few metres, which is all the measurement needs.

The residuals are not white, and the pattern is worth recording: **Canal Street reads 5–8 m
west of its fitted place at all four of its crossings and Franklin 3–8 m east at all three of
its** — the sheet's east–west module is very slightly compressed across the river relative to
the modern grid. The sign is consistent per street, so it is a property of the sheet.

## 2. The trace

Both bank lines are the two largest 8-connected components of the sheet's ink in a window over
the forks, at 40 grey levels below the local paper. **No pixel of either line was placed by
hand.** 129 vertices on the North Division shore, 117 on the West Division shore, thinned to a
4.7 m minimum spacing. Committed to
`data/traces/vectors/thompson_1830_forks_banks.json` **beside** the Wright planform, never over
it, with the pixel readings kept as the evidence.

## 3. The measurement, at named northings — the North Branch

`plat` is Thompson, `wright` is the committed 1834 planform; `E` is local ENU metres east of
the datum, negative west. A negative delta means Thompson draws the bank WEST of Wright.

| N | east bank plat E | east bank wright E | Δ | west bank plat E | west bank wright E | Δ | plat width | wright width |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | −18.6 | −10.6 | −8.0 | −127.8 | −93.4 | −34.4 | 109.2 | 82.8 |
| +20 | −43.5 | −23.4 | −20.1 | −137.4 | −96.6 | −40.8 | 93.9 | 73.2 |
| +40 | −57.9 | −32.9 | −25.0 | −147.1 | −99.7 | −47.4 | 89.2 | 66.8 |
| +60 | −66.2 | −36.0 | −30.2 | −154.2 | −102.4 | −51.8 | 88.0 | 66.4 |
| +80 | −70.2 | −36.1 | −34.1 | −158.9 | −103.1 | −55.8 | 88.7 | 67.0 |
| +100 | −71.3 | −36.2 | −35.1 | −163.9 | −103.7 | −60.2 | 92.6 | 67.5 |
| +120 | −73.6 | −33.3 | −40.3 | −163.3 | −103.2 | −60.1 | 89.7 | 69.9 |
| +140 | −73.6 | −30.9 | −42.7 | −161.8 | −101.7 | −60.1 | 88.2 | 70.8 |
| +160 | −72.8 | −31.8 | −41.0 | −161.2 | −102.2 | −59.0 | 88.4 | 70.4 |
| +180 | −72.5 | −34.6 | −37.9 | −161.3 | −105.7 | −55.6 | 88.8 | 71.1 |
| +200 | −71.3 | −37.3 | −34.0 | −160.8 | −108.3 | −52.5 | 89.5 | 71.0 |
| +220 | −70.5 | −40.1 | −30.4 | −161.0 | −109.2 | −51.8 | 90.5 | 69.1 |
| +240 | −69.9 | −42.9 | −27.0 | −159.3 | −112.5 | −46.8 | 89.4 | 69.6 |

Perpendicular distance from each committed vertex to the Thompson line, over the shared reach:
North Division shore **median 9.7 m, mean 14.4 m, p90 35.3 m, max 42.7 m** (17 vertices);
West Division shore **median 49.2 m, mean 42.4 m, p90 59.7 m, max 60.4 m** (8 vertices).

## 4. The measurement, at named eastings — the main stem

| E | plat N | wright N | Δ |
|---:|---:|---:|---:|
| 0 | −2.4 | −9.1 | +6.7 |
| +25 | +6.5 | −11.4 | +17.9 |
| +50 | +15.8 | +3.3 | +12.5 |
| +75 | +28.4 | +20.4 | +8.0 |
| +100 | +47.0 | +37.5 | +9.5 |
| +125 | +63.1 | +56.6 | +6.5 |
| +150 | *(the slough mouth — see below)* | | |
| +175 | +115.4 | +127.5 | −12.1 |
| +200 | +107.3 | +141.1 | −33.8 |
| +225 | +110.2 | +123.7 | −13.5 |
| +250 | +109.5 | +122.2 | −12.7 |
| +275 | +108.8 | +118.0 | −9.2 |
| +300 | +109.2 | +113.8 | −4.6 |
| +325 | +108.3 | +112.1 | −3.8 |
| +350 | +107.8 | +110.5 | −2.7 |

**E +150 to +200 is not a bank disagreement and must not be read as one.** Both sheets draw the
same feature there — the one watercourse running north out of the main stem that
`docs/RESEARCH/thompson_plat_sloughs.md` records, flaring at its mouth — so the north bank is
not single-valued in E across it, and sampling "the bank at E = +150" samples two different
sides of a doubled-back line on the two sheets. The 88.8 m that a naive row would print there
is an artifact of the sampling, and it is why that row is struck out rather than tabulated.
Either side of the mouth the two agree to 13 m.

## 5. Why the disagreement is not the fit

The branch readings are 200–240 m north of the northernmost control point (Fulton Street, local
N +12), so the obvious objection is that they are extrapolation. They are, and it does not
account for them:

- **Rotation.** RMS 4.9 m over a 1,900 px control baseline bounds the fitted rotation to about
  0.28°. Carried 434 px north of Fulton that is **1.1 m** of lateral error.
- **Translation.** RMS/√n is about **1.0 m**.
- So the Thompson fit contributes on the order of **3 m** to a 27–60 m disagreement.
- The Wright fit's own declared RMS is 17.5 m and can contribute that much. Even taking it at
  its worst, **15–40 m of the disagreement is between the two draughtsmen**, not between the
  two georeferences.
- The disagreement is also *structured*, which noise is not: both banks are displaced west
  together, by similar amounts, over 240 m of reach, and the channel between them is
  consistently ~20 m wider.

## 6. What each answer costs — for the owner's ruling

Nothing here moves, on purpose (T-0685 acceptance 5). The bank is the argument of the
heightfield, the water surface, the seven river landings, every waterline test and the
frontage rules that stand on them; moving it re-derives all of that and is its own unit of
work. So this memo ends at the measurement, and the ruling belongs to the owner.

**The case for Wright 1834 (the status quo).** It is a survey OF the landscape, at a date four
years nearer the scene, and the river is its subject. Thompson's sheet is a plat of lots: its
river is a boundary, drawn freehand — the stroke visibly wavers where a surveyed line would
not — and the surviving artifact is a Canal Commissioners' working copy dated to at least 1836,
so the line may be a copyist's. This is why the trace is graded `inferred` and why
`thompson_plat_1830.json` says to read the sheet for its figures and not to trace it.

**The case for Thompson 1830.** It georeferences four times tighter, and it is the legal
definition of the town: the blocks it bounds are the blocks that were sold. If the North
Branch really ran 30–50 m west of where this project puts it, the West Division's water edge
is wrong by more than a block face, and Wolf Point — the promontory the owner named — is the
part of the model most affected.

**A third answer, and the likeliest one.** The two need not be reconciled into one line. Four
years and a harbour cut separate the sheets, the branch above the forks was actively silting
and being dredged, and a 20 m difference in drawn width is exactly what two draughtsmen with
different purposes produce. What the project can honestly say is that the position of the North
Branch at Wolf Point is uncertain by ~40 m, which is **twice** the ±20 m
`thompson_plat_1830.json` currently declares — and that number, whatever the ruling, should be
what the file says.

## 7. What was NOT done

- Nothing moved: no bank, no waterline, no heightfield, no landing, no lot (acceptance 5).
- The plat's grid was not traced for geometry. The georeference exists to measure the sheet,
  and `data/sources/thompson_plat_1830.json`'s standing instruction is unchanged.
- The South Division shore (the south bank of the main stem and the east bank of the South
  Branch) is drawn on the plat and was not traced here. The ticket asked about Wolf Point.
- T-0451 — the North Division's missing north–south streets — waits on this ruling, because the
  ground those streets stand on is bounded by this bank.
