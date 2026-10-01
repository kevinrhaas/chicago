# T-1825 — the inland prairie's ground and sward: growth stands, before and after

Piece 2 of T-1820 (under T-1772). The ground and sward away from the lake, measured
on the published mirror at the critic rig's own stands, at 390×780 and 1280×800.

**Acceptance, as stated before the work.** One demonstration: the inland prairie's
ground tile and near sward carry coherent growth/thatch variation at the 0.5–3 m
scale Glessner v4's lawn study found missing from a uniform mat. The tile's mean
colour (the July measurement) and the sward's recorded heights, thatch minority and
tone must stay where they were. The draw calls, triangles and texture memory must
not move. Shown before/after at `prairie_west` (the open-prairie control) and
`public_square` (reserved sedge-meadow sward) at both viewports, with frame costs
and a written critique against the benchmark.

## What changed

1. **The ground tile** (`renderers/web/js/prairie-tile.js`). Two growth octaves
   now run across the 11 m tile, at 2.75 m and 1.4 m, on a seed of their own, so
   every texel the old octaves drew is drawn from the same values. Lush stands
   close up darker and bluer, and thin stands show last year's litter, with a
   speckle of bare loam inside the thinnest. The tile is then returned to the
   previous tile's mean, channel by channel: **mean sRGB 94.95, 107.22, 61.92
   before and after.** Luminance spread across the tile goes from SD 5.1 to 9.8.
   The substrate-zone albedo gate still reads 0.00 sRGB units of departure.
2. **The tile's repeat** (`terrain.js` `PRAIRIE_FRAGMENT`). The one fetch now
   happens after the community mosaic and is offset by it, by up to about 1.5 m.
   Neighbouring 11 m repeats therefore shear against each other instead of
   lining up in rows. This adds no fetch, no sine and no uniform. The ground
   strip imports the same fragment, so its feather still lands on the same
   ground.
3. **The near sward** (`flora.js`). A `vigourOf` field at 2.8 m and 1.4 m decides
   where in each record's OWN height range a near tuft stands (65 % field, 35 % its
   own draw). It also decides the tuft's tone (×0.86–1.14) and gathers the dead-thatch
   tufts into the thin stands (0–14 %). Over a 200 m square the field's mean is
   0.500, the thatch share 7.00 % (as before) and the tone 1.000. The mid ring's
   cards take the tone only. Their heights are untouched, because their outer
   edge is the boundary part 11 reads the sward's reach off.

## The numbers

Block-mean luminance spread over the lower 40 % of the frame (24 px blocks), the
near ground and sward:

| stand | viewport | before | after |
|---|---|---|---|
| prairie_west | 390×780 | 14.18 | 16.68 |
| prairie_west | 1280×800 | 18.19 | 19.16 |
| public_square | 390×780 | 8.42 | 8.33 |
| public_square | 1280×800 | 15.62 | 16.46 |

Frame cost, published mirror, `full` tier, SwiftShader (the runner has no GPU),
2 warm-up + 10 fenced frames, clock held. The two columns were taken back to back
on one machine:

| stand | viewport | before median | after median | draws | triangles | textures |
|---|---|---|---|---|---|---|
| prairie_west | 390×780 | 3409.9 ms | 3410.8 ms | 209 = | 1,367,428 = | 27 = |
| public_square | 390×780 | 2215.9 ms | 2220.5 ms | 169 = | 1,195,314 = | 27 = |
| prairie_west | 1280×800 | 5344.0 ms | 5348.3 ms | 225 = | 1,493,416 = | 27 = |
| public_square | 1280×800 | 4259.6 ms | 4251.6 ms | 180 = | 1,385,333 = | 27 = |

The differences are under 0.25 % in both directions, which is this instrument's
noise. The tile is still one 256 px texture, and the other tiers draw the same
material, so they pay nothing either.

## Critique against Glessner v4

What Glessner's lawn study taught was **coherent 0.5–2 m growth and thatch
variation instead of a uniform olive mat**, reference-led and at a metric scale.
That lesson carries over here, adapted. A prairie's stands are vigour and litter,
not mowing, so lush stands are darker and taller, and thin ones are lighter,
lower and show their thatch.

- **Better.** At `prairie_west` the ground between the tufts is no longer one olive.
  From 5 to 15 m it now reads as stands of closer and thinner growth, and the near
  tufts rise and fall together in patches instead of standing like a seedling crop.
  The 3×3 tile (`ground-tile-3x3.jpg`) shows no single feature that repeats as a
  glyph.
- **Still short of the photographs.** The July references show no ground at all at
  standing eye height; here the ground is still visible between tuft bundles (L32:
  the instance count is a budget, not a stem count). The tufts are still one
  archetype, and the mid-ring cards still stand at their drawn heights.
  The next gains are density and form, and both are frame-budget questions this
  ticket did not spend.
- **Not this ticket's, and seen.** At `public_square` a straight edge runs through
  the foreground where the roadbed meets the prairie. It is in the before frame
  too. Its sign flipped only because the prairie under it changed tone. The street
  section is T-1812's. The `prairie_south` stand now looks into a house on the
  south side, so it no longer measures open prairie. It was dropped here, and the
  critic rig's stand list should be revisited.

## Files

`prairie-west-390x780.jpg`, `prairie-west-1280x800.jpg`, `public-square-390x780.jpg`,
`public-square-1280x800.jpg` (before on the left or top, after on the right or
bottom), `ground-tile-3x3.jpg`. Captured with `node tools/critic_shots.mjs
--published --stations prairie_west,public_square` on dev 70f606b8 and on this
branch. All frames show reconstruction. No pixels come from a source photograph.
