# 1708 Prairie, the Thorne house — reference copies for the image gate (T-3188)

Two photographs of the Glessner townhouses, 1700-1706 South Prairie Avenue, each with 1708 Prairie
at its left edge. Neither is a picture of 1708 alone; each shows its street front beside 1706's
south corner, and they are the only pictures of it this project reads.

| file | what | source record | library id |
|---|---|---|---|
| `townhouses_1700_1706_chicagology.jpg` | 1955 x 1200 px greyscale, sha256 `56843b92bab0a3581dfa1629949584543d6d12f5e9e556b699e9df6e91275a87`; Chicagology's '1706 Prairie Avenue' page | `data/sources/chicagology_1700_1706_townhouses_photo.json` | `a16-cgy-1700-1706-townhouses` |
| `thorne_glessner_lee_christmas_ghm.jpg` | 1200 x 983 px greyscale, sha256 `d691b958d2cffc522407f1ac1443c91d7d51f740e348c5773cc348d6d90f7f63`; Glessner House Museum, 'The Glessner House Christmas Tree', The Story of a House, 14 December 2021 | `data/sources/glessner_blog_1708_1706_1700_christmas_photo.json` | `a16-ghm-blog-1708-1706-1700-christmas` |

The copies are the image store's (kevinrhaas/chicago-images, `prairie-1904/files/<library id>.jpg`),
unaltered, brought in with their attribution as the owner directed on 2026-10-11 for the pictures the
image gate builds against.

**Rights: check_required** for both. The Chicagology copy is a secondary web reproduction with no
rights statement; permission for the Glessner House Museum's scans was requested on 2026-10-02 and is
pending. Forms, counts, places and proportions are read from them; nothing is derived from either
image as an asset (no texture, no traced mesh).

**How they are used.** Their cameras are `data/reference_views/house_1708_prairie/*.json`, solved
together by T-3188 on the townhouses' front (its two corners and the party line between 1700 and
1706, from the 1911 sheet). `node tools/photo_match.mjs <camera>` renders the committed GLB from
each and writes the side-by-side and the match record the image gate reads.
