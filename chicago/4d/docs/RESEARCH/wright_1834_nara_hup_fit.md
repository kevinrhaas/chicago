# The registration of the National Archives Wright sheet, adjudicated

**Ticket:** T-0878, adopted by T-1091 on 2026-09-12. **Answer file:** `data/traces/gcp/wright_1834_nara_hup_fit_adjudication.json`,
recomputed from committed data by `tools/adjudicate_wright_na_fit.py --check` on every commit.
**New control:** `data/traces/gcp/wright_1834_nara_hup_section_corners.json`.

> **M1 IS THE FIT IN FORCE** since T-1091. `fit` in the registration carries its eleven-point
> coefficients; the eight-point affine T-0787 published is kept beside it as `retained_fit`,
> because the section's corner pixels were recovered by inverting it and the adjudication that
> compares the two fits needs both. **T-1092 completed the adoption on 2026-09-13**: the four
> SEATED traces are carried through `fit` now, and `retained_fit` is read only where reading it
> is the point. Everything below is the argument that got here, kept in the tense it was
> written in where it is about the decision, and updated where it is about the state of the
> files.

## The question

T-0787 registered the National Archives / Historic Urban Plans reproduction of James Wright's
1834 survey against eight modern street crossings, and got a 16.19 m RMS — marginally better
than the 17.5 m the BPL copy gets on the same eight. Then T-0797 read the School Section off
that sheet, and the section is a statute mile square: 1609.344 m on a side, its north-east
corner the PLSS corner of sections 9/10/15/16 and GCP G1 of the registration itself. Measured
through the fit, the square came out **1603.04 m east-west and 1658.65 m north-south** — the x
scale right to four tenths of one per cent, the y scale **three per cent long**, more than the
width of any block in the grid and eight times the fit's own RMS.

T-0878 asked whether the eight-point global affine should stand, and if not what replaces it: a
y-scale correction, a second-order term, or control at the sheet's foot.

## Why the question is answerable without re-opening the raster

T-0797 committed its measured line table in local ENU metres, and the fit is an invertible
affine. Inverting it on the four corner intersections of that table returns the pixel
coordinates the reading was taken at, to within the table's own 0.01 m rounding — 0.014 px. So
the four corners of the section, in the sheet's own pixel space, are committed evidence:

| corner | NA pixel |
|---|---|
| NE (State & Madison) | 2950.0, 3241.3 |
| NW (Halsted & Madison) | 653.9, 3169.2 |
| SW (Halsted & Twelfth) | 648.0, 5423.3 |
| SE (State & Twelfth) | 2944.1, 5495.3 |

The NE corner is the same point of the drawing as G1, whose committed pixel is 2951.0, 3225.0.
Sixteen pixels apart — twelve metres, inside the fit's own RMS, and almost all of it in y,
which is the axis the ticket is about.

## The finding, before any model is fitted

**All eight control points lie between y=1631 and y=3225 px of a 6628 px sheet.** The section
occupies y=3169–5495, entirely below every one of them. The fit's y scale is therefore measured
over a 1594 px band in the top half of the sheet and *carried* over the rest.

And the section is a ruler. A pixel length divided by a known ground length is a scale, and it
needs no control point at all:

| | the section says | the eight-point fit says | fit departure |
|---|---|---|---|
| x | 0.70055 m/px | 0.6985 | −0.29 % |
| y | 0.71397 m/px | 0.7358 | **+3.06 %** |
| x/y anisotropy | 1.92 % | 5.20 % | |

So the paper *is* anisotropic — the manuscript was torn from the upper right margin and mounted
on cloth, as its own printed caption says, and the long axis is the one that stretched — and the
fit trebles it. **The three per cent is an extrapolation error, not a scale error.** That matters
because a uniform correction cannot mend an error that is not uniform.

## The four candidates

Scored on RMS against the original eight, against the section's three other corners (where the
incumbent has never been scored), against all eleven, and on leave-one-out — each point
predicted by a fit that never saw it, which is the only number in the table that cannot be
bought by adding parameters.

