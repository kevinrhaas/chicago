# 1620 Prairie (Robert Law), its two pictures — reference copies, T-2370

The two pictures of the Robert Law house at 1620 South Prairie Avenue, brought in from the
Prairie library's image store (`chicago/prairie_1904_v1/research/images/STORE.json`) so that the
house is built against them (the image gate, `data/reference_views/README.md`).

**Rights: public domain.** A US periodical engraving of 1874 and a US newspaper sketch of 1898.
Forms, counts and proportions are read from them; no asset is derived from either.

| file | what |
|---|---|
| `law_1620_landowner_1874.jpg` | *The Land Owner*, May 1874, "Robert Law": 1136 x 756 px, sha256 `ece6ea5d877f60e649e7e2cdbac51101ec8a9d29db76f38d410d97ad573ede19` (the store's file, byte for byte). Source record `land_owner_1874_05_homes_of_chicago_1620_law`. |
| `tribune_1898_prairie_widows.jpg` | Chicago Tribune, 9 January 1898, the five-house strip: 1400 x 374 px, sha256 `0d68b58289d04804679cd9f53b83d964da19caa9a80f7e1c1dd5a5e5b995819f` (the store's file). Source record `chicago_tribune_1898_01_09_prairie_widows`. |
| `tribune_1898_1620_panel.jpg` | the strip's 1620 panel, x 300-550, y 12-318, cropped unscaled: 250 x 306 px, sha256 `3db2a4d538087137a20a521136c997d11f3eef726e74bf969d64ecc2ef6be133`. |

**Cameras.** `data/reference_views/law_house_1620_prairie/landowner_1874_from_northeast.json` and
`tribune_1898_front.json`; each `solve` field says how it was fitted and how far it can be trusted.
`node tools/photo_match.mjs <camera>` renders the committed GLB beside the picture.
