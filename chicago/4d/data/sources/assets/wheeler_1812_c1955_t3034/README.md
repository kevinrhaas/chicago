# 1812 Prairie, about 1955 — reference copy for the image gate (T-3034)

One photograph of the street front of George H. Wheeler's house at 1812 South Prairie Avenue
(Burnham & Root, 1884), taken about 1955 from the walk across Prairie Avenue, a little south of
square, so that it sees the south wall in the gap to 1816 as well as the front. Its source record is
`data/sources/chicagology_1812_wheeler_c1955_photo.json` (tier 1, a photograph); the Prairie library
lists the same picture as `a18-cgy-1812-wheeler-c1955` ("1812 S. Prairie Ave. About 1955") and marks
it "link only". It is reproduced on chicagology.com
(https://chicagology.com/chicagostreets/prairieavenue/1812prairie/). The copy here is the image
store's (kevinrhaas/chicago-images, `prairie-1904/files/a18-cgy-1812-wheeler-c1955.jpg`), brought in
with its attribution as the owner directed on 2026-10-11 for the pictures the image gate builds
against, the way 1816's photograph was (`../henderson_1816_photo_t2963/`).

**Rights: check_required.** A secondary web reproduction with no rights statement. Forms, counts,
places and proportions are read from it; nothing is derived from the image as an asset (no texture,
no traced mesh), and the copy is unaltered.

| file | what |
|---|---|
| `1812_prairie_c1955.jpg` | the photograph, 554 x 900 px greyscale, sha256 `9d42de21b9c83ceaf17f58f197b844535a60d81461385b70dab989455a40bad8` |
| (camera) | `data/reference_views/wheeler_house_1812_prairie/c1955_front.json`, solved from the photograph against the front Albert Levy's print built and the 1911 sheet's plan; its `solve` field says how and how far |

**How it is used.** `node tools/photo_match.mjs data/reference_views/wheeler_house_1812_prairie/c1955_front.json`
renders the committed GLB, with 1816 beside it, from that camera and writes it beside the
photograph, with the match record the image gate reads. The photograph is about fifty years after
the 1904 scene, so the record weighs what it shows against Levy's print of c. 1885-1900 (T-2545's
pieces T-3033 to T-3035).
