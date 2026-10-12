# T-2210 — Glessner courtyard: light pink brick and grey Joliet limestone

Glessner exterior audit GA-10. The audit found the courtyard reading dark brown with
bright, uniform trim, where the written record names light pink common brick and Joliet
limestone distinct from the street granite.

## What the sources say

- **HABS ILL-1015 data, p. 21 (1963)** (`habs_glessner_house_il_1015_data_pages`): "The
  walls toward the courtyard are of light pink brick with Joliet limestone lintels and
  sills." Foundations are Joliet limestone too; the street walls are Wellesley granite.
- **Glessner, *The Story of a House* (1923)** (`glessner_story_of_a_house_1923`, transcribed
  in the same PDF): "The courtyard elevation, of common brick of slightly pinkish color,
  with gray limestone trimmings ... By special arrangement the same brick were used in the
  adjoining house, so that all walls of the courtyard are of the same texture and color."
- **HABS photo 05 (court, c. 1923)**: rock-faced heads and sills on every courtyard window,
  a smooth roll under the tower's clerestory, brick fairly even in tone. It is monochrome,
  and orthochromatic film darkens red, so no tone was sampled from it. At its scanned
  resolution it does not resolve the bond.

## Material identity per surface (v4 model, after)

| surface | slot(s) | identity | albedo | repeat | tier |
|---|---|---|---|---|---|
| courtyard brick walls, tower, dining bay, parapets, stair cheeks | `brick` (60 %), `brick_dark_red` (20 %), `brick_buff` (14 %), `brick_smoky` (6 %) | light pink common brick (HABS; Glessner) | `court_brick_basecolor.jpg` × 0.94 / (0.86, 0.76, 0.74) / (1.0, 0.99, 0.97) / (0.66, 0.58, 0.56) | 1.7272 × 2.1336 m; unit 0.2069 × 0.0577 m, 9 mm joints, 0.066675 m course | colour reconstructed |
| rock-faced heads, sills, surrounds, tower belts | `rough_stone_trim` | Joliet limestone, rock-faced (HABS) — was the street granite's albedo | `limestone_basecolor.jpg` × (0.83, 0.88, 1.0); granite split-face normal | 1.2 m | colour reconstructed |
| dressed trim: tower roll, copings, steps, landings, date stones | `limestone_trim` | Joliet limestone, dressed | `limestone_basecolor.jpg` × (0.83, 0.88, 1.0); normal 0.65 → 0.85 | 1.2 m | colour reconstructed |
| street walls | `granite`, `granite_1..4` | Wellesley granite (HABS); unchanged | photographic study, unchanged | 0.22 m albedo / 1.6 m relief | unchanged |
| joints | `mortar` | sandy lime mortar; unchanged | unchanged | 1.2 m | unchanged |

The courtyard brick is a new albedo-only image in the Glessner v4 library, from
`brick()`'s own seed and grain, so brick's normal and roughness serve unchanged. The
grey-tan `brick_basecolor.jpg` and the cream `limestone_basecolor.jpg` are not touched:
the K01 kit's Prairie houses wear them. The K01 contract's `metric_uv` now reads
`court_brick` for the brick slots and `limestone` (1.2 m) for the rough trim, and is ok.

## Measured

Desktop, actual published `/1904/`, same cameras before and after
(`node tools/qa_glessner_t2210.mjs`, `QA_TAG=before-` for the dev captures). Patch means,
sRGB 0-255, from `court-sill`:

| patch | light | before | after |
|---|---|---|---|
| brick under the landing | neutral | 59, 47, 32 (r/b 1.83) | 94, 66, 55 (r/b 1.70) |
| brick under the landing | scene (shade) | 38, 36, 32 | 62, 50, 52 |
| rock-faced lintel, right window | neutral | 104, 102, 93 (r/b 1.13) | 125, 124, 118 (r/b 1.05) |
| rock-faced lintel, right window | scene | 86, 86, 83 | 104, 106, 107 |

The brick moves from brown to a light pink, and the rock-faced trim from the granite's
speckled warm grey to an even, finer grey, so heads and sills no longer read as the street
stone. Web GLB 45,847,408 → 45,846,968 bytes; triangles unchanged (1,246,933 full,
197,304 light). Mobile is the light tier, rebaked too.

## Colour uncertainty, kept explicit

Both hues are reconstructed (`docs/LIBERTIES.md` → `L-glessner-court-materials-2210`).
"Light pink" and "gray" bound them; nothing measures them. The neutral-light captures
(`*-neutral.png`, white hemisphere and white sun, capture only) show the material colour
without the blue sky fill; the scene captures show it as the town is lit.

## Not done here

- **Bond.** The geometry lays a stretcher (running) bond on a 0.2159 m module, and the
  captures show it wrapping the tower's curve and stopping cleanly at the jambs. No
  source read here states the bond, and photo 05 does not resolve header courses, so it
  is left as built.
- **The adjoining house.** Glessner says its courtyard wall was laid in the same brick.
  Matching that wall is the neighbour's ticket, not this one.
