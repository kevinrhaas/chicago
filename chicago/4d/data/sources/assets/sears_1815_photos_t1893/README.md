# 1815 Prairie, the Joseph Sears house — reference copy for the image gate (T-1893)

Two photographs of 1815 South Prairie Avenue printed side by side, undated: on the left the street
front square-on (the house number 1815 on the door's transom), on the right the front and south
flank obliquely from the south-west. Their source record is
`data/sources/chicagology_1815_sears_two_views.json` (tier 1, a photograph); the Prairie library
lists the print as `a18-cgy-1815-sears-two-views` ("1815 S. Prairie Avenue (two historic views)")
and marks it "link only". It is reproduced on chicagology.com
(https://chicagology.com/chicagostreets/prairieavenue/1815prairie/). The copy here is the image
store's (kevinrhaas/chicago-images, `prairie-1904/files/a18-cgy-1815-sears-two-views.jpg`), brought
in with its attribution as the owner directed on 2026-10-11 for the pictures the image gate builds
against, as 1816's was (`../henderson_1816_photo_t2963/`).

**Rights: check_required.** A secondary web reproduction with no rights statement. Forms, counts,
places and proportions are read from it; nothing is derived from the image as an asset (no texture,
no traced mesh), and the copy is unaltered.

| file | what |
|---|---|
| `sears_1815_two_views.jpg` | the two photographs, 2000 x 1295 px greyscale, sha256 `39fbfc1c58b51ccd19997e89b76380d1445a6665485416a31ac489acf8522929` |
| (camera) | `data/reference_views/sears_meeker_house_1815_prairie/chicagology_square_on.json`, the left print's camera, solved from it and the 1911 Sanborn sheet's plan; its `solve` field says how and how far |

**How it is used.** `node tools/photo_match.mjs data/reference_views/sears_meeker_house_1815_prairie/chicagology_square_on.json`
renders the committed GLB from that camera and writes it beside the photograph, with the match
record the image gate reads. The right print is the same oblique as the Glessner House Museum's
photograph (`a18-gh-sears-house-exterior`); its camera is not solved yet.
