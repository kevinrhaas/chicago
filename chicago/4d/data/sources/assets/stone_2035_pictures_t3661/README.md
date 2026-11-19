# 2035 Prairie, Mrs. H. O. Stone's house — reference copy for the image gate (T-3661)

One picture of 2035 South Prairie Avenue, brought in with its attribution as the owner directed on 2026-10-11 for
the pictures the image gate builds against (`../keith_1906_pictures_t1898/` holds the whole Tribune strip).

**Rights.** The Tribune strip is a US newspaper illustration of 1898, in the public domain. Forms, counts, places
and proportions are read from it; nothing is derived from the image as an asset (no texture, no traced mesh). The
panel is an unscaled crop of the image store's copy.

| file | what |
|---|---|
| `tribune_1898_2035_panel.jpg` | the 2035 vignette of the Chicago Tribune's strip of 9 January 1898, "Select residence district where wealth has not prevented death from visiting many houses" (`data/sources/chicago_tribune_1898_01_09_residence_district.json`; Prairie library `cgs-tribune-1898-01-09-death-strip`): the strip's x 846-1110, y 42-352 px of the store's 1400 x 356 px copy (`../keith_1906_pictures_t1898/tribune_1898_01_09_residence_strip.jpg`, sha256 `2f3996a6...`), cropped unscaled with its frame lines, 264 x 310 px greyscale, sha256 `5be80ad4cfc96a56f7a39e5e569798d42330308ded4100b71a0c669a28c34ab8`; its camera is `data/reference_views/stone_house_2035_prairie/tribune_1898_front.json` |

**How it is used.** `node tools/photo_match.mjs data/reference_views/stone_house_2035_prairie/tribune_1898_front.json`
renders the committed GLB from the panel's camera beside it and writes the match record the image gate reads. The
vignette is a freehand sketch whose camera is approximate, and its `solve` says how far.
