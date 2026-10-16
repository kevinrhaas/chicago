# 1812 Prairie, Albert Levy's photograph — reference copy for the image gate (T-2543)

One photograph of the street front of George H. Wheeler's house at 1812 South Prairie Avenue
(Burnham & Root, 1884), published in Albert Levy's Architectural Photographic Series (New York),
nos. 31 and 33, c. 1885-1900. Its source record is `data/sources/levy_1812_prairie_photo.json`
(tier 1, a photograph); the Prairie library lists the same print as `a18-rba-levy-1812-wheeler`
(Ryerson & Burnham Art and Architecture Archives, Art Institute of Chicago,
https://artic.contentdm.oclc.org/digital/collection/mqc/id/13492). The copy here is the image
store's (kevinrhaas/chicago-images, `prairie-1904/files/a18-rba-levy-1812-wheeler.jpg`), brought in
with its attribution as the owner directed on 2026-10-11 for the pictures the image gate builds
against, the way 1638's print was (`../shortall_1638_photo_t2423/`).

**Rights: public domain** (a published photographic series of the 1880s; the library's ruling).
Forms, counts and proportions are read from it; nothing is derived from the image as an asset (no
texture, no traced mesh), and the copy is unaltered.

| file | what |
|---|---|
| `1812_prairie_levy_front.jpg` | the print, 1267 x 1600 px sepia, sha256 `084dc78e2cbaa5091b68ba6244c261f7ab8654d869ee977e11fd39014f311ab2` |
| (camera) | `data/reference_views/wheeler_house_1812_prairie/levy_front.json`, solved from the print and the 1911 sheet's 8.5 m front; its `solve` field says how and how far |

**How it is used.** `node tools/photo_match.mjs data/reference_views/wheeler_house_1812_prairie/levy_front.json`
renders the committed GLB from that camera and writes it beside the print, with the match record
the image gate reads (T-1884's pieces T-2543 to T-2545).
