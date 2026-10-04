# T-2099 — what a still frame costs, at every stand, tier, viewport and year

Read 2026-10-04 on dev @ 82087b96, published mirror, with `tools/measure_still_frame.mjs`
(new). Raw rows: `t-2099-still-frame.json`. Clock held, loop stopped, frames driven by
`step()` and fenced by a one-pixel `readPixels`, the `measure_shrub_frame_cost.mjs` method.
Medians of 2 timed frames after 2 settle frames (worst = median throughout: the spread is
under 1 %).

**Read the milliseconds as SHARES.** The runner draws through SwiftShader, a software
rasteriser (`ANGLE … SwiftShader Device (Subzero)`), so a frame here takes seconds; a phone
GPU is one to two orders faster. Headless desktop boots as low-spec (PCF shadows). The
phone stand-in is 390x780 at device pixel ratio 3, touch, Image sharpness Medium (pixel
ratio 1.5), CPU throttled 4x after boot.

## 1. The table: frame ms (cpu ms) — every 1835 stand, every tier

| stand | desktop full | desktop balanced | desktop light | phone full | phone balanced | phone light |
|---|---:|---:|---:|---:|---:|---:|
| landing | 7435 | 6496 | 4389 | 5559 | 4638 | 3179 |
| sauganash_26 | 7716 | 6701 | 4430 | 5724 | 4862 | 3388 |
| lake_at_canal | 9366 | 7859 | 4874 | 6924 | 5876 | 3428 |
| the_forks | 11091 | 8242 | 4843 | 6707 | 4953 | 3155 |
| lake_and_market | 7791 | 7362 | 4890 | 4790 | 4565 | 3106 |
| prairie_west | 10113 | 7996 | 5156 | 7368 | 5745 | 3611 |
| **town_backyard** | **13487** | **10416** | **6552** | **9577** | **6963** | **4164** |
| town_lake_shoulder | 7752 | 7031 | 5320 | 4865 | 4332 | 3258 |
| town_south_water_store | 9155 | 8524 | 6419 | 5749 | 5087 | 3824 |
| from_above | 12399 | 9261 | 5260 | 8900 | 6300 | 3589 |
| cpu (submission), range | 4.5–7.4 | 4.6–7.1 | 3.6–5.2 | 18–29 | 21–27 | 15–22 |

Other years, at the stand each lands a visitor on:

| landing | desktop full | desktop balanced | desktop light | phone full | phone balanced | phone light |
|---|---:|---:|---:|---:|---:|---:|
| 1812 | 3373 | 2961 | 2495 | 2286 | 1969 | 1642 |
| **1904** (Glessner) | **15421** | **8904** | **8862** | **11418** | **5728** | **5746** |

**The worst still frame in the project is 1904's landing**: 15.4 s at desktop `full`
(3.35 M triangles, the full inspection model) and, more tellingly, 8.9 s at desktop
`light` on only 719 k triangles — 12 ms per thousand, against 6 ms at 1835's worst.
**In 1835 the worst stand at every tier and viewport is T-2084's back yard** on
Washington and Wells. CPU submission is never more than 0.7 % of a frame here, even
throttled 4x: on this evidence the still-frame cost is raster (fill, fragment shading,
vertex work), not draw-call count.

## 2. Whose milliseconds: each layer drawn alone, each pass priced against the whole

1904 landing, `light` — **the glass's transmission pass is half of every frame**:

| | desktop ms | % | phone ms | % |
|---|---:|---:|---:|---:|
| whole frame | 8890 | | 5761 | |
| structures | 4793 | 54 | 3193 | 55 |
| **(transmission pass)** | **4594** | **52** | **2950** | **51** |
| terrain | 1437 | 16 | 868 | 15 |
| street-grid | 575 | 6 | 331 | 6 |
| (shadow map render) | 95 | 1 | 104 | 2 |

The Glessner house's GLB carries `KHR_materials_transmission` on two glass materials
(both the full and the `.light` model). Any visible transmissive material makes three
draw every opaque object a second time into a target the glass samples — 36 calls and
about 265 k triangles more — which is why this frame costs MORE than its layers drawn
alone (whole 5761 against parts 4435 on the phone).

1835, T-2084's back yard, phone `light` (4209 ms) and the forks, desktop `full` (11116 ms):

| layer | phone light ms | % | ms / k tri | desktop full ms | % | ms / k tri |
|---|---:|---:|---:|---:|---:|---:|
| trees | 1246 | 30 | 6.0 | 4258 | 38 | 7.4 |
| terrain | 1159 | 28 | 7.7 | 1947 | 18 | 8.4 |
| structures | 574 | 14 | 4.4 | 1287 | 12 | 4.3 |
| yard (goods) | 429 | 10 | 44 | 205 | 2 | 1.2 |
| frontage | 413 | 10 | 2.6 | 1020 | 9 | 2.1 |
| streets | 172 | 4 | 1.6 | 427 | 4 | 2.8 |
| flora | 8 | 0 | — | 1279 | 12 | 7.9 |
| (shadow map render) | 40 | 1 | | 407 | 4 | |
| (soft shadow filter, PCFSoft over PCF) | −25 | 0 | | −37 | 0 | |

Parts alone sum to within 1 % of the whole in 1835 (4234 / 4209; 11155 / 11116), so
overlap does not distort these shares. Trees and terrain are the two costliest layers per
triangle — alpha-tested foliage and the per-fragment ground shaders. The yard's 44 ms per
thousand is the pose, not a shader: a yard good stands close in front of that eye.
Shadows are cheap everywhere read: the shadow map's own render is 1–4 %, and the soft
filter costs nothing measurable.

## 3. Image sharpness on the phone (`light`)

| stand | pixel ratio 1 | 1.5 (default) | 2 |
|---|---:|---:|---:|
| town_backyard | 3141 | 4196 | 5686 |
| from_above | 2515 | 3603 | 4855 |

Medium → Low takes 25–30 % off the frame; that is visible, and the owner's call.

## What this reading leaves for the next piece

1. **1904's transmission pass** — the largest single cause the table names, half the
   frame at both viewports. Replacing it costs something a visitor can see (the glass
   stops refracting), so it goes to the owner with before/after captures.
2. The phone's default Image sharpness (25–30 %), also visible, also the owner's.
3. Trees and terrain fragment cost in 1835 — the largest causes there; a cheaper shader
   that draws the same picture needs reading at the source.
4. Not read here: the arrival screen and a jaunt view. A still-frame ceiling per tier is
   not yet held.
