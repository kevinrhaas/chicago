# The 1812 women's dress on the shared female rig (T-3464)

Builder notes for the women of the 1812 town and of the Potawatomi camp: three roles (four
assets) on the shared portable female rig (`prepared_adult_female_25.json`, `skirt: true`), and
every row the integrator has to add to a shared file (none of those files was touched here).

| Asset id | Role | Who wears it (T-3464 / T-3467 research) |
|---|---|---|
| `lady_1812` | An officer's or trader's wife in day dress: a high-waisted gown of a small dark-blue print, long close sleeves, a narrow skirt to the ankle with its fullness behind, a white muslin kerchief crossed in front, a white cotton day cap with a narrow frill, flat black shoes | Mrs Heald, Mrs Helm, Eleanor Kinzie, the matrons |
| `woman_working_1812` | A soldier's wife or laundress: a madder-print short gown to the hip with sleeves just below the elbow, a blue homespun petticoat to the ankle, a broad natural-linen apron, a white neck kerchief, a plain linen cap, heavy shoes | the laundresses, the settlers' wives, Cicely (the Healds' servant) |
| `woman_country_1812` | Variant of `woman_working_1812` (same recipe and assembly): a French woman of the country, Wau-Bun's short gown (red print) and petticoat (dark stroud) "with a blue cotton handkerchief wrapped around her head", the apron and kerchief, moccasins | Archange Ouilmette, Mrs Bisson, Josette LaFramboise, the women of the country |
| `potawatomi_woman_1812` | A Potawatomi woman of the camp: a wrapped dark-blue strouding skirt to mid-calf with its undyed selvage at the hem, a red-print calico shirt over it to the hip, red cloth leggings, moccasins, an undecorated off-white trade blanket round the shoulders to the hip, three small silver brooches at the shirt's neck; bare-headed | the Potawatomi women of the camp and the elder woman (`potawatomi_elder_woman_1812` can wear it until a faded variant exists) |

Generator `tools/human_women_1812.py` (one module, three roles; the `role_1812.prepare` hooks
are `prepare_lady`, `prepare_working`, `prepare_potawatomi`). Recipes
`data/humans/recipes/lady_1812.json`, `woman_working_1812.json` (both variants),
`potawatomi_woman_1812.json`. Test `tools/test_human_women_1812.py` (8 tests, pure Python,
about 15 s; passes). Liberty `L-human-modular-dress-1789` for cut and colour (supplement text
below), `L418` for the body and skin path, as the private.

Hair is the looks layer's at runtime (`centre_part_knot_1835` for the town women,
`centre_part_clubbed_1812` for the Potawatomi woman), so the assets carry only the private's
own short04 hair cap (it keeps every asset inside the private's byte budget; the 1904 bun proxy's
atlas would add about 2.5 MB at LOD0). The cap and the blue cotton handkerchief are in the
assets, rigid on the head bone, as the integrator asked. The Potawatomi woman has no knot or bun
in the asset: it would only sit under the drawn hair and cost 360 triangles at every LOD.

Research read: `docs/RESEARCH/people-1812-3461/dress.json` (officer's wife and laundress, trader
and wife, woman of the country), `native.json` (`dress_evidence`),
`docs/RESEARCH/people-1812-3464/day.json` (`dress`: the officers' wives, laundresses, settlers'
wives, Cicely, the women of the country) and `docs/RESEARCH/people-1812-3467/day.json`
(`dress.potawatomi_woman_1812`, `potawatomi_elder_woman_1812`).

## 1. The dress and its evidence

Every garment is graded in its recipe with `source_ids` and the liberty; nothing is graded
attested (no witness of 1812 at Chicago describes these women's clothes in detail).

**lady_1812** (`kinzie_waubun_1856` as the person-reference record). Gown bodice and skirt
*inferred* from the Met's American linen dress of 1810-20 and Krimmel's *Sunday Morning in
Arch Street* (1811), with Wau-Bun for the officers' wives at the post; colour (a small blue
print drawn as its mean, not white silk) reconstructed. Waist band *reconstructed*. Muslin
kerchief *inferred* (Krimmel's *Merrymaking at a Wayside Inn*; Lambert's handkerchiefs). Day cap
*inferred* (the Met's American cap of 1810-20, the Pixler family c.1815, Krimmel's *Chimney
Sweeps*, Lambert). Flat shoes *reconstructed* (the shared closed shoe).

