# Glessner granite faces, colour and the Prairie door (T-2416, T-2215)

The owner, 2026-10-12, with six photographs of the north wall and the Prairie Avenue door:
the stones are "shaped almost with a bow in the front, not a ton", the faces "stand out from
the face a bit", the door arch "has the same stone treatment and should stand out more", the
detail over the door should match the close-up photographs, and "the color of the granite
stone facing is not as grey as you have it". His photographs are his own references and are
not copied here.

`before/` and `after/` are the published 1904 app, desktop, from the same seven stands
(`node tools/qa_glessner_stone.mjs`, cameras in that file). `after/` is the rebaked model.

What changed is recorded in LIBERTIES as `L-glessner-stone-faces-2416`.

Colour, read from the app's entrance-front view against the owner's colour photograph of
the same door (mean of lit wall stone either side, sRGB):

| | r/g | b/g |
|---|---|---|
| before (app) | about 1.00 | about 1.00 |
| after (app) | 1.08-1.11 | 0.92-0.94 |
| owner's photograph | 1.10-1.11 | 0.92 |

The hue now matches. The app's stone is darker than the photograph because the east face
gets only grazing sun at the scene's noon, not because of its albedo.

The north wall stands in shade in the 1904 scene's July noon light, so its bow reads only
faintly in the app; under a raking sun (a neutral review render of the GLB with a
north-west sun, `tools/photo_match.mjs` on a scratch camera) every stone's crown reads.
