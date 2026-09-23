# The Michigan St tract north of Kinzie Street

T-0796 · T-1076 (the reading) · T-1079 (the seating) · T-1080 (the name, and the road — this note)
· T-0795 (the sheet's watercourses) · T-0452 (Thompson's sloughs)

Wright's 1834 survey draws, immediately north of Kinzie Street and east of the North
Branch, a small platted square unlike anything around it: two block columns, two block
tiers, a mid-block alley ruled through every block, lot frontages well under the
Original Town's, and an east-west street lettered **Michigan St**. Every neighbour on
that sheet is whole blocks. The owner asked what it was, on 2026-09-05: *"that must be
special"*.

## What is settled

- **Its two streets are the town's.** T-1076 read them off the 600 dpi NA/HUP sheet.
  The east-west street carried east on Kinzie's Addition's own fitted slope lands 1.7 px
  — about a metre and a half of ground — from where that Addition's Michigan Street was
  read eleven hundred pixels away. The north-south street carried south across Kinzie
  lands 16.7 m from the committed `market_north`, inside the sheet's own 16.19 m RMS.
  So Wright's second `Michigan St` is not a second street of that name, and the tract is
  platted **on the town's grid**. Only its parcel module is its own.
- **Its section is 9**, not the fractional 16 the owner read — `docs/PLSS-SECTIONS.md`
  derives the whole sheet's numbering from the committed 9/10/15/16 section corner.
  Section 9 is the canal's section, the legend's *Part of Canal Sec. No. 9*.
- **It is seated** on `michigan_north` and `market_north` by
  `tools/seat_michigan_st_tract.py`, and its two street reaches, its two alleys and its
  polygon are committed (`data/traces/michigan_st_tract_seated.json`).

## What is NOT settled: the name

**No source in this repository names this tract.** That is the state of the question and
it is not being improved by guessing at it.

One candidate is raised by the corpus and the same corpus refuses it on arithmetic:

> *"It must have been west of State street, for it was upon the eighty acres to which
> (by its help) he later established a pre-emption claim and which he bought of the canal
> commissioners for $1.25 an acre, and subdivided into the familiar 'Wolcott's
> Addition.'"*
> — Moses & Kirkland, *History of Chicago*, vol. 1, editors' footnote
> (`moses_kirkland_history_of_chicago_v1`, text line 6006)

Everything general about that fits: west of State Street, bought **of the canal
commissioners**, and therefore canal land — which is section 9, which is this tract's
section. The volume names Wolcott's Addition twice more, once in David Hunter's 1834 sale
of *"the half of Kinzie's addition to Chicago, the whole of Wolcott's addition"* to
Arthur Bronson (line 13225), and once at line 93807 on the price of the land it was laid
out upon. **None of the three gives a boundary.**

**And the DATE refuses it, which the size argument below only made likely.** Moses &
Kirkland set the additions in order, at line 13122 of the same volume: the canal
commissioners' addition on fractional section 15 "was platted, under the direction of the
commissioners, by Edward B. Talcott, assistant engineer, June 13, 1836, and the plat
recorded July 20" — and

> *"It was followed by 'Wolcott's' addition, North Branch addition and Wabansia
> addition."*
> — Moses & Kirkland, *History of Chicago*, vol. 1 (`moses_kirkland_history_of_chicago_v1`,
> text line 13122)

So Wolcott's Addition was laid out AFTER June 1836. Wright surveyed in 1834 and drew this
tract already platted, two years earlier. The LAND was bought in 1830 — the same volume
prices it at $130 at line 93807 — but the buying is not the platting, and it is the platting
that would put lots, an alley and a street on Wright's sheet. **Wolcott's Addition is
refused on the calendar, and the arithmetic below is now the second reason rather than the
only one.**

And the size refuses it too. Wolcott's Addition is **eighty acres**. This tract, seated, is
200.0 m by 157.4 m — **31,486 m², or 7.78 acres**, a tenth of that. Wright draws no
platted ground adjoining it to make up the difference: north and east of it the sheet is
blank, unsurveyed, and carries the sheet's own title. So either this square is one corner
of a larger Wolcott's Addition that Wright drew only part of, or it is not Wolcott's
Addition at all, and **nothing in the corpus decides between those**.

It is therefore recorded as a candidate and nothing is graded on it. No street record,
no trace and no polygon in this project carries the name Wolcott.

## What would settle it

1. **A plat or a boundary.** Andreas on the additions north of the river; the canal
   commissioners' own sale records; the Cook County recorder's index of town plats. Any
   one of them that gives Wolcott's Addition a boundary answers this in a line.
2. **The Democrat's 1834-35 land notices.** An auction notice that lists lots by block in
   a named addition north of Kinzie would name the tract directly. The extracted issues
   in `data/research/newspapers/extracted/` have been searched for *addition*; the hits
   are Kinzie's, Dearborn, and Carpenter's, and none is north of Kinzie Street here.
3. **The curved line north of the river is NOT a road, and so it names nothing.** T-1080
   traced it off the 600 dpi NA/HUP sheet and it turned out to be a feature this project
   already holds — as **water**. See the section below. It was never going to name the
   tract; it now does not even belong to the tract's question.

## The seating, and what it cost

