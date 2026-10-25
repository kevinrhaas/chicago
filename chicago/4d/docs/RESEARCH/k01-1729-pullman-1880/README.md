# T-1880 — 1729 Prairie onto K01 from the Detroit Publishing photograph

The envelope package for the George M. Pullman house (N19A of the T-1837 programme). It refines the
district draft (T-2335) in place under `pullman_house_1729_prairie`. T-1881 owns what the
photograph shows that is not built yet and the image gate's `matches`; T-1934 owns the stable,
the ranges and the porte-cochere.

## The picture

Detroit Publishing Co., "The Pullman residence, Chicago" (plate 012551), between 1890 and 1901 and
after 1893 by the Fort Dearborn monument it shows at the end of 18th Street; Library of Congress
LC-D4-12551, no known restrictions. The Prairie library holds it as `a16-pullman-det-4a08065`. It is
committed as the image store's copy at `data/sources/assets/pullman_1729_photo_t1880/` under source
record `loc_det_4a08065_pullman_residence`. It looks north-east across the crossing of Prairie
Avenue and 18th Street at the Prairie front and the 18th Street flank.

## The plan, from the 1911 sheet (trace s20fp-1729-b1, in the house's frame: u west toward Prairie, v south)

v is given in the new frame, whose origin is the draft's moved 2.43 m north (the draft's v + 2.43).

| part | u (m) | v (m) | built as |
|---|---|---|---|
| main block | 0 – 27.75 | 0 – 17.93 | K01's main body; its north wall stops at the conservatory's south wall (the trace runs 0.1-0.9 m beyond it in places) |
| north-west block | 22.8 – 27.75 | -1.53 – 0 | K08 full-height projection, 1.2 m out (a pavilion's most) |
| 18th Street pavilion | 9.5 – 19.75 | 17.93 – 20.3 | K08 full-height projection, 6.0 m wide and 1.2 m out (a pavilion's most), centred on the sheet's |
| portico | 27.75 – 30.85 | 1.6 – 10.6 | K01's door hood on two columns with a railing, 8.0 x 3.0 m, over a landing as wide |
| stoop (p1-p2) | 30.9 – 33.5 | 1.6 – 5.05 | not as drawn: the flight is laid across the portico's width (open) |
| south-east block ('B') | -2.0 – 0 | 11.6 – 18.8 | K01 rear wing, one storey, brick, flat deck |
| round bay on the north flank | 15.8 – 19.7 | -1.6 – 0 | not built (open, T-1881) |
| 1B range north of the rear | 1.0 – 9.5 | -4.3 – 0 | `pullman_house_1729_prairie_ranges`, one storey, at the draft's massing |
| porte-cochere ('1', p4) | 15.17 – 19.84 | 19.1 – 23.7 | `pullman_house_1729_prairie_ranges`, one storey, at the draft's massing |
| stable / GARAGE ('2') | -32.25 – -21.5 | -3.6 – 16.7 | `pullman_house_1729_prairie_ranges`, two storeys under the draft's mansard |
| palm room and conservatory | -16.4 – 0.9 | -4.5 – 0 | `pullman_house_1729_prairie_conservatory` (K13), unchanged |

K01's rear wings stand on the main block's rear wall, and the stable and range do not (the
conservatory stands between), so they stay on the draft builder in a record of their own rather
than going missing.

## The camera

`data/reference_views/pullman_house_1729_prairie/detroit_det_4a08065.json`: level, f = 1093 px from
the two faces' vanishing points, the eye 65 m from the south-west corner at the crossing's
south-west corner. The front's north end and south-west corner fix it; the flank's far end falls on
the print's (x 688 against 683-690) as a check. Its `solve` says how and how far.

## Before and after, from the photograph's camera

- before: `before-draft-detroit_det_4a08065.jpg` (dev's draft, rendered from the same camera in the
  draft's frame, eye u 88.3, v 40.5): three plain storeys, six bays, no portico.
- after: `../photo-match/pullman_house_1729_prairie/detroit_det_4a08065-side-by-side.jpg`

The match record is `differs`: the massing, cornice and curb heights, cresting and portico are
fixed; the quoined piers, arched window heads, the dormers beyond two, the modillions, the
portico's columns and balustrade, the stoop's place and the 18th Street arcade are open.

No generator rule changed: the record uses K01, K05, K07, K08, K10 and K02 as they stand.
