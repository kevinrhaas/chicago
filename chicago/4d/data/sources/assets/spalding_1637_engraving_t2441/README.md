# 1637 Prairie, the remodel engraving — reference copy for the image gate (T-2441)

One line engraving of the Grosvenor house at 1637 South Prairie Avenue as Jesse Spalding remodelled
it, from the north-west across Prairie Avenue; unknown illustrator, source publication not named,
undated. Its source record is `data/sources/glessner_blog_1637_spalding_remodel_engraving.json`
(tier 1, an engraving); the Prairie library lists the same print as
`a16-ghm-blog-1637-spalding-remodel` and marks it "link only". It is reproduced by the Glessner
House Museum ('The Early History of Prairie Avenue - Part IV', The Story of a House, 7 July 2020,
https://glessnerhouse.blogspot.com/2020/07/the-early-history-of-prairie-avenue.html). The copy here
is the image store's (kevinrhaas/chicago-images, `prairie-1904/files/a16-ghm-blog-1637-spalding-remodel.jpg`),
brought in with its attribution as the owner directed on 2026-10-11 for the pictures the image gate
builds against ("pictures from chicagology and other sites are brought in with their attribution,
not left as links"), the way 1638's print was (`../shortall_1638_photo_t2423/`).

**Rights: check_required.** A secondary web reproduction whose source publication is not named.
Forms, counts and proportions are read from it; nothing is derived from the image as an asset (no
texture, no traced mesh), and the copy is unaltered.

| file | what |
|---|---|
| `spalding_1637_remodel_engraving.jpg` | the engraving, 900 x 817 px greyscale, sha256 `623aefdf2d4fa77eba389efc6ab9970af93d7c20d0782a3d6994920ff82f89fa` |
| (camera) | `data/reference_views/spalding_house_1637_prairie/spalding_remodel_engraving.json`, solved from the engraving and the 1911 Sanborn sheet's plan; its `solve` field says how and how far |

**How it is used.** `node tools/photo_match.mjs data/reference_views/spalding_house_1637_prairie/spalding_remodel_engraving.json`
renders the committed GLB from that camera and writes it beside the engraving, with the match
record the image gate reads (T-1870's pieces T-2441 and T-2442).
