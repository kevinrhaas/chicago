# 1936 Prairie, the Thompson/Allerton house — reference copy for the image gate (T-1901)

One photograph of 1936 South Prairie Avenue, undated and in winter (an electric street lamp and a fire
hydrant stand at the curb), from the south-east across the corner of Prairie Avenue and 20th Street: the
house's south flank and its street front, the belvedere tower, the verandah and the entrance porch at the
tower's foot, the iron fence on its curb, the snow-covered side lawn, and at the left the brick barn on
the alley with its own cupola. Its source record is
`data/sources/chicagology_1936_prairie_exterior_photo.json` (tier 1, a photograph); the Prairie library
lists it as `a19-cgy-1936-thompson-photo`, "link only". It is reproduced on chicagology.com
(https://chicagology.com/chicagostreets/prairieavenue/1936prairie/). The copy here is the image store's
(kevinrhaas/chicago-images, `prairie-1904/files/a19-cgy-1936-thompson-photo.jpg`), brought in with its
attribution as the owner directed on 2026-10-11 for the pictures the image gate builds against, as 1912's
was (`../moulton_1912_photo_t3277/`).

**Rights: check_required.** A secondary web reproduction with no rights statement. Forms, counts,
places and proportions are read from it; nothing is derived from the image as an asset (no texture,
no traced mesh), and the copy is unaltered.

| file | what |
|---|---|
| `allerton_1936_chicagology.jpg` | the photograph, 1955 x 1080 px greyscale, sha256 `7458a4902276cccdaa289b9767e8ab717b5dd0fcf06ba3969a97c4fa8d00e92a` |
| (camera) | `data/reference_views/house_1918_prairie/chicagology_photo.json`, solved from it and the 1911 Sanborn sheet's plan; its `solve` field says how and how far |

**How it is used.** `node tools/photo_match.mjs data/reference_views/house_1918_prairie/chicagology_photo.json`
renders the committed GLB from that camera and writes it beside the photograph, with the match record
the image gate reads.
