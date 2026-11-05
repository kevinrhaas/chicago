# T-3382: the children of the 1904 Prairie Avenue households

The owner asked for the children of every 1904 house, "if they lived there at any point",
with the years they lived there when they were not at home in 1904. Read as: the children
of each 1904 household who lived in that house at any time, including grown children gone
before 1904 and children born after it while the family was still there. Children of the
houses' former households (T-3266) are not carded.

## What was read

- **The Chicago Blue Book, 1890-1911** (every edition the project holds; there is no 1896
  or 1900 edition), Prairie Avenue street lists, 1600-2140. A same-surname name under the
  household at its number is carded as a son or daughter, graded `inferred` with the note
  "read from the shared surname" unless 'jr.' or another source states the relationship.
- **The 1910 census** (`census_1910_chicago_t624_roll241`), ED 166 (Prairie 1600-1737 and
  the west side 1800-1918) and ED 167 (the east side 1801-1945 and 2000-2140), leaves
  n1429-n1462, read by eye. Its relationship column and each mother's "children born /
  living" counts settle several Blue Book guesses. A child it lists is placed in the 1904
  house only by inference from age and the family's listings.
- **Family accounts** for the Pullman, Field and Glessner children
  (`pullman_museum_children_page`, `classic_chicago_pullman_finale`,
  `classic_chicago_prairie_kids_party`, `wikipedia_ethel_beatty`, `wikipedia_marshall_field`,
  `glessner_house_family_page`).

## The record

Each child carries `lived_here: {years, on_scene_date}`, with `on_scene_date` one of `yes`,
`no` or `unknown`, and, where the grown child heads their own 1904 household, `own_card`
(that person's id). `compile_scene.py` carries both into the directory row and reads a `no`
child as `absent` and an `unknown` one as `uncertain` on the scene date, so the map pins
and the "Here on 1 July" filter never put them in the house in 1904. Inspect lists the
`no` children under "Children who lived here in other years".

`spec.py` holds every entry with its sources; `apply.py` writes it onto the cards
(idempotent). After it: `python3 tools/build_former_residents_1904.py`,
`python3 tools/compile_scene.py --scene 1904`, `python3 tools/compile_source_use.py`.

## Not done

- The 1880 census (the Steve Morse ED finder returned nothing for these streets), so
  children grown and gone before 1890 are carded only where a family account names them.
- The 1910 census was read only for the households whose children are carded here; the rest
  keep "The 1910 census was not read for this card."
- Not carded for want of a source read: the McKinlock son, E. F. Henderson (ambiguous), the
  Spalding daughter, the other Ream children, the Lowdens' third child, the unnamed '& dr.'
  daughters of the 1890s (Corwith, Grey).
