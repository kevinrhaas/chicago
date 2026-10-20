# 1816 Prairie, the Charles M. Henderson house — reference copy for the image gate (T-2963)

One photograph of 1816 South Prairie Avenue, undated (after 1873), from the walk south-east of the
house: its street front and south flank, with 1812 Prairie's shaped gable beyond it. Its source
record is `data/sources/chicagology_1816_henderson_photo.json` (tier 1, a photograph); the Prairie
library lists the same picture as `a18-cgy-1816-henderson-photo` ("1816 S. Prairie Ave. (Charles M.
Henderson house), historic photograph") and marks it "link only". It is reproduced on chicagology.com
(https://chicagology.com/chicagostreets/prairieavenue/1816prairie/). The copy here is the image
store's (kevinrhaas/chicago-images, `prairie-1904/files/a18-cgy-1816-henderson-photo.jpg`), brought
in with its attribution as the owner directed on 2026-10-11 for the pictures the image gate builds
against, the way 1736's photograph was (`../mcbirney_1736_photo_t2933/`).

**Rights: check_required.** A secondary web reproduction with no rights statement. Forms, counts,
places and proportions are read from it; nothing is derived from the image as an asset (no texture,
no traced mesh), and the copy is unaltered.

| file | what |
|---|---|
| `henderson_1816_photo.jpg` | the photograph, 1444 x 1148 px greyscale, sha256 `6cf57cac7e3076af06121b104b57a02b9a25ac3830f01ddafe9ac2f27eb96ca8` |
| (camera) | `data/reference_views/henderson_house_1816_prairie/chicagology_photo.json`, solved from the photograph and the 1911 Sanborn sheet's plan; its `solve` field says how and how far |

**How it is used.** `node tools/photo_match.mjs data/reference_views/henderson_house_1816_prairie/chicagology_photo.json`
renders the committed GLB from that camera and writes it beside the photograph, with the match
record the image gate reads. The photograph is undated and the scene is 1904, so the record weighs
what it shows against the 1911 sheet (T-1886's pieces T-2963 and T-2964).
