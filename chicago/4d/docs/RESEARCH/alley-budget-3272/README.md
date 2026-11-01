# Down the 16th-18th west alley at Full, and Glessner's far roof relief (T-3284, piece of T-3272)

T-1932 read its desktop stand looking south down the 16th-18th west alley from 1616 Prairie's
rear (eye E 1331.2, N -2992, 1.7 m up; target E 1334, N -3015, 4 m up) at **8,049 draws /
6,055,451 triangles** against Full's 7,800 / 4,700,000. The same stand on dev 4674d8f9c reads the
same total to the triangle.

## What carries it

`QA_STANDS='[["alley-from-north",[1331.2,-2992,1.7],[1334,-3015,4]]]' node tools/qa_t3012_triangles.mjs`
(`triangles-before.json`), every draw charged to its layer and every structure range to its record:

| | total | view pass | sun's pass |
|---|---:|---:|---:|
| structures | 5,167,431 | 1,960,947 | 3,206,484 |
| of which **Glessner House** | **1,987,921** | 570,679 | **1,417,242** |
| railway | 352,330 | 324,958 | 27,372 |
| context city | 239,116 | 239,116 | 0 |
| street trees | 134,828 | 99,378 | 35,450 |

Glessner's lot centroid (E 1365.37, N -3229.04) is **240 m** from the eye: the house stands at
the alley's end and is drawn at its full inspection detail in both passes. Its sun's pass is the
whole house, and rightly by T-2529/T-3146's test: the July sun is in the south, so its shadow is
thrown toward this camera. `tools/measure_alley_t3272.mjs` hides each top-level layer in turn:
the street trees are **5,069 of the 8,049 draws** (driver multi-draw sub-draws) for 134,828
triangles. That is the draw overage, and it is not touched here.

Broken down by batch (`QA_FOCUS=glessner_house`), the roof's terracotta tile relief is the single
largest: three pieces, 275,527 triangles, drawn whole in BOTH passes.

## The change: far relief pieces draw as their crests (`renderers/web/js/far-roof-relief.js`)

T-2204's shader discards every relief fragment whose exposed course spans 6 projected pixels or
fewer; the courses are 0.127 m, so on an 800-pixel desktop the relief leaves no fragment past
about 14 m of depth. Each relief piece now carries a hidden twin holding only the triangles with a
corner whose course is not positive (crests, beds and every mixed triangle, which the shader
still decides as before), on the same vertices and material. In the colour pass, when the piece's
whole bounding sphere sits deep enough that `maxCourse x P / nearestDepth <= 6` (1% margin), the
twin is drawn in its place; otherwise nothing changes. The twin sorts and sphere-culls with its
piece's own sphere, because the transparent batch draws back to front by sphere and the pieces
meet at the ridge: the first build keyed the twin by its own sphere and changed 60 pixels at
Prairie front (40 m E), which this fixes. The sun's pass is untouched: its depth material draws
the relief whole, so taking it out there would change the shadow map, which is a different claim.

## Measured (published /1904/, desktop 1280x800, Full) — `tools/qa_t3272_far_relief.mjs`

Each stand renders the same held frame with the swap off and on and reads every pixel back; the
positive control renders it with the three relief pieces hidden outright.