**woman_working_1812 / woman_country_1812** (`kinzie_waubun_1856`). Short gown and petticoat
*inferred* from Wau-Bun's "short gown and petticoat" (Chicago, 1812), Lambert's Lower Canada
country women (1810) and Krimmel's *Black Sawyers* (1811); apron, neck kerchief and linen cap
*inferred* from Lambert; colours reconstructed (madder print, blue homespun; for the woman of
the country a red print and dark stroud, T-3464's reading). The blue cotton handkerchief round
the head *inferred* from Wau-Bun (16 August 1812), not attested, because Wau-Bun is the family's
narrative of 1856; how it is wrapped and the knot at the nape are reconstructed. Moccasins
*inferred* (Lambert; Wau-Bun's engagé). The sleeves end just below the elbow; the petticoat is
not kilted up.

**potawatomi_woman_1812** (`quaife_1913`; `review_required` and `touches_removal` with their
own prose). Strouding skirt, calico shirt, blanket and brooches *inferred* from the goods
distributed on the 13th ("blankets, broadcloths, calicoes, paints": Wau-Bun; Heald dates it the
14th) and the annual presents ("blankets, broadcloths or strouding, calicoes ... silver-works
(comprising arm-bands, bracelets, brooches; and ear-bobs)", Wau-Bun), with Quaife's 1833
synthesis as a late bound and Hubbard's calico shirt (a man's, 1818-19). The white selvage at the
hem *reconstructed*: T-3467 reads it in George Winter's 1837 Potawatomi pictures, which have no
cleared record in `data/sources`, so none is cited. Leggings *reconstructed* (the sources read
name men's leggings only). The blanket is worn round the shoulders and open in front; Currey
(1912) has the women's heads covered with blankets, the other way of wearing it, not drawn.
Not drawn: paint (there is no source for its everyday use by women on the 14th; the war paint of
the 15th is not this day), ribbonwork (the 1830s-40s pictures are later), beads, ear-bobs,
arm-bands, a cradleboard, anything ceremonial, any Plains stereotype.

New source records written (cleared, public domain, from `dress.json` `new_sources`):
`met_krimmel_1811_black_sawyers_bank_of_pennsylvania`, `met_krimmel_1811_merrymaking_wayside_inn`,
`met_krimmel_1811_sunday_morning_arch_street`, `met_krimmel_1811_chimney_sweeps_christ_church`,
`met_ci_1810_1820_american_linen_dress`, `met_ci_1810_1820_american_cap`. Also used (written by
other builders): `met_pixler_family_c1815`, `lambert_1810_travels_lower_canada_v1`.

## 2. The builds

Built one at a time with the real pinned Blender 4.5.3 binary (downloaded and sha-verified into
the scratch folder, not the bpy shim) through `tools/human_teamster_blend.py` with
`--normal-tolerance 5e-3` (the integrator's ruling). Every build reported the same LOD0 body
custom-normal readback delta, **max_vector_delta 0.0020631715119682047** (the female body; it
exceeds the default 1e-3 on this machine for every builder's and every committed asset's
rebuild). An early lady master was built from a scratch copy of the builder byte-identical but
for that bound; it was rebuilt with the flag, and every shipped GLB comes from a flagged build.
Exported with `bash tools/human_export.sh --master <scratch>/<asset>.blend`;
`python3 tools/human_contract.py --glb` passes on all 32 GLBs.

| Asset | LOD | web bytes | web triangles | master bytes |
|---|---|---|---|---|
| `lady_1812` | 0 | 4,331,320 | 41,078 | 8,679,584 |
| | 1 | 1,547,748 | 25,013 | 7,953,604 |
| | 2 | 613,000 | 12,377 | 7,329,820 |
| | 3 | 300,984 | 6,037 | 7,064,284 |
| `woman_working_1812` | 0 | 4,378,120 | 43,514 | 8,840,076 |
| | 1 | 1,587,744 | 26,472 | 8,065,080 |
| | 2 | 636,904 | 13,055 | 7,380,696 |
| | 3 | 314,836 | 6,333 | 7,082,704 |
| `woman_country_1812` | 0 | 4,375,500 | 43,244 | 8,828,776 |
| | 1 | 1,584,508 | 26,311 | 8,057,860 |
| | 2 | 635,228 | 12,979 | 7,377,008 |
| | 3 | 314,208 | 6,300 | 7,080,984 |
| `potawatomi_woman_1812` | 0 | 4,402,336 | 44,115 | 8,899,380 |
| | 1 | 1,599,060 | 26,837 | 8,101,104 |
| | 2 | 644,420 | 13,222 | 7,406,696 |
| | 3 | 319,368 | 6,402 | 7,095,112 |
| *private (budget)* | 0/1/2/3 | 4,589,652 / 1,672,800 / 680,468 / 341,616 | 44,914 / 27,310 / 13,442 / 6,489 | |

All four are under the private at every LOD in bytes and triangles: flat colours, the shared
skin atlas (the 1904 cook's bronze female atlas), the private's short04 hair atlas, the same LOD
ratios. `woman_country_1812` costs a whole asset of bytes; drop it if the phone budget needs
the room (its wearers could take `woman_working_1812`).

**Weave workaround.** As the children's notes say, the builder writes the weave material's
linear colour into an sRGB-tagged image, so cloth carrying it draws far darker than its recipe
(a blue gown went near black). Each woman's `weave_material` is her shoes.

## 3. Stills to look at

In the session scratch folder (not committed)
(the lineup rig, `dress=1&year=1812`, 3 m, 10 m and close, front, side, back, three-quarter):
the contact sheets `lady_1812-sheet.jpg`, `woman_working_1812-sheet.jpg`,
`woman_country_1812-sheet.jpg`, `potawatomi_woman_1812-sheet.jpg`; the best single frames are
`<asset>-3m-q.png` and `<asset>-3m-side.png`, and `<asset>-close-front.png` for the head covers
and kerchiefs.

## 4. What still reads wrong

- **Lady:** the kerchief still reads as a smooth white plate on the chest; its folds and the
  crossed edge barely show. The cap is smooth, like a swim cap from behind (the frill reads only
  in front). The skirt's gathers are faint; the gown reads plain dark slate rather than a print.
- **Working woman and woman of the country:** a notch in the kerchief's lower edge, and a
  crease under the bust where the short gown meets its skirt. The blue handkerchief is a smooth
  close cover with a small knot; a real wrapped handkerchief has more bulk and folds.
- **Potawatomi woman:** in the rest pose the blanket reads as a short white cape or jacket over
  the shoulders and upper arms, not a wrapped blanket (a shell skinned to the arms cannot hang as
  loose wool; how it drapes when the arms come down is unchecked). A faint relief of the bust
  shows through it. A dark fleck at the blanket's lower back edge (a small poke-through).
- **All:** the shared closed shoe stands for flat shoes and moccasins alike. No cloth simulation:
  the skirts follow the legs by weights (T-3423), and walking clearance is not checked. Prints
  and checks are drawn as their mean colour.

## 5. Rows for shared files

### assets/LICENSES.md

One row per GLB, as the private's (32 rows: `humans/<asset>.lod{0..3}.glb` and
`humans/web/<asset>.lod{0..3}.glb` for each of `lady_1812`, `woman_working_1812`,
`woman_country_1812`, `potawatomi_woman_1812`):

```
| `humans/lady_1812.lod0.glb` | Original CC0-1.0 export of the canonical builder over the shared female base and the 1812 lady's day dress (`tools/human_women_1812.py`, T-3464); the shared cleared short04 hair cap and bronze female skin atlas; reconstructed under L418 and L-human-modular-dress-1789, not a likeness. |
| `humans/woman_working_1812.lod0.glb` | Original CC0-1.0 export of the canonical builder over the shared female base and the 1812 working woman's dress (`tools/human_women_1812.py`, T-3464); the shared cleared short04 hair cap and bronze female skin atlas; reconstructed under L418 and L-human-modular-dress-1789, not a likeness. |
| `humans/woman_country_1812.lod0.glb` | Original CC0-1.0 export of the canonical builder over the shared female base and the 1812 woman of the country's dress (`tools/human_women_1812.py`, T-3464); the shared cleared short04 hair cap and bronze female skin atlas; reconstructed under L418 and L-human-modular-dress-1789, not a likeness. |
| `humans/potawatomi_woman_1812.lod0.glb` | Original CC0-1.0 export of the canonical builder over the shared female base and the everyday dress of a Potawatomi woman of the 1812 camp (`tools/human_women_1812.py`, T-3464; review required, touches removal); the shared cleared short04 hair cap and bronze female skin atlas; reconstructed under L418 and L-human-modular-dress-1789, not a likeness. |
```

(and the same text for `lod1`-`lod3` and each `humans/web/` copy).

### tools/check.sh

```sh
step "The 1812 women's dress (lady, working woman, woman of the country, Potawatomi woman) is sourced, layered, skinned and the Potawatomi figure held for review on the shared rig (T-3464)" \
  python3 tools/test_human_women_1812.py
```

### data/humans/variation/axes.json

`bases` rows (the female base age 25, as the 1904 cook; the face settings can follow
`ryan_kate_1904_cook` or be left to the kit's female defaults):

```json
"lady_1812": {"base_age_years": 25, "sex": "female", "basis": "data/humans/recipes/lady_1812.json: the prepared_adult_female_25 engineering body, an officer's or trader's wife of 1812 (Mrs Heald, Mrs Helm, Eleanor Kinzie, the matrons), T-3464."},
"woman_working_1812": {"base_age_years": 25, "sex": "female", "basis": "data/humans/recipes/woman_working_1812.json: the prepared_adult_female_25 engineering body, a soldier's wife or laundress of 1812 (the laundresses, settlers' wives, Cicely), T-3464."},
"woman_country_1812": {"base_age_years": 25, "sex": "female", "basis": "data/humans/recipes/woman_working_1812.json (variant woman_country_1812): the prepared_adult_female_25 engineering body, a French woman of the country of 1812 (Archange Ouilmette, Mrs Bisson, Josette LaFramboise), T-3464."},
"potawatomi_woman_1812": {"base_age_years": 25, "sex": "female", "basis": "data/humans/recipes/potawatomi_woman_1812.json: the prepared_adult_female_25 engineering body, a Potawatomi woman of the 1812 camp (also the elder woman), T-3464."}
```

### docs/LIBERTIES.md and data/liberties.json: supplement to L-human-modular-dress-1789

> **The 1812 women supplement, 2026-11-08 (T-3464):** the modular dress path now dresses the
> women of the 1812 town and camp on the shared female rig, one generator
> (`tools/human_women_1812.py`) and four anonymous role assets: `lady_1812` (an officer's or
> trader's wife's high-waisted day gown of a small blue print, a muslin kerchief and a day cap,
> after the Met's American linen dress and cap of 1810-20 and Krimmel's Philadelphia pictures of
> 1811), `woman_working_1812` (Wau-Bun's short gown and petticoat with an apron, kerchief and
> linen cap, after Lambert's country women of 1810 and Krimmel's *Black Sawyers*), its variant
> `woman_country_1812` (the same in a red print and dark stroud with Wau-Bun's "blue cotton
> handkerchief wrapped around her head" and moccasins), and `potawatomi_woman_1812` (a wrapped
> strouding skirt with its selvage at the hem, a calico shirt, cloth leggings, moccasins, a
> trade blanket and three small silver brooches, from the goods distributed to the camp on the
> 13th and the presents of the years before, Wau-Bun, Quaife and Hubbard; review required and
> touching removal, under the AGENTS.md standing constraint; no paint, nothing ceremonial). The
> pictures are of Philadelphia and Lower Canada and the garments in museums are of the eastern
> states; no woman at Chicago is pictured in these clothes, and no asset is a likeness of anyone.
> Every cut, ease, length, fold, colour and the Potawatomi selvage are reconstructed; prints are
> drawn as their mean colour; hair is drawn by the looks layer. **How to resolve:** a printed
> cloth texture within the budget, a crossed kerchief with real folds, a blanket that hangs as
> loose wool when the arms come down, a faded variant for the elder woman, the Potawatomi
> woman's beads and ear-bobs if a source of 1812 names them, and a review of the Potawatomi
> figure by people with standing to judge (the Newberry's Indigenous Chicago material and the
> Citizen Potawatomi Nation's own record).

### Other notes for the integrator

- **Source locators.** `lambert_1810_travels_lower_canada_v1`'s locator does not point to the
  women's passage it is cited for (the country women's short gowns, petticoats, caps and
  handkerchiefs, pp. 163-164; djvu text lines about 7128-7140); add it. The
  `kinzie_waubun_1856` record's locator does not name the 1812 passages these recipes use (the
  goods of the 13th; the "short gown and petticoat, with a blue cotton handkerchief" of 16 August;
  the annual presents in chapter I).
- **Pictures with no cleared record.** T-3467 builds on `tcha_winter_1837_sin_is_quaw`,
  `crystal_bridges_winter_1837_eight_potawatomi`, `williams_catlin_potawatomi_woman` and
  `dia_2006_44_miami_womens_leggings`, none of which has a record in `data/sources`; they are not
  cited here, and the selvage and the leggings stay reconstructed until they are.
- **Wiring ids.** `place_town.py` can use `lady_1812` (officers' wives, Eleanor Kinzie,
  matrons), `woman_working_1812` (laundresses, settlers' wives, Cicely), `woman_country_1812`
  (Archange Ouilmette, Mrs Bisson, the women of the country) and `potawatomi_woman_1812` (the
  women of the camp, the elder woman).
