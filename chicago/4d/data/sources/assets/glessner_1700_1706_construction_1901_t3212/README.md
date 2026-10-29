# 1700-1706 Prairie under construction, 1901 — reference copy for the image gate (T-3212)

One photograph of the Glessner townhouses at 1700-1706 South Prairie Avenue during their building,
1708 Prairie at its left edge and 1638 Prairie's gable at its right.

| file | what | source record | library id |
|---|---|---|---|
| `ghm_1700_1706_construction_1901.jpg` | 675 x 494 px greyscale, sha256 `1ff92f1791176a4903d03470860b37f47871e6cca149297be8248f40c98f081b`; Glessner House Museum, 'George Glessner, photographer', The Story of a House, 12 January 2015 | `data/sources/glessner_blog_1700_1706_construction_1901_photo.json` | `a16-ghm-blog-1700-1706-construction-1901` (and `st-ghm-1700-1706-under-construction-1901`, the same picture) |

The copy is the image store's (kevinrhaas/chicago-images, `prairie-1904/files/<library id>.jpg`),
unaltered, brought in with its attribution as the owner directed on 2026-10-11 for the pictures the
image gate builds against. The Prairie library catalogues it twice, under the two ids above, with the
same URL and the same bytes.

**Rights: check_required.** Permission for the Glessner House Museum's scans was requested on
2026-10-02 and is pending. Forms, counts, places and proportions are read from it; nothing is derived
from the image as an asset (no texture, no traced mesh).

**How it is used.** Its camera is `data/reference_views/<1700 or 1706>/ghm_construction_1901.json`,
solved by T-3212 on 1706's second-storey windows. `node tools/photo_match.mjs <camera>` renders the
committed GLBs from it and writes the side-by-side and the match record the image gate reads. It is
evidence of 1901: the match records argue what it shows unfinished rather than copy it into 1904.
