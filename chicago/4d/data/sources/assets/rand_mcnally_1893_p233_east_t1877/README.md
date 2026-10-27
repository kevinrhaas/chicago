# 1701-1815 Prairie, east side — Rand McNally 1893 street-front drawing, reference copy for the image gate (T-1877)

The strip 'Prairie Avenue (Looking North East)' on p. 233 of Rand, McNally & Co.'s *Bird's-Eye Views
and Guide to Chicago* (Chicago, 1893; artist not named): the east side of Prairie Avenue from 1701 to
1815, each front over its printed street number. Its source record is
`data/sources/rand_mcnally_1893_views_prairie_east_1701_1815.json` (tier 1, an illustration); the
Prairie library lists the same picture as `st-randmcnally-1893-p233-east-1700-1800`
(stream-streetscape). The copy here is the image store's (kevinrhaas/chicago-images,
`prairie-1904/files/st-randmcnally-1893-p233-east-1700-1800.jpg`), itself the Internet Archive's
scan of item randmcnallycosbi00lawr (University of Illinois at Chicago Library), brought in with its
attribution as the owner directed on 2026-10-11 for the pictures the image gate builds against, the
way 1736's McBirney photograph was (`../mcbirney_1736_photo_t2933/`).

**Rights: public domain.** Published in Chicago in 1893, before 1929. Forms, counts, places and
proportions are read from it; nothing in a scene is derived from it (no texture, no traced mesh).

| file | what |
|---|---|
| `p233_east_1701_1815.jpg` | the image store's copy, unaltered: 883 x 2400 px, the strip printed sideways on the page, sha256 `6bd8b9a5e7094ab80ded59cb3ee487d459aa1a3f4655b688d4af7b074d570693` |
| `p233_east_1701_1815_upright.jpg` | the same turned 90 degrees upright (2400 x 883 px, re-encoded at JPEG quality 92), the copy the camera reads, sha256 `432f11b41adc85eb66e7fb20b3ea038f9f1b1ef6819cd9e5f892c4e120825fb3` |
| (camera) | `data/reference_views/kellogg_house_1709_prairie/rand_mcnally_1893_p233.json`, solved from the drawing and the 1911 Sanborn sheet's plan; its `solve` field says how and how far |

**How it is used.** `node tools/photo_match.mjs data/reference_views/kellogg_house_1709_prairie/rand_mcnally_1893_p233.json`
renders the committed GLB from that camera and writes it beside the drawing, with the match record the
image gate reads (T-1877). The strip draws 1701, 1721, 1729, 1801, 1811 and 1815 too; no camera is
solved for them on it yet.
