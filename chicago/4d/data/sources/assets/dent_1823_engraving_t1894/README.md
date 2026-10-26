# 1823 Prairie, the Thomas Dent house — reference copy for the image gate (T-1894)

A halftone engraving after a photograph of 1823 South Prairie Avenue from the north-west, printed
beside an engraved portrait of Thomas Dent, undated. Its source record is
`data/sources/chicagology_1823_dent_engraving.json` (tier 1, an illustration: an engraving); the Prairie library
lists the print as `a18-cgy-1823-dent-engraving` ("1823 Prairie, Thomas Dent (engraving with
portrait)") and marks it "link only". It is reproduced on chicagology.com
(https://chicagology.com/chicagostreets/prairieavenue/1823prairie/). The copy here is the image
store's (kevinrhaas/chicago-images, `prairie-1904/files/a18-cgy-1823-dent-engraving.jpg`), brought
in with its attribution as the owner directed on 2026-10-11 for the pictures the image gate builds
against, as 1815's was (`../sears_1815_photos_t1893/`).

**Rights: check_required.** A secondary web reproduction with no rights statement. Forms, counts,
places and proportions are read from it; nothing is derived from the image as an asset (no texture,
no traced mesh), and the copy is unaltered.

| file | what |
|---|---|
| `dent_1823_engraving.jpg` | the engraving and the portrait, 2000 x 1076 px greyscale, sha256 `ef58522d4ac8f90422e4ebf253aec05a27bc06f7b47a255829684a2a2bc5bd0e` |
| (camera) | `data/reference_views/dent_house_1823_prairie/chicagology_engraving.json`, the engraving's camera, solved from it and the 1911 Sanborn sheet's plan; its `solve` field says how and how far |

**How it is used.** `node tools/photo_match.mjs data/reference_views/dent_house_1823_prairie/chicagology_engraving.json`
renders the committed GLB from that camera and writes it beside the engraving, with the match
record the image gate reads. The house's other picture, the 1883 New Chicago Album vignette
(`newberry_new_chicago_album_1883_residences`), is the same view drawn small; its camera is
T-3163's to solve.
