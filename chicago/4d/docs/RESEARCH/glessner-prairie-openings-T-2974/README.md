# Glessner's Prairie openings registered on the raised beds (T-2974)

T-2955 raised the granite string 0.20 ft, so the beds over the door datum are now 0.96, 2.46,
3.75, 4.54, 5.67, 6.88, 7.50 (the door head), 8.71, 9.34 ... (`ashlar_courses_in` laid from
-0.54). It found that two of the Prairie front's opening heights stopped sitting on a bed when
it did: the first-floor sills (9.2, now 0.14 ft under bed 9) and the basement grilles' heads
(4.7, 0.16 ft over bed 4). This piece read every Prairie aperture's sill and head on HABS
sheet 6, built two of them and ruled on the rest.

`read_openings.py` re-derives the sheet-6 numbers below from the committed scan.

## 1. How the sheet was read

Sheet 6 at its own printed 0.00 (y 5952) and 24.30 (y 4127): 75.1 px a foot, with T-2857's
horizontal scale bar (75.5 px a foot). The scan is turned slightly: the walk line reads
-0.72 at light A and -0.85 at light D, and the drawn joints drop the same way from north to
south. So each opening is also read against the joint the sheet draws seventh beside it,
the door head's, which the printed string sets at 7.50.

T-2913 found the drawn courses agree with the printed inches through the door head and run
long above it. That holds here too: drawn beds at light A against the string read 0.96 /
0.96, 4.62 / 4.54, 7.69 / 7.50, 8.98 / 8.71, 9.63 / 9.34, 12.32 / 11.88, 14.57 / 13.92.
That is +0.08 at bed 4, +0.19 at bed 7 and +0.65 at bed 15. So low on the wall an opening
is placed by the joint it is drawn on, and only up to bed 8, where the sheet, the string
and the photograph still agree.

## 2. The first-floor lights: sills to bed 8, heads 5.6 ft over them

| light | local bed 7 | sill | head | sill (rel.) | head (rel.) | height |
|---|---|---|---|---|---|---|
| A | 7.71 | 8.96 | 14.57 | 8.75 | 14.36 | 5.61 |
| B | 7.66 | 8.91 | 14.53 | 8.75 | 14.37 | 5.62 |
| C | 7.62 | 8.79 | 14.41 | 8.67 | 14.29 | 5.62 |
| D | 7.60 | 8.75 | 14.36 | 8.65 | 14.26 | 5.61 |

Each light's outer sill line is drawn on the sheet's eighth joint, and it runs straight into
that joint either side. Read against the door head's joint, the sills fall 1.15-1.25 ft over it,
at 8.65-8.75. Bed 8 is 8.71.

HABS photograph 16 is frontal and level (its forward axis is 0.03 degrees off horizontal).
Scaled on the two printed levels it shows, the door threshold (0.00, row 783) and the
second-floor soffits (24.30, row 366), that is 17.16 px a foot. On that scale the lights'
stone sills are at row 634.5, about 8.7, and their heads at row 540, about 14.2.

**Built: the sills at 8.71, from 9.2.** The sheet, the photograph and the string agree to
0.06 ft.

The heads are not put on a bed. The sheet draws each head on its fifteenth joint, which the
printed string puts at 13.92. That would make the lights 5.21 ft high. The sheet draws all
four at 5.61-5.62 and the photograph at about 5.5. The string's upper inches are what the
two sheets and the photograph do not support (§ 4), so they cannot set the head.

**Built: each head the sheet's 5.6 ft over its sill, 14.3, from 14.5.**

## 3. The basement grilles' heads to bed 4

| grille | head (sheet scale) | head (rel. to bed 7) |
|---|---|---|
| A | 4.61 | 4.40 |
| B | 4.61 | 4.45 |
| C | 4.57 | 4.45 |
| D | 4.57 | 4.49 |

The head of every grille is drawn on the sheet's fourth joint. The two readings bracket the
string's bed 4, 4.54. Referring a reading to bed 7 overcorrects this far down, because the
drift is +0.08 here, not +0.19. Sheet 5 drew the same bed at 4.56 (T-2913).

**Built: 4.54, from 4.7.** The grilles' sills stay at 0.8. Sheet 6 draws the bottom row of
cells running down to a ground line at about 0.6. The 1965 lawn stands behind a curb over
the walk, so the sheet shows no sill to read.

## 4. Ruled, not built

- **Front door (0.00-7.50).** On bed 7 since T-2971. Its header and fan are T-2972.
- **Porte-cochère head (7.0).** It is drawn on the sheet's sixth joint, which the string sets
  at 6.88. Sheet 4's passage heights, which the mouth answers to, are T-2978 (claimed), so
  the head is left to that ticket rather than moved twice.
- **The small pair (11.8-16.2).** Each light stands on a projecting sill stone. The sheet
  reads the stone's foot at 11.66 and the head at 16.0 at the south end, about 0.1-0.15 ft
  low there from the scan's turn. Both are within 0.15 ft of the record. They are above
  bed 8, where no bed can be read off the string, so they stand.
- **The second floor (19.8-24.3).** The heads are the printed 24.30. The sills are not:
  each group's colonnette bases stand on a line the sheet draws at about 19.2-19.4, and the
  lower sashes stop at about 19.97. The record's 19.8 falls between the two. That reading
  moves the colonnettes T-2965 just built, so it is filed as its own ticket: **T-2985**.
- **The string above bed 8.** On the Prairie face both sheets and photograph 16 draw the
  courses about 7 % taller than the printed inches. Sheet 5's 18th Street elevation does the
  same against the string printed beside it (T-2913). Either the draftsmen were wrong twice
  and the photograph agrees with them, or the printed string is not the Prairie front's above
  the door head. This is filed as its own ticket: **T-2986**.

## 5. Checked against habs-16-prairie-front

Re-rendered through its camera, measured at lights C and D:

| | plate | render before | render after |
|---|---|---|---|
| light opening, head to sill | 94.5 px | 90 | 95 |
| light sill over grille head | 75.5 px | 83 | 77.5 |

Every row on the render lies 8-10 px under the plate's, the same for head, sill and grille.
That offset is the camera's: its height is constrained to a reconstructed range, not
surveyed. The verdict stays `differs` because course relief is still open.

## Gate

Rebaked `glessner_house`: full and web tiers 1,385,995 triangles (-919), light 198,350, and
0 coincident faces in all three tiers (dev's web tier carried 3). Re-derived: web and light
tiers, recovery pack, sidecar, K01 baseline, vine atlas and the street opening schedule.
