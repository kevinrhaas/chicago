# K14 on a brick-fronted K01 house: 1608 Prairie at the 1886 plate's bound (T-2364)

Piece 1 of T-2361 (the newer-neighbour comparison of T-2325, package K14 of the T-1837 Prairie
programme). T-2361 was split on 2026-10-11 because it could not be one demonstration: no house now
on K01 was built after 1886 (below), and the kit refused every brick-fronted K01 house, which is
what every post-1886 candidate is. This piece teaches the kit brick fronts and shows it on one;
T-2365 (blocked on T-1872) does the comparison once 1708 Prairie stands on K01.

## Acceptance (stated before work)

1. A brick-fronted K01 house may name the K14 kit. Its walls are cut for the trails of the K06 sills
   seated on them, exactly as a stone front's are, without changing the order a brick house is built in.
2. 1608 Prairie names the kit with a completion year the evidence bounds, and its four brick walls
   and its stone dressings take their condition from the kit at that age.
3. No other K01 house moves: `k01_emit.py --check` rebuilds every other K01 asset to its committed
   bytes (1808 Prairie included). No value of the kit is changed.
4. Verified in the published /1904/ app at 1280x800 (full) and 390x780 (light) at front, oblique,
   rear and two close stands, compared with itself before, with costs.

## Which houses are newer than 1808 (the reading that split T-2361)

Robinson's 1886 atlas, plate 10 (`robinson_1886_chicago_plate_10`), read through its committed fit
(`data/traces/gcp/robinson_1886_plate_10_gcps.json`, 4.54 m RMS) with each structure's position and
main-body footprint projected onto the raster:

- 1600, 1608, 1612, 1616, 1620 and 1626/1628 each have a house drawn on their lot. **1608's 1904
  main body falls on the house drawn on lot 5**, offset about 3-4 m, inside the two fits' combined
  error (4.54 m and sheet 20's 2.46 m). So 1608 stood by 1886.
- **1708 is an empty lot** in 1886, between the mansion at 1700-1706 and the house at 1712.
- 1700 and 1706 are drawn as one older stone-fronted mansion, which the Glessner family townhouses
  later replaced.

So the newer neighbour is 1708 (or 1700/1706), all district drafts today. That is T-2365.

## What changed

- `k01_frontage.py`: a stone front seats its openings before cutting its walls; a brick house cuts
  its walls first, so when its walls needed trail columns no sill was seated yet. A brick house that
  names the kit now builds itself once without the kit, reads the K06 sills off that build
  (`Assembly.k14_sills`), and cuts its walls with them. The same seats, from the same calls; nothing
  else is taken from the first build. Its stone dressings (`limestone_trim`, and `bay_stone` on a
  brick bay) weather as the kit's `dressed_trim`, the fabric 1808's stone front gives its trim.
- `k01_frontage_params.py`: the refusal of a brick-fronted record is gone.
- `house_1608_prairie.json`: `form.condition` names the kit with `built: 1886`, the plate's bound.
  That is the youngest the evidence allows, so the weathering shown is a floor (18 years, age
  factor 0.45, the same as 1808). Liberty `L-k14-1608-brick-2364`.

Trails found: street front 1 sill and 1 downpipe, south wall 6 sills and 1 downpipe, rear 4 sills
and 2 downpipes, north party wall none.

| slot (master) | before (K03 40-year mask) | after (K14, 18 years) |
|---|---|---|
| brick (walls) | 684 vertices, min 0.740, mean 0.915 | 4,632 vertices, min 0.866, mean 0.977 |
| brick units (heads, courses) | min 0.815, mean 0.931 | min 0.922, mean 0.973 |
| bay brick | min 0.882, mean 0.975 | min 0.973, mean 0.998 |
| stone dressings (`limestone_trim`) | no tone | min 0.892, mean 0.963 |
| bay stone | no tone | min 0.860, mean 0.997 |

The web tier carries the same minima (`browser-validation-*.json`, `tones`).

## What it looks like

`comparison.jpg`: before on the left, after on the right, at desktop. **The change is slight, as it
is on 1808.** The brick foot and the band under the eaves are lighter than the 40-year mask, the
sills and heads darken a little, and faint trails run below the sills. Pixels moved by more than
4/255: 1.5 % (front), 0.4 % (oblique), 0.6 % (rear), 4.4 % (front-foot close), 4.5 % (south sills
close).

## Costs

| | before | after |
|---|---|---|
| master GLB | 2,685,080 B | 2,865,024 B |
| web GLB (what every tier loads) | 946,384 B | 960,408 B (+1.5 %) |
| triangles at the front stand, desktop | 1,773,682 | 1,777,630 (+3,948, the trail columns) |
| draw calls at the front stand, desktop / mobile | 111 / — | 111 / 79 |
| textures, shaders | — | none added: `_TONE` is a vertex channel the renderer already multiplies |
| build | ~0.9 s | ~1.8 s (the house is built twice) |

Every stand passed at both viewports with zero page errors, zero failed requests and within budget
(`browser-validation-desktop.json`, `browser-validation-mobile.json`,
`before-browser-validation-desktop.json`; frame times are this machine's software GL, relative only).

## Reproduce

    python3 generators/k01_emit.py --only house_1608_prairie
    tools/web_derivatives.sh --only house_1608_prairie__as_mapped_1904.glb
    ./tools/publish.sh
    QA_VIEWPORT=desktop node tools/qa_k14_t2364.mjs
    QA_VIEWPORT=mobile node tools/qa_k14_t2364.mjs
    QA_BEFORE=<a previous web GLB> QA_VIEWPORT=desktop node tools/qa_k14_t2364.mjs

Changing `k01_frontage.py` changes the input hash of every asset built with it, so every K01 house
and the K12, K13 and K16 pieces that import it were re-emitted to refresh `assets/manifest.json`.
Their bytes did not change.

## Still open

- T-2365: the comparison beside 1808 on 1708 Prairie, once T-1872 builds it on K01.
- 1608's completion year: a permit, a directory or a dated photograph replaces the 1886 bound.
