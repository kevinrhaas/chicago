# 2009 Prairie, the Max A. Meyer house — reference copies for the image gate (T-1913)

Two pictures of 2009 South Prairie Avenue, Burnham & Root's French Gothic rowhouse of 1888, brought in
with their attribution as the owner directed on 2026-10-11 for the pictures the image gate builds
against. Both are the image store's copies (kevinrhaas/chicago-images, `prairie-1904/files/`).

| file | what |
|---|---|
| `meyer_2009_chicagology_photo.jpg` | the undated photograph of 2009 and 2011 from the west walk, 1671 x 2000 px greyscale, sha256 `03db894ab10dff078b747f611eba3dd8d9bc3b1f35aae50435017dcd4640b4a2`; library `a20-chicagology-2009-2011-photo`; source record `data/sources/chicagology_2009_prairie_meyer_photo.json`. **Rights: check_required** (a web reproduction with no rights statement): forms, counts, places and proportions are read from it; nothing is derived from the image as an asset, and the copy is unaltered. |
| `meyer_2009_monroe_1896_plate.jpg` | Harriet Monroe's 1896 plate, p. 155, 1050 x 1600 px; library `a20-monroe-1896-meyer-house-p155`; source record `data/sources/monroe_1896_john_wellborn_root_meyer_plate.json`. Public domain (US, 1896). |
| (camera) | `data/reference_views/mayer_house_2009_prairie/chicagology_photo.json`, solved from the photograph and the 1911 Sanborn sheet's plan; its `solve` field says how and how far |

**How it is used.** `node tools/photo_match.mjs data/reference_views/mayer_house_2009_prairie/chicagology_photo.json`
renders the committed GLB from that camera and writes it beside the photograph, with the match record
the image gate reads.
