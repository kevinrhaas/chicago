# 1615 Prairie refined from the district draft to a four-storey K01 brick house under a flat roof (T-2418)

Piece 2 of T-1868 (1613, 1615 and 1619 together, split by house). 1613 is T-2417 (#745), 1619's
stone front is T-2420, and this is 1615, the pair's south half. The draft T-2335 stood is refined
**in place**: `house_1615_prairie` keeps its id, its archetype changes from `prairie_draft` to
`k01_frontage`, the draft rules' `skip` names `s20-1615-f`, and the frontage row names the house.

## What the house is

Read from sheet 20 (T-2328 trace `s20fp-1615-b1`, T-1840 census `s20-1615-f` and `s20-1615-a1`):
four storeys, brick, the south half of a pair attached to 1613, with a one-storey frame (yellow)
porch across the whole rear. **The pair is built as one**, because the sheet attests a pair and a
pair built as one reads as one front: 1613's heights, brick, sash, K09 heads, K10 cornice, K01 flat
roof and tin covering, mirrored about the party wall, so the front reads door, window, window |
window, window, door. **Its own**: the door and stoop at the south end beside the passage to 1619;
three windows a storey on that passage wall; its north wall the party wall, blank; two stacks
against the party wall beside 1613's; its rear porch; and the frame projection on its south wall,
which 1613 does not have. Liberty `L-k01-1615-brick-flat-2418`; 1615 is retired from
`L-draft-prairie-16-18-east-2335`.

## Read off the sheet, past the census

The census row names the porch and nothing else. Two more things are on the raster itself (crop
of sheet pixels x 3700-4200, y 1780-2150):

- **A small yellow piece on 1615's south wall**, in the passage: about 1.65 m long and 0.6 m out,
  1.6-3.3 m from the rear wall (pixels x 3977-4018, y 2087-2099). The trace's building outline
  takes it in (x 1421.4-1423.0, y to -2995.98) but no part or census row names it. Its place, size,
  one storey and timber are read from the map. Its form is reconstructed: a box bay window on the
  principal floor, K08's square-cornered `projection` sized to the sheet's piece, in K01's `frame`
  fabric, with one 0.75 m sash under a flat tin deck. A side entry's vestibule, a closet or a stair
  hood are just as likely, and the liberty says so. A 0.9 m sash failed the K08 kit's `closed` rule:
  in a 0.6 m deep box its reveal opened into the body. The kit's 0.75 m cheek sash keeps the box
  closed at the sheet's depth. Making the box 0.3 m deeper than the map draws would have passed
  too, and was not taken.
- **The figures `12 12 12 8` printed against the south and party walls**, and against 1613's. These
  are Sanborn's wall thicknesses in inches, storey by storey: 12 inches for the three lower storeys
  and 8 for the fourth. So the walls are laid 0.30 m thick (`inferred`). K01 lays one thickness up
  a whole wall, so the top storey's 8 inches is not built; the front, which carries no figure,
  takes the side walls' 12. T-2417's note calls these "dimension numerals", and they are why both
  drafts stopped at 5.25 m: the trace took them for bites out of the house. 1613 still carries a
  reconstructed 0.33 m; the same reading would make it 0.30 `inferred`. That change is left to
  1613's own record, not made here.

## Placement

1615's corner is 1613's own local corner (u 0, v 6.55) carried through 1613's placement
(rotation 179.611, `footprint_uv`'s clockwise convention): UTM 448497.376, 4634407.006. The two
houses close on one party wall and one front and rear line, as the trace draws them (p1 x
1412.07-1424.71 against 1613's 1412.08-1424.70). The draft stood 0.32 m off 1613's wall and 0.25 m
deeper.

## Before and after, the same stands (`tools/qa_k01_t2418.mjs`)

Actual published `/1904/` app. *Before* is `dev` at b2d2f7ada (the draft), *after* is this branch.
Desktop 1280×800 at full detail, phone 390×780 at light. Stands: front (across Prairie), oblique
from the north and south walks, rear (the yard), roof (the air), and `passage` (`QA_PART=c`), looking
down the passage between 1615 and 1619 from the yard onto the projection. There were 0 page errors
and 0 failed requests on every run, and every stand is `withinBudget`. Frame times are software GL
on the runner: a relative reading, not a device claim.

| | load to ready | JS heap | draw calls | triangles | frame (median of 12) |
|---|---|---|---|---|---|
| desktop before → after | 24.1 → 21.2 s | 32.9 → 33.3 MB | 148-183 → 160-195 (+12) | 1.976-3.323 M → 2.001-3.348 M (+24.8 k) | 2.31-3.19 → 2.35-3.23 s |
| phone before → after | 15.5 → 15.9 s | 32.9 → 33.2 MB | 116-142 → 128-154 (+12) | 540-668 k → 565-693 k (+24.8 k) | 0.67-0.90 → 0.70-0.93 s |

The ranges are over the five common stands. The master is 2.59 MB and the web derivative 1.06 MB,
1613's order. K01 has no light derivative yet, so the phone's light tier draws the full assembly.

Screens: `before-*.jpg`, `after-*.jpg`. Readings: `browser-validation-{before,after}-{desktop,mobile}.json`,
and `-c` for the passage stand.

## Not built

- The porch's door and yard steps, and any rear stair (as 1613).
- A door into the side projection, if it was a vestibule.

## Limits

- No photograph, plate or description of 1615 or of the pair has been read, and there is no picture
  for the image gate (T-1868 lists one, of 1619). Every form is the kits'.
