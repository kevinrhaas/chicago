# 1906 Prairie, the Edson Keith house — reference copies for the image gate (T-1898)

Two pictures of 1906 South Prairie Avenue, both reproduced on chicagology.com
(https://chicagology.com/chicagostreets/prairieavenue/1906prairie/): an undated nineteenth-century wood
engraving of the house from across the avenue to the south-east, and the Chicago Tribune's strip of
9 January 1898, "Select residence district where wealth has not prevented death from visiting many
houses", whose second vignette is the front of 1906. Their source records are
`data/sources/chicagology_1906_keith_engraving.json` (tier 1, engraving) and
`data/sources/chicago_tribune_1898_01_09_residence_district.json` (tier 1, newspaper); the Prairie library
lists them as `a19-cgy-1906-keith-engraving` ("link only") and `cgs-tribune-1898-01-09-death-strip`
(public domain). The copies here are the image store's (kevinrhaas/chicago-images,
`prairie-1904/files/<id>.jpg`), brought in with their attribution as the owner directed on 2026-10-11 for
the pictures the image gate builds against, as 1901's were (`../ream_1901_photos_t1903/`).

**Rights.** The engraving is check_required: a secondary web reproduction with no rights statement. The
Tribune strip is a US newspaper illustration of 1898, in the public domain. Forms, counts, places and
proportions are read from both; nothing is derived from either image as an asset (no texture, no traced
mesh), and the copies are unaltered.

| file | what |
|---|---|
| `keith_1906_engraving.jpg` | the wood engraving, 1300 x 857 px, sha256 `e844dbb769c4fceaaac2dcd2d950f69cdbb813aee4fe25a653a39f17477da3e3` |
| `tribune_1898_01_09_residence_strip.jpg` | the 1898 strip, 1400 x 356 px greyscale (the 1906 vignette at x 290-540 px), sha256 `2f3996a6175dafb0fbcab651b2e44fc7f810c45ed0b88371561fa1f298bbb29c` |
| `tribune_1898_1906_panel.jpg` | the strip's 1906 vignette cropped unscaled (the strip's x 290-542, y 47-354 px, its frame lines included), 252 x 307 px greyscale, sha256 `7fb85835c9299b2373dcf431333e8d368e54eb42310e47a787cfe6c15e163279`; its camera is `data/reference_views/edson_keith_house_1906_prairie/tribune_1898_front.json` (T-3239) |
| (camera) | `data/reference_views/edson_keith_house_1906_prairie/chicagology_engraving_southeast.json`, solved from the engraving and the 1911 Sanborn sheet's plan; its `solve` field says how and how far |

**How they are used.** `node tools/photo_match.mjs data/reference_views/edson_keith_house_1906_prairie/chicagology_engraving_southeast.json`
renders the committed GLB from that camera beside the engraving and writes the match record the image
gate reads. The vignette is read for the front's composition and its date; T-3239 solved its camera on the cropped panel
(`tribune_1898_front.json`), and `photo_match.mjs` renders the same GLB from it.

## The other pictures, weighed (T-3239)

Read from the image store; none is copied here and no camera is solved on them.

| library id | date | what it adds |
|---|---|---|
| `a19-cgy-1906-keith-photo` | undated, after the 1880s mansard | none for 1906: it is the photograph of the 1900 house (the T-1837 study's ruling; the same negative as the Glessner House Museum's '1900 PA', on which T-3207 solved 1900's camera). Its mansard, dormers and canted corner bay are not the hip-roofed front with a tower that the engraving and the 1898 vignette both draw for 1906 |
| `cgs-1906-tribune-1896-keith-suicide-scene` | 23 September 1896 | none: a lakeshore breakwater under heavy seas, with portraits of four men, captioned for Edson Keith's death; it shows no part of the house, and is set aside |
| `a19-gh-prairie-1800-1900-elevations` | c. 1914 drawing | the west side runs south to north from left to right (Allerton's 1936 first, Glessner's long front last), so 1906 is third from the south, attached to 1908's gabled front, between 1912's Chateauesque gables and 1900's mansard. About 100 px a house: it stops the south bay at about the main cornice and draws the hip flat-topped with a tall stack at its south end. Its front is otherwise not the vignette's (a broad flat bay, a square-headed window over the door), a later state, so it is weighed for the bay's height and the roof only |
