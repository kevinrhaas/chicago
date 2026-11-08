# The 1812 children's dress on child bodies (T-3465)

Builder notes for the children of the 1812 town and of the Potawatomi camp by the fort: two child
bodies prepared from pinned CC0 MakeHuman targets, five role assets built on them, and every row
the integrator has to add to a shared file (none of those files was touched here).

| Asset id | Role (who wears it) | Body | Standing height |
|---|---|---|---|
| `child_boy_1812` | A boy of the town of about 5 to 10 (garrison, settler, trader households): skeleton suit | `prepared_child_male_8.json` | 1.208 m |
| `child_girl_1812` | A girl of the town of about 5 to 10: high-waisted frock, pinafore | `prepared_child_female_8.json` | 1.205 m |
| `child_toddler_1812` | An unbreeched child of either sex, about 2 to 4, walking: white frock | `prepared_child_3.json` | 0.905 m |
| `potawatomi_boy_1812` | A Potawatomi boy of the camp, about 5 to 10: calico shirt, stroud leggings, moccasins | `prepared_child_male_8.json` | 1.208 m |
| `potawatomi_girl_1812` | A Potawatomi girl of the camp, about 5 to 10, dressed as her mother in small: calico over-blouse, wrapped stroud skirt, leggings, moccasins | `prepared_child_female_8.json` | 1.205 m |

Generator `tools/human_child_1812.py` (one module, five roles; `prepare_child_assembly` is the
`role_1812.prepare` hook). Recipes `data/humans/recipes/<asset>.json`. Test
`tools/test_human_child_1812.py` (11 tests, pure Python). Liberty: `L-human-modular-dress-1789`
(supplement text below) for cut and colour; `L418` for the body/skin path, as the private.

Research read: `docs/RESEARCH/people-1812-3465/day.json` (`dress`: toddler frock, skeleton suit,
boy's jacket and trousers, girl's frock and pinafore, girl and boy "of the country"),
`docs/RESEARCH/people-1812-3467/day.json` (`dress.potawatomi_child_1812`),
`docs/RESEARCH/people-1812-3461/dress.json` ("Children 2-12 and infants") and `native.json`.

## 1. The child bodies

**Targets.** The twelve macro targets `{caucasian,asian,african}-{male,female}-{child,baby}.target`
were fetched from the pinned MakeHuman commit `a8bc2d54ff0ac92e78ff71431b1023eda42bf482` into
`assets/authored/humans/makehuman_hm08/makehuman/data/targets/macrodetails/`, each verbatim with
its CC0 header. Their URL, bytes and SHA-256 are pinned in
`assets/authored/humans/makehuman_hm08/SOURCE-child.json`.

**Why a SOURCE-child.json and not rows in SOURCE.json.** `tools/human_base_prepare.py` embeds the
whole manifest it is given in the prepared body. Appending rows to `SOURCE.json` would change the
embedded source of every existing prepared body (and break `test_human_dress_components`, which
asserts no female path in `SOURCE.json`). So, as `SOURCE-female.json` did for the women,
`SOURCE-child.json` is a complete manifest: every `SOURCE.json` row unchanged, plus the twelve
child/baby rows. `SOURCE.json` is untouched. The child bodies are prepared with
`--source-manifest SOURCE-child.json`.

**Age method (a correction to the brief).** The pinned `apps/human.py` puts MakeHuman's age
anchors at baby = 1 year (MIN_AGE), child = 10 years (the child weight peaks at age slider
0.1875), young = 25 (MID_AGE), old = 90 (MAX_AGE). An 8-year body is therefore **between baby
and child, not "between child and young"** as the brief has it: child 7/9 + baby 2/9. A 3-year
body is baby 7/9 + child 2/9. As `adult_35` does, each weight is shared equally over the three
upstream shape categories (software category names, not ancestry), and for the 3-year body over
both sexes; coefficients sum to 1. Recipes: `child_male_8.recipe.json`,
`child_female_8.recipe.json`, `child_3.recipe.json` (each records `age_anchors_years` and
`age_method`).

