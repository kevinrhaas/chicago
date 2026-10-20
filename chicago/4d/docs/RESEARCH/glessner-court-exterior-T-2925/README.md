# T-2925: Glessner's bow and stair tower to HABS sheet 4 (the court view)

Piece 1 of T-2862. Every reading below comes off the native sheet-4 scan
(`prairie_1904_v1/research/public/glessner-habs-sheet-4.png`), on T-2228's section controls: north wall x 1165,
grade y 5858, 100.6 px/ft across and 97.7 px/ft up. `grid_crop.py` draws the S and height grid the readings were
taken against. Heights are feet above north grade. S is given first in sheet 4's own frame, then on the plan's frame
after T-2879's re-zero (+0.65 ft), which is what the record holds. Each edge is good to about ±0.05 ft (5 px).

The three images put the drawing (top) over the render from the `habs04-court-exterior` camera (bottom), at the
camera's own scale, so a line can be followed straight down from one to the other.

## The bow

Sheet 4 draws the bow from S26.21 to 38.66, which is S26.86-39.31 after the re-zero. The built bow runs 26.84-39.4.

| | sheet 4 S | plan S | height |
|---|---|---|---|
| upper broad light | 28.43-31.91 | 29.08-32.56 | 19.45-24.29 |
| upper middle light | 33.62-36.18 | 34.27-36.83 | 19.45-24.29 |
| upper narrow light | 37.15-38.04 | 37.80-38.69 | 19.45-24.29 |
| lower broad light | 28.45-31.94 | 29.10-32.59 | 9.05-14.20 |
| garden door | 33.73-36.18 | 34.38-36.83 | its foot behind the terrace coping (8.43) |
| lower narrow light | 37.21-38.04 | 37.86-38.69 | 9.05-14.20 |
| lintel courses | 28.11-38.62 | 28.76-39.27 | 14.20-15.49 and 24.29-25.62 |
| upper sill course | 28.11-38.62 | 28.76-39.27 | 18.72-19.45 |
| lower sills | 28.11-32.24 and 36.98-38.62 | 28.76-32.89 and 37.63-39.27 | 8.43-9.05 |

Before this the record gave three equal lights to a storey, spread evenly round the arc, at 9.3-14.5 and
19.5-24.0 ft, each with its own small lintel and sill. Sheet 4 draws a broad light, a middle one (the door below)
and a narrow one near the south flank, under stone courses that run unbroken past them.

An elevation draws a light on a curve by its extent along S, so each light is set on the arc
(`hall_bow_height.lights_S`) where its drawn edges project. On the render the frames, the door and the courses
fall within about 3 px (0.1 ft) of the drawn lines. The narrow lights face about 63 degrees away from the
view, so their south reveal hides about half the glass. The drawing, a section, does not show a reveal.

## The stair tower

Sheet 4 draws the drum from S51.16 to 62.33, 11.17 ft across against the plan's 10.5. T-2879 ruled the drawing's
drum wide and kept the plan's, so the tower here renders about 1.1-1.3 ft north of the drawn one. Its lights cannot
be carried by S. Each is set at its angle on the plan's drum: its offset from the drawn centre (S56.75) over the
drawn half-width (5.59 ft).

| | sheet 4 S (centre) | angle off due west | azimuth | opening height | built before |
|---|---|---|---|---|---|
| north slit, lower | 52.8 | 44 | 136 | 7.52-12.78 | 145, 7.6-12.5 |
| north slit, upper | 52.9 | 44 | 136 | 18.78-22.46 | 145, 17.8-22.0 |
| south slit, lower | 60.7 | 45 | 225 | 4.70-9.10 | 215, 4.5-9.2 |
| south slit, upper | 60.7 | 45 | 225 | 16.58-20.53 | 215, 15.7-19.8 |
| lantern, north | 52.09-54.20 | 40 | 140 | 28.2-31.9 | 135, 27.0-31.0 |
| lantern, middle | 55.47-57.92 | 0 | 180 | 28.2-31.9 | 180, 27.0-31.0 |
| lantern, south | 59.25-61.20 | 39 | 219 | 28.2-31.9 | 225, 27.0-31.0 |

- The slits are about 0.53 ft across in projection at 45 degrees, so 0.75 ft on the drum (built 1.0). Each has a
  head stone 1.23-1.27 ft high and a sill stone 0.52-0.72 ft high, both 1.29 ft across in projection, so about
  1.8 ft on the drum.
- The lantern's lights sit between a stone sill course at 27.05-28.2 ft and a lintel course running from 31.9 ft up
  to the eave at 33.21. Before, the courses were built at 25.8-27.0 and 31.0-32.5, which left a brick strip under
  the eave that the drawing does not have.
- The side lights span 29.4 and 26.5 degrees of the drawn drum (2.69 and 2.43 ft on the plan's) and the middle one
  25.3 degrees (2.32 ft). They are built 2.55 ft and 2.3 ft wide.
- On the render the slit stones and the lantern's courses fall within about 0.15 ft of the drawn heights.

## The dormers

T-2859 read the dormers on sheet 4's own S: 32.1, 45.0 and 67.8. On the plan's frame they are 32.75, 45.65 and
68.45. On the render the middle finial falls on the drawn one. The outer two stand about 7 px (0.23 ft) toward the
picture's centre. That is the far-field camera's 1% depth residual T-2859 recorded: the dormers stand about 5.5 m
behind its nominal face.

## Left for T-2926

The east wing's court face south of the stair tower (S 63-73) is drawn differently from how it is built.
The drawing has the upper storey's two windows in one continuous lintel and sill course, and the middle storey's
two framed windows in theirs. The build has four separate double-hung lights. `habs04-court-exterior` stays
`differs` until that piece lands.