The tract is seated on the committed grid rather than pasted from the sheet's fit,
because at this tract the fit is badly local. Measured north of the committed Kinzie
line, the committed grid puts Michigan Street **138.1 m** away and Wright's fit puts it
**99.9 m** away. Thompson's 1830 plat draws exactly one tier of North Division blocks in
that span, fronting Kinzie on the south and Michigan on the north, so the span has to
hold a block plus an 80 ft street: 453 ft does and 328 ft does not.

The cost is stated rather than hidden. Seated, the tract's south border stands **60.5 m**
north of Kinzie Street where the sheet draws **22.0 m** — a 38.5 m disagreement, all of
it Wright's compression in y at his sheet's western margin. The alternative, hanging the
ladder on `kinzie`, would have kept the drawn frontage and committed a **second** Michigan
Street 38 m south of the committed one, which is the one thing the reading refuses.

## The curved line north of the river: read as a road, and withdrawn

T-1075 asked for "the curved road north through the tract" and T-1080 went and traced it.
The trace is good and the reading it was put to was wrong, and both halves of that are
worth keeping.

**What was traced.** One curved double line leaves the north bank of the Main Branch a
little east of Market Street, crosses North Water Street and Kinzie Street, bulges west,
and ends at this tract's Michigan Street. Apart from the fort's road on the reservation it
is the only such line on Wright's sheet. It is read at 600 dpi by a ridge follower with
every parameter committed: `tools/read_north_side_slough_na.py`,
`data/traces/north_side_slough_na_reread.json`. `--check-sheet` re-runs the identical
trace off the raster (worst stroke disagreement 0.00 px over 36 rows) and `--check`
re-derives every metre from the committed pixels without opening it.

**Why it is not a road.** The project has held this feature since long before the ticket
existed, and holds it as a watercourse: **`north_side_slough`**, in
`data/terrain/epochs/e1834_harbor_cut/hydrology.geojson` — a 45-vertex centreline
described as *"a narrow winding watercourse running north out of the main stem, across
Kinzie Street, ending at Michigan Street"*, traced off the BPL master scan by
`tools/trace_river.py`, citing `wright_1834` for **existence and course**. Same two ends,
same reach, same ink. Five things say so and none of them is an opinion about what the
line looks like:

| | |
|---|---|
| **The geometry** | This reading's 36 sheet stations fall a **median 1.54 m** from the committed slough centreline, worst **17.91 m**. The slough record states its own vertex uncertainty as ±20 m; this sheet's fit has an RMS of 16.19 m. Two scans, two registrations, two tracers, four hundred commits apart, and every station inside either one's error. |
| **The count** | T-0795 swept the whole sheet in twenty 1:1 tiles and counted the non-river watercourses Wright draws. **One.** It is this line. (`docs/RESEARCH/wright_1834_watercourses.md`) |
| **The junction** | At NA px (2033, 2270) the west stroke *becomes* the river's north bank running south-west and the east stroke *becomes* the same bank running east: two banks continuous with the main stem's, on either side of an opening. It is drawn as a **confluence**. A road drawn to a river either stops at the bank or crosses it; this does neither. |
| **The second surveyor** | Thompson's 1830 plat draws this feature as water, across North Division block 6 — the same block the line crosses (T-0452, `docs/RESEARCH/thompson_plat_sloughs.md`). Four years earlier, same ground. |
| **The width** | 12.35 m mean between stroke centres here; 13.02 m measured on the same strokes by T-0795's independent method. The same pair of strokes, twice. |

The one argument that was ever offered FOR a road — *it curves, and it cuts diagonally
across platted blocks and lot lines* — argues against a **street** and not for a road. A
plat ruled over a watercourse is the ordinary case; a road ruled across finished blocks is
not.

**What was withdrawn.** The track record `michigan_st_tract_road` and its seating into
`data/streets/1835.json`. Neither is in this repository and neither may be re-seated: two
records of one feature, one of them water and one of them a road, is the failure this
project exists to avoid. The reading itself is kept under the feature's own name, as what
it actually is — **the only independent cross-check `north_side_slough` has**, off a
different scan under a different registration. A record whose stated uncertainty is ±20 m
gains a great deal from a second read that lands 1.54 m away.

**And it dissolves the blocker that parked this ticket.** The road record could not merge
because, seated, its ribbon's west edge sampled 10–25 cm below the summer-1835 water
surface between N 240 and N 320, so the renderer refused the panels there and T-0184's
wedge check reported the hole. That was not a rendering fault and not a tolerance to
loosen. **The ground under that line is wet because this project already carves a
watercourse along it.** The terrain was right; the road was the error. Nothing needs to
move.

## What this does NOT settle

- **It does not name the tract.** The line goes to the tract and no further, and now it is
  not even traffic — so the argument that "the tract had traffic from the river" is
  withdrawn with the road. Nothing in the corpus names this tract; see above.
- **It does not regrade the slough.** `north_side_slough` keeps its own grades, which were
  ruled on the evidence by T-0687: course `attested`, width `inferred`, depth
  `reconstructed`. A corroborating read does not promote anything, and this one is not
  allowed to. The hydrology file is generated by `tools/trace_river.py` and is not
  hand-edited here.
- **It does not say where the Green Bay road left the bank.** That question was always
  separate and no source in this repository fixes it. There is now one less candidate.

Both halves of T-1080 therefore close as refusals, which is the honest outcome and was
always a permitted one: the tract's name is refused — twice over, on size and on date —
and the road is refused, because the thing it was read from is water.
