# 2008 Calumet (P. C. Hanford), its 1883 plate and the blog's copy — reference copies for the image gate, T-3791

Paul C. Lautrup's pen perspective of Jaffray & Scott's design, "Residence of P. C. Hanford, Esq., Chicago", in *The
Inland Architect and Builder*, vol. II no. 5 (December 1883), p. 147, brought in from the Prairie library's image store
(`chicago/prairie_1904_v1/research/images/STORE.json`) so that 2008 Calumet is built against it (the image gate,
`data/reference_views/README.md`). Its source record is `data/sources/inland_architect_1883_12_hanford_plate.json`.
The Glessner House blog's copy ("Unearthing Hanford", 2015) is the same drawing, cropped and reduced.

**Rights: public domain.** A drawing published in a US architectural periodical in 1883. Forms, counts, places and
proportions are read from it; nothing in a scene is derived from it (no texture, no traced mesh).

| file | what |
|---|---|
| `inland_architect_1883_hanford_2008.jpg` | the store's copy of library image `dw-inland-1883-12-hanford-plate`, unaltered: 1636 x 2400 px greyscale, the page printed sideways, 635,472 bytes, sha256 `76b58c0580a944642375c5ffeed4ed57ba8ea3ad3c7942e22bce7331e900c3ea` |
| `inland_architect_1883_hanford_2008_upright.jpg` | the same turned 90 degrees upright (2400 x 1636 px, re-encoded at JPEG quality 92), the copy the plate's camera reads, sha256 `342efa2d6fe8dec844f726a69e558c26e26ab9053cd93cd6b232049c34842847` |
| `glessner_blog_hanford_engraving.jpg` | the store's copy of library image `a20-glessner-hanford-engraving`, unaltered: 675 x 565 px, 105,084 bytes, sha256 `75b8447705aa933e0618b56eeb8e0e67176e4c227d7c49e8ac8b09a83bac1d76`; the plate's drawing at 0.496 of the upright copy's scale (registered by cross-correlation, peak 0.664) |

**Cameras.** `data/reference_views/hanford_house_2008_calumet/inland_architect_plate.json` (solved on the upright
copy against the 1911 sheet's plan) and `glessner_blog_engraving.json` (the same camera carried onto the blog's copy);
each `solve` field says how and how far. `node tools/photo_match.mjs <camera>` renders the committed GLB beside the
picture and writes the match record the image gate reads.