| stand | off | on | saved | pixels differing | control (relief hidden) |
|---|---:|---:|---:|---:|---:|
| alley from the north (T-1932's) | 6,055,451 | **5,808,286** | 247,165 | **0** of 1,024,000 | 7 |
| alley from the south | 1,347,710 | 1,347,710 | 0 (culled anyway) | 0 | 0 (roof not on screen) |
| 18th, 150 m W of Glessner | 6,433,708 | 6,186,543 | 247,165 | 0 | 61 |
| Prairie, 60 m E / 120 m S | 7,789,182 | 7,542,017 | 247,165 | 0 | 0 |
| Prairie front, 40 m E | 4,260,648 | 4,013,483 | 247,165 | 0 | 1,844 |
| Prairie, 38 m E / 30 m S | 5,052,031 | 4,804,866 | 247,165 | 0 | 524 |
| elevated, 45 m E / 45 m N, 30 m up | 5,432,737 | 5,185,572 | 247,165 | 0 | 247 |
| over the roof, 12 m E / 18 m N, 16 m up | 3,903,301 | 3,903,301 | 0 (too close: no swap) | 0 | 6,017 |

Files: `browser-validation-desktop-{a..e}.json` (a: Prairie front; b: over the roof; c: both alley
stands; d: the two far stands; e: Prairie SE and elevated).

## What is still over, said plainly

The alley stand is still **5.81 M against 4.7 M, and 8,049 draws against 7,800**. And it is not
special: on today's dev, Full reads **6.43 M** from 150 m west of Glessner on 18th and **7.79 M**
from 120 m south-east on Prairie, and 5.05 M at T-3146's own Prairie SE stand, which that ticket
left at 4.49 M. What carries all of them is Glessner's inspection detail drawn at any distance
(1.42 M in the sun's pass alone) plus every neighbour south of the camera casting toward it. A
pixel-identical cut has no more to give there; what remains is a far-field level of detail for
Glessner in both passes, or a ceiling argued for far views, and either changes what a visitor
sees or what Full promises. That is T-3285, split off T-3272 beside this piece, not hidden here.

## Mobile proof (390×780, Full), added on the lap

`QA_VIEWPORT=390x780 node tools/qa_t3272_far_relief.mjs`, swap off against on, every pixel read back
(`browser-validation-mobile-mobile-a.json`, `-b.json`):

| stand | off | on | pixels differing | control (relief hidden) |
|---|---:|---:|---:|---:|
| alley from the north | 5,802,925 | 5,555,760 | **0** / 304,200 | 2 |
| Prairie front 40 m E | 3,761,269 | 3,514,104 | 0 | 837 |
| Prairie 38 m E / 30 m S | 3,915,870 | 3,668,705 | 0 | 226 |
| over the roof (too close, no swap) | 3,590,071 | 3,590,071 | 0 | 162 |

## T-3285: the sun's pass takes the swap too, and the far-view allowance

**What changed.** `far-roof-relief.js` now swaps each relief piece for its crests-only twin in
the sun's pass as well, on the SAME test taken from the VIEW camera (three hands it to
`onBeforeShadow`), so the sun leaves out exactly the noses the colour pass already discards.
In the sun's pass that is an LOD, not a proof: the depth material has no discard, so the
6 mm tile noses did reach the shadow map. With a 0.117 m texel and a 0.045 m normal bias
(world.js, `full`) they almost never shade anything, and the readback says where they did.
`buildings.farRelief.sun = false` keeps the sun's pass whole on its own, for the comparison.

`tools/qa_t3272_far_relief.mjs` now renders each held frame four ways: swap off; colour pass
only (T-3284's state); both passes (T-3285); and, as the sun's positive control, with the
relief batches casting nothing. The colour pass is still held to 0 pixels. The sun's swap is
held to 1 pixel in 10,000 (102 at 1280×800, 30 at 390×780). A stand whose roof is off screen
(hiding the relief changes no pixel, as T-3284's 'alley from the south' and 'Prairie 60 m E /
120 m S' already read) proves triangles only, and the tool says so instead of failing.

| stand (published dev 1d97db980 + this branch) | off | colour only | **both** | sun saved | px changed by the sun's swap | sun control (relief casts nothing) |
|---|---:|---:|---:|---:|---:|---:|
| desktop, alley from the north (T-1932's) | 5,921,288 | 5,674,123 | **5,426,958** | 247,165 | 0 | 2 |
| desktop, 18th 150 m W | 6,442,822 | 6,195,657 | **5,948,492** | 247,165 | 19 (max Δ 31) | 26 |
| desktop, Prairie 60 m E / 120 m S | 7,796,375 | 7,549,210 | **7,302,045** | 247,165 | 0 (roof off screen) | 0 |
| desktop, Prairie front 40 m E | 4,231,077 | 3,983,912 | **3,736,747** | 247,165 | 1 (Δ 1) | 1 |
| desktop, Prairie 38 m E / 30 m S | 5,210,050 | 4,962,885 | **4,715,720** | 247,165 | 0 | 0 |
| desktop, over the roof (too close: no swap) | 3,859,966 | 3,859,966 | 3,859,966 | 0 | 0 | 22 |
| mobile, alley from the north | 5,805,828 | 5,558,663 | **5,311,498** | 247,165 | 0 | 0 |
| mobile, 18th 150 m W | 5,729,937 | 5,482,772 | **5,235,607** | 247,165 | 6 (max Δ 5) | 24 |
| mobile, Prairie 60 m E / 120 m S | 7,500,011 | 7,252,846 | **7,005,681** | 247,165 | 0 (roof off screen) | 0 |

The 19 pixels at 150 m west are on Glessner's own roof (x 587-619, y 363-382): sixteen of them
1-7 levels, and one 3×3 spot up to 31 where a nose's shadow edge fell across a texel. 'Alley
from the south' has Glessner outside the sun's box and saves nothing (`-t3285-a`). Files:
`browser-validation-desktop-t3285-{a,b,c}.json`, `browser-validation-mobile-t3285-a.json`.

**What is still over, and the allowance argued for it.** Both swaps together take 494,330
triangles off every far stand, and Glessner's own detail is no longer what carries them. At
the worst stand (Prairie 60 m E / 120 m S) the structures' sun pass was 3.33 M before this
change, of which Glessner was 1.42 M and the neighbours 1.91 M. Every Prairie house inside the
240 m box is drawn whole into the shadow map whatever its distance (`qa_t3012_triangles.mjs`
breakdown, same stands). No pixel-safe cut is left there. The real fix is a far shadow level of
detail for structures, which is a renderer and GLB-contract question of its own. It is filed as
**T-3286** and named as this allowance's retirement.

Until it lands, Full declares what a far view of the district costs, by the rule every
re-basing in main.js follows (worst stand at either viewport + T-0672's absolute Full headroom,
rounded up to 5,000; draws: worst + about 5%, rounded up to 100):

- triangles: 7,302,147 (desktop, Prairie 60 m E / 120 m S) + 18,059 → **7,325,000**
- draws: 8,057 (desktop, the alley; 5,069 are street trees' sub-draws) → **8,500**

The 4.7 M ceiling and 7,800 draws are **not** raised. `stats().budget` and `withinBudget` still
hold every stand to them, because raising them would have lifted the guard off Glessner's close
stands and the spawn (3.7-4.7 M) to cover views it does not protect. The allowance is carried
beside them as `stats().farBudget` and read by `qa_t3272_far_relief.mjs`, which fails a stand
over it.

**Found, not fixed here:** Prairie 38 m E / 30 m S (T-3146's stand, left at 4.49 M) read
4,962,885 on today's dev before this change. This change brings it to 4,715,720, still 15,720
over 4.7 M. That growth came from parcels since T-3146, not from Glessner, and it is the same
sun-pass growth T-3286 is for. The elevated stand (45 m E / 45 m N, 30 m up) was not re-read
on this branch.