| model | RMS/8 | RMS/3 corners | RMS/11 | worst | **leave-one-out** | mile N–S |
|---|---|---|---|---|---|---|
| **M0** the 8-pt affine, now `retained_fit` | 16.19 | 42.71 | 26.23 | 59.12 | 23.29 | +3.06 % |
| **M1** affine, 11 pt, foot control | 18.39 | 6.22 | 16.02 | 37.00 | **20.17** | +1.03 % |
| **M2** M0, y rescaled ×0.970273 | 27.89 | 16.88 | 25.36 | 41.11 | n/a | 0.00 % |
| **M3** second-order poly, 11 pt | 16.33 | 0.74 | 13.94 | 27.80 | **51.28** | +0.23 % |

The tool reproduces M0's published 16.19 m from the control alone, which is what licenses the
rest of the table. The model keys in the answer file are `M0_retained_affine_8pt`,
`M1_affine_11pt_foot_control`, `M2_retained_affine_y_rescaled` and `M3_poly2_11pt`, and the
displacement table is measured **from the fit in force** — so each row answers what would move
if that model were adopted today.

**M2, the y-scale correction, is rejected.** It buys the mile exactly and pays 11.7 m of RMS on
the control the project already had; G2, G6 and G7 each move 29–35 m. It does not remove the
error, it moves it onto the only part of the sheet that was measured properly.

**M3, the second-order term, is rejected.** Twelve coefficients on eleven points: best in-sample
of anything here and worst out of sample by a factor of two. It also throws readings as far as
120.5 m. The leave-one-out is the measurement that says so — not a prior about polynomials.

**M1, control at the sheet's foot, is adopted** — and in force since T-1091. Same functional form, refitted on the eight
plus the section's other three corners. It is the only candidate that improves the honest
out-of-sample number, 23.29 → 20.17 m; RMS at the section's corners falls 42.71 → 6.22 m, the
worst point 59.12 → 37.00 m, and it costs 2.2 m on the original eight.

### Why M1 stops at one per cent, and why that is the right place to stop

Because the control it is given is itself long. The square the three OSM crossings make with
G1's modern position measures 1620.09–1624.23 m on its four edges against the mile — a mean
**+12.73 m, 0.79 per cent, in both axes and in the same direction**. That is what widened
streets do to a crossing of centrelines, and not what stretched paper does: Halsted Street and
Twelfth Street were both widened after 1834, Twelfth into Roosevelt Road in the 1910s, and a
widening that takes ground from one side moves the centreline. Two of the three are multi-node
crossings of a divided roadway, with node spreads of 16.95 m and 14.48 m against a maximum of
6.4 m across the registration's eight.

M1's residual mile error — +1.03 % north-south, +0.66 % east-west — straddles that 0.79 %. The
model has reproduced its control, and what is left is the control's error. Driving the mile to
zero is precisely what M2 does and precisely why M2 is rejected.

## What adoption cost

T-0878's acceptance said to measure the change on the committed traces *before* adopting, and
T-1091 adopted on that measurement. The table is the distance each trace's readings moved when
the fit changed — which is also, read the other way, the cost of going back:

| trace | readings | median move | max |
|---|---|---|---|
| School Section block numbering | 143 | 27.65 m | 84.37 m |
| Wabansia block numbering | 28 | 25.22 m | 34.81 m |
| Wabansia streets | 12 | 22.80 m | 32.63 m |
| Kinzie block name | 4 | 21.29 m | 21.29 m |
| Wabansia water lots | 60 | 17.98 m | 23.73 m |
| Michigan St tract grid | 15 | 9.98 m | 13.65 m |
| Kinzie addition block numbering | 53 | 8.19 m | 84.37 m |
| Kinzie addition street grid | 5 | 7.84 m | 13.58 m |
| School Section block grid | — | rigid, 16.21 m | (anchored on G1) |

Twenty-seven metres of median movement in the School Section's numbering is more than a block.
So adoption is a regeneration of nine committed traces, a re-seating of four grids, and a
re-bake of every structure standing on ground that moves — more than one run, which is why it
was split into **T-1091** (adopt the fit, regenerate the five pure readings) and **T-1092**
(re-seat the four grids, re-bake).

