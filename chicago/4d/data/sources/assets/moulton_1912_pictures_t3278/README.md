# 1912 Prairie, the Moulton/Lowden house — two more reference copies for the image gate (T-3278)

Two more pictures of 1912 South Prairie Avenue, brought in with their attribution as the owner
directed on 2026-10-11 for the pictures the image gate builds against. The photograph is in
`../moulton_1912_photo_t3277/`.

**Rights.** The New Chicago Album plate (Wittemann Bros., 1883) is a US publication of 1883, in the
public domain. The row elevations are a blog reproduction whose original source and rights are not
stated (check_required, the Prairie library's "unknown — link only"). Forms, counts, places and
proportions are read from both; nothing is derived from either image as an asset (no texture, no
traced mesh). Both files are unscaled crops of the image store's copies, unaltered otherwise.

| file | what |
|---|---|
| `moulton_1912_album_1883.jpg` | the 'B. F. Moulton' vignette of the New Chicago Album's 'Private Residences of Chicago' plate (`data/sources/newberry_new_chicago_album_1883_residences.json`; Prairie library `a19-nby-newchicagoalbum-1883-residences`, the image store's 2400 x 1480 px copy, sha256 `7ba41d629fb60890a887eee4a18a0574e98aa9e9326031035ea53c809b9bc1f0`): its x 940-1465, y 790-1310 px, 525 x 520 px, sha256 `8479c93215df5e498fcfa87e9cc4829a43aab228919383ac1d358845352981d9`; its camera is `data/reference_views/moulton_lowden_house_1912_prairie/album_1883.json` |
| `row_elevations_1912_front.jpg` | the 1912 front in the west row ('West Side of Prairie Ave') of the undated row elevations of the 1800 and 1900 blocks (`data/sources/glessner_blog_2011_prairie_1800_1900_elevations.json`; the full copy is `../kellogg_1923_pictures_t3282/prairie_1800_1900_row_elevations.jpg`): its x 190-346, y 195-430 px, 156 x 235 px, sha256 `6a188ecf12322445de8c9a8621968131cd2d74be06183f548a87054051efa97e`; its camera is `data/reference_views/moulton_lowden_house_1912_prairie/elevations_c1914_front.json` |

**How they are used.** `node tools/photo_match.mjs data/reference_views/moulton_lowden_house_1912_prairie/<view>.json`
renders the committed GLB from that picture's camera beside it and writes the match record the image
gate reads. The plate's camera lands within a few metres of the photograph's, so the two are one view
of the house thirty years apart; the elevation is scaled by the 1912 front's own heights. Both draw
the lower storeys taller than the record builds them, which the match records carry as open.
