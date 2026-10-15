# 1638 Prairie: the tower's smooth stage and the gate caps' flare (T-2521)

Piece 3 of 4 of T-2458. Source: `chicagology_1638_prairie_photo` (the image store's 900 x 1077 px
halftone, `data/sources/assets/shortall_1638_photo_t2423/`), through the camera T-2423 solved
(`data/reference_views/shortall_gregory_house_1638_prairie_front/chicagology_front.json`).
`print-before-after.jpg`: the print | the model before | the model after, the tower above and
the gate piers' caps below, each cropped to the same pixels of the photograph's frame.

## The tower's upper stage

Read at 3x and 4x (crop 620-880 x 230-560 px). Scale at the tower's face 77 px a metre, heights
from the porch roof at 555 px (3.57 m), as T-2396 read them.

- **No course lines.** The three street faces show no clapboard course from the porch roof to
  the cornice, where the front beside the tower shows its siding's. Smooth: built as flush
  boards laid on the clapboard's course lines, each its own paint tone (the kit's wear rule),
  with no lap and no butt.
- **A shallow frieze.** One line crosses each face at 300 px (6.88 m), 0.12 m under the cornice
  (290 px); the kit's 0.4 m frieze board put its foot at 6.6 m (322 px), where the print shows
  smooth face and the ornament. `stage.frieze_m` 0.12.
- **The casings follow the heads.** The pale band round each light runs up its pointed head
  to the point; there is no square head board or drip cap. The lights now take the gable's and
  bay's `surround: pointed` (the band's apex 6.32 m).
- **The incised ornament.** Over each light, between its point (350 px) and the frieze, a
  faint grey figure about 18 px across and 25 px high (0.23 x 0.32 m, 6.30-6.62 m), standing on
  the band's apex. The halftone cannot draw its pattern. Built as a trefoil, one lobe up, cut
  into the board: lobes 0.065 m in radius 0.055 m out from its middle (0.225 m across, 0.21 m
  high), a 12 mm groove 6 mm deep, centred at 6.43 m so its foot stands 0.014 m over the band.
  The trefoil is the gable's own figure (T-2457), reconstructed; its place and size are read.
  Rendered, it reads as faintly as the print's does.
- **Re-placed after T-2523.** T-2523 landed first and re-solved the camera on the steps (eye
  30.71 m out, f 2242 px), re-reading the tower's sills at 4.40 m, its lights' points at 6.28 m
  and its cornice at 7.05 m. Through that camera the figure's rows (320-345 px) read 6.34-6.66 m,
  its middle 6.50 m, and the casing band's apex rises with the points; the trefoil is centred
  at 6.51 m so its foot stays just clear of the band. The frieze line (300 px) reads 6.92 m,
  still 0.12-0.13 m under the cornice. The before/after crops below were taken through the
  earlier camera.

## The gate caps

The south pier's outline, row by row (pale > 110 in the 8-bit grey): the cap's top at 797 px,
77-133 px across (57 px, 0.36 m at 158.7 px a metre on the street line) to 806 px; then its
south edge steps out — 75 (808-812), 74 (814-818), 73 (820-822), 72 (824), 71 (826-830) — and
back in — 72 (832), 74 (834), 77 (836) — onto the shaft's line (77-131, 55 px). The north
pier's lower corners stand 275-338 px (63 px) over a 52 px shaft. Through the camera (height =
2.3 - (row - 657) x 9.2 / 1460): the flare starts at 1.36 m, is widest at 1.21-1.23 m and is
back on the shaft by 1.17 m. Built: the cap's boards the shaft's breadth (0.34 m) under a
0.01 m eave, each board's lower corners swept out along a quarter-sine to 0.40 m across at
1.215 m and rounded back in to its foot at 1.17 m (`pier.cap.flare`). The street and yard
boards flare across the front, the side boards across the sides, so the hood reads from any
side. The curve between the readings is reconstructed.

T-2524 will re-read every fence size at the camera T-2523 re-solves (about 116 px a metre on
the street line, not 158.7); these readings are in the same frame as T-2456's and scale with
them.

## The "pale block" south of the south pier

Not built, because it is not a different thing. Rows 946-978 at x 48-66 px read 180-200, the
tone of the lawn between the bars north of the gateway (160-200 at x 340-420), under a hedge
line at 946 px (938 px there). A bar stands at 68-70 px, hard by the plinth (32-62 against the
north bars' 2-61, dark down to 980 px), and the base runs on under it to the frame (222-240,
as north). So the barred run continues south of the pier, as the model builds it. The pale
dash at 918 px over those same 20 px stands where the model's own top rail renders (925 px);
the 7 px between them belongs to the fence heights T-2524 re-reads.

## Gate

`check_timber_kit.py --check` and `--self-test`; the four other K16 houses whose GLB input
hash includes the generator (1601, 1609, 1611, 1630 Prairie) re-baked to identical bytes.
