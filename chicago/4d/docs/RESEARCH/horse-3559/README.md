# The photographic horse against its cleared views (T-3559)

The driven horse (`renderers/web/transport/driven/horse-current26-inplace-full.glb`,
sha256 `ad9dc060…1ec6`) was rendered at the cameras of the two cleared reference views
the standing horse was made from, and read beside them:

| View | Reference (cleared) | Camera |
|---|---|---|
| Three-quarter front | `joselodos_2025_horse_anatomy` — Joselodos, *Horse posing in the grass*, 1 May 2025, Wikimedia Commons, CC0-1.0 | 4 m off the near fore, eye at 1.3 m |
| Profile | `vassil_2014_konik_horse_anatomy` — Vassil, *Konik Polski, Solutré, 26 Oct 2014*, Wikimedia Commons | 6 m square to the near side, eye at 1.2 m |
| Front | none cleared | (front, chest and leg spacing read from the render alone) |

Both references are living modern horses (a bay, a dun konik), not Chicago horses; they supply
qualitative anatomy, coat and hair, never dimensions (their source records say so). The source
records are `data/sidecars/1835/sources/<id>.json`. Evidence pictures are in
kevinrhaas/chicago-evidence under `evidence/horse-riding-3559-3560/`.

## The register

| # | Part | What the views show | The horse before | Now |
|---|---|---|---|---|
| 1 | Bay points | A bay's mane, tail and lower legs are black (the joselodos bay, below the knee and hock). | The bay and dark-bay coats painted the whole leg and the mane the body's brown. | **Resolved.** `points_linear_rgb` darkens below 0.42–0.56 m (the knee and hock), blended over 4 cm; the mane and tail take the palette's near-black mane colour. Chestnut, grey and others unchanged (`data/transport/horse-coats.recipe.json`). |
| 2 | Hair paint mask | The whole mane reads dark on a bay. | Only the darkest third of the mane cards took the mane colour; the light strands stayed brown. | **Resolved.** The mask now takes every strand below 70 % luminance. |
| 3 | Body silhouette | Barrel, croup and neck crest of a light-draft horse; the konik is shorter in the leg. | Matches the profile's proportions within the difference between the breeds. | **Kept**: the model is a heavier horse than either reference, which suits a town team. |
| 4 | Head, eye, muzzle | Dark wet eye, soft muzzle with nostril and chin. | The eye material reads dark and glossy; the muzzle reads with its nostril and darker skin. | **Kept.** |
| 5 | Mane volume | The konik's mane is thick and stands; the bay's lies heavy on the near side. | The mane is a few cards, thin at its crest and lighter than either. | **Listed.** A fuller mane needs new hair cards on the source mesh, a re-export of all three levels and a re-fit of the bridle; not done here. |
| 6 | Hooves | Dark horn on dark legs; pale horn under white socks. | Every hoof is a pale grey horn. | **Listed.** The hoof is one texture region; tinting it by sock would need a mask it does not have. |
| 7 | Feathering | Neither reference has heavy feather. | None. | **Kept.** |
| 8 | Far level at close range | — | The far level's 256-pixel maps read lighter and softer than the near ones when forced close. | **Kept**: it is drawn only beyond 55 m, where the difference is under a pixel. |

## The levels and the trot

- Near 17,390 triangles (3.46 MB GLB); mid 7,146 (636 KB, maps 512 px); far 2,142 (281 KB, maps
  256 px), from `tools/transport/horse_lods/export_horse_lods.mjs` with its receipt
  `data/transport/driven/current26-lods-receipt.json`. Each level carries the near horse's
  26 joints, inverse binds and material names, and rides the near clone's bones, so the coat,
  gait and tack are one. Through a trot cycle the far body's skinned bounds stay within 2.6 cm of
  the near's (`tools/test_horse_rig.mjs`): no pop at a swap. Swaps at 22 and 55 m with a 3 m band.
- Phones (horse maps capped) load the near horse and the far level only.
- The trot (`horse-trot-v1.json`, `tools/horse_walk_v2.mjs`): a 1.5 m cycle, diagonal pairs,
  0 mm stance slip and 0 mm stance lift over 256 sampled phases
  (`data/transport/driven/current26-trot-v1-hoof-domain.json`), inside the walk's certified
  support domain. The walk is the delivered clip, unchanged.
