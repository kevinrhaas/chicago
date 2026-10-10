# K14 condition kit: each building's age in 1904, as data, and how it reads in neutral light (T-2324)

Piece 1 of T-1856 (package K14 of the T-1837 Prairie programme). Piece 2, T-2325, applies it to a
named Prairie Avenue house and its yard. This note records the acceptance, what the kit holds, the
study and what it shows, the costs, and what is still open.

## Acceptance (stated before work)

1. The condition layers T-1856 names (an age mask, rising damp and plinth dirt, eave and chimney
   soot, water trails beneath sills and outlets, mortar weathering, painted timber, the grass edge
   at a wall foot and path wear) are metric, engine-neutral data in
   `data/components/prairie_1904/k14_condition.json`, every one with its confidence and a note.
2. One deterministic shared module, `generators/archetypes/k14_condition.py`, evaluates them for
   any generator: as the `_TONE` vertex multiplier the renderer already takes (buildings.js
   `applyPieceTone`), as a baked mask on a grid, or as a ground weight. It gives the vertex rows a
   wall needs to carry the layers.
3. Condition is the building's own age on 1904-07-01 and never a modern ruin: a floor no point
   goes under, no layer that removes or adds fabric, new work that reads clean, and older work
   visibly older but still its own material. Each property draws from its own seed.
4. A study compares new Georgian work (built 1902) with 20- and 38-year-old walls on the K02 and
   K03 fabrics under identical neutral light, with its measurements and costs committed here.
5. `tools/check_condition_kit.py` gates all of it in `check.sh`, and its self-test proves each rule
   still refuses a break. The reconstruction is one liberty, `L-k14-condition-kit-2324`.

## What the kit holds

| layer | on | what it does at full age (40 years) |
|---|---|---|
| `ground_damp` | wall | darkens from grade to a top 0.60 m up (0.15 m when new), to 0.74 at grade, the top wobbling 0.06 m along the wall by the seed |
| `eave_soot` | wall | darkens the 1.60 m under the soffit (0.40 m when new), to 0.80 at the soffit |
| `water_trails` | wall | a streak below each sill (0.90 m, 0.90) and outlet (1.60 m, 0.84), narrowing to its foot, broken into rivulets, its length within 20 per cent by the seed |
| `chimney_soot` | roof | a plume 3.0 m long and 30 degrees either side of bearing 70 (downwind of the westerlies), to 0.78 at the stack |
| `mortar` | joint | lime joints 1.5 mm deeper and 0.88; a dense dark joint 0.3 mm and 0.95 |
| `paint` | painted timber | dulls to 0.92 over a six-year repaint cycle, never older than the cycle, the repaint year spread by the seed |
| `grass_edge` | ground | a bare strip 0.25 m wide at a wall foot (0.05 m when new), its line wobbling 0.05 m |
| `path_wear` | ground | a front walk and a service walk worn along the centre, a drive in two tracks 1.5 m apart |

A layer grows linearly with the building's years standing to 40, the oldest wall the district
has, and stops there. Each fabric takes a wall layer at its own strength (`fabric_response`), from
0.4 for dark fired brick to 1.25 for Bedford limestone, and the product of the layers is held at the
floor, 0.62. Every tone is a grey multiplier, so every fabric keeps its own hue. The full-age damp
and soot are exactly the K03 1808 service wall's constants (`generators/archetypes/k03_brick.py`),
and the check holds them equal, so the mask already in the scene is this kit at full age.

The `never` list names what the kit may not express: missing, spalled or cracked fabric; broken or
boarded glass; vegetation on a wall or roof; paint failed to bare wood; a black or uniformly grimed
facade; anything under the floor.

## The study

`study.jpg`, written by `python3 generators/archetypes/k14_condition.py --study`. Rows are four
fabrics (K03 pressed red and common buff bonded panels, K02 Bedford limestone and brown sandstone);
columns are a wall built in 1902, 1884 and 1866. Each tile is a 3.0 by 4.5 m elevation from grade to
soffit with a window and its stone sill, an overflow spout and a downpipe, and under it a 1.2 m plan
strip of the ground in front: lawn, the bare edge at the wall foot and a cinder service walk running
out from the wall. Light is identical and neutral in every tile (linear albedo times tone, no
shading), so the only difference between columns is age. One fixed property seed throughout.

What it shows, read off the render:

- **1902, new Georgian work.** Every fabric reads clean: under a tenth of a per cent darker on
  average, nowhere darker than 0.984.
- **1884, 20 years.** A soft band under the eave and at the foot; the sill trail is faint, the
  lawn edge a thin line. 1.4 to 2.5 per cent darker on average.
- **1866, 38 years.** The eave band is plain, the damp band reaches knee height, rivulets run
  below the sill and the spout, the lawn has a bare edge at the wall, and the walk a beaten line.
  4.2 to 7.5 per cent darker on average; the darkest point (0.69, under the limestone's sill and
  soffit) stays above the floor, and every wall still reads as its material.
- **Fabric response.** Pale limestone shows the most and pressed red brick the least, as the
  response table intends. The first render's sill trail was a hard-edged wedge on limestone; it
  was broken into rivulets across its width before commit.

| fabric | 1902 | 1884 | 1866 | darkest point at 1866 |
|---|---|---|---|---|
| pressed red brick | 0.999 | 0.986 | 0.958 | 0.829 |
| common buff brick | 0.999 | 0.980 | 0.940 | 0.756 |
| Bedford limestone | 0.999 | 0.975 | 0.925 | 0.694 |
| brown sandstone | 0.999 | 0.984 | 0.952 | 0.804 |

(Mean luminance of the open wall against the same wall clean; `costs.json` `measured`.)

The ground strip's colours (lawn, earth, cinder and how far wear darkens the cinder) are the
study's own, to make the weights visible. The kit returns weights; how a yard surface shows them is
T-2325's to choose with the road and yard materials.

## Costs

- **On the vertex channel** (the route T-2325 takes first): no texture, no draw and no shader
  change; 4 bytes a vertex for `_TONE`. A 38-year wall with one sill and one outlet needs 7 extra
  vertex rows to carry its layers (`wall_breaks`: 0.14, 0.52, 0.63, 1.12, 2.10, 2.96, 3.90 m).
- **As a baked mask**: a 10 by 12 m wall at 32 px/m is 122,880 pixels, 1,661 bytes as an 8-bit PNG.
- **The study**: 187,534 bytes; the module renders it in under a second.
- **The gate**: `check_condition_kit.py --check` runs in about 1.5 s, `--self-test` (15 cases) in
  about 6 s.

## Still open

- No structure takes its condition from the kit yet. T-2325 applies it to a named house and its
  yard, baked and verified at both viewports, and decides whether its walls carry the layers on
  `_TONE` rows or on a baked mask.
- The K03 1808 service wall keeps its own constants; moving it onto the kit (at its own age) is a
  rebake, and belongs with a ticket that rebakes it.
- Limestone that is rinsed by run-off often goes paler, not darker, beside its trails. A grey
  multiplier under 1 cannot say that, and the kit does not try.
- Every number is reconstructed (`L-k14-condition-kit-2324`); a dated photograph of a Prairie
  Avenue house replaces that property's values.
