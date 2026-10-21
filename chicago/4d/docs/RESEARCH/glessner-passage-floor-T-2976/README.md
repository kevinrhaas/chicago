# T-2976: Glessner's carriage passage at its drawn height

The owner, walking the dev build on a phone (2026-10-21), found he had to lower his eye to about
5 ft to pass through the porte-cochère passage off Prairie Avenue and asked whether it was really
that low. It was not: the model had laid the passage floor at the display-lifted sidewalk, while
both HABS sheets draw it sunk below the ground at both mouths.

## What the sheets draw

**Sheet 6 (front elevation, 1965)**, read at its own printed lines: 0.00 AT DOOR at y 5952 and
24.30 at y 4126, so 75.14 px/ft.

| | y | ft over the door datum |
|---|---|---|
| opening head (the stone head's soffit) | 5430 | 6.95 (record 7.0) |
| 0.00 at door, printed | 5952 | 0 |
| sidewalk before the doorway, printed -0.74 | 6007 | -0.74 |
| opening's foot, both leaves drawn to it | 6093 | -1.88 (record -1.9) |

The sidewalk line returns down into the opening at both jambs, and both leaves run on below it
to the foot. Clear height from the floor to the head: **8.83 ft**, 7.8 ft between the jambs.
`sheet6-porte-floor.jpg`.

**Sheet 4 (section A-A, looking east at the court face, 1963)**, on T-2228's controls (97.7 px/ft
upright):

| | y | |
|---|---|---|
| court lintel's underside | 5154 | record 7.22 ft over y 5858 |
| T-2228's section datum (the record's 0) | 5858 | |
| ground drawn beside the mouth, both sides | 5994 | 1.39 ft under the datum |
| opening's foot | 6097 | 1.05 ft under that ground |

The opening runs on under the ground line, with rounded stones at both jambs' feet (as the
c. 1888 photograph shows them on the street face), 9.0 ft wide. Floor to lintel on the sheet:
**9.65 ft**. `sheet4-court-mouth-floor.jpg`.

## What is built

- `prairie_frontage.passage_front_z` = -1.9 over the door datum (-1.16 ft ng), the sheet-6 floor.
- `prairie_frontage.passage_court_z` = -0.93 ft ng: sheet 4's 1.05 ft under the court ground,
  taken under the model's 0.12-ft court drive.
- `v4_detail.underpass.floor` = -1.25 ft ng, so the passage's reveals reach under the paving.
- The carriage approach across the setback falls from the walk (0.21 ft) to the sunk mouth;
  a 10-ft ramp (`courtyard_ground.finish.passage_ramp_run_ft`) rises from the court mouth to
  the drive. Each has a dressed stone retaining edge along both sides, up to the ground.
- The oak leaves hang down to the sunk floor, as sheet 6 draws them.
- The passage clears **8.9 ft** under the street head and **8.15 ft** under the court lintel
  (2.48 m, `clear_m`), against 7.0 ft before. A visitor on foot or on a wagon seat passes
  through; one on horseback (eye 2.43 m) still meets the soffit.
- compile_scene declares the four sunk pieces on the sidecar (`footprint.passages[].ground`)
  from the generator's own `passage_ground()`. The renderer cuts the field out over them
  exactly (convex quads in the ground shader, `terrain.setPassageGround`) and the walk follows
  their paving (`passage-ground.js`); planting keeps off them.

## Open

T-2228's sheet-4 datum (y 5858) lies about 1.3 ft over the ground the sheet draws at the north
wall (y ~5980) and beside the court mouth (y 5994). Read from the ground the sheet draws there,
the court lintel stands 8.5 ft over the court, not the record's 7.1. Every court-face height
read on that datum is affected, so it is not changed here; filed as T-2978.

Liberty: `docs/LIBERTIES.md` L-glessner-passage-floor-2976.
