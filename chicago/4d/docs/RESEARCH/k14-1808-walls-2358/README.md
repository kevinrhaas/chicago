# K14 on 1808 Prairie's walls: the house at its own age in 1904 (T-2358)

Piece 1 of T-2325 (package K14 of the T-1837 Prairie programme), which applies the K14 condition
kit (T-2324) to a named house. T-2325 was split on 2026-10-11, because the whole ask was more than one
run's demonstration: the yard has no ground surface to weather (T-2360), the roof's slate has no rows a
plume could ride (T-2359), and no K01 house built after 1886 stands to be the newer neighbour (T-2361).

## Acceptance (stated before work)

1. 1808 Prairie's record names the kit and a completion year, and its walls take their condition from
   the kit at that age. That covers the common-brick returns and rear, the K02 rock-faced front, its
   dressed trim and its stone bay: ground damp at the wall foot and the rusticated plinth, soot under
   the soffit, and a water trail below every K06 sill and behind every downpipe.
2. No other K01 house moves: `k01_emit.py --check` rebuilds every other K01 asset to its committed bytes.
3. The kit's numbers are used as they are, with no value of its own changed to make the effect read.
4. Verified in the published /1904/ app at 1280x800 (full detail) and 390x780 (light), at front,
   oblique, rear and two close stands. Both tiers carry the tone, and the costs are recorded. The
   house is compared with itself as it stood before: the K03 full-age mask on the brick and a clean
   stone front.

## What changed

The record (`keith_house_1808_prairie.json`, form `condition`) names the kit and `built: 1886`, the
register's Cobb & Frost date. On 1904-07-01 the house has stood 18 years, so every wall layer is at
0.45 of its full-age strength. K01 (`k01_frontage.py`) now does three things for a record that names
the kit:

- every weathering slot (the K03 brick slots, `rough_stone_trim`, `limestone_trim` and `bay_stone`)
  takes `_TONE` from `k14_condition.Condition.wall_tone`, evaluated once everything is laid
  (`Assembly.condition_tones`). Each vertex is read in the frame of the wall whose plane it is nearest,
  so a reveal, a sill or a bay weathers with its own wall;
- each wall's trail sources are its seated K06 sills (their proud extent, from the sill's underside)
  and its downpipes (from 0.15 m under the soffit, 0.03 m either side of the pipe);
- the brick walls are cut with the kit's rows (`wall_breaks`) and a column at each trail's edges,
  their soft fall-off and its centre, so the trails have vertices to ride.

A record without the attribute builds exactly as before. The attribute is refused on a brick-fronted
K01 house, because those cut their walls before the sills are seated (see T-2361).

| slot | before (K03, 40-year mask) | after (K14, 18 years) |
|---|---|---|
| brick (returns and rear) | min 0.740, mean 0.935 | min 0.866, mean 0.985 |
| brick units (heads, string course) | min 0.820 | min 0.926 |
| rock-faced Lemont walling | no tone | min 0.871, mean 0.992 |
| dressed trim (sills, heads, belts) | no tone | min 0.860, mean 0.989 |
| stone bay | no tone | min 0.871, mean 0.999 |
| K11 boundary wall brick | min 0.740 | min 0.883 |

(Read off the master. The web tier carries the same minima: `browser-validation-*.json`, `tones`.)
Mid-wall, between the damp line and the soot band, 488 brick and 425 trim vertices of the master
carry a trail (122 and 425 in the welded web tier), at their darkest 0.956 and 0.949.

## What it looks like

`comparison.jpg` shows the same stands, before on the left and after on the right, at desktop. **The
change is slight, and that is the kit's verdict on an 18-year-old house**, not something lost on the way
to the screen. The rear's brick foot is lighter than the 40-year band it wore. The stone front has a
faint darkening at the plinth and under the soffit. The sill trails are a few per cent darker than the
wall around them. Pixels moved by more than 4/255: 0.4 % (front), 1.0 % (oblique), 0.2 % (rear),
1.8 % (front-foot close). The older houses the kit was studied on (T-2324, 38 years) show it plainly.
1808 was the one kit-built house, so it was the one to take it.

## Costs

| | before | after |
|---|---|---|
| master GLB | 7,147,776 B | 7,840,196 B |
| web GLB (what every tier loads) | 2,133,848 B | 2,175,620 B (+2.0 %) |
| triangles | 60,944 | 67,312 (+6,368, the trail columns) |
| draw calls at the front stand, desktop | 117 | 117 |
| textures, shaders | — | none added: `_TONE` is a vertex channel the renderer already multiplies |

Scene readings at each stand (load to ready, draws, triangles, a timed frame on this machine's
software GL, relative only) are in `browser-validation-desktop.json`, `browser-validation-mobile.json`
and `before-browser-validation-desktop.json`. Every stand passed with zero page errors, zero failed
requests and within budget. Generator: `k01_emit.py --only keith_house_1808_prairie`, about 1.3 s.

## Reproduce

    python3 generators/k01_emit.py --only keith_house_1808_prairie
    tools/web_derivatives.sh --only keith_house_1808_prairie__as_built_1886.glb
    ./tools/check.sh                                     # publishes, then gates
    node tools/qa_k14_t2358.mjs                          # both viewports, every stand
    QA_BEFORE=<a previous web GLB> QA_VIEWPORT=desktop node tools/qa_k14_t2358.mjs

## Still open

- The roof's chimney plume (T-2359), the yard's lawn edge and path wear (T-2360), and a newer
  neighbour beside it (T-2361).
- Mortar and paint layers are not applied: 1808's K02 joints and K03 panel carry their joints in
  geometry and maps that the kit's mortar recess does not reach yet.
- Every value is reconstructed (`L-k14-condition-kit-2324`, `L-k14-1808-walls-2358`). A dated
  photograph of 1808 Prairie replaces them.
