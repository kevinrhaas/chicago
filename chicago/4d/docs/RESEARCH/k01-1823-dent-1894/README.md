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

## T-3163 (piece 2 of T-1894) — the pictures worked down

**The engraving's camera, re-solved.** Read again with a pixel ruler, the pavilion's front corners
stand at x 1035 and 1232 px, not the 990 and 1155 px T-3162 fitted to, so its camera put the pavilion
about 60 px left of the print and its cornice about 65 px low, and every front opening read through
it came out 0.5-1.4 m north of its place. The new fit (eleven readings, 11 px RMS; its `solve` says
which) moves the eye back across the avenue to u 55.5, v -24.8 and lands the mansard's curb, which
it was not fitted to, on the print's. Through it:

| what | T-3162 | T-3163 |
|---|---|---|
| the triple group's lights (v) | 0.88, 1.9, 2.92 m | 1.6, 2.75, 3.9 m |
| the door (v) | 4.85 m | 6.2 m |
| the north flank's columns (u) | 2.1, 4.3, 8.4, 10.9 m | 0.25, 2.15, 5.0 (chamber storey), 7.35, 11.0 m |
| the rear range's columns on the flank | three | one (the wall from x 140 to 225 px is blank) |
| the north stack (u, top) | 7.6 m, 18.3 m | 7.8 m, 17.5 m, on the cornice |

**The vignette's camera, solved.** `album_1883.json`, on a cut of the plate committed with its
attribution at `data/sources/assets/dent_1823_album_1883_t3163/`: ten readings, 5.5 px RMS at
about 13 px a metre, so a cross-check rather than a measurement. It agrees with the engraving's
places within about 5 px, and with the curb's height where the engraving draws it higher.

**Built from the pictures:** the north flank's box bay under its hood (K08's rectangular bay; its foot
carried to grade 0.5 m proud, since K08's corbelled oriel stands only on an upper floor: open); the
pavilion carried up an attic with paired lights under a coped stone gable and finial (K08's gable,
1801's), replacing the hipped crown, which is what lets the deck carry its iron cresting (K10's);
paired-light gabled dormers on the street face and the north flank; K09 cornice hoods over the front's
windows and surrounds on the pavilion's; the stoop climbing from the north along the front (K01's side
stoop, 1621's). One generator fix, in the parameter module only: the side stoop's check against a
street-front bay read a bow's `chord_m` and failed on a projection sized by `width_m`.

**Still open** (the match records): the triple group's broad dormer, whose pediment rises over the
curb in both pictures; the stack over the rear range; the grilled arched doorway under the landing;
the narrow light beside the door on the principal storey; the box bay's corbelled foot; and, on the vignette, the slated cheeks
either side of the pavilion's pedimented attic. Each needs K01 to do something it does not, so the
ticket is released with the records saying so (T-3153: no photo follow-up tickets from a run).

- before: `before-t3162-chicagology_engraving.jpg` (T-3162's build through T-3162's camera)
- after: `../photo-match/dent_house_1823_prairie/chicagology_engraving-side-by-side.jpg` and
  `album_1883-side-by-side.jpg`
