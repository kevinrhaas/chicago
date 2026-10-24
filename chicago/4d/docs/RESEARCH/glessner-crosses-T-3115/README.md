# T-3115 — Glessner's 1886 crosses cut into the stack's rock

Found by T-3065 and carried on T-3028, which was split for it: the two crosses beside the 1886
stone on the 18th Street stack were dark quads drawn flat at `ROCK_FACE_MAX + 0.002` (0.106 m in
front of the stack's face). The rock at those two places reaches only about 0.06-0.08 m (T-3065,
the GLB's 90th percentile), so the strokes stood 2-4 cm proud of the stone round them. From Taylor
2135's north-east eye the west one stood about 2 px past the face's edge. HABS 14 shows them
incised.

**Acceptance, stated before the work:** every cross stroke lies on the stack's own rock face
(within a few millimetres of the stone beside it, never at the rock's furthest reach); Glessner
rebaked; every Glessner view re-rendered from the new GLB; HABS 14's crosses read against the
build.

## The change

`masonry_house_v4_detail.date_stones` now drapes each stroke on the faces already built. A new
helper, `_face_reach`, collects the faces standing within the rock's reach of the stack's plane
over the cross's patch, and returns the front-most face's offset at any point (by barycentric
interpolation). Each stroke is cut into 12 mm cells, and every corner sits 2 mm over that surface,
the same 2 mm the incised lettering stands over its stone. A point with no face in front of it (a
joint's gap) takes the patch's median reach. The upright is drawn as two arms either side of the
bar. The first bake drew it whole, and its 12 mm grid fell on the bar's own: 64 coincident
triangles (`k01_contract.mjs --measure`), now 0.

Nothing about the crosses' size, place or depth is newly claimed. A cut drawn as its shadow, a
matte near-black line, is the convention the 1886 and AD lettering already uses.

## Readings

| | before | after |
|---|---|---|
| strokes' offset from the stack's face plane | 0.106 m, flat | -0.010 to 0.077 m, following the rock |
| strokes in front of the rock beside them (nearest GLB vertex within 12 mm, n = 117) | 2-4 cm | median 1.4 mm, max 5.9 mm |
| Taylor 2135, west cross | about 2 px past the face's edge, in the sky | on the face (`taylor-before-after.jpg`) |

**HABS 14** (`habs14-crosses.jpg`) resolves each cross in about 10 px. The arms read about 9 px
across and 10 px tall, against the build's 11-12 and 9. That is within the print's 1-2 px at this
scale (about 18 px per foot), so the 0.6 ft size stands. The print's cuts read fainter than the
render's lines.

## Left for the pieces after this one

- **T-3116:** the crest against the fan. In this crop, HABS 14 puts the coping's junction with the
  stack about 13 px under the 1886 stone's foot, where the build meets it at the foot. That is a
  raw relative reading. T-3024 read the coping within 0.2 ft of sheet 6 through the
  crest-corrected camera, and the two have to be reconciled there.
- **T-3117:** the sign-off. Each match record's verdict is what it was before this bake. The
  render changed at the two crosses and nowhere else beyond pixel-level shading noise: the old
  and new side-by-sides differ by more than 40 grey levels at 0-197 px per view, all scattered.
