# 1900 Prairie, the Elbridge G. Keith house — reference copies for the image gate (T-3207)

One photograph of 1900 South Prairie Avenue in two prints: the Glessner House Museum's, captioned
"1900 PA" in its blog post "Elbridge Keith House" (3 November 2014,
https://glessnerhouse.blogspot.com/2014/11/elbridge-keith-house.html), and Chicagology's
(https://chicagology.com/chicagostreets/prairieavenue/1906prairie/), which captions the same
photograph as 1906 Prairie. Their source record is `data/sources/glessner_blog_1900_keith_oblique_photo.json`
(tier 1, photograph); the Prairie library lists them as `a19-gh-keith-1900-historic` and
`a19-cgy-1906-keith-photo`, both "link only". The copies here are the image store's
(kevinrhaas/chicago-images, `prairie-1904/files/<id>.jpg`), brought in with their attribution as the
owner directed on 2026-10-11 for the pictures the image gate builds against, as 1901's were
(`../ream_1901_photos_t1903/`).

**Rights: check_required.** Secondary web reproductions with no rights statement. Forms, counts,
places and proportions are read from them; nothing is derived from either image as an asset (no
texture, no traced mesh), and the copies are unaltered.

| file | what |
|---|---|
| `keith_1900_oblique_glessner.jpg` | the museum's print, 1294 x 974 px sepia, sha256 `2bf412a3d0369c7619b25c5da579805f71d07fdf90ea1442b8013627be8df755` |
| `keith_1900_oblique_chicagology.jpg` | Chicagology's print of the same photograph, 957 x 708 px greyscale, sha256 `7d053c5e4a01ac406e4152e83afd89e5798a923ca65c43ed954a05d236a1cc2e` |
| (camera) | `data/reference_views/elbridge_keith_house_1900_prairie/glessner_oblique.json`, solved from the museum's print and the 1911 Sanborn sheet's plan; its `solve` field says how and how far |

**How they are used.** `node tools/photo_match.mjs data/reference_views/elbridge_keith_house_1900_prairie/glessner_oblique.json`
renders the committed GLB from that camera beside the museum's print and writes the match record the
image gate reads. Chicagology's print is the same negative and is read only to confirm what the
museum's print shows; it takes no camera of its own. The house's later photographs (the mid-century
and 2024 fronts, the 1972 survey photograph, the c. 2014 detail) and the 1800-1900 elevation drawing
are T-3208's.

## The later pictures, weighed (T-3208)

Read from the image store, as evidence of their own dates, for what they confirm of the 1904 front.
None is copied into this repository and no camera is solved on any of them: their rights are link
only, and the oblique print governs what 1904 looked like.

| library id | date | what it adds |
|---|---|---|
| `a19-cgy-1900-keith-exterior` (top) | mid-century | a square-on front: the corner bay, the door and two window columns north of it, round-headed lights under hoods with carved crowns on both storeys, the arched PAIR over the porch, the arched dormers and the bay crown's dormer, the terrace on brackets over the basement lights, the block newels at the stoop's foot. Its lower picture is a print of the oblique negative this folder's camera is solved on, so it adds no view |
| `a19-cgy-1900-keith-2024` | 2024 | the same front in colour; modern paint, iron grilles in the principal lights and a stair rail, none of them 1904's |
| `a19-gh-keith-1900-exterior-modern` | c. 2014 | the upper front close: each hood's crown a foliate cartouche over a moulded architrave on consoles; the upper sashes follow the arches; the pair over the porch two round lights under one segmental head. The cornice is the one rebuilt after 1978 (the museum's post, `glessner_blog_2014_11_elbridge_keith_house`) |
| `a19-nrhp-keith-1972-photo` | 1972 | no file in the image store; only the library's summary is read (segmental heads, block newels, Corinthian porch), and nothing is built on it |
| `a19-gh-prairie-1800-1900-elevations` | c. 1914 drawing | each house about 100 px wide: a mansard front with dormers and nothing finer |

What T-3208 built from them and what stays open is written in the oblique view's match record
(`data/reference_views/elbridge_keith_house_1900_prairie/glessner_oblique.match.json`).

