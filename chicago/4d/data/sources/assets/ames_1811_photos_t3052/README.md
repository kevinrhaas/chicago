# 1811 Prairie, the Coleman / Ames house — two reference copies for the image gate (T-3052)

Two pictures of 1811 South Prairie Avenue that the Prairie library lists beside the Inland
Architect plate of October 1888 (`../ames_1811_plate_t2541/`), brought in with their attribution
as the owner directed on 2026-10-11 for the pictures the image gate builds against. Both copies
are the image store's (kevinrhaas/chicago-images, `prairie-1904/files/<id>.jpg`), unaltered.

| file | what |
|---|---|
| `ames_1811_chicagology_photo.jpg` | library `cgn-1811-coleman-ames-photo`, reproduced on chicagology.com (https://chicagology.com/chicagostreets/prairieavenue/1811prairie/), unknown photographer, undated (after 1886); 1303 x 1598 px greyscale, sha256 `6f5d94e0a9794ccf9f84d0f5cd0cf00c6bd09caa8e57be79d83958572bbc9b0c`. Source record `data/sources/chicagology_1811_ames_photo.json`. **A different negative from the plate.** Camera: `data/reference_views/coleman_ames_house_1811_prairie/chicagology_photo.json`, solved from the photograph, the 1911 sheet's plan and the 1904 street section |
| `ames_1811_glessner_blog_print.jpg` | library `a18-gh-1811-ames-house`, reproduced by the Glessner House Museum on its blog (https://glessnerhouse.blogspot.com/2015/01/miner-t-ames-coal-merchant.html); 562 x 675 px, toned, sha256 `d70fdce0e5b41bee5a3cd5dbb7de247d594b701600534c4e646ae3d659e359aa`. **The 1888 plate itself**, cropped and resampled: 1,381 SIFT matches fit one affine map to it within 0.80 px rms. Its source is therefore the plate's record; its camera, `glessner_blog_print.json`, is the plate's carried through that map |

**Rights: check_required** for both: secondary web reproductions with no rights statement (the
library marks both "link only"). The plate the blog print copies was published in 1888. Forms,
counts, places and proportions are read from them; nothing is derived from either image as an
asset (no texture, no traced mesh).

**How they are used.** `node tools/photo_match.mjs data/reference_views/coleman_ames_house_1811_prairie/<view>.json`
renders the committed GLB from the camera and writes the side-by-side and the match record the
image gate reads. Both pictures are of about 1888 and the scene is 1904, so what they show is
argued in the match records, not copied (AGENTS.md rule 11).
