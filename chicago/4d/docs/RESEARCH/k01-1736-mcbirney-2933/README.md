# T-2933 — 1736 Prairie onto K01 from the c. 1890 photograph

Piece 1 of T-1874 (refine 1726, 1730 and 1736). It refines the district draft (T-2334) in place
under `house_1736_prairie`. T-2934 owns 1726 and 1730; T-2935 owns 1736's flank, service wing and
rear and brings the match record to `matches`.

## The picture

The Glessner House Museum's blog reproduces a photograph of "the Ingraham/McBirney house as it
appeared circa 1890" ('The Early History of Prairie Avenue - Part IV', 7 July 2020); the Prairie
library holds it as `a16-ghm-blog-1736-mcbirney-c1890`, "link only". It is committed as the image
store's copy, with its attribution, at `data/sources/assets/mcbirney_1736_photo_t2933/` under source
record `glessner_blog_1736_mcbirney_c1890_photo` (rights `check_required`: forms, counts and
proportions are read from it, nothing is derived from it as an asset), as 1637's Grosvenor
photograph was (T-2755). The 2015 curbstone photograph the ticket also lists is a modern detail and
is T-2935's to read.

## The camera

`data/reference_views/house_1736_prairie/mcbirney_c1890_photo.json`. A level camera square to the
front: the house's verticals are vertical and the front's horizontals (cornice brackets, the
veranda's fascia and deck) run level within 2 px, so neither flank of the main body is seen. The
front's two corners at x 321 and 537 px give 32.0 px/m on the sheet's 6.75 m. The veranda's front,
1.8 m nearer, reads about 7% wider, which puts the wall about 27-28 m from the eye: the east walk of
Prairie Avenue, where the library says the photographer stood. With the eye 1.6 m over the walk the
ice wagon stands at the west curb and is 3.6 m high, so the horizon is at y 460 px. Its `solve` says
how far each step can be trusted: every height scales with the distance, bounded to about 25-31 m.

## The plan, from the 1911 sheet

| part | u (m) | v (m) | reading |
|---|---|---|---|
| main body | 0 – 23.3 | 0 – 6.75 | trace s20fp-1736-b1 p3, brick, '3B'; the draft's fit had found a 5.5 m strip |
| veranda | 23.3 – 25.1 | 0 – 6.65 | trace p1 and p2, frame porch: the photograph's veranda, its stair at the north end |
| south projections | 3.8 – 5.6, 9.9 – 12.2 | -0.9 – 0 | two small bumps on the 18th Street wall: T-2935 |
| side porch | 16.3 – 18.9 | -0.9 – 0 | frame, on the 18th Street wall: T-2935 |

The new frame's origin is the main body's rear south corner, the draft's (0, -0.75); the position
moves to it through the record's own rotation.

## Before and after, from the photograph's camera

- before: `before-draft-mcbirney_c1890_photo.jpg` (dev's draft, rendered from the same camera in the
  draft's frame, eye v 3.28)
- after: `../photo-match/house_1736_prairie/mcbirney_c1890_photo-side-by-side.jpg`

The match record lists what is fixed and what is still open.

## The left of the picture

Left of the house, partly behind a tree, the photograph shows a lower front set back about 3 m, with
a one-storey canted bay and a dormer over it, and its cornice a little under the house's. Through
the camera it would stand on 1736's own south side yard and past the lot line, and the 1911 sheet
draws nothing there. Whether it was 1736's own south part in c. 1890, gone by 1911, or a building
the camera's distance places wrongly, is open on the match record for T-2935.

## Two generator rules, widened (additive)

- `k07_entrances.Entrance._veranda` (with `k01_frontage_params` validating
  `entrance_kit.veranda`): square posts on the deck's front edge, a beam the deck's run and a hipped
  lean-to roof from the wall, standing on a stoop's landing and its terraces. A post that stands off
  the deck or in the flight's mouth is refused. K01 paints the posts, beam and roof with the walls.
- `wall_finish.paint.opaque`: K01's paint was only a factor over the brick's map, and no factor over
  the buff brick is as light as the photograph's walls; an opaque paint is the slot's colour itself.

Both are inert for every record that does not name them: the other 22 K01, 1 K12, 1 K13 and 5 K16
assets rebuilt byte-identical, and only their manifest input hashes moved.
