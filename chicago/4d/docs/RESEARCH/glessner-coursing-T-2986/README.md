# Glessner's granite string above the door head: which the Prairie front follows (T-2986)

T-2974 found that sheet 6, sheet 5 and HABS photograph 16 all draw the Prairie front's courses
above bed 7 taller than the printed `ashlar_courses_in`, and that T-2913 had found the same on
sheet 5's 18th Street elevation. It left two readings open: the draftsmen were wrong twice and the
photograph happens to agree with them, or the printed string is not the Prairie front's above the
door head. This piece re-read the printed string figure by figure and measured every bed sheet 6
draws from the door head to the second-floor windows.

`read_coursing.py` re-derives every number below from the committed scans.

## 1. The printed string, re-read

Sheet 5 prints the string down the left of the North (18th St.) Entrance elevation (scan x
1450-1520, y 900-3260). Read at the scan's full resolution, bottom to top:

    18" 18" 15½ 9½ 13½ 14½ 7½ 14½ 7½ 11½ 7½ 11½ 7½ 9½ 7½ 20" 8½ 11½ 17½ 7½ 9½ 8½ 9½ 4"

That is 270 in. The record has 271, because it copied the 22nd course as 9½. The sheet prints
**8½**, and three readings agree. The figure itself is clearly an 8, the same 8 as the 17th
course's. Van Zanten drew the joints around it 8.5 in apart, between two courses he drew 9.6 and
9.7 in. Sheet 6 draws the same course 8.2-8.8 in, between two of 9.2-10.0.

Everything else in the record matches the sheet. The slip moves bed 23 and the 4-inch cap 1 in
lower: bed 23 from 21.71 to 21.63 ft over the door datum. On 18th Street that takes the
second-floor heads T-1999 set at the string's sum to bed 23 from 267 in (22.25 ft ng) to
**266 in (22.17 ft ng)**. That is a rebake, so it is filed as its own ticket (§ 5).

## 2. The Prairie front's courses are the printed string's courses

Sheet 6 is not a hand drawing. Its title block says it was photographed on 6 April 1965 with a
Santoni phototheodolite and plotted on a Wild A-7 Autograph at Ohio State under Perry Borchers.
Its 0.00, 24.30 and 48.62 ± 0.02 levels are survey values. HABS photograph 16, which T-2974 used to
check sheet 6, is one of the Borchers plates sheet 6 was plotted from (the photographs' index:
"nos. 13-17 copies of 1965 photogrammetric plates"). So it is the same evidence as sheet 6, not a
third reading.

Measured on three clear piers, sheet 6 draws 17 beds between the door head and the top of the
second-floor windows. The printed string has 17 courses above bed 7. Sheet 6's run of courses is
the string's, course for course (S 40-43, in inches):

| course | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| printed | 14½ | 7½ | 11½ | 7½ | 11½ | 7½ | 9½ | 7½ | 20 | 8½ | 11½ | 17½ | 7½ | 9½ | 8½ | 9½ |
| sheet 6 | 15.5 | 8.2 | 12.1 | 8.6 | 10.6 | 8.5 | 10.3 | 8.2 | 19.3 | 9.6 | 12.1 | 17.9 | 8.6 | 9.2 | 8.8 | 9.7 |

Every high course and every low course is in the same place, including the one 20-inch course,
the 17½ above it and the short 8½. So the second of T-2974's readings is ruled out. The printed
string is not some other wall's. Its courses are the Prairie front's, and they run level round the
NE corner, as T-2955 had them.

The 4-inch cap is where the two faces part. On 18th Street it is the last course under the north
range's eave. On the Prairie front, sheet 6 draws an 8-inch course there and the wall goes on up
to the 24.30 soffit.

## 3. The heights: the printed inches stand

What is left is height alone. Sheet 6 draws bed 7 to bed 23 as 14.77 ft on all three piers
(7.62-7.73 to 22.39-22.49). The printed string makes it 14.13 ft. That is 4.5 % more, about
0.65 ft by bed 23. Most of the excess is in the low courses, each drawn 0.7-1.1 in over its
printed 7½. The 20-inch and 17½-inch courses draw true or short.