**T-1091 did the first half.** `fit` is M1; `retained_fit` is the eight-point affine, kept whole
with its own per-point residuals in `gcps[].residual_m_in_retained_8pt_fit`; the three foot
corners carry a `residual_m` each; and the five pure readings were regenerated by their own
generators. Two of the five came back byte-identical — the Kinzie block name and Kinzie's
Addition's block numbering are seated on the committed grid rather than carried through the
sheet's own fit, so a change of registration does not reach them, and their regeneration is the
check that says so.

**T-1092 did the other half, on 2026-09-13.** The same seven tools — `read_kinzie_addition_streets`,
`read_michigan_st_tract`, `read_wabansia_streets`, `seat_wabansia_streets`, `carry_kinzie_west`,
`generate_school_section_grid` and `measure_school_section_tier_skew` — read `fit` now, and each
says so at the line where it loads it. Fifty street records moved with them: the School Section's
twenty-seven, Kinzie's Addition's eleven, the Michigan St tract's four, Wabansia's six and
`kinzie_west`, plus `madison`, `monroe`, `adams`, `jackson`, `hubbard` and `michigan_north`, which
the section grid and the Addition's seating own.

**The re-bake came out empty, and that is a result rather than a shortcut.** `validate.py --stale`
re-ran over all 384 assets and found none stale, because the ground these four grids describe is
the town's UNBUILT survey — the School Section's platted blocks south and west of the built town,
the Addition's street grid, the Michigan St tract and Wabansia — and no committed structure stands
on any of it. A structure is positioned by its own coordinate, not by the street it fronts, so a
corridor that moves 16 m does not move a mesh; what it moves is every derivation that CITES a
committed street line. Four of those had to be re-derived in the same commit and were: the
Washington-Madison tier's seven numeral crop boxes, four of the West Division's eighteen — both
of which had a gate on every commit and no writer until this ticket gave
`read_washington_madison_numerals.py` and `read_west_division_numerals.py` a `--write` — the
yard goods, whose frontages are chosen off street faces, and the land-tract join. The reading
is never rewritten by either: `read_at` is the window the numeral was actually read on, only
the cited box moves, and a box that no longer holds its own read window is an error rather than
a widening.

**Two figures were typed into tools rather than read from the registration, and both were the
superseded fit's 16.19 m.** `read_wabansia_streets.py` quoted it as the tolerance its Kinzie
cross-check is judged against, and `read_wright_legend_swatches.py` as the grace on chip 5's
band containment. Both read `fit["rms_m"]` now. The first mattered: through M1 the sheet puts
Wabansia's Kinzie 20.9 m from the committed line where the eight-point fit put it 8.8 m, so the
gap is no longer inside the registration's own RMS, and the record says so in those words
instead of asserting agreement. The identification does not rest on that gap — Wright letters
`Kinzie` inside the corridor — but the note used to read as though it did.

## The datum is not at risk

`tools/rederive_datum.py` fits from `data/traces/gcp/wright_1834_gcps.json`, the BPL master, and
never reads this sheet. Adopting M1 moves readings taken off the NA scan; it does not move the
scene origin or anything keyed to the BPL registration. That was the one thing the ticket
feared, and it is not there.

## The practical rule now

A reading taken south of Madison Street off the NA sheet used to carry about three per cent of y
error; through M1 it carries about one, and that one is the control's rather than the paper's.
The rule underneath has not changed and is why T-0797's grid was never wrong: **anchor on a
length that is known on the ground, not on the paper.** M1 is still one affine over a sheet
whose paper is not uniform — 37.00 m at its worst control point — and a reading that needs
better than that needs its own local control, not a better global fit.

## What holds this

`tools/check_wright_nara_registration.py --check-properties` scores the fit against **all
eleven** of its control points, holds `rms_m_on_the_eight` and `rms_m_on_the_three_corners`
apart so the 2.20 m the adoption cost the original eight stays visible, and re-derives the
retained fit's own arithmetic beside it. Its `--self-test` breaks eighteen things and watches
each one fire, five of them T-1091's. `tools/adjudicate_wright_na_fit.py --check` re-runs this
whole page's measurement on every commit, and since T-1091 also refits the eleven points and
compares the result with the coefficient block actually committed — so a hand edit to those six
numbers is caught rather than silently redefining the baseline of the displacement table.
