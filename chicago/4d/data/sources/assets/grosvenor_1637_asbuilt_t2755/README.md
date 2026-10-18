# 1637 Prairie, the Grosvenor house as built — reference copy for the image gate (T-2755)

One photograph of the south side of the Grosvenor house at 1637 South Prairie Avenue, c. 1870,
before Jesse Spalding remodelled it, from the south-west across Prairie Avenue; photographer and
original holder not named. Its source record is `data/sources/glessner_blog_1637_grosvenor_asbuilt_photo.json`
(tier 1, a photograph); the Prairie library lists the same picture as
`a16-ghm-blog-1637-grosvenor-asbuilt` ("South side of the Grosvenor house as built, c. 1870") and
marks it "link only". It is reproduced by the Glessner House Museum ('The Early History of Prairie
Avenue - Part IV', The Story of a House, 7 July 2020,
https://glessnerhouse.blogspot.com/2020/07/the-early-history-of-prairie-avenue.html). The copy here
is the image store's (kevinrhaas/chicago-images, `prairie-1904/files/a16-ghm-blog-1637-grosvenor-asbuilt.jpg`),
brought in with its attribution as the owner directed on 2026-10-11 for the pictures the image gate
builds against, the way the remodel engraving was (`../spalding_1637_engraving_t2441/`).

**Rights: check_required.** A secondary web reproduction with no rights statement. Forms, counts,
places and proportions are read from it; nothing is derived from the image as an asset (no texture,
no traced mesh), and the copy is unaltered.

| file | what |
|---|---|
| `grosvenor_1637_asbuilt_photo.jpg` | the photograph, 460 x 900 px greyscale (a crop of a wider plate), sha256 `75198e2332b04505f6bfbbc7b5567130138baee19cd79c332f728123a64b3a2d` |
| (camera) | `data/reference_views/spalding_house_1637_prairie/grosvenor_asbuilt_photo.json`, solved from the photograph and the 1911 Sanborn sheet's plan; its `solve` field says how and how far |

**How it is used.** `node tools/photo_match.mjs data/reference_views/spalding_house_1637_prairie/grosvenor_asbuilt_photo.json`
renders the committed GLB from that camera and writes it beside the photograph, with the match
record the image gate reads. The photograph is c. 1870 and the scene is 1904, so the record weighs
each thing it shows as kept or replaced by the remodel (T-2449's pieces T-2755 and T-2756).
