# 1729 Prairie, the Pullman palm house and stable, 1894 — reference copy for the image gate (T-3193)

The Inland Architect's photographic plate "Palm House and Stable of George M. Pullman, Chicago.
S. S. Beman, Architect." (The Inland Architect and News Record, vol. 24, no. 1, 1894), taken from
across 18th Street looking north-east: the palm house's drum and dome at left, the square belvedere
behind the range's parapet, and the stable's arcade, corner bay, upper storey and hipped roof at
right. Art Institute of Chicago, Ryerson and Burnham Archives
(https://digital-libraries.artic.edu/digital/collection/mqc/id/8429). Its source record is
`data/sources/inland_1894_pullman_palm_house_stable.json` (tier 1, a photograph); the Prairie library
lists it as `a16-inland-1894-pullman-palm-house-stable`. The copy here is the image store's
(kevinrhaas/chicago-images, `prairie-1904/files/a16-inland-1894-pullman-palm-house-stable.jpg`),
brought in with its attribution as the owner directed on 2026-10-11 for the pictures the image gate
builds against, the way the 16555 photograph was (`../pullman_1729_palm_house_t3165/`).

**Rights: public domain** (published in the United States in 1894). Forms, counts, places and
proportions are read from it; nothing is derived from the image as an asset (no texture, no traced
mesh), and the copy is unaltered.

| file | what |
|---|---|
| `inland_1894_pullman_palm_house_stable.jpg` | the plate with its mount and caption, 2000 x 1384 px, sha256 `4cd3f1eef5e267d8e2769c48d0fbfc79fb4ed256303efca48a9274d2bf9c5580` |
| (camera) | `data/reference_views/pullman_house_1729_prairie_conservatory/inland_1894_plate.json`, solved from the plate against the palm house, the stable and the 18th Street wall; its `solve` field says how and how far |

**How it is used.** `node tools/photo_match.mjs data/reference_views/pullman_house_1729_prairie_conservatory/inland_1894_plate.json`
renders the committed GLBs from that camera beside the plate, with the match record the image gate reads.
