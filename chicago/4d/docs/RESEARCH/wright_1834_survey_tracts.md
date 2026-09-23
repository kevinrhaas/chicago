# The nine survey tracts of Wright's 1834 legend, on the ground

*T-1101 — piece 1 of T-1097, itself piece 2 of T-0792. Record:
`data/reconstruction/1835_survey_tracts.json`. Tool: `tools/build_survey_tracts.py`.
Gated by `tools/check.sh`.*

## 1. What was asked, and what the colour could not give

Wright's 1834 legend is nine coloured chips, each naming a survey and most of them
dating it. It is the only place on any sheet this project holds that says **who surveyed
what ground and when**. T-0792 asked for nine tract polygons off those colours.

T-1096 measured the chips first (`docs/RESEARCH/wright_1834_legend_swatches.md`) and
found the method could not work as asked: nine names, **six** separable colours, and a
per-pixel spread inside a single chip wider than the distance between some pairs of
them. Chips 3 and 7 are 10 RGB units apart; 4, 6 and 9 lie within 30 of each other. So a
wash on the sheet can be assigned to a CLASS of chips and never to a chip.

This piece answers the question the other way round. **Every boundary here comes from
ground this project already holds** — the committed reservation ring, the PLSS section
grid carried from G1, Wabansia's committed seating, the committed street lines of
Kinzie's Addition and of the Original Town's four named bounds. Not one is traced off a
wash. A wash is 17 px of ink at 600 dpi, about 12 m of ground; every boundary here is
known to better than that already, so reading one off colour would be a loss of
precision dressed as evidence.

The colour is then used for the one thing it is good for: **agreeing or disagreeing.**

## 2. What was placed — seven of nine

| chip | tract | acres | boundary from | grade | bands of its own class on it |
|---|---|---:|---|---|---:|
| 1 | U.S. Military Reservation | 65.70 | the committed reservation ring | inferred | **1 of 1** |
| 2 | Surveyed by Canal Com. in 1830 (the Original Town) | 256.12 | Kinzie / State / Madison / Des Plaines, each a committed line | conjectural | 0 of 2 |
| 3 | Wabansia, surveyed 1831 | 77.88 | the committed seating (T-1086) | inferred | 0 |
| 4 | Kinzie's Addition, surveyed 1833 | 85.10 | the envelope of its own five north-south streets | reconstructed | 2 |
| 5 | School Section, surveyed 1833 | 640.00 | section 16, T39N R14E | inferred | **13 of 15** |
| 7 | Fractional Section 15 | 204.38 | section 15 cut on the east by the committed shore | reconstructed | **3 of 4** |
| 9 | Part of Canal Section No. 9 | 383.16 | section 9 with the Original Town cut out | conjectural | 7 |

**The strongest three are the ones the colour confirms.** Chip 1's class has exactly one
band on the whole sheet and it stands inside the committed reservation. Chip 5's fifteen
bands trace the perimeter of a one-mile square and thirteen of them fall inside section 16,
the school section by statute — the square is not derived from the colour, the colour is
what agrees with it. Chip 7's class has four bands and three are on section 15.

**The reservation carries an independent control, and it lands.** The parent ticket named
it: Wright's `L. House` glyph, committed at `data/traces/wright_1834_lighthouse_glyph.json`,
should stand INSIDE chip 1's polygon. It does — **40.88 m inside**, which is the figure
the ticket predicted to the decimetre before this file existed.

## 3. What was refused, and every refusal carries its number

**Chip 3, Wabansia — no colour evidence at all.** Its class has four bands and not one
stands on it. T-1096 measured why: Wabansia's boundary stroke in the north-west has faded
far enough to classify with chip 8's duller orange. The polygon stands on the committed
seating and the colour agreement is **absent, not weak**, and the gate holds it that way:
if a later reading ever gave Wabansia bands of its own class, `check.sh` fails rather
than let this paragraph stand unchallenged.

**Chip 2, the Canal Commissioners' 1830 survey — two bands, neither on the tract.** Its
class has the fewest bands on the sheet, and both sit at the Madison / State corner —
48 m and 146 m from it — where four tracts meet and the colours crowd. They cannot place anything.
The Original Town is placed from its four named bounds instead, and — this matters — that
placing is graded **conjectural**, because *no source record this project holds states
those four bounds*. `thompson_plat_1830` carries the plat's figures (roughly 0.375 square
miles, 80-ft streets, 18-ft alleys) and not its perimeter. The four streets are the
standard account; the standard account is not a citation. What CAN be checked is checked:
all 19 committed plat blocks fall inside the rectangle, and the rectangle over-runs the
printed three-eighths of a square mile by 6.7 %, as an envelope of four outer bounds must.

**Chips 6 and 8 are not resolved — and the reason is ground, not evidence.** The parent
ticket's method was: inside a class whose other members are named ground, the band that
is NOT on named ground belongs to the unnamed chip. Applied:

| | bands | excluded | on a class mate | on other named ground | on unnamed ground |
|---|---:|---:|---:|---:|---:|
| chip 6 (class 4/6/9) | 40 | 8 | 9 | 16 | **7** |
| chip 8 (class 8 alone) | 54 | 23 | — | 28 | **3** |

