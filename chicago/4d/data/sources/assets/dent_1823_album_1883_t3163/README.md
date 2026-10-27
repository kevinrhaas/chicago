# 1823 Prairie, the Thomas Dent house — the 1883 New Chicago Album vignette, for the image gate (T-3163)

The "Thomas Dent" vignette of the plate "Private Residences of Chicago" in *The New Chicago Album*
(Chicago: Wittemann Bros., 1883), Newberry Library, via CARLI Digital Collections
(https://collections.carli.illinois.edu/digital/collection/nby_chicago/id/7411). Its source record is
`data/sources/newberry_new_chicago_album_1883_residences.json`; the Prairie library lists the plate as
`a19-nby-newchicagoalbum-1883-residences`.

**Rights: no known restrictions.** The Newberry "makes its collections available for any lawful
purpose, commercial or non-commercial, without licensing or permission fees to the library". Forms,
counts and places are read from it; nothing is derived from the image as an asset (no texture, no
traced mesh).

| file | what |
|---|---|
| `dent_1823_album_1883.jpg` | the vignette cut unaltered from the image store's copy of the plate (`prairie-1904/files/a19-nby-newchicagoalbum-1883-residences.jpg`, 2400 x 1480 px, sha256 `7ba41d629fb60890a887eee4a18a0574e98aa9e9326031035ea53c809b9bc1f0`) at x 545-935 and y 465-890 px, the box the source record's locator names: 390 x 425 px, sha256 `266ad0e2bc64f4ed5e08799f6c974f6a3150a4fa7170145700272596e1611588` |
| (camera) | `data/reference_views/dent_house_1823_prairie/album_1883.json`, solved from the cut and the 1911 Sanborn sheet's plan; its `solve` field says how and how far |

**How it is used.** `node tools/photo_match.mjs data/reference_views/dent_house_1823_prairie/album_1883.json`
renders the committed GLB from that camera beside the vignette, with the match record the image
gate reads. The house's other picture is the Chicagology engraving (`../dent_1823_engraving_t1894/`).
