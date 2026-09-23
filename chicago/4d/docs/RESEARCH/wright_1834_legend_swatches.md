# Wright's 1834 legend: nine chips, and how many colours they actually carry

T-0792 piece 1 · the record is `data/traces/wright_1834_legend_swatches.json`, built and
gated by `tools/read_wright_legend_swatches.py`

J. S. Wright's 1834 manuscript survey carries, low on its eastern half, a column of nine
small painted chips with a line of writing beside each. It is the only place on any sheet
this project holds that says **who surveyed what ground and when**. Three open tickets ask
for a wash to be read "against the legend's swatches" — T-0792 for the tract layer itself,
T-0796 for the small platted square north of Kinzie Street, T-1082 for the colour between
Wright's bank shading and his inked bank line — and until this reading none of them could,
because no chip had a committed colour, a pixel box, or any statement of how far apart the
nine of them are.

## The chips, measured

Read off the NA/Historic Urban Plans scan (5050 × 6628 at 600 dpi,
`wright_1834_nara_hup`) rather than the BPL copy: at 600 dpi a chip is 54 px wide and at
the BPL scan's resolution it would be half that. Each chip's interior is sampled with its
inked border eroded away — 54 px across, 21 to 34 px down, roughly a thousand pixels each.

| # | the hand writes | read as | date | median RGB | per-channel sd |
|---|---|---|---|---|---|
| 1 | U. S. Military Reservation | U.S. Military Reservation | — | 44, 65, 93 | 19, 22, 24 |
| 2 | Surveyed by Canal Com. in 1830 | the Original Town | 1830 | 176, 68, 48 | 44, 36, 26 |
| 3 | Wonbonsia Surveyed in 1831 | Wabansia | 1831 | 145, 38, 14 | 31, 16, 10 |
| 4 | Kinzies Addⁿ. Surveyed „ 1833 | Kinzie's Addition | 1833 | 54, 44, 29 | 33, 31, 20 |
| 5 | School Section „ 1833 | the School Section | 1833 | 218, 136, 26 | 61, 47, 15 |
| 6 | Surveyed. ———— 1833 | **no tract named** | 1833 | 70, 67, 40 | 39, 38, 27 |
| 7 | Fractional Section 15 | Fractional Section 15 | — | 135, 37, 11 | 41, 30, 20 |
| 8 | Surveyed in 1833 | **no tract named** | 1833 | 180, 112, 39 | 51, 42, 22 |
| 9 | Part of Canal Sec. No 9 | Part of Canal Section No. 9 | — | 57, 50, 23 | 53, 47, 37 |

Two notes on the reading of the hand. Line 3 is written **Wonbonsia**; the project spells
the tract Wabansia everywhere else and that is what the line is taken to say, but the
sheet's own spelling is kept in the record so the next reader can disagree. Lines 4 and 5
end in a ditto mark carrying *Surveyed* down from line 3.

## The result that matters, and it is a refusal

T-0792's second ask is to read the two unnamed swatches — line 6's *Surveyed 1833* and
line 8's *Surveyed in 1833* — "by matching swatch to ground on the sheet", and explicitly
**not** by guessing from the legend's order. Measured, that method cannot do it.

The nine chips do not carry nine separable colours. Grouped by single linkage at 35 RGB
units they collapse to **six**, and the two closest pairs are not close calls:

| | separation |
|---|---|
| chip 4 *Kinzie's Addition* and chip 9 *Part of Canal Section 9* | **9.0** |
| chip 3 *Wabansia* and chip 7 *Fractional Section 15* | **10.0** |
| chip 6 *Surveyed 1833* and chip 9 | 27.0 |
| chip 4 and chip 6 | 30.0 |
| chip 5 *School Section* and chip 8 *Surveyed in 1833* | 47.0 |

Against that, the spread **inside a single chip** runs from 10 to **60.8** RGB units per
channel. A chip is one patch of one wash on one piece of paper, and its own pixels differ
from one another by more than most of these chips differ from each other. So a pixel of
wash somewhere on the sheet cannot be assigned to a chip. It can be assigned to a class:

    [1]  navy                  U.S. Military Reservation
    [2]  bright red-orange     the Original Town, surveyed by the canal commissioners 1830
    [3,7] dark red             Wabansia  OR  Fractional Section 15
    [4,6,9] dark olive         Kinzie's Addition  OR  the unnamed 1833 survey  OR  Canal Section 9
    [5]  orange-yellow         the School Section
    [8]  duller orange         the unnamed 1833 survey

