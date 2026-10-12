# 1612 Prairie, the photograph — reference copy, supplied 2026-10-11

One photograph of the Goodman (later Studebaker, then Bishop Anderson) house at 1612 South
Prairie Avenue, from the south-east on the Prairie Avenue walk, supplied by the project owner
on 2026-10-11 as the view the house should have been built against. Its source record is
`data/sources/chicagology_1612_prairie_photo.json` (tier 1, a period photograph; undated,
probably c. 1900-1930); the Prairie library lists the same print as
`a16-cgy-1612-studebaker-photo` and marks it "link only", which is why T-2344 never opened it.

**Rights: check_required.** A secondary web reproduction whose original holder is not named.
Forms, counts and proportions are read from it; nothing is derived from the image as an
asset, and the copy here is greyscale and reduced to 2000 px.

| file | what |
|---|---|
| `1612_prairie_front_from_southeast.jpg` | the print, 2000 x 2094 px, sha256 `5e3e3d3c6360a045de4b7a1d7b897a9f463c3969a9ef716612ba77e89ed1eeb4` |
| (camera) | `data/reference_views/goodman_house_1612_prairie/front_from_southeast.json` (moved there by T-2368), solved from the print and the Sanborn's 11.25 m front; its `solve` field says how |

**How it is used.** `node tools/photo_match.mjs data/reference_views/goodman_house_1612_prairie/front_from_southeast.json --out <dir>`
renders the committed GLB from that camera and writes it beside the print. Every height the
record reads off the photograph is a measurement through that solve, and its note says which
pixel it was read at; `docs/RESEARCH/k01-1612-goodman-2366/` holds the before and after.