**Ruled: the printed inches stay the course heights on every granite face, the Prairie front's
included.** Three reasons. None of them is decisive alone:

1. **The north wall has no room for the taller courses.** The courses are one coursing round the
   corner (§ 2), so taller beds on the Prairie front mean taller beds on 18th Street. Sheet 4's
   section, a third hand, puts the street eave 23.1 ft over north grade. The printed string
   tops out at 270 in, 22.50 ft, under that eave, with 0.6 ft left for the gutter's cornice.
   Van Zanten drew the courses beside his own figures 6.0 % long (courses 3-24: 250 in drawn
   against 234 printed). At that length the string's top would be 23.85 ft, 0.75 ft *above*
   the eave, so his drawn courses are refused outright. Sheet 6's beds, carried round the
   corner, are refused only narrowly. Its bed 23 at 22.39-22.49 over the door datum, plus the
   0.54 to north grade and the 4-inch cap, puts the cap's top at 23.3, 0.2 ft over the eave.
   That is about as close as a scaled section can be read. Only the printed inches leave room
   under the roof sheet 4 draws.
2. **Drawn lines here are not dimensions.** Sheet 5's 18th Street courses depart from the figures
   written between them by -5 % to +26 %, course by course (`read_coursing.py`). Courses 7, 13, 17
   and 22 are drawn true, while 9 and 18 are drawn 16-18 % long. Those are freehand joints with
   figures written between them. The Prairie elevation on the same sheet runs long by the same
   amount (T-2913), so its long courses carry no weight of their own.
3. **The figures are the only course dimensions anyone wrote down.** Sheet 6 prints no course
   height. Its levels are 0.00, 24.30 and the chimney, and none of them falls on a bed between
   7.50 and 24.30 that could test the string. Its 4.5 % comes from inked joint lines scaled
   between two printed levels, not from a figured dimension. The inking is a draftsman's
   (E. N. DeLony's) fair copy of the plotter's manuscript, which is not in the record.

**What this does not settle.** Sheet 6 is metric, and over beds 7-23 it disagrees with the
string by 4.5 %, and the scaled eave on sheet 4 refuses it by only about 0.2 ft, about what the section can be read to. That is
the strongest reading against this ruling, and it is recorded here and in LIBERTIES
(L-glessner-coursing-2986) as the dissent, not explained away. The question re-opens on a
measurement independent of both 1960s surveys. The 1888 front photograph
`a18-gh-glessner-front-with-keith` is one, if a camera solve can carry it from the door (7.50)
to the second-floor soffit (24.30) and read beds 15 and 19 between them. HABS field notes FN-128
are another, if they show how the string was taken.

## 4. What the ruling means for the Prairie front's openings

T-2974's rule stands. Up to bed 8 an opening is put on the bed it is drawn on. Above it, an
opening keeps its own measured height, and the beds are not moved to meet it.

- **The first-floor heads** stay at sheet 6's 14.3 ft, 5.6 ft over their sills on bed 8. On the
  printed string that is 0.38 ft up the 20-inch course (13.92-15.59), where sheet 6 draws the
  head on its own fifteenth bed. That is the dissent of § 3, seen at one opening. It is recorded,
  not resolved by moving either one.
- **The second-floor sills (T-2985).** The colonnette bases sheet 6 draws at 19.2-19.4 fall
  between printed bed 19 (18.71) and bed 20 (19.33). T-2985 should read them against the
  photograph and the sheet as heights, not snap them to a bed.

## 5. Filed

- **T-2996**: the 22nd course to the printed 8½ in, the north second-floor heads to 266 in (22.17 ft ng)
  with the north views' landmarks that quote 22.25, and a rebake. It is not done here because
  three runs are rebaking Glessner today (T-2928, T-2978, T-2985), and a fourth rebake of the
  house for a 1-inch move would only cost one of them a lap.

## Gate

Docs only: no record, mesh or derived file changes. `./tools/check.sh` green on the branch.
