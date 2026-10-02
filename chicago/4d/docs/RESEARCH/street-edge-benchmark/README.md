# The street edge against the photographic benchmark — T-1815

Piece 3 of 3 of T-1211. The plank walks, crossings, stoops, mounting blocks, tie rails, wagon
aprons and hitching posts that `renderers/web/js/frontage.js` lays, reviewed in the **published
browser output** at 390×780 and 1280×800 against the promoted Glessner v4 baseline, before and
after one change. The change is in the renderer only: no record, generator or GLB moved.

## How the captures were taken

`node tools/street_edge_review.mjs <mirror-root> <out> --tag before|after` serves a published
mirror (`site/` after `./tools/publish.sh`; the before tree is the same publish taken from `dev`
at `78175dfd`). It opens `/4d/walk/?year=1835` at Full detail, holds the animation clock, hides
the chrome, and shoots four fixed stands at the walker's eye height, reading
`__chicago4d.stats()` on each frame and the layer's own triangle total. Every pair below is the
same stand, camera, sun and exposure (12:30, 1 July 1835, `world.js`'s own rig). Left is before,
right is after. Zero page errors and zero console errors on either tree at either viewport.

| stand | what is in it | desktop | mobile |
|---|---|---|---|
| `lake-trades` | Lake Street at Dole's, looking south: Dole's forwarding wagon apron, Mason's smithy (bare ground and a tie rail), the walk | [lake-trades-desktop.jpg](lake-trades-desktop.jpg) | [lake-trades-mobile.jpg](lake-trades-mobile.jpg) |
| `lake-close` | Dole's wagon apron from 3 m, pitched down onto the boards | [lake-close-desktop.jpg](lake-close-desktop.jpg) | [lake-close-mobile.jpg](lake-close-mobile.jpg) |
| `tavern` | across Lake to the Mansion House: crossing, mounting block, stoop, hitching posts | [tavern-desktop.jpg](tavern-desktop.jpg) | [tavern-mobile.jpg](tavern-mobile.jpg) |
| `store-stoops` | down the walk on Lake's south side at the store row (east 592–604 m): walk, string piece, two store stoops | [store-stoops-desktop.jpg](store-stoops-desktop.jpg) | [store-stoops-mobile.jpg](store-stoops-mobile.jpg) |

[against-glessner-v4.jpg](against-glessner-v4.jpg) puts the after crossing from the `tavern`
stand beside Glessner v4's own close capture (`1835-fabric-proof/desktop-glessner-close.jpg`,
the promoted 1904 default under the same `world.js` light).

## What was wrong before, read off the before frames

1. **White timber at every business door.** T-1800 took the walks off the signboard tone, and the
   fittings and hitching posts stayed on it (`TIMBER`, L\* 78.7). In `lake-close` Dole's wagon
   apron is the brightest surface in the frame. In `tavern` the Mansion House stoop and its posts
   read as painted white. The owner's plank-colour correction (2026-09-30) was still unmet there.
2. **No surface.** Every board was one flat colour with no grain, no end grain and no roughness
   change, so at 2 m a deck read as grey card cut into strips.
3. **Crates for steps.** A stoop or mounting block step was one solid box. It had no tread, seam
   or nosing, so nothing cast a line down the riser and the step did not read as a step.
4. **Floating at the foot.** The string pieces and posts reach the ground, but at the shadow map's
   texel size their feet showed no contact. They read as set on the mud, not in it.

## What changed

| defect | correction | Glessner v4 method |
|---|---|---|
| white fittings and posts | the walk's four weathered tones (L\* 33–62), keyed on the business each one serves (`inOwnerTone`) | **adapted**: restraint by tint, not by a second map (four kilns, one clay) |
| no surface | the library's `clapboard_board_face` bound to the layer's one material: `normal_gl` relief, `orm` roughness and AO, and the basecolor's luminance ratio as albedo modulation at 0.65 strength | **reused**: original seeded PBR, metric scale, relief and colour from one recipe |
| grain direction | a metric UV laid per box face, `u` along the box's **longest** side, so the grain runs across the walk on a deck board, along it on a string piece, and up a post | **adapted**: Glessner's metric UV survives export. Here the layer lays the boxes, so it can also know the grain axis that the fabric proof's shader could not (its defect 4) |
| tile repeat | each board starts the 4.48 m tile at its own seeded offset | **adapted**: Glessner breaks the period with two repeat rates. One rate plus a per-board offset does it here without a second sample |
| board ends | end-grain faces at 0.72 of the face | new; the end grain is geometry already, and this gives it its own tone |
| no contact | the foot of every upright face darkened by up to 40 % (14 % on a post) | new, as a vertex term. Glessner's contact comes from its shadow map, which reaches this timber only at the coarsest scale |
| crate steps | carcass set back 0.03 m under a tread of 0.2 m boards with 0.012 m seams | **reused**: shape is geometry, surface is map. The seams and nosing are boxes, and no map draws a joint |

