# 1729 Prairie, the George M. Pullman house, between 1890 and 1901 — reference copy for the image gate (T-1880)

One photograph of the Pullman house at the north-east corner of Prairie Avenue and 18th Street,
taken from the south-west corner of the crossing, looking north-east: the Prairie front and the
18th Street flank, with the 1893 Fort Dearborn monument at the end of 18th Street on the right.
Detroit Publishing Co., "The Pullman residence, Chicago", plate 012551; Library of Congress Prints
and Photographs Division, LC-D4-12551, LC-DIG-det-4a08065 (https://www.loc.gov/pictures/item/2016801921/).
Its source record is `data/sources/loc_det_4a08065_pullman_residence.json` (tier 1, a photograph);
the Prairie library lists the same picture as `a16-pullman-det-4a08065`. The copy here is the image
store's (kevinrhaas/chicago-images, `prairie-1904/files/a16-pullman-det-4a08065.jpg`), the
Library's 1024 x 804 derivative, brought in with its attribution as the owner directed on
2026-10-11 for the pictures the image gate builds against.

**Rights: no known restrictions on publication** (the Library's statement). Forms, counts, places
and proportions are read from it; nothing is derived from the image as an asset (no texture, no
traced mesh), and the copy is unaltered.

| file | what |
|---|---|
| `loc_det_4a08065_pullman_residence.jpg` | the photograph, 1024 x 804 px greyscale, sha256 `60140932328aa19142c1545028a1b2afee6767d3aff79cff3d98cd27cbc87d8c` |
| (camera) | `data/reference_views/pullman_house_1729_prairie/detroit_det_4a08065.json`, solved from the photograph and the 1911 Sanborn sheet's plan; its `solve` field says how and how far |

**How it is used.** `node tools/photo_match.mjs data/reference_views/pullman_house_1729_prairie/detroit_det_4a08065.json`
renders the committed GLB from that camera and writes it beside the photograph, with the match
record the image gate reads. The photograph is of 1890-1901 (after 1893 by the monument) and the
scene is 1904, so the record weighs what it shows against the 1911 sheet (T-1880, T-1881).
