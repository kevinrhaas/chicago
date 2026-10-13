# T-2214 (GA-13A) — Glessner's 18th Street datestone, read from outside

The audit's finding: *the close north-gable view confirms the 1886 inscription is mirrored from
outside.* `before-app-capture.jpg` (cropped from the audit's `details/desktop-north-gable.png`)
shows it: "6881" and ".D.A".

## What the sources show

- **HABS photograph 4** (`habs_glessner_photo_04_18th_street_gable_c1923`, audit #117; a c. 1923
  copy, rights unknown, so it is cited and nothing is derived from it), read from the LOC master
  TIFF: the stack rises flush out of the gable's apex, the raking copings dying into its sides.
  On its face, an incised **AD** ligature (A on the viewer's left) over an incised **1886**, the
  date flanked by two incised crosses. The mount's handwriting reads the right way round, so the
  print is not reversed.
- **HABS sheet 6** (1965, no known restrictions), the north stack seen edge-on from the east: its
  face lies on the gable's coping line, within about 0.1 ft, and two stones stand about 0.2 ft
  proud of it at 43.6-45.5 and 45.8-47.2 ft above north grade, which are the heights the record
  already had.

## What changed (record + generator, one bake)

- `date_stones` (`masonry_house_v4_detail.py`) lays each glyph to the viewer's right **as seen
  from outside** the face. On the north face that is -x; the old code advanced +x (east), which from
  18th Street is right to left.
- The figures and monogram are drawn as cuts (the matte near-black lining the generator already
  uses for shadow), scaled to the photograph's share of each stone's width, on dressed stones
  standing 0.06 m beyond the rock face's furthest reach. Two crosses sit midway in the margins.
- Stone widths are photograph 4's shares of the stack's face (61 % and 55 %), centred.
- The stack's face moves from S 0.5 to S 0 (flush, per sheet 6 and photograph 4), and a parapet
  gable that names a `stack` (`masonry_house.py`, `_stack_cut`) stops its coping at the stack's
  sides. The gable is drawn as a full-width piece up to the stack's base, so its courses still run
  over the fan, plus a piece either side of the stack. Before, the parapet rose to a point
  in front of the stack, and the datestones floated on that plane, partly in front of the stack.
- The stack's copper base flashing is kept off the flush face.

`after-review-render.jpg` is `tools/photo_match.mjs` rendering the new GLB from a rough camera
on photograph 4's viewpoint (the side-by-side is not committed: the photograph's rights are
unknown). The camera is not solved. The image gate for the house is T-2228's.

Liberties: `docs/LIBERTIES.md` § `L-glessner-datestone-2214`.
