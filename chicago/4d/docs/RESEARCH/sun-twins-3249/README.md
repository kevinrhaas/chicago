# T-3249 — shadow-only house shapes for the phone's sun pass

T-3247 measured the 1904 phone frame (390x780, `light`) south from 1801 Prairie. The sun's
shadow pass drew about 600 k structure triangles at full detail into a map 23.4 cm a texel.
Cornices, reveals, mullions, sash and trim are under a texel there. They cost the pass
triangles and change no texel. The owner asked for "simpler shadow-only house shapes".

## What changed (renderers/web/js/far-shadow.js, buildings.js, main.js)

A low-spec build for a tier below `full` cuts **one texel twin per structure per batch run**.
It uses T-3286's vertex clustering with a 12 cm cell over all of that structure's pieces in
the batch. At `light` (`DETAIL.light.shadowTwinsByTexel`), the sun's pass swaps a structure's
pieces for its twin wherever the twin's edge moves no further than one texel of the map
(sqrt(3) x 0.12 = 0.208 m against 0.234 m). The bound is taken in the light's frame, so it
holds at any distance. The colour pass never draws a twin.

- **No vertex of its own.** Each pool is drawn at the member vertex nearest its centroid,
  which keeps the same reach. The twin is only an index into its pieces' vertices, rebased
  onto their batch ranges after they are laid (`rebaseGroupTwin`).
- **Swapped only where it pays.** A group is swapped only when every piece in it is shown,
  and only when the twin draws fewer triangles than the pieces would. The pieces counted are
  those whose shadow can reach the view (shadow-casters.js's test) and that stand in the
  sun's box, each at its far twin's count. Otherwise T-3286's per-piece path stands.
- **Phones only.** A desktop's `light` map is 11.7 cm, under the twin's reach, so a desktop
  cuts none. `full` and `balanced` never swap one.

### Why at load and not at bake time

The ticket asked for stand-ins made at bake time. They are cut at load instead, from the
same geometry, by the same clustering T-3286 already ships (about 0.45 s on this machine for
1904). The download grows by nothing. No new derived artifact enters the bake contract or
the manifests (K36 to K39), and the GLB contract (docs/GLB-CONTRACT.md) is unchanged. A
baked stand-in would also have to be fetched and kept in memory beside the house. The load-
time twin borrows the house's own vertices, so all it adds is an index.

## Readings (published /1904/, 390x780, `light`; run-mobile.txt, browser-validation-mobile.json)

Structure triangles in the sun's pass are the frame's count minus the same frame with no
structure casting. "dev" is T-3286's screen bound alone (the build before this change).
"Whole" is every piece cast whole.

| stand (T-3247's) | whole | dev | this | vs dev | vs whole |
|---|---:|---:|---:|---:|---:|
| south from 1801 Prairie | 737,007 | 505,877 | 220,981 | -56.3% | -70.0% |
| Prairie & 18th | 532,287 | 412,968 | 182,030 | -55.9% | -65.8% |
| lakeside, looking south | 0 | 0 | 0 | — | — |
| air, 120 m over Indiana Ave | 35,419 | 35,419 | 30,434 | -14.1% | -14.1% |

- **Lakeside:** no structure casts toward that view. Its sun pass is the railway's
  (T-3247), so there is nothing to swap there.
- **Air over Indiana:** the view is south over the roofs, and most of the houses whose
  shadows fall on screen straddle the frustum or the sun's box. The cost test sends those
  to the cheaper per-piece path. The structures' share of that pass is small (35 k).
- **Pixels against the full models:** 301, 119, 0 and 3 of 304,200 pixels differ (35, 16, 0
  and 0 by more than 8 levels; max 48). The pictures `mobile-*-marked.jpg` paint every
  differing pixel magenta: specks along façade reveals and one mansard slope, which by eye
  read the same in `-whole` and `-texel`. Rendering the same frame twice changed 0 pixels.
- **Hook time:** 0.9–1.9 ms a shadow pass for the swap and its cost test, on this machine.
- **Desktop 1280x800 `light`:** unchanged (11.7 cm texel; no twin is cut).

## Memory (measure_memory.mjs --only mobile, resident estimate)

| year | dev | this | ceiling |
|---|---:|---:|---:|
| 1904 | 375.6 MB | 381.8 MB | 400 |
| 1835 | — | 490.3 MB | 550 |
| 1812 | — | 203.4 MB | 225 |

The +6.2 MB on 1904 is the twins' 2.43 M index entries, 0.8 M triangles across 603
structures. Two other designs were measured and dropped. One centroid twin per piece cost
+24.1 MB (399.7 of 400). One index-only twin per piece cost +13.3 MB, because twenty
thousand instance records weigh more than their index.

## Shadow acne

`node tools/check_shadow_bias.mjs`: PASS (phone `light` 23.4 cm, -0.0008 / 9.0 cm). The
biases are untouched. A twin's faces lie within the 0.208 m reach of the house's own
surfaces, and the pixel readings above show no acne or leak where the twins cast.

Re-run: `node tools/qa_t3249_sun_twins.mjs` after `tools/publish.sh`
(`QA_SHOTS=1` for the pictures, `QA_VIEWPORT=1280x800` for the desktop).
