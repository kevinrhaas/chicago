# T-3162 (piece 1 of T-1894) — 1823 Prairie onto K01 from its engraving and the 1883 album vignette

It refines the district draft (T-2330) in place under `dent_house_1823_prairie`.
T-3163 (piece 2 of T-1894) owns what the pictures show that is not built yet, the vignette's camera,
and the match records' `matches`.

## The pictures

- **The Chicagology engraving** (`chicagology_1823_dent_engraving`; Prairie library
  `a18-cgy-1823-dent-engraving`, "link only"). A halftone after a photograph, the house from the
  north-west across Prairie Avenue, printed beside an engraved portrait of Thomas Dent. Undated. Its
  verticals are vertical, so it was taken with a level camera and a rising front. It is the picture
  the camera is solved for. It is committed as the image store's copy, with its attribution, at
  `data/sources/assets/dent_1823_engraving_t1894/` (rights `check_required`: forms and proportions
  only).
- **The 1883 New Chicago Album vignette** (`newberry_new_chicago_album_1883_residences`; Prairie
  library `a19-nby-newchicagoalbum-1883-residences`, no known restrictions). The same view, drawn
  small and dated. It shows the stone front against the brick flank, and the pavilion's pedimented
  attic. It is cited, not committed. Its camera is T-3163's.

Both draw one state of the house, two years after it was built (1881) and later. Nothing read so far
records an alteration before 1904.

## The plan, from the 1911 sheet (trace s28fp-1823-b1, in the lot's frame: u toward the street, v south)

| part | u (m) | v (m) | built as |
|---|---|---|---|
| front block | 20.8 – 32.85 | -7.71 – 6.17 | K01's main body, 12.05 x 13.88 m; the frame's origin is its rear north corner |
| south pavilion | 32.85 – 33.97 | 0.43 – 6.15 | a K08 projection 5.74 m wide and 1.12 m forward, flush with the south wall, under K01's hipped crown |
| rear range ('rear2B') | 14.1 – 20.8 | -7.71 – 4.4 | K01 rear wing, two storeys under a flat tin deck; the north wall runs on unbroken, the south side narrows |

## The camera

`data/reference_views/dent_house_1823_prairie/chicagology_engraving.json`, level, from the far walk of
Prairie Avenue north-west of the house. Eleven points (corners at grade, the base course and the
cornice; plan places from the sheet's trace) fitted by least squares, 9.4 px RMS. Its `solve` says
how it was fitted and how far it holds.

## Before and after, from the engraving's camera

- before: `before-draft-chicagology_engraving.jpg` (dev's draft, rendered from the same camera in the
  draft's frame, eye u 46.64, v -17.56)
- after: `../photo-match/dent_house_1823_prairie/chicagology_engraving-side-by-side.jpg`

## What K01 could not carry, and so is open

- The pavilion's pediment of paired lights in front of its steep roof. K05's steepest hipped crown
  (65 degrees at its end) peaks about 2 m under the engraving's roof.
- The mansard's cresting. The broad carved pediment over the triple group: K05's gable head stands
  over one sash. The north flank's paired lights under one pediment.
- The north flank's one-storey box bay under a hood. The stack over the rear range, where K01 stands
  no stack.
- The stoop that climbs from the north. The narrow light beside the door. The grilled arched basement
  doorway under the landing. The moulded window heads.

No generator rule was changed: every part is the K01, K02, K05 and K08 kits as they stand. The front
is K02's Bedford limestone because the Lemont profile cannot course a base under a 2.35 m principal
floor.