**Heights.** CDC 2000 stature-for-age, 10th centile, the centile the 1812 research uses (after
Steckel 1985 and Komlos 2003 for early-19th-century children): boy 8 y 120.8 cm, girl 8 y
120.5 cm; 3 y boy 90.5 cm, girl 89.2 cm. The toddler is built at 0.905 m (the tool refuses below
0.9 m, and one body serves both sexes). Built heights (crown): 1.208, 1.205, 0.905 m.

| Body | sha256 | Height | Heads tall | Hip / height |
|---|---|---|---|---|
| `prepared_child_male_8.json` | `573c17c5…26b90` | 1.208 | about 6.3 | 0.51 |
| `prepared_child_female_8.json` | `24933040…66972` | 1.205 | about 6.4 | 0.51 |
| `prepared_child_3.json` | `f040bece…ac142` | 0.905 | about 5.2 | 0.467 |
| (adult engineering body, for comparison) | | 1.75 | about 7.5 | |

All three keep the 56-joint skeleton, the complete source mesh, UVs and the 1117 helper vertices
(the reports record it); `human_contract.py --glb` passes on every export.

**Does one 8-year body scaled to 0.9 m read as a child, or as a shrunken older child?** As a
shrunken older child. A 3-year-old is about 5.2 heads tall with the hip at 0.47 of the height;
the 8-year body is 6.3 heads with the hip at 0.51, so at 0.9 m it has a small head, long legs and
a slim trunk: a miniature schoolchild, not a toddler. Hence the third body at 3 years.

### Ages each body can stand for, and the height range it takes

The variation kit scales a figure's height about its feet; `human-variation.js` clips
`looks.height_scale` to 0.88-1.12. CDC 10th-centile heights against the bodies:

| Body | 0.88-1.12 covers | Reads right for | Recommended clip for children |
|---|---|---|---|
| 8-year (boy 1.208, girl 1.205) | 1.06-1.35 m, about ages 5.5-10.5 | 5 to 10 | **0.85-1.18** (about 1.03-1.42 m: ages 5 to 12). Above about 1.15 the head is a little large for an 11-12-year-old; acceptable at street distance, not in a close portrait. |
| 3-year (0.905) | 0.80-1.01 m, about ages 2-4.7 | 2 to 4 | **0.88-1.15** (0.80-1.04 m: ages 2 to 5). Below 0.88 is a child in arms (not drawn). |

The research's walking children run about 2.5 to 13. The five figures of 11 to 13 (one boy and
girl of the country, a girl of the frock, two Potawatomi children of 12) are the ones the 8-year
body serves least well. **A 12-year body is the next body worth building** if the close views
matter: the same method gives child 13/15 + young 2/15 for 12 years, at about 142 cm (CDC 10th
centile, to be read off the table when built), and the five dress roles rebuild on it with no
code change. Not built here. **No younger body is needed:** infants in arms are not drawn.

### Rows the variation kit needs for children (axes.json and human-variation.js)

The kit's age drive assumes adult anchors; for a child it must be switched off:

- `(age - base_age) * per_year` moves the old macro (young 25 to old 90); for a child it adds an
  old-age blend to a child body.
- The face axis `(age - base) / (base - 25)` gives a positive "older" value for any child (base
  below 25 makes the denominator negative).
- A record without an age falls into `default_band_years` [22, 58].

Proposed `data/humans/variation/axes.json` `bases` rows (the integrator decides the flag name;
`age_drive: false` is what is meant: no macro age movement, no face age term, no default band):

```json
"child_boy_1812": {"base_age_years": 8, "sex": "male", "age_drive": false, "height_clip": [0.85, 1.18], "basis": "data/humans/recipes/child_boy_1812.json: the prepared_child_male_8 engineering body (baby 2/9 + child 7/9), T-3465. Age is not driven: the kit's age model runs young (25) to old (90)."},
"child_girl_1812": {"base_age_years": 8, "sex": "female", "age_drive": false, "height_clip": [0.85, 1.18], "basis": "data/humans/recipes/child_girl_1812.json: the prepared_child_female_8 engineering body, T-3465. Age is not driven."},
"child_toddler_1812": {"base_age_years": 3, "sex": "either", "age_drive": false, "height_clip": [0.88, 1.15], "basis": "data/humans/recipes/child_toddler_1812.json: the prepared_child_3 engineering body (baby 7/9 + child 2/9, both sexes), T-3465. Age is not driven."},
"potawatomi_boy_1812": {"base_age_years": 8, "sex": "male", "age_drive": false, "height_clip": [0.85, 1.18], "basis": "data/humans/recipes/potawatomi_boy_1812.json: the prepared_child_male_8 engineering body, T-3465. Age is not driven."},
"potawatomi_girl_1812": {"base_age_years": 8, "sex": "female", "age_drive": false, "height_clip": [0.85, 1.18], "basis": "data/humans/recipes/potawatomi_girl_1812.json: the prepared_child_female_8 engineering body, T-3465. Age is not driven."}
```

