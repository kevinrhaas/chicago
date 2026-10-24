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

## T-2960 — the upper windows' heads and the veranda open beneath

Piece 1 of T-2935 (T-2961 has the street wall and the set-back front; T-2962 the flank, the
service wing, the coach house and the mansard's date). Read off the same photograph at 32 px/m
(34 px/m at the veranda's front):

| what | the photograph | built |
|---|---|---|
| upper lights' heads | a segmental arch rising about 7 px (0.22 m) over the 28 px light, its springs rounded | K01 cuts the hole segmental at 0.22 of the span (`street_front_round_heads.head`, `rise_over_span`); K06's one-over-one segmental sash, built to the same rise |
| their hoods | a flat moulded cornice hood about 54 px (1.7 m) across, its underside about 2 px over the crown, a drop under each end just outside the jambs about 11 px (0.35 m) deep | K09's cornice hood on its two scrolled consoles over the crown (`hood`), its block 0.25 m past each jamb, about 1.7 m across with the cornice's return |
| under the deck | each post's lower length runs on down to grade, the raised basement dark between them | K07's veranda `open_under`: the posts carried to grade as piers, a 0.2 m skirt (the deck's edge, y 450-457 px), the void 0.5 m back (reconstructed) |
| deck and balustrade | painted timber: a top rail 0.8 m over the deck and a light, pierced-looking infill | the balustrade's `fabric: painted_timber`, slender balusters at 0.14 m; the deck in the walls' paint |

Still open: the veranda roof's slope, the street-line wall and the lower front left of the house
(T-2961). The posts' section is `not shown` (each is about 6 px across).

Three generator rules widened (additive, each inert for a record that does not name it):
`street_front_round_heads` may name `head: segmental`, its `rise_over_span`, and a K09 `hood` in
place of the band and key (`k01_frontage.hole` cuts the segmental curve; `k09_frontage.head` lays
the hood); K07's veranda may stand `open_under` (`k07_entrances._terrace` and `_veranda`); and
`entrance_kit.balustrade.fabric` may be `painted_timber`, which K01 paints with the walls.

## T-2962 / T-2994 — the 18th Street wall's three bays and the mansard's date

T-2962 (piece 3 of T-2935) was split: T-2994 builds the flank's bays and argues the mansard's date;
T-2995 has the roof behind the curb, the rear behind the brick bay and the coach house.

**The sheet, re-read off the raster** (sheet 20 at x 2650-3180, y 5895-6070). The 18th Street wall
carries three projections, every one drawn **canted** (its face shorter than its foot), about 0.85 m
out, read from the trace's outline in the record's frame:

| | colour | at the wall (u, m) | face (u, m) | built |
|---|---|---|---|---|
| rear | yellow, frame | 3.37 - 6.01 | 3.94 - 5.36 | K08 canted bay, frame, one storey to 5.75 m |
| middle | pink, brick | 9.42 - 12.75 | 9.93 - 12.21 | K08 canted bay, brick, two storeys to a flat top at 9.25 m |
| front | yellow, frame | 15.97 - 19.17 | 16.48 - 18.51 | K08 canted bay, frame, one storey to 5.75 m |

The trace's role rule called the front one a frame porch (part p4: frame and under 15 m2 on a
masonry house). The sheet draws it in solid lines, closed and canted exactly as the rear one is,
where it draws the veranda in a porch's dashes, so it is built as a frame bay. Neither yellow bay has
a storey figure, so each is one storey (1730's yellow bay, T-2934). The brick bay rises under the
roof: the mansard's dashed curb turns down into its rear cheek. K01 cannot carry the mansard's face
out over a bay, so the bay stands to a flat top 0.65 m under the eave.

**The curb.** The dashed line runs about 1.2 m inside the street front and about 1.0 m inside the
18th Street wall, from the front back only as far as the brick bay (u about 9.9). None is drawn along
the north wall or over the rear 9.9 m. The sheet prints `12 12 8` against the north wall (u about
14-17) and `14 12 12` against the south (u about 13-15), wall thicknesses in inches by storey; whether
they start at the basement is not settled, so whether the north side and the rear stand as a straight
brick third storey is left to T-2995. Today K05 builds the mansard on all four walls.

**The mansard's date.** The Glessner House Museum's post on early Prairie Avenue
(`glessner_blog_2020_07_early_history_prairie_iv`, read 2026-10-22) has the house 'completed in
1864' for Granville S. Ingraham. Its author judges the mansard 'may well have been a later addition'
to an Italianate house of the Civil War years. That is a judgement made from the photographs, not a
record, and nothing read here dates the mansard. The Keith house at 1900 Prairie had its mansard
added in the 1880s (`glessner_blog_2014_11_elbridge_keith_house`). The 1904 scene does not depend
on the answer: the c. 1890 photograph (earliest 1885) shows the mansard and the 1911 sheet draws its
curb, so it stood through 1904.

**From 18th Street.** `south-flank-t2994.jpg` is the committed GLB rendered from a camera in 18th
Street (u 12, v -24, eye 1.6 m, looking north). It is a review render, not a reference view: no
picture of this wall is known.

## T-2995 — the roof behind the curb, the rear, and the coach house

Piece 2 of T-2962. Both readings are off sheet 20 and its key
(`chicago/reference/prairie-avenue/sanborn-1911-and-robinson-1886/sanborn_1911_vol3_key.jpg`).

**The ruling.** The key draws a *mansard roof* as a dashed line inside a building's outline, and
*'Figures 20, 16, 12, 8 indicate thickness of wall in inches'*, one figure a storey. On 1736 the dashed
line runs inside the street front and inside the 18th Street wall back to the brick bay (u about 9.9),
and nowhere else. The north wall's `12 12 8` and the south wall's `14 12 12` are three figures each,
the three storeys of the sheet's `3B` over the basement. So the north wall is brick through the third
storey (8 inches at the top). The rear, which the curb line leaves out as it leaves out the north, is
ruled the same (inferred: no figures stand on it). The mansard stands on the street front and on the
18th Street wall forward of the brick bay. The north side, the rear and the 18th Street wall behind
the bay rise as a straight brick third storey, the service side.

**Built.** K01 learns `mansard.straight` (`generators/archetypes/k01_mansard_straight.py`): the
straight walls are carried up from the eave as coped brick parapets 0.45 m over the curb, and the
eave box and the lower faces are cut away outside their planes. Where a mansard face runs on past a
straight wall (the street front's at the north wall, the south face at u 9.9) its section is closed in
the wall's brick. The bracketed cornice and the gutter stop at the same ends, the gutter with stop
ends, and the downpipes move from the rear corners (which no longer carry a gutter) to the 18th Street
wall at u 13.3 and 22.9. The south face's second dormer (u 8.0) goes with the mansard behind the bay.
No picture sees the straight walls, so their third storey is built blank
(L-k01-1736-roof-rear-2995). The change is inert for every record that does not name it: the other 24
K01 assets, both K12 coach houses, the K13 conservatory and the five K16 fronts rebuilt byte-identical.

- `roof-rear-t2995.jpg`: from 18th Street (south-west), the committed GLB
- `rear-north-t2995.jpg`: from over the alley (north-west), the rear and north walls under their parapets

**The coach house.** `house_1736_prairie_coach_house` moves from the district draft onto the K12 kit
(L-k12-1736-coach-house-2995), the second K12 coach house after 1812's. Read off the raster by median
darkness profiles: the alley wall at column 2227, the east wall at 2528.5, the north wall at row 5910.5,
the south wall on the 18th Street line at row 6063, so 15.31 m deep by 7.74 m along the alley at the
sheet's 0.050779 m a pixel. It is `2` storeys, brick, with `12 8` on its north wall, and the key's
window symbol (strokes across the wall, a dot for each storey) stands on the alley wall about 3.3 m from
the north end. 1730's alley building stands on its north line from the alley to about 7.6 m back; the
house's rear wall is 7.31 m east. GARAGE is a 1911 use, so it is built as the house's stable and coach
house, as 1812's is. It has a party wall at the north end, the kit's open gable on 18th Street, and a
window pair where the sheet's mark stands, with the carriage bay toward the street. The draft rules skip
census row `s20-1736-r1`.

- `coach-house-t2995.jpg`: the K12 GLB from 18th Street (the gable), from the alley, and from the yard
