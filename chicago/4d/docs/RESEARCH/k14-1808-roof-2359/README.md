# K14 on 1808 Prairie's roof: the chimney plume at the house's own age (T-2359)

Piece 2 of T-2325 (package K14 of the T-1837 Prairie programme). Piece 1 weathered the walls
(T-2358) and the yard (T-2360); this one lays the kit's `chimney_soot` layer on the slate leeward
of 1808's two K15 stacks, the library's on the south hip and the hall's on the north.

## Acceptance (stated before work)

1. 1808's slate carries the kit's plume (`k14_condition.Condition.roof_tone`) leeward of each K15
   stack, at the house's own age (built 1886, 18 years on 1904-07-01, factor 0.45), on a compass
   bearing (the house's frame turned by its placement's rotation).
2. The covering is cut with the rows the plume needs, so `_TONE` has vertices to ride, and the
   emitted shell stays closed (check_roof_kit's own measure: no open edges, one shell, nothing
   doubled, degenerate or crossing).
3. The kit's numbers are used as they are. No other K01/K12/K13/K16 house moves:
   `k01_emit --check` and its siblings rebuild every other asset to its committed bytes.
4. Verified in the published /1904/ app at 1280x800 (full detail) and 390x780 (light), at a roof
   stand and a close stand on each stack, with a before/after comparison and the costs.

## What changed

- `k01_frontage.Assembly.k14_roof_rows` cuts the joined K05 shell for emission only. A box is put
  round each plume's wedge in plan. The covering is cut on the box's sides, then inside it by plan
  lines x = c and z = c, 0.225 m apart (`K14_PLUME_ROWS` = 6 to the plume's 1.35 m). Any face a cut
  put a point on the edge of (a flashing, a cricket, the fascia, the slate just outside the box)
  takes that point and is fanned from its centroid. `roof_shell`, the solid the roof and chimney
  gates read, is unchanged. Measured with `check_roof_kit.measure`, the emitted shell is 0 open
  edges, 0 misoriented, 1 shell, 0 doubled, 0 degenerate, 0 crossings, 0 hidden, volume 707.539 m3
  (the solid's 707.538).
- `condition_tones` then tones every `slate_covering` vertex: the product of the kit's plume from
  each stack, read from the stack's centre with the offset turned through `rotation_deg` (-0.669).
  The params now resolve `condition.rotation_deg` from the record's placement.

| | full (master) | web (every tier) |
|---|---|---|
| slate vertices | 4,299 | 888 |
| carrying the plume | 1,014 | 182 |
| darkest | 0.9462 | 0.9462 |

The darkest the kit allows at 18 years is 0.901, at the stack's centre. The stack stands there,
so the darkest slate is at its lee face.

## What it looks like

`comparison.jpg`: before, after, and their difference x10, at the three desktop stands. **At 18
years the plume is too faint to pick out by eye.** It darkens dark slate by at most about 5 %,
which is 1 to 3 levels of 255 on screen. The x10 difference shows it where it belongs: a fan
east-north-east of each stack, on the south hip's slate for the library's and down to the north
eave for the hall's. Pixels moved by more than 1/255: 0.07 % (roof), 1.42 % (library stack),
0.26 % (hall stack); by more than 4/255, 0.00 to 0.06 %. The same kit at 40 years would be about
twice as dark and 3.0 m long. This is the kit's verdict on a young roof, not a loss on the way to
the screen.

## Costs

| | before | after |
|---|---|---|
| master GLB | 8,763,700 B | 8,874,528 B |
| web GLB (what every tier loads) | 2,471,860 B | 2,478,204 B (+0.26 %) |
| roof triangles emitted | — | +820 (covering 644 → 1,419; flashing, cricket, fascia mended) |
| scene triangles at the stands, desktop | 3,102,925 / 3,080,263 / 3,065,305 | +1,640 at each |
| draw calls at the stands, desktop | 121 / 119 / 116 | 121 / 119 / 116 |
| textures, shaders | — | none added: `_TONE` is a vertex channel the renderer already multiplies |

Readings at each stand (load to ready, draws, triangles, a timed frame on this machine's
software GL, relative only) are in `browser-validation-desktop.json`,
`browser-validation-mobile.json` and `before-browser-validation-desktop.json`. Every stand
passed with zero page errors, zero failed requests and within budget.

## Reproduce

    python3 generators/k01_emit.py --only keith_house_1808_prairie
    tools/web_derivatives.sh --only keith_house_1808_prairie__as_built_1886.glb
    ./tools/check.sh                                     # publishes, then gates
    node tools/qa_k14_t2359.mjs                          # both viewports, every stand
    QA_BEFORE=<a previous web GLB> QA_VIEWPORT=desktop node tools/qa_k14_t2359.mjs

## Still open

- A newer neighbour beside it (T-2361).
- Slate has no entry in the kit's `fabric_response`, so it takes the plume at 1.0, the kit's
  default. Every value is reconstructed (`L-k14-condition-kit-2324`, `L-k14-1808-roof-2359`).
  A dated photograph of 1808 Prairie's roof would replace them.
