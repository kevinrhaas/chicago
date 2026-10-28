# 1827 Prairie, the John W. Doane house — reference copies for the image gate (T-3171, T-3191)

One photograph of 1827 South Prairie Avenue, undated (after the house's completion in 1882), taken from
the west side of Prairie Avenue a little south of the house: the Prairie front from the street tree at
its north end to the south-west corner and its square tower, and the south flank running back to the
coach house. Its source record is `data/sources/chicagology_1827_doane_exterior.json` (tier 1, a
photograph); the Prairie library lists this copy as `cgn-1827-doane-exterior` and the Glessner House
Museum blog's smaller copy of the same photograph as `a18-gh-doane-exterior`, both "link only". It is
reproduced on chicagology.com (https://chicagology.com/chicagostreets/prairieavenue/1827prairie/). The
copy here is the image store's (kevinrhaas/chicago-images, `prairie-1904/files/cgn-1827-doane-exterior.jpg`),
brought in with its attribution as the owner directed on 2026-10-11 for the pictures the image gate
builds against, as 1828's was (`../shipman_1828_photos_t1887/`).

**Rights: check_required.** A secondary web reproduction with no rights statement. Forms, counts,
places and proportions are read from it; nothing is derived from the image as an asset (no texture,
no traced mesh), and the copy is unaltered.

| file | what |
|---|---|
| `doane_1827_exterior.jpg` | the photograph, 1444 x 1770 px greyscale, sha256 `64e06383a60fdcc6a68ad1aa32db91dde8d1678f0a671ea1447768f487f5ac13` |
| (camera) | `data/reference_views/doane_house_1827_prairie/chicagology_doane_exterior.json`, solved from it and the 1911 Sanborn sheet's plan; its `solve` field says how and how far |
| `doane_1827_glessner_blog_print.jpg` | library `a18-gh-doane-exterior`: the Glessner House Museum blog's copy of **the same photograph** (https://glessnerhouse.blogspot.com/2013/08/electricity-comes-to-prairie-avenue-1882.html), toned, 561 x 600 px, a little wider at the right (the coach house), sha256 `9c2686002d5fd54c90cc027c2a49a442050867e9f2d55617e437c8d7acf7d720`. 1,656 SIFT matches fit one affine map to the Chicagology copy within 0.40 px RMS, so its camera, `glessner_blog_print.json`, is that one carried through the map (T-3191). **Rights: check_required**, as above |
| `doane_1827_tribune_1927_fire.jpg` | library `a18-cgy-1827-fire-1927`: "Fire Destroys Old Residence", Chicago Tribune, 1 January 1927, the house burning on the night of 31 December 1926, from Chicagology's scan (https://chicagology.com/chicagostreets/prairieavenue/1827prairie/); the image store's 1400 x 1265 px copy, sha256 `b6c408eb91f0dfdb60fa7fc2d30c50975cc4352606fe5f36a4e90ab5d4ad0181`. **Rights: public domain** (a US newspaper photograph published in 1927). A night halftone: its camera, `tribune_1927_fire.json`, is fitted to eight points on the crown, the tower's lit pair and a lit dormer (T-3191), and it is read for silhouettes and openings only |

**Which way it looks.** The Prairie library records the camera "north-west of the house, facing
south-east". It is south-west of it, facing north-east: the public walk and the iron fence run along
the left-hand face, so that face is the Prairie front; the right-hand face has an open lawn beside it
and the coach house beyond its far end (the 1911 sheet's coach house runs 5 m further south than the
house), so it is the south flank; and 1823 Prairie stands only 3 m north of the house on the sheet, so
no camera north-west of 1827 could see a flank at all.

**How it is used.** `node tools/photo_match.mjs data/reference_views/doane_house_1827_prairie/chicagology_doane_exterior.json`
renders the committed GLB from that camera and writes it beside the photograph, with the match record
the image gate reads.
