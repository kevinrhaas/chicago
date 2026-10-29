# 1701 Prairie, the Hibbard house — reference copies for the image gate (T-3240)

Two photographs of the William G. Hibbard house, 1701 South Prairie Avenue.

| file | what | source record | library id |
|---|---|---|---|
| `hibbard_1701_chicagology_front.jpg` | 1945 x 1207 px greyscale, sha256 `9906bb5ba57ac1a698bcf9686d7be726c469e33561ecccf2c72874cbb95a6fa6`; Chicagology's '1701 Prairie Avenue' page | `data/sources/chicagology_1701_hibbard_photo.json` | `cgn-1701-hibbard-photo-wide` |
| `hibbard_1701_ghm_rear.jpg` | 675 x 456 px greyscale, sha256 `6ca5124a0a6b3134e7b98e817edb87622a98aada87b89d01f00497d10f8caeca`; Glessner House Museum, 'Prairie Avenue in 1874', The Story of a House, 16 June 2014 | `data/sources/glessner_blog_1701_hibbard_rear_photo.json` | `a16-ghm-blog-1701-hibbard-rear` |

The copies are the image store's (kevinrhaas/chicago-images, `prairie-1904/files/<library id>.jpg`),
unaltered, brought in with their attribution as the owner directed on 2026-10-11 for the pictures the
image gate builds against.

**Rights: check_required** for both: secondary web reproductions with no rights statement. Forms,
counts, places and proportions are read from them; nothing is derived from either image as an asset
(no texture, no traced mesh).

**How they are used.** Their cameras are `data/reference_views/hibbard_house_1701_prairie/*.json`,
solved by T-3240 on the house's corners (plan places from the 1911 sheet's trace).
`node tools/photo_match.mjs <camera>` renders the committed GLB from each and writes the side-by-side
and the match record the image gate reads.