The face axes (nose, jaw, brow...) are adult targets; on a child they should be drawn at a
reduced scale (the women's `face_draw_scale` 0.5 is a reasonable start) and not checked here.

## 2. The walk

**Baked walk (in the GLB).** `tools/human_grounded_gait.py` draws the asset's walk clip at
0.6 m/s on a 1.2 s cycle with a 4 cm pelvis drop and a 6.5 cm swing lift, sized for the adult
leg (0.8603 m); a child's leg cannot reach those steps (the solver refuses them). As a stopgap
that touches no shared file, `apply_child_walk()` in the child module scales speed, drop and lift
by leg / 0.8603 for the build process only (it sets the gait module's constants and the
builder's `SPEED_M_S`, and only when the running `__main__` is `human_teamster_blend.py`).

| Asset | Leg scale | Walk speed | Stride (one cycle) |
|---|---|---|---|
| `child_boy_1812`, `potawatomi_boy_1812` | 0.662 | 0.397 m/s | 0.476 m |
| `child_girl_1812`, `potawatomi_girl_1812` | 0.649 | 0.389 m/s | 0.467 m |
| `child_toddler_1812` | 0.447 | 0.268 m/s | 0.322 m |

Exported clips carry these speeds; the walk and idle were checked at child size in the stills
(feet planted, no knee lock, no foot through the ground).

**Shared fix (rows for the integrator).** (1) `human_teamster_blend.py` should take a walk scale
from the recipe (`"walk": {"leg_scale": "auto"}` or a number) instead of the monkeypatch; the
child module's `child_walk()` is the formula. (2) `renderers/web/js/human-gait.js` `gaitProfile`
uses adult speeds (1.35 / 1.25 m/s) with stride 0.83 / 0.78 x height and has no age term; for a
child it needs a paediatric profile: cadence rises and stride (as a fraction of height) falls
toward the young ages. Order of magnitude only, not from a source cited here: about 1 m/s at 8
years and somewhat under at 3, free walking; the integrator should take the numbers from a cited
paediatric gait table, or simply use leg-scaled speed as above. Until then a child placed on a path will glide.

## 3. The dress

All garments are graded `inferred` or `reconstructed`, with cleared `source_ids` (public domain or
no known restrictions) and `L-human-modular-dress-1789`. Flat colours on the shared skin atlas,
no new textures.

**`child_boy_1812`: skeleton suit.** The research offers a skeleton suit for boys of 4-8 and a
cutaway jacket, waistcoat and round hat for 8-13; the coordinator asked for one boy. The skeleton
suit is taken: it is the boy's dress of about 1810 and has the clearest picture (Joshua Johnson's
Rutter children, about 1805; the Pixler boys, about 1815). A short dark blue jacket, buttoned down
the front (4 horn buttons), long sleeves; high trousers of the same cloth buttoned onto it with a
row of 7; a wide white shirt collar turned out over the jacket; black shoes; bare head.
*Not modelled:* the collar's frill (it read as a jagged edge at the scale drawn: drawn plain and
said so), the cutaway jacket and round hat of the older boys, shirtsleeves-and-barefoot for
chores. An 11-12-year-old in a skeleton suit is a liberty (they had moved to jacket and trousers).

