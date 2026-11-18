# 2026 Prairie, the Louis Wahl house — reference copy for the image gate (T-3608)

One wood engraving of 2026 South Prairie Avenue (964 Prairie before the 1909 renumbering), from
*The Land Owner*, May 1874, captioned "LOUIS WAHL": the house from the walk south-east of it, its
street front and south flank. Its source record is
`data/sources/land_owner_1874_05_homes_of_chicago_2026_wahl.json`; the Prairie library lists the
same picture as `a20-chicagology-2026-wahl-landowner-1874` ("Louis Wahl [residence] (The Land Owner,
May 1874)"), reproduced on chicagology.com
(https://chicagology.com/chicagostreets/prairieavenue/2026prairie/). The copy here is the image
store's (kevinrhaas/chicago-images, `prairie-1904/files/a20-chicagology-2026-wahl-landowner-1874.jpg`),
byte for byte, brought in with its attribution as the owner directed on 2026-10-11 for the pictures
the image gate builds against, as 1816's Land Owner plate was (`../henderson_1816_photo_t2963/`).

**Rights: public domain** (a US periodical engraving published in 1874; the web copy is a faithful
reproduction of a two-dimensional work). Forms, counts, places and proportions are read from it;
nothing is derived from it as an asset (no texture, no traced mesh), and the copy is unaltered.

| file | what |
|---|---|
| `wahl_2026_landowner_1874.jpg` | the engraving, 1400 x 1125 px, sha256 `f09857bdce3dcfe247a804f71d873471ae1ecf2699c66a2be5a02092d09dcd48` (the store's display copy of the library's 1447 x 1163 px fetch of 2026-10-02) |
| (camera) | `data/reference_views/house_2026_prairie/landowner_1874.json`, solved from the engraving and the 1911 Sanborn sheet's plan; its `solve` field says how and how far |

**How it is used.** `node tools/photo_match.mjs data/reference_views/house_2026_prairie/landowner_1874.json`
renders the committed GLB from that camera beside the engraving and writes the match record the
image gate reads. The engraving is of 1874 and the scene is 1904, so the record weighs what it shows
against the 1911 sheet (T-3608, piece 2 of T-1910).
