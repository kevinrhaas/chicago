# 1834 Prairie, the Fernando Jones house — reference copies for the image gate (T-1888)

One photograph of 1834 South Prairie Avenue, undated and before the mansard storey of 1886, in two
prints of the same negative: the front and the north flank with its canted bay, the stoop and the
low stone wall before the lawn. Its source records are `data/sources/chicagology_1834_jones_photo.json`
(tier 1, a photograph) and `data/sources/glessner_blog_2015_08_van_osdel.json` (the Glessner House
Museum's blog post that reproduces it); the Prairie library lists them as `cgs-1834-jones-photo` and
`a18-gh-1834-fernando-jones`, both "link only". The copies here are the image store's
(kevinrhaas/chicago-images, `prairie-1904/files/<id>.jpg`), brought in with their attribution as the
owner directed on 2026-10-11 for the pictures the image gate builds against, as 1828's were
(`../shipman_1828_photos_t1887/`).

**The prints are laterally reversed.** Both show the flank with the canted bay on the left of the
front. Read that way the camera stands south-east of the house and the bay sits on the south flank at
its rear, where the 1911 sheet draws a straight wall; the flank's windows then come out 2.5-3 m wide
and the principal point has to stand at the print's right edge. Turned the right way round the camera
stands where the library says it does (north-east, across Prairie Avenue), the bay falls on the north
flank where the sheet draws it, 9-14 m back from the front, and the fit closes within 2 px. So the
cameras in `data/reference_views/jones_house_1834_prairie/` carry `mirrored: true`: their pixels are
the picture turned back, and the side-by-side shows these copies, unaltered, turned back.

**Rights: check_required.** Secondary web reproductions with no rights statement. Forms, counts,
places and proportions are read from them; nothing is derived from the images as an asset (no
texture, no traced mesh), and the copies are unaltered.

| file | what |
|---|---|
| `jones_1834_chicagology.jpg` | Chicagology's print, the image store's copy, 1200 x 900 px greyscale, sha256 `b56b80160679f820ed88e84b46eaf9a96c838b317fe1791ebf78d2773156fe52`; library `cgs-1834-jones-photo` |
| `jones_1834_glessner.jpg` | the Glessner House Museum blog's print of the same negative, sepia, 675 x 506 px (the same framing at 0.5625 scale), sha256 `4180b8c58b74f7611529056a55633e18f01a35f37ad769ebda8bfefeff219283`; library `a18-gh-1834-fernando-jones` |

**How it is used.** `node tools/photo_match.mjs data/reference_views/jones_house_1834_prairie/chicagology_photo.json`
renders the committed GLB from the solved camera and writes it beside the photograph turned back, with
the match record the image gate reads; `glessner_photo.json` is the same camera at the smaller print's
scale.
