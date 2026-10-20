# T-2926: Glessner's east-wing court face south of the stair tower, to HABS sheet 4

Piece 2 of T-2862, after T-2925 (the bow and stair tower). Every reading below comes off the native sheet-4 scan
(`prairie_1904_v1/research/public/glessner-habs-sheet-4.png`), on T-2228's section controls: north wall x 1165,
grade y 5858, 100.6 px/ft across and 97.7 px/ft up. The readings were taken on
`../glessner-court-exterior-T-2925/grid_crop.py` crops. Heights are feet above north grade. S is given first in sheet 4's
own frame, then on the plan's frame after T-2879's re-zero (+0.65 ft), which is what the record holds. The frame is
checked here too: the courtyard wall's section, drawn at S73.3-73.9, lands on the plan's 74.0-74.55. Each edge is good
to about ±0.05 ft.

`native_over_render.py` makes the three images: the drawing on top, the render from the `habs04-court-exterior`
camera below, at the camera's own scale and on one grid, so a line can be followed straight down from one to the
other.

## The two storeys over the underpass

| | sheet 4 S | plan S | height |
|---|---|---|---|
| lights over the underpass | 63.69-66.70 and 69.18-72.25 | 64.34-67.35 and 69.83-72.90 | 12.1-15.5 |
| their sill course | 63.38-72.61 | 64.03-73.26 | 11.3-12.1 |
| their lintel course | 63.38-72.61 | 64.03-73.26 | 15.5-16.76 |
| lights under the eave | 64.19-66.23 and 69.66-71.71 | 64.84-66.88 and 70.31-72.36 | 21.2-24.9 |
| their sill course | 63.86-72.0 | 64.51-72.65 | 20.45-21.2 |
| their lintel course | 63.86-72.0 | 64.51-72.65 | 24.9-26.1 |

Before this, the record gave four equal lights 2.5 ft wide at S62.0-64.5 and 67.5-70.0, read at 19.5 px/ft on an
origin taken from the stair tower. Each stood under its own small lintel and on its own sill, the lower pair at
12.3-16.9 ft. Sheet 4 draws the lower pair 3.0 ft wide and the upper pair 2.05 ft wide. Each pair stands on one
continuous sill course under one continuous lintel course. In the record the courses are `band` items with style
`rough_course`, and the lights carry `"courses": true`, so they lay no stones of their own.

## The underpass exit

| | sheet 4 S | plan S | height |
|---|---|---|---|
| opening | 62.31-71.31 | 62.96-71.96 | 0-7.22 |
| corbels | 62.31-62.80 and 70.77-71.31 | 0.5 ft in from each jamb | 6.0-7.22, lower inner corner rounded about 0.45 ft |
| stone lintel | 62.31 to the wing's south end (73.35) | 62.96-74.0 | 7.22-8.9 |

Before, the record had 63.3-72.9 and 0-8.1, a plain rectangle with no lintel stone. The underpass's court-end
ceiling (`v4_detail.underpass`) and the courtyard drive's outline follow the new mouth. An elevation does not draw
how far a corbel runs into the passage, so 1.5 ft is reconstructed.

## The south leader

Sheet 4 draws the east court's south leader at the wing's south end: its pipe at S72.80-73.27 (plan 73.68), under a
hopper head 0.47 m across its top (S72.26-73.80) and hanging under the gutter at 26.1-26.87 ft. T-2228 had placed it
at S61.61, beside the stair tower, a bounded reconstruction. The `plain` head profile is already a hopper, so the
record gives it a `hopper` size and drops it 0.15 m below the gutter rim. Its top renders at the drawn 26.87 ft.

## On the render

The lights, courses, corbels, passage lintel and leader each fall within about 0.2 ft of their drawn lines. The offset
is toward the picture's centre: the far-field camera's 1% depth residual that T-2859 recorded.

## Left for T-2928

Sheet 4 differs from the build between the bow and the stair tower too, and no earlier review recorded it. The
first-floor window is drawn about 9.6-14.2 ft under a deep lintel stone (built 9.5-14.6 under a thin one). The narrow
second-floor light is drawn about 20.0-25.0 under a stone at 25.0-26.2. The garden-level light's grille at S47-50
differs. The court-east-north leader at S42.4 is not drawn. `habs04-court-exterior` stays `differs` until that
strip lands.
