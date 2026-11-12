# 1702-1812 Prairie, west side — Rand McNally 1893 street-front drawing, reference copy for the image gate (T-1872)

The strip 'Prairie Avenue (Looking North West)' on p. 233 of Rand, McNally & Co.'s *Bird's-Eye Views
and Guide to Chicago* (Chicago, 1893; artist not named): the west side of Prairie Avenue from 1702 to
1812, each front over its printed street number. Its source record is
`data/sources/rand_mcnally_1893_views_prairie_west_1702_1812.json` (tier 1, an illustration); the
Prairie library lists the same picture as `st-randmcnally-1893-p233-west-1700-1800`
(stream-streetscape), and Chicagology's arrowed crop of it for its 1712 page as
`cgn-1712-randmcnally-1893-strip`. The copy here is the image store's (kevinrhaas/chicago-images,
`prairie-1904/files/st-randmcnally-1893-p233-west-1700-1800.jpg`), itself the Internet Archive's
scan of item randmcnallycosbi00lawr (University of Illinois at Chicago Library), brought in with its
attribution as the owner directed on 2026-10-11 for the pictures the image gate builds against, as
the companion east strip was (`../rand_mcnally_1893_p233_east_t1877/`).

**Rights: public domain.** Published in Chicago in 1893, before 1929. Forms, counts, places and
proportions are read from it; nothing in a scene is derived from it (no texture, no traced mesh).

| file | what |
|---|---|
| `p233_west_1702_1812.jpg` | the image store's copy, unaltered: 864 x 2400 px, the strip printed sideways on the page, sha256 `82af4d9c96fa77c6644f8dc1970c5bfc63b9b46df2083a56ae27663f5e65446a` |
| `p233_west_1702_1812_upright.jpg` | the same turned 90 degrees anticlockwise, upright (2400 x 864 px, re-encoded at JPEG quality 92), the copy the camera reads, sha256 `adf8c46b8b3fc3d5515f955a66591245d6b8fff568335a0c5842df367be7c5c4` |
| (camera) | `data/reference_views/house_1712_prairie/rand_mcnally_1893_p233.json`, solved from the drawing and the 1911 Sanborn sheet's plan; its `solve` field says how and how far |

**How it is used.** `node tools/photo_match.mjs data/reference_views/house_1712_prairie/rand_mcnally_1893_p233.json`
renders the committed GLB from that camera and writes it beside the drawing, with the match record the
image gate reads (T-1872). Until this copy came in, 1712's record said no picture of the house was
known: the one picture the library filed under the address is the 1939 model of the Kodak plant that
replaced it. The strip draws 1702 (the house before the Glessner townhouses), 1720, 1726, 1730, 1736,
1800, 1808 and 1812 too; no camera is solved for them on it yet.
