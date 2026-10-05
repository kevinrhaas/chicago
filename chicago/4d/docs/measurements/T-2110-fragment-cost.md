# T-2110 — what trees and the ground pay per fragment, and a cheaper tree that draws the same picture

Read 2026-10-04 on dev @ 07a28a03, published mirror, with `tools/measure_still_frame.mjs`
and its two new switches: `--probe` (each layer drawn alone as shipped, then with a cheaper
material swapped onto its meshes, then the whole frame with that layer drawn last) and
`--capture dir` (each row's frame written as a PNG). Raw rows: `t-2110-fragment-cost.json`.
SwiftShader again, so **read the milliseconds as shares** (T-2099-still-frame.md § the
method). Phone = 390x780 at dpr 3, touch, CPU throttled 4x, `light`; desktop = 1280x800,
`full`. Zero page errors in every run.

## 1. Whose milliseconds inside the two layers

T-2099 found trees (30–38 %) and terrain (18–28 %) the costliest layers in 1835. Each
was drawn alone and then with a variant that changes ONE thing. The variants that draw a
different picture are there to price a piece, not to be shipped.

**Trees**, drawn alone (ms over an empty frame):

| variant | phone `light`, back yard | desktop `full`, the forks |
|---|---:|---:|
| as shipped (before) | 1312 | 4398 |
| bump map off | 911 (−31 %) | 3092 (−30 %) |
| Lambert instead of Standard, same cut-out | 595 (−55 %) | 1993 (−55 %) |
| unlit, same cut-out (the floor) | 326 (−75 %) | 1051 (−76 %) |

Three quarters of what a tree costs is fragment shading, not the cards' cover. The bump
alone is 30 %. It reads the atlas three times more per fragment (three.js's `dHdxy_fwd`),
and on a **leaf card** `patchTreeWind` keeps only 3.5 % of the normal it bends. So
almost all of that 30 % buys nothing a visitor can see. The physical light model (GGX
over Lambert) is the next quarter, and replacing it would change the picture: the
leaves would lose their faint sheen. That is not done here.

**Terrain** (the ground mesh), drawn alone:

| variant | phone `light`, back yard | phone `light`, from above | desktop `full`, the forks |
|---|---:|---:|---:|
| as shipped | 1144 | 1393 | 1984 |
| no turf (empty turf box) | 1010 (−12 %) | 1400 (0 %) | 1733 (−13 %) |
| lit plain, none of the ground's own chunks | 658 (−42 %) | 927 (−33 %) | 1060 (−47 %) |
| unlit plain (the floor) | 261 (−77 %) | 353 (−75 %) | 321 (−84 %) |

The ground's own GLSL (prairie tile, sward grain and its normal, two substrate zones,
turf) is a third to a half of its cost, and lighting is most of the rest. The turf chunk's
eight value noises cost 12–13 % where the turf mask covers the screen, and nothing from
the air, because the box test skips them. No single piece of the prairie or sward chunk
stands out the way the trees' bump does. Their cost is spread across three `sin`s, two
texture fetches and four `normalize`s, and none of those can be dropped without changing
the ground. **No same-picture saving was found in the ground shader this run.** What is
left there is a design choice: bake the turf noises into a texture, or light the ground
with Lambert. Each changes the picture slightly, so each would go to the owner first.

**Draw order is not the leak.** The whole frame was redrawn with trees, then terrain,
sorted after every other opaque thing, so that covered fragments fail the depth test
before shading. It moved the frame by under 0.5 % at every stand read, and by zero
pixels. Overdraw from sort order is not where these layers lose time.

## 2. The fix: no bump on a leaf card

`renderers/web/js/tree-surface.js`: the bump is computed only where `aLeaf` is 0 (bark).
`aLeaf` is 0 or 1 for a whole card, so the branch is uniform across every triangle and
the bump's screen-space derivatives stay defined. Bark keeps its full bump.

| | before | after | change |
|---|---:|---:|---:|
| trees alone, phone `light`, back yard | 1312 | 1153 | −12 % |
| trees alone, desktop `full`, the forks | 4398 | 3805 | −13.5 % |
| whole frame, desktop `full`, the forks | 12447 | 11775 | −5.4 % |
| whole frame, phone `light`, back yard (Medium) | 4488 | 4356 | −2.9 % |
| whole frame, phone `light`, from above (Medium) | 3773 | 3633 | −3.7 % |
| whole frame, phone `light`, the forks (Medium) | 3423 | 3564 | +4 %, see below |

The forks phone row read slower after the fix. That reading's CPU submission jumped from
26 ms to 206 ms, a throttled-CPU stall, and the same stand at Low read 1.6 % faster. Its
layer-alone reading and every other row went the other way. Treat it as noise and
re-read it if a later run doubts it.

**The picture does not move.** Before and after frames compared pixel for pixel:

| frame | pixels that differ | most a channel moves (of 255) |
|---|---:|---:|
| desktop `full`, the forks | 0.017 % | 1 |
| phone `light`, from above (Low / Medium) | 0.10 % / 0.10 % | 2 / 1 |
| phone `light`, the forks (Low / Medium) | 0.004 % / 0.004 % | 1 / 1 |
| phone `light`, back yard (Low / Medium) | 0 | 0 |

## 3. Image sharpness on the phone: put to the owner

| phone `light` | Low (pixel ratio 1) | Medium (1.5, today's default) | Low saves |
|---|---:|---:|---:|
| the forks | 2562 | 3564 | 28 % |
| T-2084's back yard | 3222 | 4356 | 26 % |
| from above | 2563 | 3633 | 29 % |

The same frames side by side are in `t-2110-sharpness/phone-light-low-medium.jpg`. Low is
softer on the cabin's log courses and on the town's roofs from the air. That is visible,
and the default is the owner's call, asked on the ticket. A visitor can already choose
it in Settings → Image sharpness.

## Read it again

    node tools/measure_still_frame.mjs --only mobile --tiers light \
      --stands town_backyard,from_above --probe --frames 3
    node tools/measure_still_frame.mjs --only desktop --tiers full \
      --stands the_forks --probe --frames 2 --capture /tmp/frames
