# 1912 Prairie, the Moulton/Lowden house — reference copy for the image gate (T-3277)

One photograph of 1912 South Prairie Avenue, undated (an electric street lamp stands at the curb), from
the far side of Prairie Avenue north-east of the house: its street front from the south gable past the
round tower to the north corner block, its entrance under a striped awning at the head of a high stoop,
and the front corner of its north flank. Its source record is
`data/sources/chicagology_1912_prairie_exterior_photo.json` (tier 1, a photograph); the Prairie library
lists it as `a19-cgy-1912-exterior`, "link only". It is reproduced on chicagology.com
(https://chicagology.com/chicagostreets/prairieavenue/1912prairie/). The copy here is the image
store's (kevinrhaas/chicago-images, `prairie-1904/files/a19-cgy-1912-exterior.jpg`), brought in with
its attribution as the owner directed on 2026-10-11 for the pictures the image gate builds against, as
1828's was (`../shipman_1828_photos_t1887/`).

**Rights: check_required.** A secondary web reproduction with no rights statement. Forms, counts,
places and proportions are read from it; nothing is derived from the image as an asset (no texture,
no traced mesh), and the copy is unaltered.

**Orientation.** The print is the right way round (T-3277): its round bay falls where the 1911 sheet
draws the front's bulge, 3.25 m from the north wall, and its right-hand flank is the north flank.

| file | what |
|---|---|
| `moulton_1912_chicagology.jpg` | the photograph, 1218 x 1974 px greyscale, sha256 `edfbb93fb891e8f549e6aa782b2609f7a7b6fcde87847a46fbce72e00c350010` |
| (camera) | `data/reference_views/moulton_lowden_house_1912_prairie/chicagology_photo.json`, solved from it and the 1911 Sanborn sheet's plan; its `solve` field says how and how far |

**How it is used.** `node tools/photo_match.mjs data/reference_views/moulton_lowden_house_1912_prairie/chicagology_photo.json`
renders the committed GLB from that camera and writes it beside the photograph, with the match record
the image gate reads.
