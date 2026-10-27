# 1834 Prairie, the Fernando Jones house, onto K01 from its photograph (T-3183, piece 1 of T-1888)

The district draft (T-2329) stood 1834 up as a three-storey box from the 1911 sheet's trace. This
refines it in place, under its own id `jones_house_1834_prairie`, as a `k01_frontage` record read off
the one photograph of the house against the sheet. Liberty: `L-k01-1834-jones-1888`.

## The picture, and why it is turned round

One undated photograph from before the mansard storey of 1886, in two prints of one negative: the
Chicagology print (`chicagology_1834_jones_photo`, 1200 x 900 px) and the Glessner House Museum blog's
(`glessner_blog_2015_08_van_osdel`, 675 x 506 px, the same framing at 0.5625). Both are committed
unaltered at `data/sources/assets/jones_1834_photos_t1888/` (rights check_required: forms, counts,
places and proportions only).

Both prints show the flank with the canted bay to the LEFT of the front. Two readings were fitted to
the same observations (the front's two corners, the wall head, water table and grade at both, the
bay's junction, the flank's one upper window's 0.9 m sash):

| reading | camera | the bay on the sheet | flank window | principal point | cost (px^2) |
|---|---|---|---|---|---|
| as printed | south-east of the house | south flank, u 0-5.45 — the sheet draws a straight wall there | 2.5-3 m wide | x 1905 (off the print) | 31.8 |
| turned back | north-east, across Prairie Avenue (the Prairie library's own caption) | north flank, u 8.5-13.3 — the sheet draws a bay there | 0.9 m | x 509 (near the middle) | 5.6 |

So the print is laterally reversed. The cameras (`data/reference_views/jones_house_1834_prairie/`)
carry `mirrored: true`, which T-1888 adds to `tools/photo_match.mjs`: their pixels are the picture
turned back, and the side-by-side shows the committed copy turned back.

## What the camera reads

Eye at u 55.07, v 23.79 (about 33 m before the front and 14 m north of the north wall), 1.0 m over
the house's grade, yaw -118.64, f 2313 px, principal point (508.5, 725.1), level. Through it:

- the water table (principal floor) 2.2 m, the second floor about 6.15 m, the wall head 9.75 m;
- four columns at 1.18, 3.50 (the door), 5.88 and 8.37 m from the south corner of the 9.58 m front;
- principal windows about 0.95 m wide, 3.0-5.25 m; upper about 0.9 m wide, 6.85-9.0 m; the door's
  hood top about 5.6 m;
- the old roof's cornice top 10.85 m, centre gable apex 12.1 m, oculus 10.4 m (before 1886);
- the north flank: blank for 5.9 m, a window a storey at s 6.6, the round-headed pair at s 9.0-10.2,
  the bay from s 9.0, about 3 m long, its top 5.7 m.

## What changed (same camera, before and after)

- `before-t3183-chicagology_photo.jpg`: the draft from this camera.
- `../photo-match/jones_house_1834_prairie/chicagology_photo-side-by-side.jpg`: the K01 house.

## Kit changes (T-1888, additive)

- `entrance_bay` may name a bay's number (1 the southmost), for a front entered in an inner bay that
  is not its middle one. Every existing record names south, north or middle and is unchanged.
- `stone_front.brick_above_m` may stand at the principal floor: a stone basement under a brick front.
  `street_front_round_heads` then cuts its windows in that brick.

## Open for T-3184

The door's hood; the iron balconettes; the stoop's iron railings; the second-floor belt K01 lays and
the print lacks; the north flank's stone basement; the wall's end at the bay; the bay's round-headed
lights and bracketed top; the cornice's depth; the basement lights' round heads; the walk's opening in
the stone wall. Both match records list them.