Chip 6 — one of the two the ticket wants resolved — sits in a class with two named tracts.
Chip 8 — the other — stands alone at 35 but is 47 from chip 5, about three quarters of
chip 5's own spread, which is not a separation anyone should build a polygon on.

**This is recorded as a refusal rather than answered.** Colour alone does not resolve the
two ambiguous swatches, and `tools/check.sh` now gates the refusal itself: if a later edit
ever made the nine chips look separable, the step says so, because the refusal rests on
exactly that arithmetic.

What is left is **position**, and it is a good method rather than a consolation. Inside a
class whose other members are named ground, the band that is not on named ground belongs
to the unnamed chip. Making that argument needs the tract polygons, which is piece 2.

## The bands, and the one chip-to-ground reading this makes

Every pixel of the sheet near a class colour, clear of the paper and carrying some chroma,
thinned to the broad boundary bands by requiring an 8 × 8 px cell to be at least 45 %
covered, then joined into components of 40 cells or more: **116 bands**. The record keeps
the eight largest per class with their pixel boxes and their local metres.

The one reading made here is chip 5's, because it can be tested rather than asserted.
Section 16's four sides are already committed — seated on the PLSS corner at State and
Madison and a nominal mile, by work (`school_section_blocks_1834.json`) that never looked
at a colour. Both sides of the table below moved under T-1092, which re-seated that
section grid onto the eleven-point registration T-1091 adopted and re-derived these
bands through the same fit; the containment is what survived the move, which is more
than the agreement claimed before. Every one of those four sides falls **inside** the band of chip 5's colour:

| side | committed | the yellow band spans | outside the band by |
|---|---|---|---|
| north (Madison) | N −519.1 | −579.8 … −514.7 | 0.0 m |
| south (12th) | N −2128.4 | −2169.2 … −2048.8 | 0.0 m |
| east (State) | E +841.9 | +544.9 … +848.1 | 0.0 m |
| west | E −767.5 | −777.2 … −727.5 | 0.0 m |

A band is 40 to 120 m thick — brush, bleed, and the cell grid — so its outer edge is not
an estimate of a line and is not treated as one; containment is the claim a painted
boundary wash actually makes. The two derivations never referred to each other, and they
agree on all four sides. That is the reason to think the other eight chips are worth
reading off ground in piece 2, and it is the only chip-to-ground reading this file makes.

## What the bands say that piece 2 will have to handle

- **Navy appears exactly once on the whole sheet**, as a single band along the main stem
  east of the forks (E 868…1197, N 9…268 — the river's mouth and the ground either side of
  it). Whatever the blue chip colours, it colours one place, and that place is the
  reservation's river frontage. Nothing else on the sheet is that colour.
- **The bright red-orange of the Original Town survives in two short stretches only**, both
  at the town's south-east corner around State and Madison. The 1830 survey's boundary
  wash has faded or been overpainted everywhere else; the Original Town's extent will have
  to come from its own streets, not from its chip.
- **The dark-red class lands entirely in and around Fractional Section 15** at this
  threshold — its shore edge, and State Street as its west edge. Wabansia's boundary
  stroke, in the north-west, is faded far enough that it classifies with the *duller
  orange* rather than with its own chip. A tract layer that assigned ground by nearest
  chip would therefore put Wabansia in the wrong class, which is the concrete form the
  refusal above takes.
- **The largest band on the sheet is not a tract.** Chip 8's class returns an 8,184-cell
  region over the lake quadrant (E 1528…1983, N −2447…−1290): that is the sheet's foxing
  and the repair of the tear its own caption describes, not a wash. Any polygon work off
  the orange class needs a damage mask first. The neat line is committed here (x 620…4400,
  y 960…5720) and bands centred outside it are marked, but this one is inside it.

## What this does not claim

Nothing here is geometry anything else may stand on. The local metres come from the
committed NA/HUP affine, whose y scale is under challenge in T-0878 — the School Section's
mile measures 1658.65 m north-south against 1603.04 m east-west on the same fit — so they
are stated as indicative, to say which part of town a band is in. The chip colours are the
only `documented` claim in the record; the section-16 containment is `inferred`, with its
reasoning above; no tract is named, no polygon is authored, and no confidence anywhere in
the project was raised on the strength of this.
