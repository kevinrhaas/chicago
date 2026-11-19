# 2108 Prairie, the Mark Kimball house — reference copy for the image gate (T-3667)

One picture of 2108 South Prairie Avenue, brought in with its attribution as the owner directed on 2026-10-11 for
the pictures the image gate builds against (`../keith_1906_pictures_t1898/` holds the whole Tribune strip).

**Rights.** The Tribune strip is a US newspaper illustration of 1898, in the public domain. Forms, counts, places
and proportions are read from it; nothing is derived from the image as an asset (no texture, no traced mesh). The
panel is an unscaled crop of the image store's copy.

| file | what |
|---|---|
| `tribune_1898_2108_panel.jpg` | the 2108 vignette of the Chicago Tribune's strip of 9 January 1898, "Select residence district where wealth has not prevented death from visiting many houses" (`data/sources/chicago_tribune_1898_01_09_residence_district.json`; Prairie library `cgs-tribune-1898-01-09-death-strip`): the strip's x 1128-1392, y 42-352 px of the store's 1400 x 356 px copy (`../keith_1906_pictures_t1898/tribune_1898_01_09_residence_strip.jpg`), cropped unscaled with its frame lines, 264 x 310 px greyscale, sha256 `9194d7d5e0f629bf52cf1415c0a3bb06ea699ec8d38af86b02f8d351f55256db`; its camera is `data/reference_views/mark_kimball_house_2108_prairie/tribune_1898_front.json` |

**How it is used.** `node tools/photo_match.mjs data/reference_views/mark_kimball_house_2108_prairie/tribune_1898_front.json`
renders the committed GLB from the panel's camera beside it and writes the match record the image gate reads. The
vignette is a freehand sketch whose camera is approximate, and its `solve` says how far.