**`child_girl_1812`: frock and pinafore.** High-waisted frock to above the ankle (Rutter girl;
Emma Van Name, about 1805; the Beecher child's frock, about 1813), short puffed sleeves, round
neck, in a faded rose printed cotton (a flat colour; so that the girls are not all in white beside
the toddlers). A linen pinafore over it, bib on the breast and broad apron (reconstructed, as
the research says). Brown shoes, bare head. *Not modelled:* sunbonnet or cap, apron ties and
straps, the print.

**`child_toddler_1812`: white frock, either sex, 2-4.** The unbreeched child: white high-waisted
frock to the ankle (the Beecher frock was a boy's), short puffed sleeves, red-brown shoes, bare
head. *Not modelled:* cap, pinafore, bare feet in summer.

**`potawatomi_boy_1812` and `potawatomi_girl_1812`: the camp's children.** Built because no other
builder was making `potawatomi_child_1812` (the Native-dress builder makes only the man and the
woman) and it was cheap on these bodies. They follow `dress.potawatomi_child_1812` of
`people-1812-3467/day.json` within the AGENTS.md standing constraint: everyday dress of 14 August
1812 in trade cloth, nothing ceremonial, no paint (that is the 15th), no feathers, beads, silver
or ornament, nothing of the Plains or of later decades, hair plain (the one short cut every
figure shares; the research gives no child's hairstyle). Both keep `review_required: true` and
`touches_removal: true` with their own prose in the recipe; `prepare_child_assembly` refuses
them without it.
- *Boy:* madder-red calico shirt worn loose to mid-thigh with long sleeves (calico among the goods
  of the 13th, Wau-Bun; Hubbard's calico shirts), blue stroud leggings to above the knee,
  smoked-deerskin moccasins (the shared closed shoe stands for them). The breechcloth is under the
  shirt and not made.
- *Girl:* rose calico over-blouse to the hips with elbow sleeves, a dark blue stroud skirt wrapped
  to mid-calf with its white selvage at the hem (Quaife 1913: the women's blue or printed
  cottons), red stroud leggings, moccasins. *Not modelled:* the head kerchief "of some", brooches,
  the wrap's overlap and tie; no ribbonwork (pictured from about 1840).
- Sources (all cleared): `kinzie_waubun_1856`, `quaife_1913`, `hubbard_autobiography_1911`,
  `keating_1824_narrative_v1`, `currey_1912_old_fort_dearborn`. The research's one picture of
  Potawatomi children, George Winter's of 1837 (Tippecanoe County Historical Association,
  `tcha_winter_1837_sin_is_quaw` in the research), is permission-only: it is named in prose as
  reference, no source record is made for it, and nothing of it enters the asset.
- *Review needed:* by people with standing to judge, and against the Newberry's Indigenous Chicago
  material. The reasons are in each recipe's `review_reason` and `touches_removal_reason`.

**Can the Métis "of the country" children (the Ouilmette and Mirandeau children) honestly wear
`child_boy_1812` / `child_girl_1812`?** Only as a declared stand-in. The research dresses them
differently: the boy in a calico shirt, loose trousers, moccasins and a red cap (the engagé's
summer dress cut down), the girl in a short gown and petticoat with a blue cotton handkerchief and
moccasins (Wau-Bun's "French woman of the country"). The skeleton suit and the pinafore frock are
eastern town dress; their silhouettes are close (jacket and trousers; a bodice and ankle-length
skirt) but the moccasins, kerchief, calico and cap are not there. A better fit than either:
`potawatomi_boy_1812` is closer to the boy of the country (calico shirt and moccasins; leggings
instead of trousers), and the girl of the country is between `child_girl_1812` and
`potawatomi_girl_1812`. If they wear these assets the instance should say so in its own words
("dress of the town's children stands in for the short gown and handkerchief the research gives
her") and grade the appearance `reconstructed`. A proper pair (`child_boy_country_1812`,
`child_girl_country_1812`) is a cheap variant of this module if wanted.

## 4. The builds

Build: `$B -b --factory-startup --python tools/human_teamster_blend.py -- --recipe
data/humans/recipes/<asset>.json --variant <asset> --output <scratch>/<asset>.blend
--normal-tolerance 5e-3`, then `bash tools/human_export.sh --master <scratch>/<asset>.blend`.
Contract (`human_contract.py --glb`) passes on all 40 GLBs.

**LOD0 normal readback, max vector delta** (accepted under `--normal-tolerance 5e-3`; this
machine's short2 encoding fails the 1e-3 default on every body, the committed private included at
0.00129): boy and Potawatomi boy 0.0036919; girl and Potawatomi girl 0.0024111; toddler
0.0017932 (the delta belongs to the body, so the two assets on one body agree).

Each asset is lighter than the private (`private_first_infantry_1812`) at every LOD, in bytes and
triangles (the test checks the bytes):

| Asset | Web LOD0 | LOD1 | LOD2 | LOD3 | Triangles LOD0 / 1 / 2 / 3 |
|---|---|---|---|---|---|
| `child_boy_1812` | 4,497,068 | 1,596,320 | 629,248 | 307,772 | 41,299 / 25,148 / 12,435 / 6,066 |
| `child_girl_1812` | 4,288,448 | 1,523,320 | 601,836 | 294,216 | 37,050 / 22,597 / 11,248 / 5,556 |
| `child_toddler_1812` | 4,398,384 | 1,533,532 | 594,220 | 287,124 | 35,484 / 21,659 / 10,808 / 5,369 |
| `potawatomi_boy_1812` | 4,432,932 | 1,550,924 | 602,640 | 291,104 | 38,813 / 23,655 / 11,740 / 5,768 |
| `potawatomi_girl_1812` | 4,322,020 | 1,541,344 | 612,464 | 303,464 | 39,496 / 24,064 / 11,928 / 5,848 |
| (private, for comparison) | 4,589,652 | 1,672,800 | 680,468 | 341,616 | 44,914 / 27,310 / 13,442 / 6,489 |

Master (`assets/humans/`) LOD0 is 8.5-8.9 MB per asset (the private's is 9.2 MB). The skin atlas is
the shared one; no new textures (flat colours, plus the builder's own 256 px weave).

**Chest smoothing.** The shells are cut from the body's own topology, and on a child the nipples,
areolae and navel showed through every bodice and shirt at 3 m. `_drape()` (in the module) sets
each front chest point's depth from an area-weighted moving least-squares quadratic of the
garment round it (sigma 1.5 cm), never more than the ease less 4 mm inward. The shared
`cloth_torso` envelope was tried first and ballooned the chest and back into a barrel (the
`v4_*` stills); a Laplacian diffusion sank the dense nipple patches into dishes. Faint marks
remain in close views (see below).

## 5. Stills to look at

In the scratch folder (`<scratch>/dress/children/stills/`, the session scratch folder, renderer: three.js with ACES,
the shared assets, a ground plane; not committed):

- `<scratch>/dress/children/stills/final_lineup_y0_10m.jpg`, `final_lineup_y90_10m.jpg`, `final_lineup_y180_10m.jpg`:
  all five beside the private at 10 m (LOD1), front, side and back.
- `<scratch>/dress/children/stills/final_lineup_y0_3m.jpg`: the same at 3-5 m (LOD0).
- `<scratch>/dress/children/stills/final_child_boy_1812_3m_sheet.jpg`, `final_child_girl_1812_3m_sheet.jpg`,
  `final_child_toddler_1812_3m_sheet.jpg`, `final_potawatomi_boy_1812_3m_sheet.jpg`,
  `final_potawatomi_girl_1812_3m_sheet.jpg`: front, side, back at 3 m; `v7_pg.jpg` is the
  Potawatomi girl's chest close up at 1.4 m.
- `<scratch>/dress/children/stills/final_walk_idle.jpg`: the walk at two phases in profile and the idle, all six.
- Before and after: `v2_*` (the first fitted builds), `v3_potawatomi_*` (first Potawatomi build:
  the back flare of the shirt tail and peplum, the legging breaking through the moccasin top),
  `v4_child_boy_1812_3m_sheet.jpg` (the barrel from `cloth_torso`), `v6_pg.jpg` / `v7_pg.jpg`
  (the chest before and after the final smoothing).

## 6. What still reads wrong

- **Faint marks at the nipples in close views** (the Potawatomi girl's blouse most, the frocks
  less): the dense tiny triangles of the areola keep a little shading after the depth is
  smoothed. Invisible at 10 m, faint at 3 m, visible at 1.4 m.
- **Arms read a little muscular** in the long sleeves (the boy's jacket, the Potawatomi boy's
  shirt): the shell follows the arm's deltoid and biceps relief.
- **The Potawatomi boy's moccasins draw near-black** instead of smoked tan (they carry the
  builder's weave, see the shared-code note); the girl's draw right.
- **The boy's collar edge** is a little ragged at the shoulder tips (white flecks at 3 m), and the
  frill of the pictures is not there.
- **The frock skirts flare more behind than in front** (A-line centred on the spine): at 3 m in
  profile the girl's skirt reads with a slight train. Acceptable for an ankle-length frock; a
  front-back centred hem would be truer.
- **Everyone has the same short slicked hair and the default child face** (the shared short04
  hair). The girls of 1812 (and the Potawatomi girls: the research gives women long parted hair)
  want longer hair; the variation kit and `human-hair-styles.js` are where that belongs.
- **The 11-13-year-olds** stand on the 8-year bodies (section 1): above a height scale of about
  1.15 they read as tall 8-year-olds. If the kit's clip is widened to ages five to fourteen
  (about 1.26), the oldest will look stretched; a 12-year body is the fix.
- **Shared rig limits:** the idle stands with the arms a little out (A-pose); the moccasin is the
  shared closed shoe, 145 mm tall; no cloth simulation (skirts ride the pelvis and legs).

## 7. Rows for shared files

### assets/LICENSES.md

A paragraph for the section that holds the female base (T-1789 "original adult dress components
and verified female source base"), then the rows:

> `assets/authored/humans/makehuman_hm08/prepared_child_male_8.json`,
> `prepared_child_female_8.json`, `prepared_child_3.json`, their reports and the three
> `child_*.recipe.json` are original CC0-1.0 engineering derivatives of the same pinned MakeHuman
> graphical data (T-3465). The twelve child and baby macro targets preserve their upstream CC0
> notices; exact upstream commit, source URLs, bytes and SHA256 are in `SOURCE-child.json`, which
> repeats every `SOURCE.json` row unchanged. Category names are software provenance, not ancestry.

```
| `authored/humans/makehuman_hm08/SOURCE-child.json` | Project-authored CC0-1.0 graphical-source provenance, exact official upstream hashes and notices (T-3465). |
| `authored/humans/makehuman_hm08/child_male_8.recipe.json` | Original CC0-1.0 graphical blend recipe; reconstructed engineering parameters, no resident ancestry or portrait. |
| `authored/humans/makehuman_hm08/child_female_8.recipe.json` | Original CC0-1.0 graphical blend recipe; reconstructed engineering parameters, no resident ancestry or portrait. |
| `authored/humans/makehuman_hm08/child_3.recipe.json` | Original CC0-1.0 graphical blend recipe; reconstructed engineering parameters, no resident ancestry or portrait. |
| `authored/humans/makehuman_hm08/prepared_child_male_8.json` | CC0-1.0 engineering derivative of verified MakeHuman graphical data; complete anatomy/UV/rig retained. |
| `authored/humans/makehuman_hm08/prepared_child_male_8.report.json` | Project-authored CC0-1.0 preparation measurements and explicit unqualified limitations. |
| `authored/humans/makehuman_hm08/prepared_child_female_8.json` | CC0-1.0 engineering derivative of verified MakeHuman graphical data; complete anatomy/UV/rig retained. |
| `authored/humans/makehuman_hm08/prepared_child_female_8.report.json` | Project-authored CC0-1.0 preparation measurements and explicit unqualified limitations. |
| `authored/humans/makehuman_hm08/prepared_child_3.json` | CC0-1.0 engineering derivative of verified MakeHuman graphical data; complete anatomy/UV/rig retained. |
| `authored/humans/makehuman_hm08/prepared_child_3.report.json` | Project-authored CC0-1.0 preparation measurements and explicit unqualified limitations. |
```

One row per target (12), for `{caucasian,asian,african}-{male,female}-{child,baby}.target`:

```
| `authored/humans/makehuman_hm08/makehuman/data/targets/macrodetails/<category>-<sex>-<age>.target` | Verbatim MakeHuman graphical asset, CC0-1.0 explicit upstream header; original credit retained, pinned commit/URL/hash in SOURCE-child.json. |
```

One row per GLB (5 assets x 4 LODs x master and web = 40), e.g. for the boy:

```
| `humans/child_boy_1812.lod0.glb` | Original CC0-1.0 export of the canonical builder over the 8-year male child base and the 1812 children's components (`tools/human_child_1812.py`, T-3465); reconstructed under L418 and L-human-modular-dress-1789, not a likeness. |
| `humans/web/child_boy_1812.lod0.glb` | (same text) |
```

with "8-year female child base" for `child_girl_1812` and `potawatomi_girl_1812`, "3-year child
base" for `child_toddler_1812`, and "8-year male child base" for `potawatomi_boy_1812`; for the
two Potawatomi assets add "; review required, touches removal (AGENTS.md standing constraint)".

### tools/check.sh

```sh
step "The 1812 children's dress (town boy, girl and toddler; Potawatomi boy and girl) is sourced, layered and skinned on child bodies of the shared rig (T-3465)" \
  python3 tools/test_human_child_1812.py
```

### data/humans/variation/axes.json

The five `bases` rows in section 1 (with the kit change they need: no age drive for children,
and the wider height clips).

### docs/LIBERTIES.md and data/liberties.json: supplement to L-human-modular-dress-1789

> **The 1812 children supplement, 2026-11-08 (T-3465):** the modular dress path now dresses
> children, on two new CC0 engineering bodies blended from the pinned MakeHuman child and baby
> macro targets (an 8-year boy and girl at 120.8 and 120.5 cm, a 3-year child of either sex at
> 90.5 cm: CDC 2000 10th centile, the research's centile; ages linear between MakeHuman's baby (1)
> and child (10) anchors). Five anonymous role assets, `tools/human_child_1812.py`:
> `child_boy_1812` (a skeleton suit after Joshua Johnson's Rutter children and the Pixler
> family), `child_girl_1812` (a high-waisted frock after the Rutter girl, Emma Van Name and the
> Beecher frock, with a reconstructed pinafore), `child_toddler_1812` (the unbreeched child's
> white frock), and `potawatomi_boy_1812` and `potawatomi_girl_1812` (calico, stroud and
> moccasins of the camp, after Wau-Bun, Quaife, Hubbard and Keating; review required and touching
> removal, under the AGENTS.md standing constraint). The pictures are of Baltimore and rural
> Pennsylvania children in their best, and George Winter's 1837 picture of Potawatomi children is
> reference only (permission required, nothing taken). Every cut, ease, length, colour and the
> pinafore are reconstructed; no child at Chicago is pictured or described in these clothes, and
> no asset is a likeness of anyone. The baked walk is scaled to the child's leg (a stopgap until
> the builder takes a walk scale). **How to resolve:** a 12-year body for the 11-13-year-olds,
> the frill of the boy's collar, sunbonnets and caps, bare feet in summer, the head kerchief of
> the Potawatomi girls, and a review of the Potawatomi pair by people with standing to judge.

### Other shared-code notes (not rows; for whoever owns the builder)

- **Weave darkening (affects the private too).** `human_teamster_blend.py` writes the weave
  material's *linear* colour into an image tagged sRGB (the "original reconstructed cloth weave"),
  so the cloth it lands on draws far darker than its recipe colour: a rose bodice went maroon, a
  blue jacket black, the private's linen overalls are greyer than recipe. Fix: write
  `linear_to_srgb(base)` into the pixels (or tag the image Non-Color and keep linear values).
  Workaround here: each child's `weave_material` is its shoes (dark leather barely changes); the
  Potawatomi girl's is the stroud's white selvage (draws light grey, an acceptable undyed list).
  The Potawatomi boy's moccasins carry it and draw darker than smoked deerskin.
- **Shared shoe height.** `fitted_shoes` is open at a fixed 145 mm, which on the toddler reaches
  more than half way to the knee (hidden by the frock) and on the 8-year bodies is a short boot.
  The Potawatomi recipes raise `shoe_clearance_m` to 0.009 so the moccasin stands outside the
  legging and its top reads as a clean cuff; a height scaled to the ankle would be better.
- **Normal tolerance.** All builds need `--normal-tolerance 5e-3` on this machine (above).
