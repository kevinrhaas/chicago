# 1901 Prairie, the Norman B. Ream house — reference copies for the image gate (T-1903)

Two photographs of 1901 South Prairie Avenue, both reproduced on chicagology.com
(https://chicagology.com/chicagostreets/prairieavenue/1901prairie/): the front captioned "In 1898 as
owned by Mr. Ream", from across the avenue to the south-west, and an undated nearer view of the front's
south part and the south flank. Their source records are `data/sources/chicagology_1901_ream_1898.json`
and `data/sources/chicagology_1901_ream_exterior.json` (tier 1, photographs); the Prairie library lists
them as `a19-cgy-1901-ream-1898` and `a19-cgy-1901-exterior`, both "link only". The copies here are the
image store's (kevinrhaas/chicago-images, `prairie-1904/files/<id>.jpg`), brought in with their
attribution as the owner directed on 2026-10-11 for the pictures the image gate builds against, as
1828's were (`../shipman_1828_photos_t1887/`).

**Rights: check_required.** Secondary web reproductions with no rights statement. Forms, counts,
places and proportions are read from them; nothing is derived from either image as an asset (no
texture, no traced mesh), and the copies are unaltered.

| file | what |
|---|---|
| `ream_1901_1898_front.jpg` | the 1898 photograph, 981 x 673 px greyscale, sha256 `86070921794e13ab8816336bd7eec5a65774ed9d313efed15d76820110582892` |
| `ream_1901_exterior.jpg` | the undated exterior view, 1928 x 1176 px greyscale, sha256 `f149c559704fa37545432dc354005d3d239d685dfc31089829769c9de3511db3` |
| `pictorial_1893_ream_plate.jpg` | Rand McNally's *Pictorial Chicago* (1893), the Ream plate (public domain): the image store's display copy of the page, turned upright, levelled by the 1.45 degrees it was printed askew and cropped to the plate, 995 x 715 px, sha256 `582d316f2cfd878b54b3713364131511dcea229fbf3f27207469b047d59ba1c2`. The same photograph as `ream_1901_1898_front.jpg` (T-3186), so that picture dates from 1893 or before |
| (camera) | `data/reference_views/ream_house_1901_prairie/chicagology_1898_front.json`, solved from the 1898 photograph and the 1911 Sanborn sheet's plan; its `solve` field says how and how far |

**How they are used.** `node tools/photo_match.mjs data/reference_views/ream_house_1901_prairie/chicagology_1898_front.json`
renders the committed GLB from that camera beside the 1898 photograph and writes the match record the
image gate reads. The exterior view is read for the south flank and the canted corner; its camera is
T-3186's, with the 1893 Pictorial Chicago plate's.

The 1893 plate (T-3186, source record `data/sources/rand_mcnally_pictorial_chicago_1893_ream.json`) is a third reference copy, and its camera, `pictorial_1893_plate.json`, is the 1898 view's carried through an image-to-image fit: the chicagology '1898' copy is this plate cropped. The 1896 edition reprints the same negative and is not copied here.