Ten bands are left, and **every single one of them falls in a place this project's own
geometry does not reach**: seven beyond the four sections the PLSS grid is carried across
(L219), three north of where the committed lake-shore trace ends. Nothing is left over
that could be an unrecorded survey.

So the honest reading is not "the method failed". It is: *the method ran out of ground.*
Carrying the section grid past the four sections it is held to, or committing the shore
north of its present end, is what would let these two chips be adjudicated at all — and
that is a more useful thing to leave behind than a polygon nobody could defend.

## 4. The damage mask, and why it is measured rather than drawn

Chip 8's largest region on the whole sheet is **8,184 cells over the lake quadrant**
(E 1528…1983, N −2447…−1290). It is not a survey: it is the foxing and the mounted repair
the sheet's own caption describes. A hand-drawn box round it would be an invention.

The rule used instead is a property of what a survey tract IS — **Wright washed land** —
so a band whose centroid stands east of the committed lake shore, inside a committed
lacuna box (`…nara_hup_gcps.json § lacunae`), inside the legend column, or outside the
neat line, cannot be a tract wash whatever its colour. The lake-quadrant region falls to
the first of those, measured. Across all six classes, 32 of 116 bands are excluded:
**21 water, 8 off-map, 2 in the legend, 1 in lacuna L1.**

The mask's own limit is recorded with it: the committed shore trace ends at local north
43 m, so the water rule cannot reach anything above that — which is exactly where three
of chip 8's three surviving bands stand.

## 5. The tracts are not disjoint, and the ninth chip says so

Four of the nine chips are PLSS sections, which tile the township; four of the others are
plats standing INSIDE one of those sections. A band can therefore be inside two tracts at
once, and the question "which tract is this wash" has a right answer: **the most specific
one.** That is the order the record's `PRECEDENCE` carries, and it is the order the ninth
chip's own wording implies — *Part of Canal Sec. No 9* is what is left of the section once
the plats inside it are taken out. The cut is only taken because the Original Town's east
and south bounds stand within 11.93 m and 6.12 m of section 9's own lines; past 25 m the
tool refuses the cut rather than force it.

Wabansia's seated outline also falls inside section 9's constructed square. That is
recorded as a containment, not used as a citation — a polygon falling inside a square is
not evidence about which section a plat was laid out in, and the register's section-9
entries are NOT assigned to Wabansia on those grounds.

## 6. Who held the ground, and where the register is silent

Taken from `data/research/land_sales/entries.json`, which names the entryman, the aliquot
and the date. An entry is a patent, **not a chain of title**: it says this ground was
entered by this man on this date, and nothing about who held it on 1 July 1835.

- **Canal Commissioners 1830** — the seven canal (`CN`) entries in section 9, 28 September
  to 5 October 1830: James Kinzie, Thomas Hartzell, Alexander Wolcott, Edmond Roberts.
  The chip's own date, in the register.
- **Kinzie's Addition** — Robert A. Kinzie, north fraction of section 10, **102.29 acres,
  7 May 1831**. The register spells the surname two ways across the two rows and both are
  carried rather than silently merged. The street envelope committed here is **17.19 acres
  short** of the patent, and it should be: the patent covers the water lots between North
  Water Street and the river and the shore-cut blocks east of Sand Street, neither of them
  committed geometry (T-0799, T-0800).
- **School Section** — 337 school-section (`SC`) rows, 22–23 October 1833. The chip's own
  date again.
- **Refused:** the reservation (federal ground, no patent on the scene date — Beaubien's
  1835 pre-emption is recorded under section 10 and is not treated as making the
  reservation his), Wabansia (no committed record says which section it was platted in),
  fractional section 15 (its only entry is Mark Noble Jr's, 31 May 1836, after the scene
  date), and section 9's remainder (sorting the seven 1830 entries onto polygons is
  T-1102's work).

## 7. The registration moved under this file, and the agreement got better

T-1091 adopted the eleven-point M1 registration of the NA sheet while this was being
written, which moves every band's local metres. That is exactly the kind of drift the
gate exists to catch, and it caught it: the record was rebuilt on the new fit rather
than re-stated. **The agreement improved across the board.** The School Section went
from twelve of fifteen bands inside its square to thirteen, and chip 8's unnamed-ground
remainder from four bands to three. T-1092 then re-seated the four grids the same sheet
places, which moved Wabansia's outline, Kinzie's Addition and the Original Town again;
the record was rebuilt a second time rather than re-stated, and Kinzie's Addition picked
up a second band of its own class in the move. Nothing here was tuned to either fit —
the same tool, the same thresholds, better ground underneath.

## 8. What this leaves for T-1102 and for the parent

T-1102 owns the rest of T-1097: every land-sale row sorted onto a tract polygon, and the
generators taught to read the layer. Nothing in this file is drawn yet, which is why no
new entry is filed in `docs/LIBERTIES.md`: the section grid's construction is already
L219's, and the two envelopes and the cut here are graded on the record rather than
hidden. **The commit that first draws this layer is the one that owes a liberty**, because
that is the commit where a visitor could be misled by it.

Two findings also belong to other open tickets and are filed as evidence, not as new
tickets: chip 6 and chip 8 both need ground this project has not carried yet, and the
shore trace's north end is the limit that stops the water mask.
