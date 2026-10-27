# 1720 Prairie, the John Tyrrell house — reference copy for the image gate (T-3180)

One undated photograph of the street front of the house at 1720 South Prairie Avenue (Otis L.
Wheelock, architect, 1868), from the Prairie Avenue walk looking west; photographer and original
holder not named. Its source record is `data/sources/glessner_blog_1720_tyrrell_photo.json` (tier
1, a photograph); the Prairie library lists the same picture as `a16-ghm-blog-1720-tyrrell-house`
and marks it "link only". It is reproduced by the Glessner House Museum ('Burley & Tyrrell,
Chicago's Forgotten Retailer', The Story of a House, 18 January 2022,
https://glessnerhouse.blogspot.com/2022/01/burley-tyrrell-chicagos-forgotten.html). The copy here
is the image store's (kevinrhaas/chicago-images, `prairie-1904/files/a16-ghm-blog-1720-tyrrell-house.jpg`),
brought in with its attribution as the owner directed on 2026-10-11 for the pictures the image
gate builds against, the way 1736's McBirney photograph was (`../mcbirney_1736_photo_t2933/`).

**Rights: check_required.** A secondary web reproduction with no rights statement. Forms, counts,
places and proportions are read from it; nothing is derived from the image as an asset (no texture,
no traced mesh), and the copy is unaltered.

| file | what |
|---|---|
| `tyrrell_1720_photo.jpg` | the photograph, 1200 x 1119 px greyscale, sha256 `8bcc2366a0f42187342eb728565c1e9f4f174181977230ce70aebda733719b81` |
| (camera) | `data/reference_views/walker_house_1720_prairie/tyrrell_front.json`, solved from the photograph and the 1911 Sanborn sheet's plan; its `solve` field says how and how far |

**How it is used.** `node tools/photo_match.mjs data/reference_views/walker_house_1720_prairie/tyrrell_front.json`
renders the committed GLB from that camera and writes it beside the photograph, with the match
record the image gate reads (T-1873's pieces T-3180, T-3181 and T-3182).
