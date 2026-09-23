# Every watercourse Wright draws — the whole sheet, counted

T-0795 · the reading is `tools/audit_wright_watercourses.py`, the record is
`data/traces/wright_1834_watercourse_audit.json`

The owner added the National Archives / Historic Urban Plans facsimile of Wright's 1834
survey on 2026-09-05 and asked, among much else, *"where the various sloughs are."* Every
Wright reading this project held had been taken inside a WINDOW of the BPL/Leventhal scan
— the forks box, the harbour box. This sheet is whole. So this is the walk of all of it.

**Method.** Twenty tiles, 1012 × 1100 NA pixels each, covering x 600..4648 and y 400..5900
— everything inside the neat line — read at 1:1, one screen pixel per raster pixel. The two
lacunae (`gcps.lacunae` L1 and L2) are cloth backing and carry no ink. Coordinates through
the eleven-point affine adopted by T-1091, RMS 16.02 m.

## THE COUNT: one

Wright draws the river — Main Branch, North Branch, South Branch, the harbour cut, the lake
shore, the sand bar — and **exactly one watercourse that is not the river**: a double line
leaving the north bank of the main stem at the North Water / Kinzie corner and running north,
across Kinzie Street, to Michigan Street inside the Michigan St tract. Nothing in the West
Division. Nothing in Wabansia. Nothing in the School Section. Nothing along the lake shore.
Nothing in the Reserved blocks or the Fractional Section.

The town carries four. Only one of them ever claimed to be a line on this sheet, and the
other three say so themselves:

| record | what it claims Wright for | on this sheet |
|---|---|---|
| `north_side_slough` | existence **and course** | drawn, and re-measured below |
| `lasalle_slough_lower` / `_upper` | existence and **mouth only** (course: Conley/Stelzer 1933) | the mouth is drawn; no inland course |
| `state_slough_course` | **nothing** — chicagology + Conley/Stelzer | not drawn, as expected |
| `state_slough_mouth` | the traced **re-entrant** only | the re-entrant is drawn |
| `west_prairie_swale_a` / `_b` | **nothing** — no source at all | not drawn |

So the count comes out even. That is the result the ticket asked for: *"A count of four that
matches what the town has is a result; a fifth is a finding."* There is no fifth.

## The one that is drawn, re-measured

45 stations along the committed `north_side_slough` centreline, sampled perpendicular to the
line, looking for the pair of inked strokes that bracket it.

- **41 of 45 stations find the pair.**
- The centre of the pair departs from the committed centreline by **1.78 m median, 8.03 m at
  worst** — inside a fit whose own RMS is 16.02 m, and a quarter of it.
- The drawn corridor is **13.02 m between stroke centres** (range 6.96–22.83 m).

The BPL window reading and the whole NA sheet agree about this watercourse to under two
metres. Nothing moves.

**One discrepancy, recorded rather than resolved.** The terrain's width for this watercourse
was measured as twice the interior distance transform of the surviving *wash* fragments on the
BPL scan, and came out **7.1 m**. The distance between the two inked strokes on the NA sheet is
**13.0 m**, nearly twice that. The wash and the ink are not the same statement — a bank tint
laid inside a drafted channel is narrower than the channel — and a hand-drawn double line on a
cadastral plat carries no surveyed width in any case. No width is taken from this reading. The
figure is written down so that whoever next prices this channel starts from both numbers.

## THE FINDING: the same ink was being read twice — SETTLED, T-1080, 2026-09-13

**T-1080 was tracing this watercourse as a road.** Its `michigan_st_tract_road` — 262 m, North
Water Street to Michigan Street, the "curved double line" Wright draws through the Michigan St
tract — ran down the same two strokes. Its own reading puts 12.35 m between them; this one
puts 13.02 m. Its centreline and this one's are the same line to a couple of metres over the
whole reach. **T-1080 has now withdrawn the road**, on the evidence below and on a direct
measurement of the two centrelines against each other; the section at the foot of this note
says what survives.

That ticket's PR was held, and its WIP note said why: the T-0184 wedge check refuses the road
ribbon because the ground under it is 10–25 cm below the summer-1835 water surface. **It is
below the water surface because this project already carves that line as a watercourse.** The
blocker is not terrain relief disagreeing with a road; it is the road and the slough being the
same feature, modelled twice.

