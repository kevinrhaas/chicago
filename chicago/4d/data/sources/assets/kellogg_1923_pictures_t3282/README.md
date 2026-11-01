# 1923 Prairie, the Kellogg house — reference copies for the image gate (T-3282)

Two pictures of 1923 South Prairie Avenue, brought in with their attribution as the owner directed on
2026-10-11 for the pictures the image gate builds against (`../keith_1906_pictures_t1898/` holds the
same Tribune strip for 1906).

**Rights.** The Tribune strip is a US newspaper illustration of 1898, in the public domain. The row
elevations are a blog reproduction whose original source and rights are not stated (check_required, the
Prairie library's "unknown — link only"). Forms, counts, places and proportions are read from both;
nothing is derived from either image as an asset (no texture, no traced mesh). The full copy is the
image store's, unaltered; the two panels are unscaled crops of the store's copies.

| file | what |
|---|---|
| `tribune_1898_1923_panel.jpg` | the 1923 vignette of the Chicago Tribune's strip of 9 January 1898, "Select residence district where wealth has not prevented death from visiting many houses" (`data/sources/chicago_tribune_1898_01_09_residence_district.json`; Prairie library `cgs-tribune-1898-01-09-death-strip`): the strip's x 566-828, y 44-352 px of the store's 1400 x 356 px copy (`../keith_1906_pictures_t1898/tribune_1898_01_09_residence_strip.jpg`), cropped unscaled with its frame lines, 262 x 308 px greyscale, sha256 `28c1b1cb04552a885b2e831e8773cfbd37dab54396fa55e88c2f17962f981285`; its camera is `data/reference_views/kellogg_house_1923_prairie/tribune_1898_front.json` |
| `prairie_1800_1900_row_elevations.jpg` | the undated row elevations of the 1800 and 1900 blocks, 'East Side of Prairie Ave' / 'West Side of Prairie Ave', reproduced in the Glessner House blog's "Business Encroachment on Prairie Avenue" (18 April 2011; https://glessnerhouse.blogspot.com/2011/04/business-encroachment-on-prairie-avenue.html), creator unknown (`data/sources/glessner_blog_2011_prairie_1800_1900_elevations.json`; Prairie library `a19-gh-prairie-1800-1900-elevations`): the image store's copy, 1600 x 464 px, sha256 `8392d418e65d1c9a0bd957c1ed711a7ba2773753ee1f6dca004f759e9801bbbe` |
| `row_elevations_1923_front.jpg` | the 1923 front in that drawing's east row (third from the right): its x 1325-1450, y 40-205 px cropped unscaled, 125 x 165 px, sha256 `54d7697d1855792e47cfc046a55c7ee2bbdbca06f894f0bdb162196cd2681d9b`; its camera is `data/reference_views/kellogg_house_1923_prairie/elevations_c1914_front.json` |

**How they are used.** `node tools/photo_match.mjs data/reference_views/kellogg_house_1923_prairie/<view>.json`
renders the committed GLB from that picture's camera beside it and writes the match record the image gate
reads. The elevation's camera is scaled by the drawing's own row (1905's front beside it), not by 1923's
front, which the drawing draws about 4 m narrower than the 1911 sheet; the vignette is a freehand sketch
whose camera is approximate, and its `solve` says how far.
