# 1736 Prairie, the Ingraham/McBirney house c. 1890 — reference copy for the image gate (T-2933)

One photograph of the street front of the house at 1736 South Prairie Avenue, c. 1890, from the
east side of Prairie Avenue looking west across the street; photographer and original holder not
named. Its source record is `data/sources/glessner_blog_1736_mcbirney_c1890_photo.json` (tier 1, a
photograph); the Prairie library lists the same picture as `a16-ghm-blog-1736-mcbirney-c1890`
("Ingraham/McBirney house as it appeared circa 1890") and marks it "link only". It is reproduced
by the Glessner House Museum ('The Early History of Prairie Avenue - Part IV', The Story of a
House, 7 July 2020, https://glessnerhouse.blogspot.com/2020/07/the-early-history-of-prairie-avenue.html).
The copy here is the image store's (kevinrhaas/chicago-images,
`prairie-1904/files/a16-ghm-blog-1736-mcbirney-c1890.jpg`), brought in with its attribution as the
owner directed on 2026-10-11 for the pictures the image gate builds against, the way 1637's
Grosvenor photograph was (`../grosvenor_1637_asbuilt_t2755/`).

**Rights: check_required.** A secondary web reproduction with no rights statement. Forms, counts,
places and proportions are read from it; nothing is derived from the image as an asset (no texture,
no traced mesh), and the copy is unaltered.

| file | what |
|---|---|
| `mcbirney_1736_photo_c1890.jpg` | the photograph, 900 x 611 px greyscale, sha256 `c3b9a67372ccd09aea1798b29b39dc484d5e4d3c13ea10e2afe03df2d2b16062` |
| (camera) | `data/reference_views/house_1736_prairie/mcbirney_c1890_photo.json`, solved from the photograph and the 1911 Sanborn sheet's plan; its `solve` field says how and how far |

**How it is used.** `node tools/photo_match.mjs data/reference_views/house_1736_prairie/mcbirney_c1890_photo.json`
renders the committed GLB from that camera and writes it beside the photograph, with the match
record the image gate reads. The photograph is c. 1890 and the scene is 1904, so the record weighs
what it shows against the 1911 sheet (T-1874's pieces T-2933 and T-2935).
