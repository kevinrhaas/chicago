# 1828 Prairie, the Daniel B. Shipman house — reference copy for the image gate (T-1887)

One photograph of 1828 South Prairie Avenue, undated (Chicagology captions it "about 1897"), from the
roadway of Prairie Avenue a little south of the house: its street front from the canted bay to the
porch and stoop, with an electric runabout at the curb. Its source record is
`data/sources/chicagology_1828_shipman_automobile.json` (tier 1, a photograph); the Prairie library
lists this copy as `cgn-1828-shipman-automobile-copy` and the Glessner House Museum blog's smaller copy
of the same photograph as `a18-gh-shipman-1828-with-automobile`, both "link only". It is reproduced on
chicagology.com (https://chicagology.com/chicagostreets/prairieavenue/1828prairie/). The copy here is
the image store's (kevinrhaas/chicago-images, `prairie-1904/files/cgn-1828-shipman-automobile-copy.jpg`),
brought in with its attribution as the owner directed on 2026-10-11 for the pictures the image gate
builds against, as 1816's was (`../henderson_1816_photo_t2963/`).

**Rights: check_required.** A secondary web reproduction with no rights statement. Forms, counts,
places and proportions are read from it; nothing is derived from the image as an asset (no texture,
no traced mesh), and the copy is unaltered.

| file | what |
|---|---|
| `shipman_1828_automobile.jpg` | the photograph, 1200 x 969 px greyscale, sha256 `c758e387f00acae0068286d86a69065154ee0f03e3edb234ab9ad936aba2e957` |
| `shipman_1828_partial.jpg` | the Glessner House Museum's damaged partial view of the north part of the front, its porch and its mansard, 387 x 675 px greyscale, sha256 `c2b23da61891304ec9e26a3793b1ee7875a59cd816b51873e5cb684a28333334`; source record `data/sources/glessner_blog_1828_shipman_partial.json`, library `a18-gh-shipman-1828-partial` |
| (camera) | `data/reference_views/house_1828_prairie/chicagology_automobile.json`, solved from it and the 1911 Sanborn sheet's plan; its `solve` field says how and how far |

**How it is used.** `node tools/photo_match.mjs data/reference_views/house_1828_prairie/chicagology_automobile.json`
renders the committed GLB from that camera and writes it beside the photograph, with the match record
the image gate reads. The partial view shows the second storey and the mansard the automobile
photograph cuts off, and is read for them; its camera is `data/reference_views/house_1828_prairie/glessner_partial.json`
(T-3168). The automobile photograph is also 1824 Prairie's reference view, on a camera fitted to that house
(`data/reference_views/marsh_house_1824_prairie/chicagology_automobile.json`).
