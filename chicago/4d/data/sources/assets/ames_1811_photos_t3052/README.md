# 1811 Prairie, the Coleman / Ames house — three reference copies for the image gate (T-3052, T-3101)

Two pictures of 1811 South Prairie Avenue that the Prairie library lists beside the Inland
Architect plate of October 1888 (`../ames_1811_plate_t2541/`), brought in with their attribution
as the owner directed on 2026-10-11 for the pictures the image gate builds against. Both copies
are the image store's (kevinrhaas/chicago-images, `prairie-1904/files/<id>.jpg`), unaltered.

| file | what |
|---|---|
| `ames_1811_chicagology_photo.jpg` | library `cgn-1811-coleman-ames-photo`, reproduced on chicagology.com (https://chicagology.com/chicagostreets/prairieavenue/1811prairie/), unknown photographer, undated (after 1886); 1303 x 1598 px greyscale, sha256 `6f5d94e0a9794ccf9f84d0f5cd0cf00c6bd09caa8e57be79d83958572bbc9b0c`. Source record `data/sources/chicagology_1811_ames_photo.json`. **A different negative from the plate.** Camera: `data/reference_views/coleman_ames_house_1811_prairie/chicagology_photo.json`, solved from the photograph, the 1911 sheet's plan and the 1904 street section |
| `ames_1811_glessner_blog_print.jpg` | library `a18-gh-1811-ames-house`, reproduced by the Glessner House Museum on its blog (https://glessnerhouse.blogspot.com/2015/01/miner-t-ames-coal-merchant.html); 562 x 675 px, toned, sha256 `d70fdce0e5b41bee5a3cd5dbb7de247d594b701600534c4e646ae3d659e359aa`. **The 1888 plate itself**, cropped and resampled: 1,381 SIFT matches fit one affine map to it within 0.80 px rms. Its source is therefore the plate's record; its camera, `glessner_blog_print.json`, is the plate's carried through that map |
| `ames_1811_habs_1965_kimball_court.jpg` | library `a18-kimball-habs-photo-01`: Harold Allen for the Historic American Buildings Survey, June 1965, "VIEW: WEST (PRAIRIE AVE.) AND SOUTH (COURT) ELEVATIONS - W. W. Kimball House, 1801 South Prairie Avenue" (HABS IL-1077, call number HABS ILL,16-CHIG,75--1; Library of Congress, https://www.loc.gov/pictures/item/il0136.photos.580872p/), fetched from https://tile.loc.gov/storage-services/service/pnp/habshaer/il/il0100/il0136/photos/580872pv.jpg; 1024 x 776 px greyscale, sha256 `7ace480beb382d33473f7870395255bbfce13ab703b6df4b0b8506c08df50254` (the library's `original_sha256`). A photograph of 1801; it sees 1811 only at its right edge, the front's north pier across the court. Camera: `data/reference_views/coleman_ames_house_1811_prairie/habs_1965.json`, fitted to 1801 and checked on 1811's pier (T-3101) |

**Rights: check_required** for the two web copies: secondary web reproductions with no rights statement (the
library marks both "link only"). The plate the blog print copies was published in 1888. Forms,
counts, places and proportions are read from them; nothing is derived from either image as an
asset (no texture, no traced mesh).

**How they are used.** `node tools/photo_match.mjs data/reference_views/coleman_ames_house_1811_prairie/<view>.json`
renders the committed GLB from the camera and writes the side-by-side and the match record the
image gate reads. Both pictures are of about 1888 and the scene is 1904, so what they show is
argued in the match records, not copied (AGENTS.md rule 11).

**The HABS photograph's rights:** no known restrictions (a HABS photograph made for the U.S. Government; the Library of Congress states no known restrictions on publication). It is a picture of 1965, so what it shows is argued against the in-period pictures in its match record, not copied; what it shows of 1811, the north pier, the 1888 plate and the Chicagology photograph show too.

**Not a reference view here: the Building Budget sketch** (library `dw-rb-building-budget-1887-entrance-sketch-18xx-prairie`, Cobb & Frost, July 1887). Its phase guard (T-1892's brief: possibly 1808 rather than 1811, so not a controlling detail until resolved) stands, and T-3101 read it again: the caption's house number is not legible at the 1056 px copy ("18?9"), and its entrance is not 1811's. It draws an open loggia of four round arches on clustered columns, reached by a stair rising ALONG the front beside it with a scrolled cheek; the plate and the Chicagology photograph both show 1811's entrance as one deep round arch reached by a broad straight stair rising square to the front between scrolled cheeks, with a small arcade of lights to its south. So it is given no camera under 1811 and builds nothing on it; if it is resolved to 1811 after all, that comparison is the place to start.
