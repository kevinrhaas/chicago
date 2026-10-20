# T-2963 — 1816 Prairie onto K01 from the Chicagology photograph

Piece 1 of T-1886 (refine 1816 Henderson). It refines the district draft (T-2329) in place under
`henderson_house_1816_prairie`. T-2964 owns what the photograph shows that is not built yet, the
1874 Land Owner engraving, and both match records' `matches`.

## The picture

Chicagology reproduces an undated photograph (after 1873) of Charles M. Henderson's house; the
Prairie library holds it as `a18-cgy-1816-henderson-photo`, "link only". It is committed as the
image store's copy, with its attribution, at `data/sources/assets/henderson_1816_photo_t2963/` under
source record `chicagology_1816_henderson_photo` (rights `check_required`: forms, counts and
proportions are read from it, nothing is derived from it as an asset).

## The plan, from the 1911 sheet (trace s28fp-1816-b1, in the lot's frame)

| part | u (m) | v (m) | built as |
|---|---|---|---|
| front block | 34.3 – 46.3 | -4.72 – 10.10 | K01's main body, 12.0 x 14.82 m; the new frame's origin is its rear south corner |
| canted front bay | 46.0 – 48.0 | -4.42 – 2.45 | K08 canted bay, 6.87 m at the wall, 1.65 m out, 2.4 m of front, carrying the cornice round it |
| porch (frame) | 46.6 – 48.6 | 2.7 – 5.8 | K01's door hood on two columns (new, below), 3.0 x 2.0 m |
| south flank bay | 34.6 – 39.4 | -5.71 – -4.72 | K08 canted bay, 4.85 m at the wall, 1.0 m out |
| rear range ('rear2B') | 22.4 – 34.3 | 0.3 – 7.9 | K01 rear wing, two storeys under a tin deck |
| step south of the rear range | 32.2 – 34.3 | -2.9 – 0.3 | not built (T-2964) |

## The camera

`data/reference_views/henderson_house_1816_prairie/chicagology_photo.json`, level, from the east walk
of Prairie Avenue south-east of the house. Its `solve` says how it was fitted and how far it holds:
the south-east corner on its pixel, the flank bay and the north end within 15-25 px, the porch's
columns 60-75 px right of the print's. Read against the trace, the print puts the porch and the
front bay about a metre further south than the 1911 sheet does; the match record leaves that open.

## Before and after, from the photograph's camera

- before: `before-draft-chicagology_photo.jpg` (dev's draft, rendered from the same camera in the
  draft's frame, eye u 55.05, v -32.47)
- after: `../photo-match/henderson_house_1816_prairie/chicagology_photo-side-by-side.jpg`

## Two generator rules, widened (additive)

- `k01_frontage_params`: a canted K08 bay standing on grade may come out up to 1.8 m (it was 1.2):
  1816's front bay is 1.65 m out on its sheet. An oriel keeps 1.2.
- `entrance_kit.hood.columns` and `hood.railing_fabric`: K01's door hood (T-2480) may stand on two
  turned columns over square plinths at the landing's front corners, with a flat respond against
  the wall behind each, so a hood becomes a porch; and its railing may be iron. Both are inert for
  every record that does not name them.
