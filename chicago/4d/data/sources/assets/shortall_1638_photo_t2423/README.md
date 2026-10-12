# 1638 Prairie, the photograph — reference copy for the image gate (T-2423)

One halftone photograph of the street front of the Shortall (later Gregory) house at 1638 South
Prairie Avenue, from the Prairie Avenue walk; unknown photographer, undated. Its source record is
`data/sources/chicagology_1638_prairie_photo.json` (tier 1, a photograph); the Prairie library
lists the same print as `a16-cgy-1638-gothic-photo` and marks it "link only". It is reproduced on
chicagology.com (Prairie Avenue, 1638 S. Prairie,
https://chicagology.com/chicagostreets/prairieavenue/1638prairie/). The copy here is the image
store's (kevinrhaas/chicago-images, `prairie-1904/files/a16-cgy-1638-gothic-photo.jpg`), brought in
with its attribution as the owner directed on 2026-10-11 for the pictures the image gate builds
against ("pictures from chicagology and other sites are brought in with their attribution, not left
as links"), the way 1612's print was (`../goodman_1612_photo_owner_2026_10/`).

**Rights: check_required.** A secondary web reproduction whose original holder is not named.
Forms, counts and proportions are read from it; nothing is derived from the image as an asset (no
texture, no traced mesh), and the copy is unaltered.

| file | what |
|---|---|
| `1638_prairie_front.jpg` | the print, 900 x 1077 px greyscale, sha256 `c57ee5e7463331d871a9ae4555fb95b8da8b8c2a3640a1a8a24fc907aa021646` |
| (camera) | `data/reference_views/shortall_gregory_house_1638_prairie_front/chicagology_front.json`, solved from the print, the Sanborn's 8.13 m front and the fence's base; its `solve` field says how and how far |

**How it is used.** `node tools/photo_match.mjs data/reference_views/shortall_gregory_house_1638_prairie_front/chicagology_front.json`
renders the committed GLB from that camera and writes it beside the print, with the match record
the image gate reads (T-1865's pieces T-2423 to T-2426).
