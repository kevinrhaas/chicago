# T-3321 — 1808 Prairie's alley wall (piece 1 of T-1944)

HABS IL-1015 sheet 2 (first floor plan, 1963) turns the Glessner courtyard's south wall south
along the alley, off the granite gate pier. T-2201 built the court wall and left this return to
T-1944, because it stands on 1808 Prairie's alley line (L-glessner-court-wall-2201). It is now
built on 1808's record as `alley_wall` (plan, inferred) and `alley_wall_height` (reconstructed),
by `k11_frontage.alley_wall`.

## The run, measured

Committed scan `chicago/prairie_1904_v1/research/public/glessner-habs-sheet-2.png`, 37.2 px/ft,
crop x 7400-8400, y 1700-2700 (north is down on the sheet, so south is up):

| what | pixels | feet | 1808's frame |
|---|---|---|---|
| west face | the heavy line that runs on as the pier's outer face | W 162.0 | u -31.378 |
| thickness (hatch, x 689-742) | 53 | 1.4 ± 0.15 | east face u -30.948 |
| length from the court wall's north face (y 200-504) | 304 | 8.2 | s 7.921 (south end) |
| north end | the court wall's south face | S 75.1 | s 10.085 |

Glessner's frame is x = (161.25 - W) x 0.3048, y = (74.0 - S) x 0.3048; 1808's origin is
that frame's (31.149, -10.42) on the same bearing.

**Height and coping** (reconstructed): the court wall's own, 9.2 ft over Glessner's model grade
(2.804 m) under 0.18 m of stone that overhangs 0.06 m on each free side, so the two copings meet
at one line. The north end abuts the court wall: its end face is not drawn and its coping stops
0.06 m short, under the court wall's overhang. Liberty `L-1808-alley-return-1944`.

**Brick:** the K11 wall's slot of 1808's K03 panel (common buff), outside the envelope's
materials, so the house's origin and grade are still read off the house alone
(`k01_contract --measure-asset keith_house_1808_prairie`: every verdict ok).

**Web tier at 16 bits.** The run carries the GLB's plan 31 m back to the alley; at 14 bits the
longer grid collapsed 10 sub-millimetre triangles of the house's own carving (the corner boss's
dress stone, the bay stone) and the K01 contract refused the tier. `tools/web_derivatives.sh`
gives this one asset 16 bits, as it gives Glessner's v4 master; same size (3.49 MB).

## Photo matches

All 16 of 1808's records re-rendered on the new GLB. Nine side-by-sides changed, each only in a
small box: in seven the wall draws where the picture shows the Glessner house (these records
render 1808 alone), recorded `not shown`; verdicts unchanged (`matches`), image gate holds.

## Browser evidence

`node tools/qa_1808_alley_return_t3321.mjs` on the published `/1904/` app, desktop 1280×800 at
`full` and mobile 390×780 at `light`: four stands each (alley-corner, the T-2201 stand for
before and after; alley-south; yard-east; overhead). Zero page errors and zero failed requests.
The frame budget's triangle line is over at the stands that look up 18th Street (desktop
alley-corner 6.14 M and alley-south 5.67 M against 4.7 M; mobile alley-corner 1.48 M against
1.27 M): the district's load since T-2201 measured 2.94 M at the same stand. This run adds
20 triangles.