**Rejected.** `plank_walk_weathered` as the substrate: its map draws eleven board seams across 4 m,
so on modelled boards the seams double up (the fabric proof's `courses-close` finding).
Glessner's per-building texture sets were also rejected: this layer is one material for the whole
town, and that is how it stays at zero added draw calls. Normal-mapped bevels were rejected
because a normal map cannot change a silhouette. The arrises stay square (see below).

## The critique, read off the after frames

- **Colour.** No white timber remains at any stand. The apron, the stoops and the posts sit in the
  same grey-brown family as the walks beside them. Neighbouring businesses differ by a tone step,
  not by a hue. Under the store row's own shade the stoops read blue-grey. That is the sky light,
  and the boards' albedo is unchanged there.
- **Grain and scale.** At 2–4 m the crossing boards show grain along their length, a few drying
  checks and broad weathering across each board. No two neighbours carry the same figure. At
  10 m and beyond the grain becomes tone, as it should. No 4.48 m period is visible down the
  `store-stoops` walk.
- **Joinery and depth.** Each stoop and mounting block step now has a tread line and a nosing
  shadow, and the seams between tread boards read at 3 m. Board ends and the dark gap under each
  board (its underside, at 0.5) give the deck depth where before it was a flat print.
- **Contact.** String pieces, apron planks and stoop carcasses darken toward the mud. They read as
  bedded, not pasted on. Posts darken only slightly, which is right at their height.
- **Shimmer.** Anisotropy is 8 and the colour map is mipmapped from full resolution, so the far
  walk shows no moiré in the stills. A walking capture was not taken.
- **Against Glessner v4.** Glessner's close granite still has richer surface response than any
  timber here: its rock face has real geometric relief and a 2048 px albedo. The street edge now
  matches it on the method: shape in geometry, metric seeded relief, tint restraint. **It does
  not yet match it on the arris.** Glessner models each stone's edges, and these boards are still
  sharp boxes. A rounded or worn top edge is real geometry: at about 8 more triangles for each of
  the layer's ~29,000 boxes it is roughly a quarter of a million triangles town-wide. That is a
  re-budget, and it is not spent here (see costs).

## Costs, measured

Desktop and mobile, Full detail, published mirror, SwiftShader. From `before-stats.json` and
`after-stats.json`:

| reading | before | after |
|---|---|---|
| the layer's triangles, town-wide | 345,598 | **349,174** (+3,576, +1.0 %; the treads) |
| the layer's meshes (= its draw calls at most) | 65 | 65 |
| draw calls at `lake-trades` / `lake-close` / `tavern`, desktop | 126 / 107 / 114 | 126 / 107 / 114 |
| frame triangles at the same three stands, desktop | 1,042,823 / 858,480 / 1,130,177 | +7,056 each (main and shadow pass) |
| textures resident | 25 | 28 |
| payload | — | +0.69 MB (normal 159 KB, orm 281 KB, basecolor 252 KB, sheet 1 KB) |

**Every tier.** The layer is not tiered: it lays the same geometry and binds the same material at
Full, Balanced and Light. So +3,576 triangles, or +7,152 counting the shadow pass, is an upper
bound on what this adds at any stand and any tier, and it adds no draw call anywhere. That
fits inside Balanced's 46,232 and Light's 52,975 triangles clear at their worst stands
(`1835_photographic_fabric_preparation.md` § 1). The smoke's ceiling legs hold all three tiers
to their limits. The GPU cost is three 1024² maps with mips, about 16 MiB. The modulation map
is built once at load from the basecolor, a single pass over 1 M texels.

`measure_detail_ceilings.mjs --against` over both trees did not finish inside one 600 s call, and
was not re-run in parts. The figures above stand on the layer's own count, not that sweep.

## Still owed (the stop condition)

*Every business front has the street edge its trade would have had.* That condition is T-1813's
and T-1814's deal. This piece judged the finish of what they laid, and it found no front without
its fitting at these stands. What stays open against the benchmark is the square arris (above)
and the fences and sign posts, which keep the signboard tone they share with the yard and the
signs (L320).