Three things the sheet says about which reading is right. They were stated here and decided on
T-1080, which is where the adjudication lives (`docs/RESEARCH/michigan_st_tract.md`):

1. **It is drawn as a confluence.** At NA px (2033, 2270) the west stroke *becomes* the
   river's north bank running south-west, and the east stroke *becomes* the same bank running
   east. The tributary's two banks are continuous with the main stem's, on either side of an
   opening. A road drawn to a river either stops at the bank or crosses it; this does neither.
2. **A second map corroborates it as water.** Thompson's 1830 plat draws one watercourse
   across North Division block 6 — the same block this line crosses (T-0452,
   `docs/RESEARCH/thompson_plat_sloughs.md`). Thompson drew that ground four years earlier and
   drew this feature as water.
3. **T-1080's own argument for a road cut both ways.** "It curves, and it cuts diagonally
   across platted blocks and lot lines" is equally true of a stream — more so, since a plat
   ruled over a stream is the ordinary case and a road ruled across finished blocks is not.

## The two mouths, confirmed

Both bank re-entrants the terrain's records cite are on this sheet, and both land inside the
±20 m the georeference allows, so neither scan is disbelieved and no course moves.

| | picked at (NA px) | E, through the fit | the record's E-range | agrees |
|---|---|---|---|---|
| La Salle slough mouth | 2403, 2495 | **+449.9** m | +462 .. +469 | within 12.1 m |
| State Street slough mouth | 2968, 2515 | **+848.6** m | +850 .. +856 | within 1.4 m |

Picked by eye at 8× and 5× with a 20 px grid ruled over the crop, ±5 px (±3.6 m). The pixels
are committed so the next reader can re-open the sheet at those spots and disagree.

The La Salle mouth is a sharp V notched into the south bank at the west end of the South Water
block numbered 50. The State Street mouth is a narrow inlet at the foot of State Street. Both
are unmistakable at 1:1; neither carries an inland course.

## The prairie swales: the sheet's silence, recorded

`west_prairie_swale_a` and `west_prairie_swale_b` are placed, not read — the dossier's zone 18
says the West Division wet prairie carried "1–2 ft slough swales" and says nothing about where.
The tiles covering their ground (NA px 1230..1720 × 1930..2680 and outward) carry platted
blocks, lot lines, the red ward band and nothing else.

**Wright draws no watercourse on the West Division's prairie.** They stay `reconstructed` with
no source, and the silence is now written on both records — which is worth the line, because
"no source has been found" and "the one sheet that would show it has been looked at and shows
nothing" are different states and only the second of them is a finding.

## What this closes

T-0795 asked whether T-0793 and T-0794's traces need a slough ticket after them. They do not:
the whole sheet has now been walked and there is no watercourse on it that the town does not
already hold.

## The road reading it retired, and the cross-check it left behind (T-1080)

This note found the same ink being read twice. T-1080 was the other reader, and it has now
been adjudicated: **the "curved road north through the Michigan St tract" was
`north_side_slough`**, and the road record is withdrawn rather than committed. The argument
is written out in `docs/RESEARCH/michigan_st_tract.md` § *The curved line north of the
river: read as a road, and withdrawn*.

What survives is worth more than what went. T-1080's trace was taken off the **600 dpi
NA/HUP sheet** under the `wright_1834_nara_hup` fit; `north_side_slough` was traced off the
**BPL master scan** under `wright_1834_gcps.json`. That makes it the only independent read
that record has, and it is kept under the feature's own name for that reason:

- `tools/read_north_side_slough_na.py` — the ridge follower, every parameter committed
- `data/traces/north_side_slough_na_reread.json` — the reading, with its `identity` block

**The agreement, re-derived rather than transcribed** (`--check` recomputes it from
committed data): 36 sheet stations, **median 1.54 m** from the committed centreline, worst
**17.91 m**, none outside either reading's stated uncertainty (±20 m on the record's
vertices, 16.19 m RMS on this sheet's fit). This note's own recheck came at the same
feature from the other end — 41 of 45 committed stations found the bracketing pair of
strokes, 1.78 m median departure, 8.03 m worst — and the two land in the same place.

The slough's grades are untouched. A corroborating read is not a promotion, and the
hydrology file stays generated rather than hand-edited.
