# T-2978: Glessner's sheet-4 section datum, ruled; the court's fall to the passage built

T-2976 found that T-2228 reads every court-face height on HABS sheet 4 (section A-A, 1963) over
y 5858, while the sheet draws ground about 1.3 ft lower at the north wall and beside the passage
mouth. This note re-reads the sheet's own ground lines, tests the candidate zeros against the
printed and measured heights on sheets 5 and 6, and rules. All readings are on the native scan
(`glessner-habs-sheet-4.png`, 9648 x 7584), T-2228's controls unless stated: north wall x 1165,
100.6 px/ft across (the sheet's scale bar), 97.7 px/ft up.

## What sheet 4 draws at the ground

Read at the foot of the grass strokes, which stand up from the ground line (the north wall's
rough face and both jambs of the court mouth end on that line):

| | y | over y 5858 at 97.7 px/ft |
|---|---|---|
| lawn along the east wing's court face, S 26-53 (plan) | 5868 | -0.10 |
| ground outside the 18th Street wall (a short stub of grass) | 5991 | -1.36 |
| ground beside the court mouth, both sides | 5997 | -1.42 |
| foot of the court mouth's opening (rounded stones at both jambs) | 6097 | -2.45 |
| underside of the court lintel | 5154 | 7.21 |

Between plan S 53.15 and 62.35 (sheet S 52.5-61.7, T-2879's +0.65 ft) the lawn's line falls
1.32 ft to the ground beside the mouth, reaching it at the north jamb.
`sheet4-court-ground-profile.jpg`, `sheet4-north-wall-foot.jpg`.

**So y 5858 is the court lawn**, as sheet 4 draws it under the east wing's court face (T-2228's
pick sits in the grass strokes, 10 px over their foot, inside its own 12-px uncertainty). It is
not the ground at the 18th Street wall, y 5991, which is what the record's frame calls `ng`.
The 97.7 px/ft vertical scale is older than T-2228: T-1730's v2 fixed it from the street-side
ground to sheet 6's printed north-chimney top, and its readings reproduce on a zero of about
y 5990 (its stair-tower eave, 34.57 ft, is (5990 - 2613) / 97.7). T-2228 moved the zero to the
lawn and kept the scale.

## Can the sheets place the lawn over the streets?

Two families of zero, each tested against heights fixed by other sheets (ng = the 18th Street
grade, 0.20 ft over the Prairie walk, T-2955; sheet 6's door datum = ng + 0.54):

| check | other source | lawn zero (y 5858, 97.7) | street zero (y 5991, 98.6 fitted) |
|---|---|---|---|
| north chimney top, y 1142 | sheet 6 prints 48.62 door = 49.16 ng | 48.27 (-0.89) | 49.16 (fitted) |
| east-wing ridge (crest foot), y 1473 | sheet 6, between its 24.30 and 48.62 ticks: 45.73 ng | 44.88 (-0.85) | 45.80 (+0.07) |
| ground at the 18th Street wall, y 5991 | is the 18th Street grade, 0 ng | -1.36 | 0 |
| court-mouth floor, y 6097 | sheet 6's street-mouth floor, -1.9 door = -1.36 ng | -2.45 (passage falls 1.1 ft inward) | -1.07 (about level) |
| 18th Street wall top under the soffit, y 3555 | sheet 5's printed course string, 22.58 ft (eave course to 23.1); photographs 13 and 15, 23.8-23.9 | 23.57 | 24.70 (+0.8 to +2.1) |

Neither zero answers every check. On the street zero the roof and the ground agree with sheets 5-6
and the passage floor runs level, but the 18th Street wall reads 0.8-2.1 ft too tall; on the lawn
zero that wall agrees with the photographs, but the 18th Street ground stub sits 1.36 ft under the
grade it is and the roof 0.9 ft under sheet 6's printed chimney. The interval from the stub to
the wall top (2436 px) is 24.2-24.9 ft at any scale between 97.7 and 100.6, against 22.6-23.9 ft
elsewhere: one of the sheet's lines near the north wall is drawn about a foot off, and nothing
on sheets 2-6 says which. A hand-measured 1963 section of a court face measures that face from
the ground it stands on; where that ground stands over the streets is the one thing it is weakest
at. **The sheets bound the lawn at 0 to +1.25 ft over the 18th Street grade and do not fix it.**

## Ruling

1. **The court-face heights stand.** Every T-2228-family reading (T-2228, T-2859, T-2879,
   T-2925, T-2926, T-2218's terrace) is a height over the court lawn sheet 4 draws, which is how
   the sheet measured them, and the model lays that lawn on north grade. The record's datum
   label for them is corrected in prose: `ng` there means the lawn, laid on the 18th Street
   grade. No opening, lintel, eave, dormer or tower height moves.
2. **The lawn stays on north grade.** Raising it and the whole court face by up to 1.25 ft
   (the street zero) is inside the bound but not evidenced over the lawn zero; recorded as
   `L-glessner-court-fall-2978`, with what would settle it.
3. **The fall is datum-free and is built.** Whatever the lawn's height, the same few inches of
   paper draw the court ground 1.32 ft lower beside the mouth than along the face, and the
   opening's foot 1.02 ft lower again. The model's court was level, so the mouth stood 1.3 ft
   short of the sheet over its ground and the passage cleared 8.15 ft at the court lintel where
   the sheet draws 9.65.

## What is built

- `courtyard_ground.finish.mouth_fall`: the court ground (lawn, drive, the terrace approach)
  falls 1.32 ft across plan S 53.15-62.35, as drawn, and lies 1.32 ft down from the court face
  out to the section plane (W 51.5), then rises back to the court's level by W 71.5. The strip
  between the drive and 1808 Prairie's wall keeps the court's level behind the drive's edge.
- `prairie_frontage.passage_court_z` = -2.45 ft over the face's zero (the sheet's opening foot),
  so the passage clears **9.67 ft** under the court lintel (sheet 9.65) and the lintel stands
  8.6 ft over the drive before the mouth (sheet 8.63). T-2976's 10-ft ramp now rises 1.05 ft
  from that floor to the sunk drive, as the sheet's 1.02 ft. `underpass.floor` = -2.6 ng.
- The stair tower's rough-stone footing and a short footing on the face between the tower and
  the mouth (plan S 61.29-62.96) run down to the sunk ground; the grass follows it.
- compile_scene declares the fall's four quads with the passage's four, so the renderer cuts the
  field out over them and the walk follows them (eight pieces, the renderer's cap).
- `habs04-court-exterior` re-run on the new master: the opening now runs past the lawn line to
  the sunk drive, as the sheet's opening box does (verdict stays `differs` for the open items).

## Not changed, and open

- The street-mouth floor (sheet 6) stays at -1.9 door; the passage floor now falls 1.1 ft from
  the street to the court mouth. On the street zero it would run level; that difference is the
  bound above, not a second reading.
- The fall's westward extent (W 51.5 to 71.5) is invented: the sheet draws one profile, at the
  face or at its section plane, and the low ground is carried to the plane so the model agrees
  with either reading. The strip behind the drive is kept at the court's level though the sheet
  draws the ground south of the mouth low too, because 1808 Prairie's wall stands on it.
- Photograph 5 (c. 1923, rights unresolved, read only) shows a drive between curbs running down
  into the mouth; no geometry is taken from it.
