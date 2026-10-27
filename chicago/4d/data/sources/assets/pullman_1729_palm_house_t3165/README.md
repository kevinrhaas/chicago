# 1729 Prairie, the Pullman palm house, 1892-94 — reference copy for the image gate (T-3165)

One photograph of Solon S. Beman's 1892 range between the George M. Pullman house and its stable,
taken from 18th Street looking north: the palm house's columned drum and dome at centre, the raised
terrace and its steps before it, the house's 18th Street porch at left and the stable at right.
J. W. Taylor (Chicago), "Pullman, George M., Residence" (holder's note: "west front, showing portion
enclosing palm house and stable"); Art Institute of Chicago, Ryerson and Burnham Archives, no. 16555
(https://digital-libraries.artic.edu/digital/collection/mqc/id/29190). Its source record is
`data/sources/aic_taylor_16555_pullman_west_front.json` (tier 1, a photograph); the Prairie library
lists the same picture as `a16-aic-taylor-pullman-west-front-palm-house` and marks it "link only".
The copy here is the image store's (kevinrhaas/chicago-images,
`prairie-1904/files/a16-aic-taylor-pullman-west-front-palm-house.jpg`), brought in with its
attribution as the owner directed on 2026-10-11 for the pictures the image gate builds against, the
way 1736's McBirney photograph was (`../mcbirney_1736_photo_t2933/`).

**Rights: check_required.** The holder asks that publication questions go to its archives. Forms,
counts, places and proportions are read from it; nothing is derived from the image as an asset (no
texture, no traced mesh), and the copy is unaltered.

| file | what |
|---|---|
| `aic_taylor_16555_pullman_west_front.jpg` | the photograph, 1200 x 1107 px with its border and grey scale, sha256 `ac3c59513afea361ab73f82c36b8ba7bc75728eeb05cabc4262fa7c7c5dd11d1` |
| (camera) | `data/reference_views/pullman_house_1729_prairie_conservatory/taylor_16555_west_front.json`, solved from the photograph and the 1911 Sanborn sheet's plan; its `solve` field says how and how far |

**How it is used.** `node tools/photo_match.mjs data/reference_views/pullman_house_1729_prairie_conservatory/taylor_16555_west_front.json`
renders the committed GLB from that camera and writes it beside the photograph, with the match
record the image gate reads. The photograph is of 1892-94 and the scene is 1904; the c. 1905 CHM
negative of the same front and the 1911 sheet both still show the range.
