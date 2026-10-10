# T-2267 — Glessner v4 regenerated without coincident faces (2026-10-10)

The K01 contract's measure (`node tools/k01_contract.mjs --measure`, T-2265) found
coincident triangles in the canonical Glessner v4 package: two triangles on the same
three points of the contract's 1 mm grid. This ticket found where each came from in the
generator, fixed the generator rather than the mesh, and rebaked.

| tier | before (package `eb00c3fc…`) | after (package `e32e94ff…`) |
| --- | --- | --- |
| full master | 15 | **0** |
| web (0.83 mm lattice) | 40 | 5, all quantization (below) |
| light (own reduced build) | 8 | **0** |

## Where they came from

Found by replaying the v4 construction in plain Python (the same `DetailBuilder`, with
Blender's emission stubbed) and matching each coincident GLB triangle to the `raw` face
that emitted it.

1. **Acanthus leaf roots and tips** (`masonry_house_v4_ornament.Relief.leaf`). The full
   master's six `limestone_trim` faces on the Prairie Avenue front. A blade's width runs to
   a floor of `.015**.68` of its width at t = 0 and t = 1. That is about 0.7 mm on a capital
   leaf, so the first and last rows were ten cells of 0.07-0.14 mm, each with a 10 mm
   closing strip. On the 1 mm grid they fold onto one another (the entrance fan's
   tympanum, 3.36-3.55 m). Where four capital leaves fan from one root point (45°, 135°,
   225°, 315°, ledge at 7.50 m), one leaf's root strips lie on another's. **Fix:** the
   root and tip rows close on the midrib. Their cells become triangles, and a closing strip
   whose edge has collapsed is not emitted.
2. **Ridge barrels that run on into each other** (`masonry_house_v4_roof_edges.add_ridges`).
   The full master's nine `roof_plane_1`/`roof_plane_2` faces at x = 11.54 m. Two ranges
   carry the same east-west ridge line (`at` 18.105 m, `z` 10.394 m): one stops at
   11.5397 m and the next starts there. Each closed its barrel with a cap in that one
   plane, back to back. **Fix:** where one run ends exactly where another on the same line
   begins, neither cap is emitted, so the barrel continues through the joint.
3. **Chimney flashing pieces that meet at the main ridge**
   (`masonry_house_v4_roof_edges.add_abutments`). The light tier's eight `copper` faces at
   x = 45.11 m. A chimney wall's apron is split where it crosses the ridge. Consecutive
   pieces share one section at the joint (the same t samples the same roof), and each
   closed it. **Fix:** pieces that meet are not capped where they meet. In the full master
   the same code happened not to produce an exact match.

Triangles: full 1,220,197 → 1,209,879; light 199,744 → 198,064 (the 200,000 ceiling is
kept). Download: web 52,071,720 → 51,933,560 bytes, light 27,014,548 → 27,001,116.

## The web tier's five

All five are back to back on `limestone_trim`, at the roots of the fan's sill leaves and
one capital-scroll leaf. Each is a sliver whose shortest edge is at most 1.9 mm: vertices
either side of a leaf's midrib that the web encoding (int16 under a 27.19 m node scale,
0.83 mm a step) rounds onto one lattice point. The web tier is the master re-encoded. It
carries the master's 1,209,879 triangles one for one, and the master has none at 1 mm. So
the five are the lattice's, which is what the ticket's acceptance allows ("their remainder
is explained by quantization alone").

The verdict now states that condition instead of taking it on trust
(`coincidentVerdict` in `tools/k01_contract.mjs`, and the contract's `coincident_rule`).
The master must have none. A derived tier must have none, or have quantized positions
and the master's triangle count, in which case its remainder is written into the
baseline under `quantization` with its position step and largest sliver edge. Light is
built separately (`tools/_glessner_lod.py`), so light may keep none. Six new self-test
cases cover the rule (master refused, not one-for-one refused, unquantized refused, light
refused, the explained case and the step read from a synthetic int16 GLB).

A tighter rule was tried first and dropped: "every member triangle has an edge within
two steps". It fitted 3 of the 5. Widening its threshold until it fitted would have been
tuning a gate to pass.

## Fixed-camera views

`PW_EXECUTABLE=/usr/bin/chromium QA_OUT=<dir> node tools/qa_glessner_t2267.mjs` loads the
published `/1904/` app (desktop 1280×800 Full, mobile 390×780 Light) and holds six
cameras. Four are close up on the repaired places: the entrance fan, a porch capital, the
ridge joint and the chimney flashing. Two are the T-2205 overall silhouettes. The
*before* set ran on dev's package (`eb00c3fc…`), copied into the same published tree.
Both runs pass, with zero page errors, zero failed requests, dark glass and every stand
within budget.

Pixel difference, before → after ([pixel-diff.json](pixel-diff.json), threshold 8/255):

| view | desktop | mobile |
| --- | --- | --- |
| entrance fan | 445 px (0.043 %), all on the fan's leaves | 66 px |
| capital | 214 px (0.021 %), all on the capitals | 42 px |
| ridge joint | 3 px | 4 px |
| chimney flashing | 0 | 0 |
| northeast | 5 px | 2 px |
| courtyard | 2 px | 0 |

The changed pixels sit at leaf roots and tips ([fan](diff-desktop-entrance-fan.png),
[capital](diff-desktop-capital.png), amplified ×8). Nothing else in the house moved:
the hidden caps and flashing ends were inside continuous stock, so their views are
unchanged.

| View | Before | After |
| --- | --- | --- |
| Entrance fan | [Full](before/desktop-entrance-fan.png) · [Light](before/mobile-entrance-fan.png) | [Full](after/desktop-entrance-fan.png) · [Light](after/mobile-entrance-fan.png) |
| Porch capital | [Full](before/desktop-capital.png) · [Light](before/mobile-capital.png) | [Full](after/desktop-capital.png) · [Light](after/mobile-capital.png) |
| Ridge joint | [Full](before/desktop-ridge-joint.png) · [Light](before/mobile-ridge-joint.png) | [Full](after/desktop-ridge-joint.png) · [Light](after/mobile-ridge-joint.png) |
| Chimney flashing | [Full](before/desktop-chimney-flashing.png) · [Light](before/mobile-chimney-flashing.png) | [Full](after/desktop-chimney-flashing.png) · [Light](after/mobile-chimney-flashing.png) |
| Street silhouette | [Full](before/desktop-northeast.png) · [Light](before/mobile-northeast.png) | [Full](after/desktop-northeast.png) · [Light](after/mobile-northeast.png) |
| Courtyard silhouette | [Full](before/desktop-courtyard.png) · [Light](before/mobile-courtyard.png) | [Full](after/desktop-courtyard.png) · [Light](after/mobile-courtyard.png) |

These are SwiftShader captures, not a hardware benchmark.

## Reproduction

The pinned Blender 4.5.3 built only Glessner with
`generators/build.py -- --only glessner_house --no-bake`, then
`tools/web_derivatives.sh --only glessner_house__as_built_1887.glb` produced web and
light and repacked the recovery package ([bake](bake.log),
[derivatives](derivatives.log)). The three legacy comparison versions (pre-v4, v2, v3)
were rebuilt by that bake without their ordinary UV unwrap. Their inputs hash did not
change, so their committed masters, web copies and `manifest.versions.json` entries were
restored byte for byte instead of re-derived. Then `node tools/k01_contract.mjs
--measure` re-measured the baseline. `tools/check.sh`: 808 steps, none red.
