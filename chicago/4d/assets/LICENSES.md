# Asset licenses

Every file under `assets/` needs an entry here, matched by its path relative to
`assets/`. `tools/check.sh` fails if one is missing. CC0 and CC-BY only unless a
clearance is recorded below.

Generated output (`gltf/`, `web/`) is covered by the project's own license and by the
provenance of the data it was generated from — but any **texture, audio, or authored
asset** brought in from outside needs its own row, with a URL and the license name.

Two files here are build RECORDS rather than assets, carry no third-party content, and
are covered by the project's own license along with the output they describe:
`manifest.json`, written by the Blender build, records data → master; and
`manifest.web.json`, written by `tools/web_derivatives.sh`, records master →
derivative (ROADMAP K39). A third, `manifest.versions.json`, records both links for
the structure VERSIONS under `gltf/versions/` and `web/versions/` (T-1727) — generated
output of the same kind, from alternate records under `data/structures/versions/`.

## Rights gating

A source whose `rights_status` is `check_required` or `restricted` in `data/sources/`
may be cited in text but **must not have assets derived from it**. The validator
enforces this against the source's `asset_use` field. Currently gated:

| source | status | why |
|---|---|---|
| `conley_stelzer_1933` | `check_required` | 1933 US publication; BPL asserts no known restrictions but a dealer reports a 1933 copyright stamp. Public domain only if the 1961 renewal lapsed. Run a Stanford Copyright Renewal Database check and record the outcome in the source record before deriving any asset. |
| `chicagology_*` | `check_required` | The site carries no license statement. It is a transcription and finding aid; re-source every image from the holding institution before it enters the model. |
| `drloih_hotels` | `check_required` | Unfootnoted blog; leads only. |

## Recorded clearances — the CC0/CC-BY default, excepted

The default above is CC0 and CC-BY only. Each exception is a decision recorded here,
with what it permits and what it does not.

| item | licence | cleared for | NOT cleared for |
|---|---|---|---|
| `data/sources/assets/saari_2018_dupage_tallgrass/dupage_tallgrass_2018-07-24.jpg` — Cassi Saari, *Restored tallgrass prairie in DuPage County, Illinois*, 24 July 2018, [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Restored_tallgrass_prairie_in_DuPage_County,_Illinois.jpg) | **CC BY-SA 4.0**, attribution required | **Verbatim redistribution in this repository, and measurement.** Committed byte-for-byte unmodified (SHA-1 `0da00f1178e7790b04c05364d78f7cb6a43992ae`, identical to the Commons API's SHA-1 for the file page), so what is redistributed is the licensed work and not an adaptation — ShareAlike is not triggered. Source record `saari_2018_dupage_tallgrass`; attribution carried there, in the README beside the image, and here. | **Any derived asset.** A crop, a resample, a texture, a colour LUT or a tile built from it is an adaptation, and CC BY-SA 4.0 would require releasing that adaptation under CC BY-SA 4.0. This project derives nothing from it: it is read by `tools/measure_reference.py` and never enters a scene. `tools/publish.sh` does not copy `data/sources/`, so it is not on the published site. Anyone wanting to derive from it must take the ShareAlike obligation on deliberately, not by accident. |
| `data/sources/assets/samstone_2017_tallgrass_trail/tallgrass_prairie_trail_2017-09-08.jpg` — Samstone13, *Tallgrass Prairie Trail*, 8 September 2017, [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Tallgrass_Prairie_Trail.jpg) | **CC BY-SA 4.0**, attribution required | **Verbatim redistribution in this repository, and measurement.** Committed byte-for-byte unmodified (SHA-1 `c2da32962b8c4ddb73b8f2cd36f4a39abeff7628`), so what is redistributed is the licensed work and not an adaptation — ShareAlike is not triggered. Source record `samstone_2017_tallgrass_trail`; it is the road-contrast reference for R-M1b. | **Any derived asset.** A crop, a resample, a texture or a tile built from it is an adaptation and would have to be released under CC BY-SA 4.0. This project derives nothing from it: it is measured and never enters a scene. `tools/publish.sh` does not copy `data/sources/`, so it is not on the published site. |
| `data/sources/assets/haas_2021_sagebrush_two_track/sagebrush_two_track_2021-06-26.jpg` — Kevin Haas, *Earth two-track through sagebrush steppe*, 26 June 2021 | **All rights reserved.** The owner's own photograph, deliberately NOT under an open licence | **Reading it, to check the figures derived from it.** Committed verbatim (SHA-1 `9fdb465d952b98adb6ada9356f21df8c76897bd1`, 4032x3024) so a reader can verify a measurement against the pixels it came from — which is this project's standard and why it is committed rather than withheld. Source record `haas_2021_sagebrush_two_track`; it is the far-band road-contrast reference for R-M1b. | **Reuse of any kind.** No redistribution, no republication, no derived asset — not a crop, a resample, a texture or a tile. VISIBLE IS NOT REUSABLE: this is the one row in this table outside the CC0/CC-BY default, at the owner's direction of 2026-08-15. `tools/publish.sh` does not copy `data/sources/`, so it is not on the published site. |

| `gifford_tremont_house_no_1` — N. Roswell Gifford, first Tremont drawing, reproduced by [Chicagology](https://chicagology.com/prefire/prefire021/) | **Owner-approved attributed project use**, 2026-10-22; original publication/collection and copyright status unresolved | Reference, picture comparison/source display and this project’s explicitly reconstructed Tremont appearance. Credit and source link retained in the source record and research comparison. Generated model contains no external image texture. | Public-domain status, copyright-holder permission, an open redistribution licence or any geographic/metric survey claim. |

Held out of the published tree entirely, by the user's instruction:

| item | disposition |
|---|---|
| `chicago/reference/photos/old-chicago-complete-map.png` (Nelson & Winters, *Old Chicago*, © 1940) | **Reference and research only — never published**, per Kevin's instruction. Now formally citable as `nelson_winters_1940` in `data/sources/` (tier 6, `asset_use: orientation`): toponym and trail-network cross-checks only, no geometry, never sole evidence. Public domain only if the 1968 renewal lapsed — unchecked. |

## Third-party assets

### The 1835 PBR texture library — `textures/chicago_1835_pbr/`

The first texture arrival this file anticipated. Supplied by the owner 2026-09-19; 25
materials, procedurally synthesised by the generator that ships inside it
(`tools/generate_1835_pbr_library.py`, seeded per material, deterministic). Provenance and
the measurements that say which maps may be bound to a surface are in
`docs/RESEARCH/texture_library.md`; adoption is T-1450.

| item | licence | cleared for | NOT cleared for |
|---|---|---|---|
| `textures/chicago_1835_pbr/**` — *Chicago 1835 PBR Texture Library v1.0.0*, original procedural output generated for this project. Full text at `textures/chicago_1835_pbr/LICENSE.txt` | **Project-permissive, CC0-equivalent.** "The maps and generator may be used, modified, and redistributed with the project." No third-party photograph is embedded or sampled in the production maps | **Use, modification and redistribution with the project**, including derived and regenerated maps — the generator ships, so a map may be re-derived rather than re-authored. | **Stripping the confidence labels.** The licence carries one condition and it is this project's own standard: *"Historical confidence labels and provenance notes should remain attached so reconstructed surfaces are not silently represented as attested evidence."* Every `material.json` carries its `confidence` tier and its note, and they travel with the maps. |
| `textures/chicago_1835_pbr/tools/source_mud_ai.png` — the flat-lit mud study `muddy_rutted_street` is derived from | as above | **Reading, and deriving the mud maps from it**, which is what it is for | **Being described as a photograph.** It is an AI-generated study, not a camera image and not a period source. It is evidence of nothing about 1835 and is committed so the derivation can be checked. |

**Not published.** `tools/publish.sh` copies named files and `assets/web/*.glb`; it does not
walk `assets/`, so this directory stays in the repository and off the live site. It is carried
for the web renderer's relief maps and for the Unreal target's DirectX normals, packed ORM and
16-bit displacement. The `.webp` beside ten of the maps is a lossless derivative of
its PNG master, the same pixels in fewer bytes, written and held pixel-identical by
`tools/web_textures.py` (T-1973). Beside the two signboard-wood sheets the same tool writes
four DERIVED tiles instead (T-2590): `_grain.webp`, the basecolor's grain read down to 512²,
turned a quarter and normalised about mid-grey, and `_normal_turned.webp`, the normal read
down and turned with its vectors — what `renderers/web/js/signage.js` used to compute from
the maps at every boot, now computed once and held to that computation pixel for pixel.
Those fourteen are the one exception to "not published": `tools/publish.sh` copies them by
name to `data/textures/`, where the relief modules bind them. They carry the library's
licence and its one condition unchanged.

**The `.ktx2` beside six of them (T-2582, T-2590)** — the two roof coverings' `normal_gl`
and `orm` and the wet prairie muck's and the dune sand's basecolor — is the same map
GPU-compressed by
`tools/ktx2_sheets.py` with KTX-Software 4.3.2 (Basis Universal: ETC1S for the colour, UASTC
for the data maps), from the PNG master. It is lossy where the `.webp` is not, a derivative
for the GPU and not a new map, and `tools/publish.sh` copies it by name beside its `.webp`
or `.png`. It carries the library's licence and its one condition unchanged. The sand's
`_basecolor.luma.json` beside it is one number derived from its master by the same tool
— the mean linear luminance the ground strip once read from the image's pixels — and
carries no pixels at all.

**The wall relief's `.ktx2` and its statement (T-2588)** — `clapboard_board_face` and
`hewn_log_face` each carry a `_normal_gl.ktx2` (the normal, UASTC) and an `_orl.ktx2`, the
map `renderers/web/js/relief-pack.js` used to pack in the page from the `orm` and the
basecolor (R = AO, G = roughness, B = the basecolor's luminance over its mean; ETC1S), written
by `tools/ktx2_sheets.py` from the PNG masters, plus `_orl.json` stating the mean roughness
and the masters' hashes. Derivatives of the library's own maps, lossy, for the GPU; they
carry the library's licence and its one condition unchanged.

**The frontage timber's two (T-2589)** — the board face's `orm` and
`clapboard_board_face_grain.ktx2`, the albedo modulation `renderers/web/js/frontage.js` used to
derive from the basecolor at load — are written the same way by the same tool, from the PNG
masters (the grain from the basecolor master, by `packGrain`'s own arithmetic); the layer's
normal is the wall's `_normal_gl.ktx2` above. The grain is a derived map of the library's
basecolor, not a new image; both carry the library's licence and its one condition unchanged.

Every file, as the checker matches them one by one:

```
textures/chicago_1835_pbr/LICENSE.txt
textures/chicago_1835_pbr/README.md
textures/chicago_1835_pbr/RESEARCH_NOTES.md
textures/chicago_1835_pbr/contact_sheet.jpg
textures/chicago_1835_pbr/ground/lake_michigan_dune_sand/lake_michigan_dune_sand_ao.png
textures/chicago_1835_pbr/ground/lake_michigan_dune_sand/lake_michigan_dune_sand_basecolor.ktx2
textures/chicago_1835_pbr/ground/lake_michigan_dune_sand/lake_michigan_dune_sand_basecolor.luma.json
textures/chicago_1835_pbr/ground/lake_michigan_dune_sand/lake_michigan_dune_sand_basecolor.png
textures/chicago_1835_pbr/ground/lake_michigan_dune_sand/lake_michigan_dune_sand_height16.png
textures/chicago_1835_pbr/ground/lake_michigan_dune_sand/lake_michigan_dune_sand_metallic.png
textures/chicago_1835_pbr/ground/lake_michigan_dune_sand/lake_michigan_dune_sand_normal_dx.png
textures/chicago_1835_pbr/ground/lake_michigan_dune_sand/lake_michigan_dune_sand_normal_gl.png
textures/chicago_1835_pbr/ground/lake_michigan_dune_sand/lake_michigan_dune_sand_orm.png
textures/chicago_1835_pbr/ground/lake_michigan_dune_sand/lake_michigan_dune_sand_roughness.png
textures/chicago_1835_pbr/ground/lake_michigan_dune_sand/material.json
textures/chicago_1835_pbr/ground/muddy_rutted_street/material.json
textures/chicago_1835_pbr/ground/muddy_rutted_street/muddy_rutted_street_ao.png
textures/chicago_1835_pbr/ground/muddy_rutted_street/muddy_rutted_street_basecolor.png
textures/chicago_1835_pbr/ground/muddy_rutted_street/muddy_rutted_street_height16.png
textures/chicago_1835_pbr/ground/muddy_rutted_street/muddy_rutted_street_metallic.png
textures/chicago_1835_pbr/ground/muddy_rutted_street/muddy_rutted_street_normal_dx.png
textures/chicago_1835_pbr/ground/muddy_rutted_street/muddy_rutted_street_normal_gl.png
textures/chicago_1835_pbr/ground/muddy_rutted_street/muddy_rutted_street_orm.png
textures/chicago_1835_pbr/ground/muddy_rutted_street/muddy_rutted_street_roughness.png
textures/chicago_1835_pbr/ground/packed_black_loam/material.json
textures/chicago_1835_pbr/ground/packed_black_loam/packed_black_loam_ao.png
textures/chicago_1835_pbr/ground/packed_black_loam/packed_black_loam_basecolor.png
textures/chicago_1835_pbr/ground/packed_black_loam/packed_black_loam_height16.png
textures/chicago_1835_pbr/ground/packed_black_loam/packed_black_loam_metallic.png
textures/chicago_1835_pbr/ground/packed_black_loam/packed_black_loam_normal_dx.png
textures/chicago_1835_pbr/ground/packed_black_loam/packed_black_loam_normal_gl.png
textures/chicago_1835_pbr/ground/packed_black_loam/packed_black_loam_orm.png
textures/chicago_1835_pbr/ground/packed_black_loam/packed_black_loam_roughness.png
textures/chicago_1835_pbr/ground/river_stone_gravel_fill/material.json
textures/chicago_1835_pbr/ground/river_stone_gravel_fill/river_stone_gravel_fill_ao.png
textures/chicago_1835_pbr/ground/river_stone_gravel_fill/river_stone_gravel_fill_basecolor.png
textures/chicago_1835_pbr/ground/river_stone_gravel_fill/river_stone_gravel_fill_height16.png
textures/chicago_1835_pbr/ground/river_stone_gravel_fill/river_stone_gravel_fill_metallic.png
textures/chicago_1835_pbr/ground/river_stone_gravel_fill/river_stone_gravel_fill_normal_dx.png
textures/chicago_1835_pbr/ground/river_stone_gravel_fill/river_stone_gravel_fill_normal_gl.png
textures/chicago_1835_pbr/ground/river_stone_gravel_fill/river_stone_gravel_fill_orm.png
textures/chicago_1835_pbr/ground/river_stone_gravel_fill/river_stone_gravel_fill_roughness.png
textures/chicago_1835_pbr/ground/wet_prairie_muck/material.json
textures/chicago_1835_pbr/ground/wet_prairie_muck/wet_prairie_muck_ao.png
textures/chicago_1835_pbr/ground/wet_prairie_muck/wet_prairie_muck_basecolor.ktx2
textures/chicago_1835_pbr/ground/wet_prairie_muck/wet_prairie_muck_basecolor.png
textures/chicago_1835_pbr/ground/wet_prairie_muck/wet_prairie_muck_height16.png
textures/chicago_1835_pbr/ground/wet_prairie_muck/wet_prairie_muck_metallic.png
textures/chicago_1835_pbr/ground/wet_prairie_muck/wet_prairie_muck_normal_dx.png
textures/chicago_1835_pbr/ground/wet_prairie_muck/wet_prairie_muck_normal_gl.png
textures/chicago_1835_pbr/ground/wet_prairie_muck/wet_prairie_muck_orm.png
textures/chicago_1835_pbr/ground/wet_prairie_muck/wet_prairie_muck_roughness.png
textures/chicago_1835_pbr/manifest.json
textures/chicago_1835_pbr/masonry/cat_and_clay_chimney/cat_and_clay_chimney_ao.png
textures/chicago_1835_pbr/masonry/cat_and_clay_chimney/cat_and_clay_chimney_basecolor.png
textures/chicago_1835_pbr/masonry/cat_and_clay_chimney/cat_and_clay_chimney_height16.png
textures/chicago_1835_pbr/masonry/cat_and_clay_chimney/cat_and_clay_chimney_metallic.png
textures/chicago_1835_pbr/masonry/cat_and_clay_chimney/cat_and_clay_chimney_normal_dx.png
textures/chicago_1835_pbr/masonry/cat_and_clay_chimney/cat_and_clay_chimney_normal_gl.png
textures/chicago_1835_pbr/masonry/cat_and_clay_chimney/cat_and_clay_chimney_orm.png
textures/chicago_1835_pbr/masonry/cat_and_clay_chimney/cat_and_clay_chimney_roughness.png
textures/chicago_1835_pbr/masonry/cat_and_clay_chimney/material.json
textures/chicago_1835_pbr/masonry/chicago_clay_brick_lime_mortar/chicago_clay_brick_lime_mortar_ao.png
textures/chicago_1835_pbr/masonry/chicago_clay_brick_lime_mortar/chicago_clay_brick_lime_mortar_basecolor.png
textures/chicago_1835_pbr/masonry/chicago_clay_brick_lime_mortar/chicago_clay_brick_lime_mortar_height16.png
textures/chicago_1835_pbr/masonry/chicago_clay_brick_lime_mortar/chicago_clay_brick_lime_mortar_metallic.png
textures/chicago_1835_pbr/masonry/chicago_clay_brick_lime_mortar/chicago_clay_brick_lime_mortar_normal_dx.png
textures/chicago_1835_pbr/masonry/chicago_clay_brick_lime_mortar/chicago_clay_brick_lime_mortar_normal_gl.png
textures/chicago_1835_pbr/masonry/chicago_clay_brick_lime_mortar/chicago_clay_brick_lime_mortar_orm.png
textures/chicago_1835_pbr/masonry/chicago_clay_brick_lime_mortar/chicago_clay_brick_lime_mortar_roughness.png
textures/chicago_1835_pbr/masonry/chicago_clay_brick_lime_mortar/material.json
textures/chicago_1835_pbr/masonry/limestone_rubble_lime_mortar/limestone_rubble_lime_mortar_ao.png
textures/chicago_1835_pbr/masonry/limestone_rubble_lime_mortar/limestone_rubble_lime_mortar_basecolor.png
textures/chicago_1835_pbr/masonry/limestone_rubble_lime_mortar/limestone_rubble_lime_mortar_height16.png
textures/chicago_1835_pbr/masonry/limestone_rubble_lime_mortar/limestone_rubble_lime_mortar_metallic.png
textures/chicago_1835_pbr/masonry/limestone_rubble_lime_mortar/limestone_rubble_lime_mortar_normal_dx.png
textures/chicago_1835_pbr/masonry/limestone_rubble_lime_mortar/limestone_rubble_lime_mortar_normal_gl.png
textures/chicago_1835_pbr/masonry/limestone_rubble_lime_mortar/limestone_rubble_lime_mortar_orm.png
textures/chicago_1835_pbr/masonry/limestone_rubble_lime_mortar/limestone_rubble_lime_mortar_roughness.png
textures/chicago_1835_pbr/masonry/limestone_rubble_lime_mortar/material.json
textures/chicago_1835_pbr/props/blue_painted_shutter/blue_painted_shutter_ao.png
textures/chicago_1835_pbr/props/blue_painted_shutter/blue_painted_shutter_basecolor.png
textures/chicago_1835_pbr/props/blue_painted_shutter/blue_painted_shutter_height16.png
textures/chicago_1835_pbr/props/blue_painted_shutter/blue_painted_shutter_metallic.png
textures/chicago_1835_pbr/props/blue_painted_shutter/blue_painted_shutter_normal_dx.png
textures/chicago_1835_pbr/props/blue_painted_shutter/blue_painted_shutter_normal_gl.png
textures/chicago_1835_pbr/props/blue_painted_shutter/blue_painted_shutter_orm.png
textures/chicago_1835_pbr/props/blue_painted_shutter/blue_painted_shutter_roughness.png
textures/chicago_1835_pbr/props/blue_painted_shutter/material.json
textures/chicago_1835_pbr/props/signboard_weathered/material.json
textures/chicago_1835_pbr/props/signboard_weathered/signboard_weathered_ao.png
textures/chicago_1835_pbr/props/signboard_weathered/signboard_weathered_basecolor.png
textures/chicago_1835_pbr/props/signboard_weathered/signboard_weathered_grain.webp
textures/chicago_1835_pbr/props/signboard_weathered/signboard_weathered_height16.png
textures/chicago_1835_pbr/props/signboard_weathered/signboard_weathered_metallic.png
textures/chicago_1835_pbr/props/signboard_weathered/signboard_weathered_normal_dx.png
textures/chicago_1835_pbr/props/signboard_weathered/signboard_weathered_normal_gl.png
textures/chicago_1835_pbr/props/signboard_weathered/signboard_weathered_normal_turned.webp
textures/chicago_1835_pbr/props/signboard_weathered/signboard_weathered_orm.png
textures/chicago_1835_pbr/props/signboard_weathered/signboard_weathered_roughness.png
textures/chicago_1835_pbr/props/wrought_iron_forged/material.json
textures/chicago_1835_pbr/props/wrought_iron_forged/wrought_iron_forged_ao.png
textures/chicago_1835_pbr/props/wrought_iron_forged/wrought_iron_forged_basecolor.png
textures/chicago_1835_pbr/props/wrought_iron_forged/wrought_iron_forged_height16.png
textures/chicago_1835_pbr/props/wrought_iron_forged/wrought_iron_forged_metallic.png
textures/chicago_1835_pbr/props/wrought_iron_forged/wrought_iron_forged_normal_dx.png
textures/chicago_1835_pbr/props/wrought_iron_forged/wrought_iron_forged_normal_gl.png
textures/chicago_1835_pbr/props/wrought_iron_forged/wrought_iron_forged_orm.png
textures/chicago_1835_pbr/props/wrought_iron_forged/wrought_iron_forged_roughness.png
textures/chicago_1835_pbr/roofs/roof_boards_weathered/material.json
textures/chicago_1835_pbr/roofs/roof_boards_weathered/roof_boards_weathered_ao.png
textures/chicago_1835_pbr/roofs/roof_boards_weathered/roof_boards_weathered_basecolor.png
textures/chicago_1835_pbr/roofs/roof_boards_weathered/roof_boards_weathered_height16.png
textures/chicago_1835_pbr/roofs/roof_boards_weathered/roof_boards_weathered_metallic.png
textures/chicago_1835_pbr/roofs/roof_boards_weathered/roof_boards_weathered_normal_dx.png
textures/chicago_1835_pbr/roofs/roof_boards_weathered/roof_boards_weathered_normal_gl.ktx2
textures/chicago_1835_pbr/roofs/roof_boards_weathered/roof_boards_weathered_normal_gl.png
textures/chicago_1835_pbr/roofs/roof_boards_weathered/roof_boards_weathered_normal_gl.webp
textures/chicago_1835_pbr/roofs/roof_boards_weathered/roof_boards_weathered_orm.ktx2
textures/chicago_1835_pbr/roofs/roof_boards_weathered/roof_boards_weathered_orm.png
textures/chicago_1835_pbr/roofs/roof_boards_weathered/roof_boards_weathered_orm.webp
textures/chicago_1835_pbr/roofs/roof_boards_weathered/roof_boards_weathered_roughness.png
textures/chicago_1835_pbr/roofs/wood_shingles_weathered/material.json
textures/chicago_1835_pbr/roofs/wood_shingles_weathered/wood_shingles_weathered_ao.png
textures/chicago_1835_pbr/roofs/wood_shingles_weathered/wood_shingles_weathered_basecolor.png
textures/chicago_1835_pbr/roofs/wood_shingles_weathered/wood_shingles_weathered_height16.png
textures/chicago_1835_pbr/roofs/wood_shingles_weathered/wood_shingles_weathered_metallic.png
textures/chicago_1835_pbr/roofs/wood_shingles_weathered/wood_shingles_weathered_normal_dx.png
textures/chicago_1835_pbr/roofs/wood_shingles_weathered/wood_shingles_weathered_normal_gl.ktx2
textures/chicago_1835_pbr/roofs/wood_shingles_weathered/wood_shingles_weathered_normal_gl.png
textures/chicago_1835_pbr/roofs/wood_shingles_weathered/wood_shingles_weathered_normal_gl.webp
textures/chicago_1835_pbr/roofs/wood_shingles_weathered/wood_shingles_weathered_orm.ktx2
textures/chicago_1835_pbr/roofs/wood_shingles_weathered/wood_shingles_weathered_orm.png
textures/chicago_1835_pbr/roofs/wood_shingles_weathered/wood_shingles_weathered_orm.webp
textures/chicago_1835_pbr/roofs/wood_shingles_weathered/wood_shingles_weathered_roughness.png
textures/chicago_1835_pbr/timber/fresh_sawn_framing/fresh_sawn_framing_ao.png
textures/chicago_1835_pbr/timber/fresh_sawn_framing/fresh_sawn_framing_basecolor.png
textures/chicago_1835_pbr/timber/fresh_sawn_framing/fresh_sawn_framing_height16.png
textures/chicago_1835_pbr/timber/fresh_sawn_framing/fresh_sawn_framing_metallic.png
textures/chicago_1835_pbr/timber/fresh_sawn_framing/fresh_sawn_framing_normal_dx.png
textures/chicago_1835_pbr/timber/fresh_sawn_framing/fresh_sawn_framing_normal_gl.png
textures/chicago_1835_pbr/timber/fresh_sawn_framing/fresh_sawn_framing_orm.png
textures/chicago_1835_pbr/timber/fresh_sawn_framing/fresh_sawn_framing_roughness.png
textures/chicago_1835_pbr/timber/fresh_sawn_framing/material.json
textures/chicago_1835_pbr/timber/heavy_timber_weathered/heavy_timber_weathered_ao.png
textures/chicago_1835_pbr/timber/heavy_timber_weathered/heavy_timber_weathered_basecolor.png
textures/chicago_1835_pbr/timber/heavy_timber_weathered/heavy_timber_weathered_grain.webp
textures/chicago_1835_pbr/timber/heavy_timber_weathered/heavy_timber_weathered_height16.png
textures/chicago_1835_pbr/timber/heavy_timber_weathered/heavy_timber_weathered_metallic.png
textures/chicago_1835_pbr/timber/heavy_timber_weathered/heavy_timber_weathered_normal_dx.png
textures/chicago_1835_pbr/timber/heavy_timber_weathered/heavy_timber_weathered_normal_gl.png
textures/chicago_1835_pbr/timber/heavy_timber_weathered/heavy_timber_weathered_normal_turned.webp
textures/chicago_1835_pbr/timber/heavy_timber_weathered/heavy_timber_weathered_orm.png
textures/chicago_1835_pbr/timber/heavy_timber_weathered/heavy_timber_weathered_roughness.png
textures/chicago_1835_pbr/timber/heavy_timber_weathered/material.json
textures/chicago_1835_pbr/timber/sawn_board_weathered/material.json
textures/chicago_1835_pbr/timber/sawn_board_weathered/sawn_board_weathered_ao.png
textures/chicago_1835_pbr/timber/sawn_board_weathered/sawn_board_weathered_basecolor.png
textures/chicago_1835_pbr/timber/sawn_board_weathered/sawn_board_weathered_height16.png
textures/chicago_1835_pbr/timber/sawn_board_weathered/sawn_board_weathered_metallic.png
textures/chicago_1835_pbr/timber/sawn_board_weathered/sawn_board_weathered_normal_dx.png
textures/chicago_1835_pbr/timber/sawn_board_weathered/sawn_board_weathered_normal_gl.png
textures/chicago_1835_pbr/timber/sawn_board_weathered/sawn_board_weathered_orm.png
textures/chicago_1835_pbr/timber/sawn_board_weathered/sawn_board_weathered_roughness.png
textures/chicago_1835_pbr/tools/generate_1835_pbr_library.py
textures/chicago_1835_pbr/tools/source_mud_ai.png
textures/chicago_1835_pbr/walls/board_and_batten_weathered/board_and_batten_weathered_ao.png
textures/chicago_1835_pbr/walls/board_and_batten_weathered/board_and_batten_weathered_basecolor.png
textures/chicago_1835_pbr/walls/board_and_batten_weathered/board_and_batten_weathered_height16.png
textures/chicago_1835_pbr/walls/board_and_batten_weathered/board_and_batten_weathered_metallic.png
textures/chicago_1835_pbr/walls/board_and_batten_weathered/board_and_batten_weathered_normal_dx.png
textures/chicago_1835_pbr/walls/board_and_batten_weathered/board_and_batten_weathered_normal_gl.png
textures/chicago_1835_pbr/walls/board_and_batten_weathered/board_and_batten_weathered_orm.png
textures/chicago_1835_pbr/walls/board_and_batten_weathered/board_and_batten_weathered_roughness.png
textures/chicago_1835_pbr/walls/board_and_batten_weathered/material.json
textures/chicago_1835_pbr/walls/clapboard_board_face/clapboard_board_face_ao.png
textures/chicago_1835_pbr/walls/clapboard_board_face/clapboard_board_face_basecolor.png
textures/chicago_1835_pbr/walls/clapboard_board_face/clapboard_board_face_basecolor.webp
textures/chicago_1835_pbr/walls/clapboard_board_face/clapboard_board_face_grain.ktx2
textures/chicago_1835_pbr/walls/clapboard_board_face/clapboard_board_face_height16.png
textures/chicago_1835_pbr/walls/clapboard_board_face/clapboard_board_face_metallic.png
textures/chicago_1835_pbr/walls/clapboard_board_face/clapboard_board_face_normal_dx.png
textures/chicago_1835_pbr/walls/clapboard_board_face/clapboard_board_face_normal_gl.ktx2
textures/chicago_1835_pbr/walls/clapboard_board_face/clapboard_board_face_normal_gl.png
textures/chicago_1835_pbr/walls/clapboard_board_face/clapboard_board_face_normal_gl.webp
textures/chicago_1835_pbr/walls/clapboard_board_face/clapboard_board_face_orm.ktx2
textures/chicago_1835_pbr/walls/clapboard_board_face/clapboard_board_face_orm.png
textures/chicago_1835_pbr/walls/clapboard_board_face/clapboard_board_face_orm.webp
textures/chicago_1835_pbr/walls/clapboard_board_face/clapboard_board_face_orl.json
textures/chicago_1835_pbr/walls/clapboard_board_face/clapboard_board_face_orl.ktx2
textures/chicago_1835_pbr/walls/clapboard_board_face/clapboard_board_face_roughness.png
textures/chicago_1835_pbr/walls/clapboard_board_face/material.json
textures/chicago_1835_pbr/walls/clapboard_red_oxide/clapboard_red_oxide_ao.png
textures/chicago_1835_pbr/walls/clapboard_red_oxide/clapboard_red_oxide_basecolor.png
textures/chicago_1835_pbr/walls/clapboard_red_oxide/clapboard_red_oxide_height16.png
textures/chicago_1835_pbr/walls/clapboard_red_oxide/clapboard_red_oxide_metallic.png
textures/chicago_1835_pbr/walls/clapboard_red_oxide/clapboard_red_oxide_normal_dx.png
textures/chicago_1835_pbr/walls/clapboard_red_oxide/clapboard_red_oxide_normal_gl.png
textures/chicago_1835_pbr/walls/clapboard_red_oxide/clapboard_red_oxide_orm.png
textures/chicago_1835_pbr/walls/clapboard_red_oxide/clapboard_red_oxide_roughness.png
textures/chicago_1835_pbr/walls/clapboard_red_oxide/material.json
textures/chicago_1835_pbr/walls/clapboard_weathered_oak/clapboard_weathered_oak_ao.png
textures/chicago_1835_pbr/walls/clapboard_weathered_oak/clapboard_weathered_oak_basecolor.png
textures/chicago_1835_pbr/walls/clapboard_weathered_oak/clapboard_weathered_oak_height16.png
textures/chicago_1835_pbr/walls/clapboard_weathered_oak/clapboard_weathered_oak_metallic.png
textures/chicago_1835_pbr/walls/clapboard_weathered_oak/clapboard_weathered_oak_normal_dx.png
textures/chicago_1835_pbr/walls/clapboard_weathered_oak/clapboard_weathered_oak_normal_gl.png
textures/chicago_1835_pbr/walls/clapboard_weathered_oak/clapboard_weathered_oak_orm.png
textures/chicago_1835_pbr/walls/clapboard_weathered_oak/clapboard_weathered_oak_roughness.png
textures/chicago_1835_pbr/walls/clapboard_weathered_oak/material.json
textures/chicago_1835_pbr/walls/clapboard_white_lead_paint/clapboard_white_lead_paint_ao.png
textures/chicago_1835_pbr/walls/clapboard_white_lead_paint/clapboard_white_lead_paint_basecolor.png
textures/chicago_1835_pbr/walls/clapboard_white_lead_paint/clapboard_white_lead_paint_height16.png
textures/chicago_1835_pbr/walls/clapboard_white_lead_paint/clapboard_white_lead_paint_metallic.png
textures/chicago_1835_pbr/walls/clapboard_white_lead_paint/clapboard_white_lead_paint_normal_dx.png
textures/chicago_1835_pbr/walls/clapboard_white_lead_paint/clapboard_white_lead_paint_normal_gl.png
textures/chicago_1835_pbr/walls/clapboard_white_lead_paint/clapboard_white_lead_paint_orm.png
textures/chicago_1835_pbr/walls/clapboard_white_lead_paint/clapboard_white_lead_paint_roughness.png
textures/chicago_1835_pbr/walls/clapboard_white_lead_paint/material.json
textures/chicago_1835_pbr/walls/clapboard_whitewash/clapboard_whitewash_ao.png
textures/chicago_1835_pbr/walls/clapboard_whitewash/clapboard_whitewash_basecolor.png
textures/chicago_1835_pbr/walls/clapboard_whitewash/clapboard_whitewash_height16.png
textures/chicago_1835_pbr/walls/clapboard_whitewash/clapboard_whitewash_metallic.png
textures/chicago_1835_pbr/walls/clapboard_whitewash/clapboard_whitewash_normal_dx.png
textures/chicago_1835_pbr/walls/clapboard_whitewash/clapboard_whitewash_normal_gl.png
textures/chicago_1835_pbr/walls/clapboard_whitewash/clapboard_whitewash_orm.png
textures/chicago_1835_pbr/walls/clapboard_whitewash/clapboard_whitewash_roughness.png
textures/chicago_1835_pbr/walls/clapboard_whitewash/material.json
textures/chicago_1835_pbr/walls/hewn_log_face/hewn_log_face_ao.png
textures/chicago_1835_pbr/walls/hewn_log_face/hewn_log_face_basecolor.png
textures/chicago_1835_pbr/walls/hewn_log_face/hewn_log_face_basecolor.webp
textures/chicago_1835_pbr/walls/hewn_log_face/hewn_log_face_height16.png
textures/chicago_1835_pbr/walls/hewn_log_face/hewn_log_face_metallic.png
textures/chicago_1835_pbr/walls/hewn_log_face/hewn_log_face_normal_dx.png
textures/chicago_1835_pbr/walls/hewn_log_face/hewn_log_face_normal_gl.png
textures/chicago_1835_pbr/walls/hewn_log_face/hewn_log_face_normal_gl.ktx2
textures/chicago_1835_pbr/walls/hewn_log_face/hewn_log_face_normal_gl.webp
textures/chicago_1835_pbr/walls/hewn_log_face/hewn_log_face_orm.png
textures/chicago_1835_pbr/walls/hewn_log_face/hewn_log_face_orm.webp
textures/chicago_1835_pbr/walls/hewn_log_face/hewn_log_face_orl.json
textures/chicago_1835_pbr/walls/hewn_log_face/hewn_log_face_orl.ktx2
textures/chicago_1835_pbr/walls/hewn_log_face/hewn_log_face_roughness.png
textures/chicago_1835_pbr/walls/hewn_log_face/material.json
textures/chicago_1835_pbr/walls/hewn_log_oak_chinked/hewn_log_oak_chinked_ao.png
textures/chicago_1835_pbr/walls/hewn_log_oak_chinked/hewn_log_oak_chinked_basecolor.png
textures/chicago_1835_pbr/walls/hewn_log_oak_chinked/hewn_log_oak_chinked_height16.png
textures/chicago_1835_pbr/walls/hewn_log_oak_chinked/hewn_log_oak_chinked_metallic.png
textures/chicago_1835_pbr/walls/hewn_log_oak_chinked/hewn_log_oak_chinked_normal_dx.png
textures/chicago_1835_pbr/walls/hewn_log_oak_chinked/hewn_log_oak_chinked_normal_gl.png
textures/chicago_1835_pbr/walls/hewn_log_oak_chinked/hewn_log_oak_chinked_orm.png
textures/chicago_1835_pbr/walls/hewn_log_oak_chinked/hewn_log_oak_chinked_roughness.png
textures/chicago_1835_pbr/walls/hewn_log_oak_chinked/material.json
textures/chicago_1835_pbr/walls/vertical_sawn_board/material.json
textures/chicago_1835_pbr/walls/vertical_sawn_board/vertical_sawn_board_ao.png
textures/chicago_1835_pbr/walls/vertical_sawn_board/vertical_sawn_board_basecolor.png
textures/chicago_1835_pbr/walls/vertical_sawn_board/vertical_sawn_board_height16.png
textures/chicago_1835_pbr/walls/vertical_sawn_board/vertical_sawn_board_metallic.png
textures/chicago_1835_pbr/walls/vertical_sawn_board/vertical_sawn_board_normal_dx.png
textures/chicago_1835_pbr/walls/vertical_sawn_board/vertical_sawn_board_normal_gl.png
textures/chicago_1835_pbr/walls/vertical_sawn_board/vertical_sawn_board_orm.png
textures/chicago_1835_pbr/walls/vertical_sawn_board/vertical_sawn_board_roughness.png
textures/chicago_1835_pbr/waterfront/dock_timber_tar_darkened/dock_timber_tar_darkened_ao.png
textures/chicago_1835_pbr/waterfront/dock_timber_tar_darkened/dock_timber_tar_darkened_basecolor.png
textures/chicago_1835_pbr/waterfront/dock_timber_tar_darkened/dock_timber_tar_darkened_height16.png
textures/chicago_1835_pbr/waterfront/dock_timber_tar_darkened/dock_timber_tar_darkened_metallic.png
textures/chicago_1835_pbr/waterfront/dock_timber_tar_darkened/dock_timber_tar_darkened_normal_dx.png
textures/chicago_1835_pbr/waterfront/dock_timber_tar_darkened/dock_timber_tar_darkened_normal_gl.png
textures/chicago_1835_pbr/waterfront/dock_timber_tar_darkened/dock_timber_tar_darkened_orm.png
textures/chicago_1835_pbr/waterfront/dock_timber_tar_darkened/dock_timber_tar_darkened_roughness.png
textures/chicago_1835_pbr/waterfront/dock_timber_tar_darkened/material.json
textures/chicago_1835_pbr/waterfront/plank_walk_weathered/material.json
textures/chicago_1835_pbr/waterfront/plank_walk_weathered/plank_walk_weathered_ao.png
textures/chicago_1835_pbr/waterfront/plank_walk_weathered/plank_walk_weathered_basecolor.png
textures/chicago_1835_pbr/waterfront/plank_walk_weathered/plank_walk_weathered_height16.png
textures/chicago_1835_pbr/waterfront/plank_walk_weathered/plank_walk_weathered_metallic.png
textures/chicago_1835_pbr/waterfront/plank_walk_weathered/plank_walk_weathered_normal_dx.png
textures/chicago_1835_pbr/waterfront/plank_walk_weathered/plank_walk_weathered_normal_gl.png
textures/chicago_1835_pbr/waterfront/plank_walk_weathered/plank_walk_weathered_orm.png
textures/chicago_1835_pbr/waterfront/plank_walk_weathered/plank_walk_weathered_roughness.png
```

### The Prairie Avenue 1904 street-surface library — `textures/prairie_1904_pbr/`

T-1728. Seven procedural materials for the 1904 scene's roadways, alleys, walks, curbs and
parkways, built by the generator that ships inside it (`tools/generate_prairie_1904_pbr.py`,
deterministic, seeded per material) in the 1835 library's map-for-map layout at 512 px. Which
surface wears which material, and on what evidence, is `data/street_surfaces/1904.json`'s to
say; the look of every map is reconstructed (`docs/LIBERTIES.md` L296).

| item | licence | cleared for | NOT cleared for |
|---|---|---|---|
| `textures/prairie_1904_pbr/**` — *Prairie Avenue 1904 street-surface PBR library v1.0.0*, original procedural output generated for this project. Full text at `textures/prairie_1904_pbr/LICENSE.txt` | **Project-permissive, CC0-equivalent**, the 1835 library's terms. No third-party photograph or image is embedded, sampled or traced | **Use, modification and redistribution with the project**, including regenerated maps | **Stripping the confidence labels.** Each `material.json` says its appearance is reconstructed and that the surfaces file, not the map, carries the evidence |

**Published in part.** `tools/publish.sh` ships each material's `material.json` and its three
`*_web.jpg` maps to `data/textures/prairie_1904_pbr/`; the PNG masters, the DirectX normal and the
16-bit height stay in the repository.
Beside each `*_web.jpg` it also ships a `.ktx2` of the same map (T-2582): the PNG master
GPU-compressed by `tools/ktx2_sheets.py` with KTX-Software 4.3.2 at the web map's size. A
derivative for the GPU, not a new map; it carries the library's licence unchanged.

Every file, as the checker matches them one by one:

```
textures/prairie_1904_pbr/LICENSE.txt
textures/prairie_1904_pbr/README.md
textures/prairie_1904_pbr/alley/earth_and_cinders/earth_and_cinders_ao.png
textures/prairie_1904_pbr/alley/earth_and_cinders/earth_and_cinders_basecolor.ktx2
textures/prairie_1904_pbr/alley/earth_and_cinders/earth_and_cinders_basecolor.png
textures/prairie_1904_pbr/alley/earth_and_cinders/earth_and_cinders_basecolor_web.jpg
textures/prairie_1904_pbr/alley/earth_and_cinders/earth_and_cinders_height16.png
textures/prairie_1904_pbr/alley/earth_and_cinders/earth_and_cinders_metallic.png
textures/prairie_1904_pbr/alley/earth_and_cinders/earth_and_cinders_normal_dx.png
textures/prairie_1904_pbr/alley/earth_and_cinders/earth_and_cinders_normal_gl.ktx2
textures/prairie_1904_pbr/alley/earth_and_cinders/earth_and_cinders_normal_gl.png
textures/prairie_1904_pbr/alley/earth_and_cinders/earth_and_cinders_normal_gl_web.jpg
textures/prairie_1904_pbr/alley/earth_and_cinders/earth_and_cinders_orm.ktx2
textures/prairie_1904_pbr/alley/earth_and_cinders/earth_and_cinders_orm.png
textures/prairie_1904_pbr/alley/earth_and_cinders/earth_and_cinders_orm_web.jpg
textures/prairie_1904_pbr/alley/earth_and_cinders/earth_and_cinders_roughness.png
textures/prairie_1904_pbr/alley/earth_and_cinders/material.json
textures/prairie_1904_pbr/contact_sheet.jpg
textures/prairie_1904_pbr/curb/sandstone_curbstone/material.json
textures/prairie_1904_pbr/curb/sandstone_curbstone/sandstone_curbstone_ao.png
textures/prairie_1904_pbr/curb/sandstone_curbstone/sandstone_curbstone_basecolor.ktx2
textures/prairie_1904_pbr/curb/sandstone_curbstone/sandstone_curbstone_basecolor.png
textures/prairie_1904_pbr/curb/sandstone_curbstone/sandstone_curbstone_basecolor_web.jpg
textures/prairie_1904_pbr/curb/sandstone_curbstone/sandstone_curbstone_height16.png
textures/prairie_1904_pbr/curb/sandstone_curbstone/sandstone_curbstone_metallic.png
textures/prairie_1904_pbr/curb/sandstone_curbstone/sandstone_curbstone_normal_dx.png
textures/prairie_1904_pbr/curb/sandstone_curbstone/sandstone_curbstone_normal_gl.ktx2
textures/prairie_1904_pbr/curb/sandstone_curbstone/sandstone_curbstone_normal_gl.png
textures/prairie_1904_pbr/curb/sandstone_curbstone/sandstone_curbstone_normal_gl_web.jpg
textures/prairie_1904_pbr/curb/sandstone_curbstone/sandstone_curbstone_orm.ktx2
textures/prairie_1904_pbr/curb/sandstone_curbstone/sandstone_curbstone_orm.png
textures/prairie_1904_pbr/curb/sandstone_curbstone/sandstone_curbstone_orm_web.jpg
textures/prairie_1904_pbr/curb/sandstone_curbstone/sandstone_curbstone_roughness.png
textures/prairie_1904_pbr/parkway/grass_plat/grass_plat_ao.png
textures/prairie_1904_pbr/parkway/grass_plat/grass_plat_basecolor.ktx2
textures/prairie_1904_pbr/parkway/grass_plat/grass_plat_basecolor.png
textures/prairie_1904_pbr/parkway/grass_plat/grass_plat_basecolor_web.jpg
textures/prairie_1904_pbr/parkway/grass_plat/grass_plat_height16.png
textures/prairie_1904_pbr/parkway/grass_plat/grass_plat_metallic.png
textures/prairie_1904_pbr/parkway/grass_plat/grass_plat_normal_dx.png
textures/prairie_1904_pbr/parkway/grass_plat/grass_plat_normal_gl.ktx2
textures/prairie_1904_pbr/parkway/grass_plat/grass_plat_normal_gl.png
textures/prairie_1904_pbr/parkway/grass_plat/grass_plat_normal_gl_web.jpg
textures/prairie_1904_pbr/parkway/grass_plat/grass_plat_orm.ktx2
textures/prairie_1904_pbr/parkway/grass_plat/grass_plat_orm.png
textures/prairie_1904_pbr/parkway/grass_plat/grass_plat_orm_web.jpg
textures/prairie_1904_pbr/parkway/grass_plat/grass_plat_roughness.png
textures/prairie_1904_pbr/parkway/grass_plat/material.json
textures/prairie_1904_pbr/roadway/macadam_limestone/macadam_limestone_ao.png
textures/prairie_1904_pbr/roadway/macadam_limestone/macadam_limestone_basecolor.ktx2
textures/prairie_1904_pbr/roadway/macadam_limestone/macadam_limestone_basecolor.png
textures/prairie_1904_pbr/roadway/macadam_limestone/macadam_limestone_basecolor_web.jpg
textures/prairie_1904_pbr/roadway/macadam_limestone/macadam_limestone_height16.png
textures/prairie_1904_pbr/roadway/macadam_limestone/macadam_limestone_metallic.png
textures/prairie_1904_pbr/roadway/macadam_limestone/macadam_limestone_normal_dx.png
textures/prairie_1904_pbr/roadway/macadam_limestone/macadam_limestone_normal_gl.ktx2
textures/prairie_1904_pbr/roadway/macadam_limestone/macadam_limestone_normal_gl.png
textures/prairie_1904_pbr/roadway/macadam_limestone/macadam_limestone_normal_gl_web.jpg
textures/prairie_1904_pbr/roadway/macadam_limestone/macadam_limestone_orm.ktx2
textures/prairie_1904_pbr/roadway/macadam_limestone/macadam_limestone_orm.png
textures/prairie_1904_pbr/roadway/macadam_limestone/macadam_limestone_orm_web.jpg
textures/prairie_1904_pbr/roadway/macadam_limestone/macadam_limestone_roughness.png
textures/prairie_1904_pbr/roadway/macadam_limestone/material.json
textures/prairie_1904_pbr/roadway/sheet_asphalt/material.json
textures/prairie_1904_pbr/roadway/sheet_asphalt/sheet_asphalt_ao.png
textures/prairie_1904_pbr/roadway/sheet_asphalt/sheet_asphalt_basecolor.ktx2
textures/prairie_1904_pbr/roadway/sheet_asphalt/sheet_asphalt_basecolor.png
textures/prairie_1904_pbr/roadway/sheet_asphalt/sheet_asphalt_basecolor_web.jpg
textures/prairie_1904_pbr/roadway/sheet_asphalt/sheet_asphalt_height16.png
textures/prairie_1904_pbr/roadway/sheet_asphalt/sheet_asphalt_metallic.png
textures/prairie_1904_pbr/roadway/sheet_asphalt/sheet_asphalt_normal_dx.png
textures/prairie_1904_pbr/roadway/sheet_asphalt/sheet_asphalt_normal_gl.ktx2
textures/prairie_1904_pbr/roadway/sheet_asphalt/sheet_asphalt_normal_gl.png
textures/prairie_1904_pbr/roadway/sheet_asphalt/sheet_asphalt_normal_gl_web.jpg
textures/prairie_1904_pbr/roadway/sheet_asphalt/sheet_asphalt_orm.ktx2
textures/prairie_1904_pbr/roadway/sheet_asphalt/sheet_asphalt_orm.png
textures/prairie_1904_pbr/roadway/sheet_asphalt/sheet_asphalt_orm_web.jpg
textures/prairie_1904_pbr/roadway/sheet_asphalt/sheet_asphalt_roughness.png
textures/prairie_1904_pbr/roadway/vitrified_paving_brick/material.json
textures/prairie_1904_pbr/roadway/vitrified_paving_brick/vitrified_paving_brick_ao.png
textures/prairie_1904_pbr/roadway/vitrified_paving_brick/vitrified_paving_brick_basecolor.ktx2
textures/prairie_1904_pbr/roadway/vitrified_paving_brick/vitrified_paving_brick_basecolor.png
textures/prairie_1904_pbr/roadway/vitrified_paving_brick/vitrified_paving_brick_basecolor_web.jpg
textures/prairie_1904_pbr/roadway/vitrified_paving_brick/vitrified_paving_brick_height16.png
textures/prairie_1904_pbr/roadway/vitrified_paving_brick/vitrified_paving_brick_metallic.png
textures/prairie_1904_pbr/roadway/vitrified_paving_brick/vitrified_paving_brick_normal_dx.png
textures/prairie_1904_pbr/roadway/vitrified_paving_brick/vitrified_paving_brick_normal_gl.ktx2
textures/prairie_1904_pbr/roadway/vitrified_paving_brick/vitrified_paving_brick_normal_gl.png
textures/prairie_1904_pbr/roadway/vitrified_paving_brick/vitrified_paving_brick_normal_gl_web.jpg
textures/prairie_1904_pbr/roadway/vitrified_paving_brick/vitrified_paving_brick_orm.ktx2
textures/prairie_1904_pbr/roadway/vitrified_paving_brick/vitrified_paving_brick_orm.png
textures/prairie_1904_pbr/roadway/vitrified_paving_brick/vitrified_paving_brick_orm_web.jpg
textures/prairie_1904_pbr/roadway/vitrified_paving_brick/vitrified_paving_brick_roughness.png
textures/prairie_1904_pbr/tools/generate_prairie_1904_pbr.py
textures/prairie_1904_pbr/walk/portland_cement_walk/material.json
textures/prairie_1904_pbr/walk/portland_cement_walk/portland_cement_walk_ao.png
textures/prairie_1904_pbr/walk/portland_cement_walk/portland_cement_walk_basecolor.ktx2
textures/prairie_1904_pbr/walk/portland_cement_walk/portland_cement_walk_basecolor.png
textures/prairie_1904_pbr/walk/portland_cement_walk/portland_cement_walk_basecolor_web.jpg
textures/prairie_1904_pbr/walk/portland_cement_walk/portland_cement_walk_height16.png
textures/prairie_1904_pbr/walk/portland_cement_walk/portland_cement_walk_metallic.png
textures/prairie_1904_pbr/walk/portland_cement_walk/portland_cement_walk_normal_dx.png
textures/prairie_1904_pbr/walk/portland_cement_walk/portland_cement_walk_normal_gl.ktx2
textures/prairie_1904_pbr/walk/portland_cement_walk/portland_cement_walk_normal_gl.png
textures/prairie_1904_pbr/walk/portland_cement_walk/portland_cement_walk_normal_gl_web.jpg
textures/prairie_1904_pbr/walk/portland_cement_walk/portland_cement_walk_orm.ktx2
textures/prairie_1904_pbr/walk/portland_cement_walk/portland_cement_walk_orm.png
textures/prairie_1904_pbr/walk/portland_cement_walk/portland_cement_walk_orm_web.jpg
textures/prairie_1904_pbr/walk/portland_cement_walk/portland_cement_walk_roughness.png
```

### The Prairie Avenue 1904 lakefront railway library — `textures/prairie_1904_rail/`

T-2478. Four procedural materials for the 1904 scene's Illinois Central right-of-way (cinder
ballast, trodden cinders, a weedy verge, a crosstie's top) and one alpha card for the verges' grass
tufts, built by the generator that ships inside it (`tools/generate_prairie_1904_rail.py`,
deterministic, seeded per material, borrowing the street library's noise). Which ground wears which
material is `data/railway/1904_spec.json`'s to say; the look of every map is reconstructed
(`docs/LIBERTIES.md` L-ic-tracks-2478). T-2479 added four more under `edge/` for the railway's edge
against the lake (the riprap face, one limestone block's face, the cap timber, the made ground),
equally reconstructed (L-ic-lake-edge-2479).

| item | licence | cleared for | NOT cleared for |
|---|---|---|---|
| `textures/prairie_1904_rail/**` — *Prairie Avenue 1904 lakefront railway PBR library v1.1.0*, original procedural output generated for this project. Full text at `textures/prairie_1904_rail/LICENSE.txt` | **Project-permissive, CC0-equivalent**, the 1835 library's terms. No third-party photograph or image is embedded, sampled or traced | **Use, modification and redistribution with the project**, including regenerated maps | **Stripping the confidence labels.** Each `material.json` says its appearance is reconstructed and that the railway spec, not the map, carries the evidence |

**Published in part.** `tools/publish.sh` ships each material's `material.json` and its three
`*_web.jpg` maps (the tuft's one `grass_tuft_web.png`) to `data/textures/prairie_1904_rail/`; the PNG
masters and the 16-bit height stay in the repository.

Every file, as the checker matches them one by one:

```
textures/prairie_1904_rail/LICENSE.txt
textures/prairie_1904_rail/README.md
textures/prairie_1904_rail/ballast/cinder_ballast/cinder_ballast_basecolor.png
textures/prairie_1904_rail/ballast/cinder_ballast/cinder_ballast_basecolor_web.jpg
textures/prairie_1904_rail/ballast/cinder_ballast/cinder_ballast_height16.png
textures/prairie_1904_rail/ballast/cinder_ballast/cinder_ballast_normal_gl.png
textures/prairie_1904_rail/ballast/cinder_ballast/cinder_ballast_normal_gl_web.jpg
textures/prairie_1904_rail/ballast/cinder_ballast/cinder_ballast_orm.png
textures/prairie_1904_rail/ballast/cinder_ballast/cinder_ballast_orm_web.jpg
textures/prairie_1904_rail/ballast/cinder_ballast/material.json
textures/prairie_1904_rail/contact_sheet.jpg
textures/prairie_1904_rail/edge/cap_timber/cap_timber_basecolor.png
textures/prairie_1904_rail/edge/cap_timber/cap_timber_basecolor_web.jpg
textures/prairie_1904_rail/edge/cap_timber/cap_timber_height16.png
textures/prairie_1904_rail/edge/cap_timber/cap_timber_normal_gl.png
textures/prairie_1904_rail/edge/cap_timber/cap_timber_normal_gl_web.jpg
textures/prairie_1904_rail/edge/cap_timber/cap_timber_orm.png
textures/prairie_1904_rail/edge/cap_timber/cap_timber_orm_web.jpg
textures/prairie_1904_rail/edge/cap_timber/material.json
textures/prairie_1904_rail/edge/limestone_block/limestone_block_basecolor.png
textures/prairie_1904_rail/edge/limestone_block/limestone_block_basecolor_web.jpg
textures/prairie_1904_rail/edge/limestone_block/limestone_block_height16.png
textures/prairie_1904_rail/edge/limestone_block/limestone_block_normal_gl.png
textures/prairie_1904_rail/edge/limestone_block/limestone_block_normal_gl_web.jpg
textures/prairie_1904_rail/edge/limestone_block/limestone_block_orm.png
textures/prairie_1904_rail/edge/limestone_block/limestone_block_orm_web.jpg
textures/prairie_1904_rail/edge/limestone_block/material.json
textures/prairie_1904_rail/edge/made_ground/made_ground_basecolor.png
textures/prairie_1904_rail/edge/made_ground/made_ground_basecolor_web.jpg
textures/prairie_1904_rail/edge/made_ground/made_ground_height16.png
textures/prairie_1904_rail/edge/made_ground/made_ground_normal_gl.png
textures/prairie_1904_rail/edge/made_ground/made_ground_normal_gl_web.jpg
textures/prairie_1904_rail/edge/made_ground/made_ground_orm.png
textures/prairie_1904_rail/edge/made_ground/made_ground_orm_web.jpg
textures/prairie_1904_rail/edge/made_ground/material.json
textures/prairie_1904_rail/edge/riprap_limestone/material.json
textures/prairie_1904_rail/edge/riprap_limestone/riprap_limestone_basecolor.png
textures/prairie_1904_rail/edge/riprap_limestone/riprap_limestone_basecolor_web.jpg
textures/prairie_1904_rail/edge/riprap_limestone/riprap_limestone_height16.png
textures/prairie_1904_rail/edge/riprap_limestone/riprap_limestone_normal_gl.png
textures/prairie_1904_rail/edge/riprap_limestone/riprap_limestone_normal_gl_web.jpg
textures/prairie_1904_rail/edge/riprap_limestone/riprap_limestone_orm.png
textures/prairie_1904_rail/edge/riprap_limestone/riprap_limestone_orm_web.jpg
textures/prairie_1904_rail/foliage/grass_tuft/grass_tuft_web.png
textures/prairie_1904_rail/foliage/grass_tuft/material.json
textures/prairie_1904_rail/ground/trodden_cinders/material.json
textures/prairie_1904_rail/ground/trodden_cinders/trodden_cinders_basecolor.png
textures/prairie_1904_rail/ground/trodden_cinders/trodden_cinders_basecolor_web.jpg
textures/prairie_1904_rail/ground/trodden_cinders/trodden_cinders_height16.png
textures/prairie_1904_rail/ground/trodden_cinders/trodden_cinders_normal_gl.png
textures/prairie_1904_rail/ground/trodden_cinders/trodden_cinders_normal_gl_web.jpg
textures/prairie_1904_rail/ground/trodden_cinders/trodden_cinders_orm.png
textures/prairie_1904_rail/ground/trodden_cinders/trodden_cinders_orm_web.jpg
textures/prairie_1904_rail/manifest.json
textures/prairie_1904_rail/timber/tie_timber/material.json
textures/prairie_1904_rail/timber/tie_timber/tie_timber_basecolor.png
textures/prairie_1904_rail/timber/tie_timber/tie_timber_basecolor_web.jpg
textures/prairie_1904_rail/timber/tie_timber/tie_timber_height16.png
textures/prairie_1904_rail/timber/tie_timber/tie_timber_normal_gl.png
textures/prairie_1904_rail/timber/tie_timber/tie_timber_normal_gl_web.jpg
textures/prairie_1904_rail/timber/tie_timber/tie_timber_orm.png
textures/prairie_1904_rail/timber/tie_timber/tie_timber_orm_web.jpg
textures/prairie_1904_rail/tools/generate_prairie_1904_rail.py
textures/prairie_1904_rail/verge/weedy_verge/material.json
textures/prairie_1904_rail/verge/weedy_verge/weedy_verge_basecolor.png
textures/prairie_1904_rail/verge/weedy_verge/weedy_verge_basecolor_web.jpg
textures/prairie_1904_rail/verge/weedy_verge/weedy_verge_height16.png
textures/prairie_1904_rail/verge/weedy_verge/weedy_verge_normal_gl.png
textures/prairie_1904_rail/verge/weedy_verge/weedy_verge_normal_gl_web.jpg
textures/prairie_1904_rail/verge/weedy_verge/weedy_verge_orm.png
textures/prairie_1904_rail/verge/weedy_verge/weedy_verge_orm_web.jpg
```

### The Prairie Avenue 1904 K03 brick library — `textures/prairie_1904_brick/`

T-2290 (piece 1 of T-1845, package K03 of T-1837). Four joint-free brick fabrics (pressed red,
common buff, dark fired, rough red-brown), two mortars, `profiles.json` (joints, bonds, specials
and firing spread as data) and four bonded LOD panels rendered from it, built by the generator
that ships inside it (`tools/generate_prairie_1904_brick.py`, deterministic, seeded per fabric).
Which house is built of which brick is the T-1837 register's and each house's own evidence to say;
the look of every map is reconstructed (`docs/LIBERTIES.md` L-k03-brick-library-2290).

| item | licence | cleared for | NOT cleared for |
|---|---|---|---|
| `textures/prairie_1904_brick/**`: *Prairie Avenue 1904 K03 brick library v1.0.0*, original procedural output generated for this project. Full text at `textures/prairie_1904_brick/LICENSE.txt` | **Project-permissive, CC0-equivalent**, the street library's terms. No third-party photograph or image is embedded, sampled or traced | **Use, modification and redistribution with the project**, including regenerated maps | **Stripping the confidence labels.** Each `material.json` and `profiles.json` says its appearance is reconstructed and that the register, not the map, carries the evidence |

**Not published yet.** `tools/publish.sh` ships nothing from this library until a component binds it
(T-2291).

Every file, as the checker matches them one by one:

```
textures/prairie_1904_brick/LICENSE.txt
textures/prairie_1904_brick/README.md
textures/prairie_1904_brick/brick/common_buff/common_buff_basecolor.png
textures/prairie_1904_brick/brick/common_buff/common_buff_basecolor_web.jpg
textures/prairie_1904_brick/brick/common_buff/common_buff_height16.png
textures/prairie_1904_brick/brick/common_buff/common_buff_normal_gl.png
textures/prairie_1904_brick/brick/common_buff/common_buff_normal_gl_web.jpg
textures/prairie_1904_brick/brick/common_buff/common_buff_orm.png
textures/prairie_1904_brick/brick/common_buff/common_buff_orm_web.jpg
textures/prairie_1904_brick/brick/common_buff/common_buff_roughness.png
textures/prairie_1904_brick/brick/common_buff/material.json
textures/prairie_1904_brick/brick/dark_fired/dark_fired_basecolor.png
textures/prairie_1904_brick/brick/dark_fired/dark_fired_basecolor_web.jpg
textures/prairie_1904_brick/brick/dark_fired/dark_fired_height16.png
textures/prairie_1904_brick/brick/dark_fired/dark_fired_normal_gl.png
textures/prairie_1904_brick/brick/dark_fired/dark_fired_normal_gl_web.jpg
textures/prairie_1904_brick/brick/dark_fired/dark_fired_orm.png
textures/prairie_1904_brick/brick/dark_fired/dark_fired_orm_web.jpg
textures/prairie_1904_brick/brick/dark_fired/dark_fired_roughness.png
textures/prairie_1904_brick/brick/dark_fired/material.json
textures/prairie_1904_brick/brick/pressed_red/material.json
textures/prairie_1904_brick/brick/pressed_red/pressed_red_basecolor.png
textures/prairie_1904_brick/brick/pressed_red/pressed_red_basecolor_web.jpg
textures/prairie_1904_brick/brick/pressed_red/pressed_red_height16.png
textures/prairie_1904_brick/brick/pressed_red/pressed_red_normal_gl.png
textures/prairie_1904_brick/brick/pressed_red/pressed_red_normal_gl_web.jpg
textures/prairie_1904_brick/brick/pressed_red/pressed_red_orm.png
textures/prairie_1904_brick/brick/pressed_red/pressed_red_orm_web.jpg
textures/prairie_1904_brick/brick/pressed_red/pressed_red_roughness.png
textures/prairie_1904_brick/brick/rough_red_brown/material.json
textures/prairie_1904_brick/brick/rough_red_brown/rough_red_brown_basecolor.png
textures/prairie_1904_brick/brick/rough_red_brown/rough_red_brown_basecolor_web.jpg
textures/prairie_1904_brick/brick/rough_red_brown/rough_red_brown_height16.png
textures/prairie_1904_brick/brick/rough_red_brown/rough_red_brown_normal_gl.png
textures/prairie_1904_brick/brick/rough_red_brown/rough_red_brown_normal_gl_web.jpg
textures/prairie_1904_brick/brick/rough_red_brown/rough_red_brown_orm.png
textures/prairie_1904_brick/brick/rough_red_brown/rough_red_brown_orm_web.jpg
textures/prairie_1904_brick/brick/rough_red_brown/rough_red_brown_roughness.png
textures/prairie_1904_brick/mortar/mortar_dark/material.json
textures/prairie_1904_brick/mortar/mortar_dark/mortar_dark_basecolor.png
textures/prairie_1904_brick/mortar/mortar_dark/mortar_dark_basecolor_web.jpg
textures/prairie_1904_brick/mortar/mortar_dark/mortar_dark_height16.png
textures/prairie_1904_brick/mortar/mortar_dark/mortar_dark_normal_gl.png
textures/prairie_1904_brick/mortar/mortar_dark/mortar_dark_normal_gl_web.jpg
textures/prairie_1904_brick/mortar/mortar_dark/mortar_dark_orm.png
textures/prairie_1904_brick/mortar/mortar_dark/mortar_dark_orm_web.jpg
textures/prairie_1904_brick/mortar/mortar_dark/mortar_dark_roughness.png
textures/prairie_1904_brick/mortar/mortar_lime/material.json
textures/prairie_1904_brick/mortar/mortar_lime/mortar_lime_basecolor.png
textures/prairie_1904_brick/mortar/mortar_lime/mortar_lime_basecolor_web.jpg
textures/prairie_1904_brick/mortar/mortar_lime/mortar_lime_height16.png
textures/prairie_1904_brick/mortar/mortar_lime/mortar_lime_normal_gl.png
textures/prairie_1904_brick/mortar/mortar_lime/mortar_lime_normal_gl_web.jpg
textures/prairie_1904_brick/mortar/mortar_lime/mortar_lime_orm.png
textures/prairie_1904_brick/mortar/mortar_lime/mortar_lime_orm_web.jpg
textures/prairie_1904_brick/mortar/mortar_lime/mortar_lime_roughness.png
textures/prairie_1904_brick/panel/common_buff_common_6/common_buff_common_6_basecolor.png
textures/prairie_1904_brick/panel/common_buff_common_6/common_buff_common_6_basecolor_web.jpg
textures/prairie_1904_brick/panel/common_buff_common_6/common_buff_common_6_height16.png
textures/prairie_1904_brick/panel/common_buff_common_6/common_buff_common_6_normal_gl.png
textures/prairie_1904_brick/panel/common_buff_common_6/common_buff_common_6_normal_gl_web.jpg
textures/prairie_1904_brick/panel/common_buff_common_6/common_buff_common_6_orm.png
textures/prairie_1904_brick/panel/common_buff_common_6/common_buff_common_6_orm_web.jpg
textures/prairie_1904_brick/panel/common_buff_common_6/common_buff_common_6_roughness.png
textures/prairie_1904_brick/panel/common_buff_common_6/material.json
textures/prairie_1904_brick/panel/pressed_red_flemish_dark_headers/material.json
textures/prairie_1904_brick/panel/pressed_red_flemish_dark_headers/pressed_red_flemish_dark_headers_basecolor.png
textures/prairie_1904_brick/panel/pressed_red_flemish_dark_headers/pressed_red_flemish_dark_headers_basecolor_web.jpg
textures/prairie_1904_brick/panel/pressed_red_flemish_dark_headers/pressed_red_flemish_dark_headers_height16.png
textures/prairie_1904_brick/panel/pressed_red_flemish_dark_headers/pressed_red_flemish_dark_headers_normal_gl.png
textures/prairie_1904_brick/panel/pressed_red_flemish_dark_headers/pressed_red_flemish_dark_headers_normal_gl_web.jpg
textures/prairie_1904_brick/panel/pressed_red_flemish_dark_headers/pressed_red_flemish_dark_headers_orm.png
textures/prairie_1904_brick/panel/pressed_red_flemish_dark_headers/pressed_red_flemish_dark_headers_orm_web.jpg
textures/prairie_1904_brick/panel/pressed_red_flemish_dark_headers/pressed_red_flemish_dark_headers_roughness.png
textures/prairie_1904_brick/panel/pressed_red_running/material.json
textures/prairie_1904_brick/panel/pressed_red_running/pressed_red_running_basecolor.png
textures/prairie_1904_brick/panel/pressed_red_running/pressed_red_running_basecolor_web.jpg
textures/prairie_1904_brick/panel/pressed_red_running/pressed_red_running_height16.png
textures/prairie_1904_brick/panel/pressed_red_running/pressed_red_running_normal_gl.png
textures/prairie_1904_brick/panel/pressed_red_running/pressed_red_running_normal_gl_web.jpg
textures/prairie_1904_brick/panel/pressed_red_running/pressed_red_running_orm.png
textures/prairie_1904_brick/panel/pressed_red_running/pressed_red_running_orm_web.jpg
textures/prairie_1904_brick/panel/pressed_red_running/pressed_red_running_roughness.png
textures/prairie_1904_brick/panel/rough_red_brown_running/material.json
textures/prairie_1904_brick/panel/rough_red_brown_running/rough_red_brown_running_basecolor.png
textures/prairie_1904_brick/panel/rough_red_brown_running/rough_red_brown_running_basecolor_web.jpg
textures/prairie_1904_brick/panel/rough_red_brown_running/rough_red_brown_running_height16.png
textures/prairie_1904_brick/panel/rough_red_brown_running/rough_red_brown_running_normal_gl.png
textures/prairie_1904_brick/panel/rough_red_brown_running/rough_red_brown_running_normal_gl_web.jpg
textures/prairie_1904_brick/panel/rough_red_brown_running/rough_red_brown_running_orm.png
textures/prairie_1904_brick/panel/rough_red_brown_running/rough_red_brown_running_orm_web.jpg
textures/prairie_1904_brick/panel/rough_red_brown_running/rough_red_brown_running_roughness.png
textures/prairie_1904_brick/profiles.json
textures/prairie_1904_brick/tools/generate_prairie_1904_brick.py
```

### The Prairie Avenue 1904 stone library (K02) — `textures/prairie_1904_stone/`

T-2288, piece 1 of T-1844. Seven procedural stone fabrics for the 1904 programme's walls, trim and
foundations (rock-faced granite, brown sandstone, light fawn sandstone (T-1881), Lemont and Bedford
limestone, dressed trim, foundation rubble), built by the generator that ships inside it
(`tools/generate_prairie_1904_stone.py`, deterministic, seeded per fabric). Which building wears
which stone is its structure record's to say; the look of every map is reconstructed
(`docs/LIBERTIES.md` L-k02-stone-library-2288).

| item | licence | cleared for | NOT cleared for |
|---|---|---|---|
| `textures/prairie_1904_stone/**` — *Prairie Avenue 1904 stone library (K02) v1.0.0*, original procedural output generated for this project. Full text at `textures/prairie_1904_stone/LICENSE.txt` | **Project-permissive, CC0-equivalent**, the 1835 and 1904 street libraries' terms. No third-party photograph or image is embedded, sampled or traced | **Use, modification and redistribution with the project**, including regenerated maps | **Stripping the confidence labels.** Each `material.json` says its appearance is reconstructed and that a structure record, not the map, carries the evidence |

**Not published.** No scene binds these maps yet and `tools/publish.sh` ships none of them; T-2289
lays them on the 1808 Prairie exemplar.

Every file, as the checker matches them one by one:

```
textures/prairie_1904_stone/LICENSE.txt
textures/prairie_1904_stone/README.md
textures/prairie_1904_stone/contact_sheet.jpg
textures/prairie_1904_stone/dressed_trim/dressed_trim_basecolor.png
textures/prairie_1904_stone/dressed_trim/dressed_trim_basecolor_web.jpg
textures/prairie_1904_stone/dressed_trim/dressed_trim_height16.png
textures/prairie_1904_stone/dressed_trim/dressed_trim_normal_gl.png
textures/prairie_1904_stone/dressed_trim/dressed_trim_normal_gl_web.jpg
textures/prairie_1904_stone/dressed_trim/dressed_trim_orm.png
textures/prairie_1904_stone/dressed_trim/dressed_trim_orm_web.jpg
textures/prairie_1904_stone/dressed_trim/material.json
textures/prairie_1904_stone/foundation_rubble/foundation_rubble_basecolor.png
textures/prairie_1904_stone/foundation_rubble/foundation_rubble_basecolor_web.jpg
textures/prairie_1904_stone/foundation_rubble/foundation_rubble_height16.png
textures/prairie_1904_stone/foundation_rubble/foundation_rubble_normal_gl.png
textures/prairie_1904_stone/foundation_rubble/foundation_rubble_normal_gl_web.jpg
textures/prairie_1904_stone/foundation_rubble/foundation_rubble_orm.png
textures/prairie_1904_stone/foundation_rubble/foundation_rubble_orm_web.jpg
textures/prairie_1904_stone/foundation_rubble/material.json
textures/prairie_1904_stone/granite_rock_faced/granite_rock_faced_basecolor.png
textures/prairie_1904_stone/granite_rock_faced/granite_rock_faced_basecolor_web.jpg
textures/prairie_1904_stone/granite_rock_faced/granite_rock_faced_height16.png
textures/prairie_1904_stone/granite_rock_faced/granite_rock_faced_normal_gl.png
textures/prairie_1904_stone/granite_rock_faced/granite_rock_faced_normal_gl_web.jpg
textures/prairie_1904_stone/granite_rock_faced/granite_rock_faced_orm.png
textures/prairie_1904_stone/granite_rock_faced/granite_rock_faced_orm_web.jpg
textures/prairie_1904_stone/granite_rock_faced/material.json
textures/prairie_1904_stone/limestone_bedford/limestone_bedford_basecolor.png
textures/prairie_1904_stone/limestone_bedford/limestone_bedford_basecolor_web.jpg
textures/prairie_1904_stone/limestone_bedford/limestone_bedford_height16.png
textures/prairie_1904_stone/limestone_bedford/limestone_bedford_normal_gl.png
textures/prairie_1904_stone/limestone_bedford/limestone_bedford_normal_gl_web.jpg
textures/prairie_1904_stone/limestone_bedford/limestone_bedford_orm.png
textures/prairie_1904_stone/limestone_bedford/limestone_bedford_orm_web.jpg
textures/prairie_1904_stone/limestone_bedford/material.json
textures/prairie_1904_stone/limestone_lemont/limestone_lemont_basecolor.png
textures/prairie_1904_stone/limestone_lemont/limestone_lemont_basecolor_web.jpg
textures/prairie_1904_stone/limestone_lemont/limestone_lemont_height16.png
textures/prairie_1904_stone/limestone_lemont/limestone_lemont_normal_gl.png
textures/prairie_1904_stone/limestone_lemont/limestone_lemont_normal_gl_web.jpg
textures/prairie_1904_stone/limestone_lemont/limestone_lemont_orm.png
textures/prairie_1904_stone/limestone_lemont/limestone_lemont_orm_web.jpg
textures/prairie_1904_stone/limestone_lemont/material.json
textures/prairie_1904_stone/sandstone_brown/material.json
textures/prairie_1904_stone/sandstone_brown/sandstone_brown_basecolor.png
textures/prairie_1904_stone/sandstone_brown/sandstone_brown_basecolor_web.jpg
textures/prairie_1904_stone/sandstone_brown/sandstone_brown_height16.png
textures/prairie_1904_stone/sandstone_brown/sandstone_brown_normal_gl.png
textures/prairie_1904_stone/sandstone_brown/sandstone_brown_normal_gl_web.jpg
textures/prairie_1904_stone/sandstone_brown/sandstone_brown_orm.png
textures/prairie_1904_stone/sandstone_brown/sandstone_brown_orm_web.jpg
textures/prairie_1904_stone/sandstone_fawn/material.json
textures/prairie_1904_stone/sandstone_fawn/sandstone_fawn_basecolor.png
textures/prairie_1904_stone/sandstone_fawn/sandstone_fawn_basecolor_web.jpg
textures/prairie_1904_stone/sandstone_fawn/sandstone_fawn_height16.png
textures/prairie_1904_stone/sandstone_fawn/sandstone_fawn_normal_gl.png
textures/prairie_1904_stone/sandstone_fawn/sandstone_fawn_normal_gl_web.jpg
textures/prairie_1904_stone/sandstone_fawn/sandstone_fawn_orm.png
textures/prairie_1904_stone/sandstone_fawn/sandstone_fawn_orm_web.jpg
textures/prairie_1904_stone/tools/generate_prairie_1904_stone.py
```

| path | source | license | notes |
|---|---|---|---|

### The Prairie Avenue 1904 roof library (K04) — `textures/prairie_1904_roofs/`

T-2292. Eleven procedural fabrics for the 1904 programme's roof coverings, flashings and rainwater
goods, built by the generator that ships inside it (`tools/generate_prairie_1904_roofs.py`,
deterministic, seeded per fabric) from the modules in `data/components/prairie_1904/k04_roofs.json`,
with the study renderer beside it. The look of every map is reconstructed (`docs/LIBERTIES.md`
L-k04-roof-library-2292); the flat tile's module is HABS's for Glessner, and nothing else here is
measured.

| item | licence | cleared for | NOT cleared for |
|---|---|---|---|
| `textures/prairie_1904_roofs/**` — *Prairie Avenue 1904 roof-covering library (K04) v1.0.0*, original procedural output generated for this project. Full text at `textures/prairie_1904_roofs/LICENSE.txt` | **Project-permissive, CC0-equivalent**, the 1904 street-surface library's terms. No third-party photograph or image is embedded, sampled or traced | **Use, modification and redistribution with the project**, including regenerated maps | **Stripping the confidence labels.** Each `material.json` says its appearance is reconstructed and names the data file its module comes from |

The files:

```
textures/prairie_1904_roofs/LICENSE.txt
textures/prairie_1904_roofs/README.md
textures/prairie_1904_roofs/copper_sheet/copper_sheet_basecolor.png
textures/prairie_1904_roofs/copper_sheet/copper_sheet_basecolor_web.jpg
textures/prairie_1904_roofs/copper_sheet/copper_sheet_normal_gl.png
textures/prairie_1904_roofs/copper_sheet/copper_sheet_normal_gl_web.jpg
textures/prairie_1904_roofs/copper_sheet/copper_sheet_orm.png
textures/prairie_1904_roofs/copper_sheet/copper_sheet_orm_web.jpg
textures/prairie_1904_roofs/copper_sheet/copper_sheet_roughness.png
textures/prairie_1904_roofs/copper_sheet/material.json
textures/prairie_1904_roofs/copper_standing_seam/copper_standing_seam_basecolor.png
textures/prairie_1904_roofs/copper_standing_seam/copper_standing_seam_basecolor_web.jpg
textures/prairie_1904_roofs/copper_standing_seam/copper_standing_seam_normal_gl.png
textures/prairie_1904_roofs/copper_standing_seam/copper_standing_seam_normal_gl_web.jpg
textures/prairie_1904_roofs/copper_standing_seam/copper_standing_seam_orm.png
textures/prairie_1904_roofs/copper_standing_seam/copper_standing_seam_orm_web.jpg
textures/prairie_1904_roofs/copper_standing_seam/copper_standing_seam_roughness.png
textures/prairie_1904_roofs/copper_standing_seam/material.json
textures/prairie_1904_roofs/lead_sheet/lead_sheet_basecolor.png
textures/prairie_1904_roofs/lead_sheet/lead_sheet_basecolor_web.jpg
textures/prairie_1904_roofs/lead_sheet/lead_sheet_normal_gl.png
textures/prairie_1904_roofs/lead_sheet/lead_sheet_normal_gl_web.jpg
textures/prairie_1904_roofs/lead_sheet/lead_sheet_orm.png
textures/prairie_1904_roofs/lead_sheet/lead_sheet_orm_web.jpg
textures/prairie_1904_roofs/lead_sheet/lead_sheet_roughness.png
textures/prairie_1904_roofs/lead_sheet/material.json
textures/prairie_1904_roofs/manifest.json
textures/prairie_1904_roofs/painted_tin_sheet/material.json
textures/prairie_1904_roofs/painted_tin_sheet/painted_tin_sheet_basecolor.png
textures/prairie_1904_roofs/painted_tin_sheet/painted_tin_sheet_basecolor_web.jpg
textures/prairie_1904_roofs/painted_tin_sheet/painted_tin_sheet_normal_gl.png
textures/prairie_1904_roofs/painted_tin_sheet/painted_tin_sheet_normal_gl_web.jpg
textures/prairie_1904_roofs/painted_tin_sheet/painted_tin_sheet_orm.png
textures/prairie_1904_roofs/painted_tin_sheet/painted_tin_sheet_orm_web.jpg
textures/prairie_1904_roofs/painted_tin_sheet/painted_tin_sheet_roughness.png
textures/prairie_1904_roofs/slate_fishscale/material.json
textures/prairie_1904_roofs/slate_fishscale/slate_fishscale_basecolor.png
textures/prairie_1904_roofs/slate_fishscale/slate_fishscale_basecolor_web.jpg
textures/prairie_1904_roofs/slate_fishscale/slate_fishscale_normal_gl.png
textures/prairie_1904_roofs/slate_fishscale/slate_fishscale_normal_gl_web.jpg
textures/prairie_1904_roofs/slate_fishscale/slate_fishscale_orm.png
textures/prairie_1904_roofs/slate_fishscale/slate_fishscale_orm_web.jpg
textures/prairie_1904_roofs/slate_fishscale/slate_fishscale_roughness.png
textures/prairie_1904_roofs/slate_pennsylvania/material.json
textures/prairie_1904_roofs/slate_pennsylvania/slate_pennsylvania_basecolor.png
textures/prairie_1904_roofs/slate_pennsylvania/slate_pennsylvania_basecolor_web.jpg
textures/prairie_1904_roofs/slate_pennsylvania/slate_pennsylvania_normal_gl.png
textures/prairie_1904_roofs/slate_pennsylvania/slate_pennsylvania_normal_gl_web.jpg
textures/prairie_1904_roofs/slate_pennsylvania/slate_pennsylvania_orm.png
textures/prairie_1904_roofs/slate_pennsylvania/slate_pennsylvania_orm_web.jpg
textures/prairie_1904_roofs/slate_pennsylvania/slate_pennsylvania_roughness.png
textures/prairie_1904_roofs/slate_vermont/material.json
textures/prairie_1904_roofs/slate_vermont/slate_vermont_basecolor.png
textures/prairie_1904_roofs/slate_vermont/slate_vermont_basecolor_web.jpg
textures/prairie_1904_roofs/slate_vermont/slate_vermont_normal_gl.png
textures/prairie_1904_roofs/slate_vermont/slate_vermont_normal_gl_web.jpg
textures/prairie_1904_roofs/slate_vermont/slate_vermont_orm.png
textures/prairie_1904_roofs/slate_vermont/slate_vermont_orm_web.jpg
textures/prairie_1904_roofs/slate_vermont/slate_vermont_roughness.png
textures/prairie_1904_roofs/terracotta_flat_tile/material.json
textures/prairie_1904_roofs/terracotta_flat_tile/terracotta_flat_tile_basecolor.png
textures/prairie_1904_roofs/terracotta_flat_tile/terracotta_flat_tile_basecolor_web.jpg
textures/prairie_1904_roofs/terracotta_flat_tile/terracotta_flat_tile_normal_gl.png
textures/prairie_1904_roofs/terracotta_flat_tile/terracotta_flat_tile_normal_gl_web.jpg
textures/prairie_1904_roofs/terracotta_flat_tile/terracotta_flat_tile_orm.png
textures/prairie_1904_roofs/terracotta_flat_tile/terracotta_flat_tile_orm_web.jpg
textures/prairie_1904_roofs/terracotta_flat_tile/terracotta_flat_tile_roughness.png
textures/prairie_1904_roofs/tin_flat_seam_painted/material.json
textures/prairie_1904_roofs/tin_flat_seam_painted/tin_flat_seam_painted_basecolor.png
textures/prairie_1904_roofs/tin_flat_seam_painted/tin_flat_seam_painted_basecolor_web.jpg
textures/prairie_1904_roofs/tin_flat_seam_painted/tin_flat_seam_painted_normal_gl.png
textures/prairie_1904_roofs/tin_flat_seam_painted/tin_flat_seam_painted_normal_gl_web.jpg
textures/prairie_1904_roofs/tin_flat_seam_painted/tin_flat_seam_painted_orm.png
textures/prairie_1904_roofs/tin_flat_seam_painted/tin_flat_seam_painted_orm_web.jpg
textures/prairie_1904_roofs/tin_flat_seam_painted/tin_flat_seam_painted_roughness.png
textures/prairie_1904_roofs/tin_standing_seam_painted/material.json
textures/prairie_1904_roofs/tin_standing_seam_painted/tin_standing_seam_painted_basecolor.png
textures/prairie_1904_roofs/tin_standing_seam_painted/tin_standing_seam_painted_basecolor_web.jpg
textures/prairie_1904_roofs/tin_standing_seam_painted/tin_standing_seam_painted_normal_gl.png
textures/prairie_1904_roofs/tin_standing_seam_painted/tin_standing_seam_painted_normal_gl_web.jpg
textures/prairie_1904_roofs/tin_standing_seam_painted/tin_standing_seam_painted_orm.png
textures/prairie_1904_roofs/tin_standing_seam_painted/tin_standing_seam_painted_orm_web.jpg
textures/prairie_1904_roofs/tin_standing_seam_painted/tin_standing_seam_painted_roughness.png
textures/prairie_1904_roofs/tools/generate_prairie_1904_roofs.py
textures/prairie_1904_roofs/tools/study_prairie_1904_roofs.py
textures/prairie_1904_roofs/zinc_sheet/material.json
textures/prairie_1904_roofs/zinc_sheet/zinc_sheet_basecolor.png
textures/prairie_1904_roofs/zinc_sheet/zinc_sheet_basecolor_web.jpg
textures/prairie_1904_roofs/zinc_sheet/zinc_sheet_normal_gl.png
textures/prairie_1904_roofs/zinc_sheet/zinc_sheet_normal_gl_web.jpg
textures/prairie_1904_roofs/zinc_sheet/zinc_sheet_orm.png
textures/prairie_1904_roofs/zinc_sheet/zinc_sheet_orm_web.jpg
textures/prairie_1904_roofs/zinc_sheet/zinc_sheet_roughness.png
```

## Generated assets

`gltf/` and `web/` are build output. Canonical archetype assets are regenerated by
`tools/bake.sh` from `data/` and `generators/`, and tracked in `assets/manifest.json`
with the input hash and the Blender version that produced them. Explicitly flagged
review massings for the anonymous reconstruction programme are regenerated without
Blender by `generators/inferred_placeholder.py`; the glTF asset itself carries
`asset.extras.placeholder: true`, the viewer says so, and `tools/check.sh` compares
the bytes to the source record. Do not hand-edit either kind; stale output is a check
failure.

| path | origin | license | notes |
|---|---|---|---|
| `gltf/sauganash_hotel__frame_1831.glb` | `tools/bake.sh` (this repo, Blender 4.5.3) from `data/structures/sauganash_hotel.json` | project license | The Milestone 0 bake. Generated output; its provenance is the provenance of the record it was generated from, tracked in `assets/manifest.json`. |
| `gltf/keith_house_1808_prairie__as_built_1886.glb` | `python3 generators/k01_emit.py` (this repo, pure Python, no Blender) from `data/structures/keith_house_1808_prairie.json` | project license | The first K01 component assembly (T-2266). Generated output; its provenance is its record's, tracked in `assets/manifest.json`. Embeds two images verbatim from `textures/glessner-v4/` (`limestone_basecolor.jpg`, `brick_basecolor.jpg`), original procedural pixels under that library's project-permissive terms (`textures/glessner-v4/LICENSE.txt`). |
| `web/keith_house_1808_prairie__as_built_1886.glb` | `tools/web_derivatives.sh` from the master above | project license | The web derivative of the K01 assembly; same provenance and the same two library images. |
| `gltf/pullman_house_1729_prairie_conservatory__as_standing_1904.glb` | `python3 generators/k13_emit.py` (this repo, pure Python, no Blender) from `data/structures/pullman_house_1729_prairie_conservatory.json` and the K13 kit | project license | The first K13 conservatory in the scene (T-2306). Generated output; its provenance is its record's, tracked in `assets/manifest.json`. Flat colours only: no image is embedded. |
| `web/pullman_house_1729_prairie_conservatory__as_standing_1904.glb` | `tools/web_derivatives.sh` from the master above | project license | The web derivative of the K13 conservatory; same provenance. |
| `gltf/shortall_gregory_house_1638_prairie_front__as_standing_1904.glb` | `python3 generators/k16_emit.py` (this repo, pure Python, no Blender) from `data/structures/shortall_gregory_house_1638_prairie_front.json` and the K16 kit | project license | The first K16 timber front in the scene (T-2323). Generated output; its provenance is its record's, tracked in `assets/manifest.json`. Flat colours only: no image is embedded. |
| `web/shortall_gregory_house_1638_prairie_front__as_standing_1904.glb` | `tools/web_derivatives.sh` from the master above | project license | The web derivative of the K16 timber front; same provenance. |
| `gltf/wheeler_house_1812_prairie_coach_house__as_standing_1904.glb` | `python3 generators/k12_emit.py` (this repo, pure Python, no Blender) from `data/structures/wheeler_house_1812_prairie_coach_house.json` | project license | The first K12 coach house on a named lot (T-2321). Generated output; its provenance is its record's, tracked in `assets/manifest.json`. Flat colours only; embeds no image. |
| `web/wheeler_house_1812_prairie_coach_house__as_standing_1904.glb` | `tools/web_derivatives.sh` from the master above | project license | The web derivative of the 1812 coach house; same provenance, no image. |
| `gltf/*__draft_1904.glb` (the one hundred and thirty-nine `prairie_draft` records) | `python3 generators/draft_emit.py` (this repo, pure Python, no Blender) from the matching `data/structures/*.json` record, written by `tools/draft_prairie_1904.py` | project license | The Prairie Avenue district draft (T-2329, T-2330, T-2334, T-2335, T-2351) and its named context buildings off the avenue (T-2982). Generated output; its provenance is its record's, tracked in `assets/manifest.json`. Flat colours only: no image is embedded. |
| `web/*__draft_1904.glb` | `tools/web_derivatives.sh` from the masters above | project license | The web derivatives of the district draft; same provenance. |
| `gltf/recon_1835_*__inferred_1835.glb` and matching `web/` derivatives | `generators/inferred_placeholder.py` from the matching `data/structures/recon_1835_*.json` record | project license | Pure-Python review massing for the 108 anonymous inferred roofs. Every file self-identifies as a placeholder and is replaced, not silently promoted, when the canonical family bake lands. |
| `humans/c4d_fixture.lod0.glb` | `tools/human_export.sh` (this repo, Blender 4.5.3): `tools/human_fixture_blend.py` builds the master, `tools/human_export.py` exports it | project license | The portable-human pipeline's CI fixture (T-1787, liberty L417): a figure that is nobody, built from primitives. Its master is the script, so the `.blend` is rebuilt on every run and this file is never the only copy. Its one texture, a 64 px twill, is generated in the script; nothing third-party is sampled or embedded. |
| `humans/web/c4d_fixture.lod0.glb` | `tools/human_export.sh` from the master above (gltf-transform `meshopt`, the `tools/web_derivatives.sh` pin) | project license | The Meshopt derivative of the fixture's LOD0; same provenance. |
| `humans/c4d_fixture.lod1.glb` | `tools/human_export.sh` (this repo, Blender 4.5.3): `tools/human_fixture_blend.py` builds the master, `tools/human_export.py` exports it | project license | The portable-human pipeline's CI fixture (T-1787, liberty L417): a figure that is nobody, built from primitives. Its master is the script, so the `.blend` is rebuilt on every run and this file is never the only copy. Its one texture, a 64 px twill, is generated in the script; nothing third-party is sampled or embedded. |
| `humans/web/c4d_fixture.lod1.glb` | `tools/human_export.sh` from the master above (gltf-transform `meshopt`, the `tools/web_derivatives.sh` pin) | project license | The Meshopt derivative of the fixture's LOD1; same provenance. |
| `humans/c4d_fixture.lod2.glb` | `tools/human_export.sh` (this repo, Blender 4.5.3): `tools/human_fixture_blend.py` builds the master, `tools/human_export.py` exports it | project license | The portable-human pipeline's CI fixture (T-1787, liberty L417): a figure that is nobody, built from primitives. Its master is the script, so the `.blend` is rebuilt on every run and this file is never the only copy. Its one texture, a 64 px twill, is generated in the script; nothing third-party is sampled or embedded. |
| `humans/web/c4d_fixture.lod2.glb` | `tools/human_export.sh` from the master above (gltf-transform `meshopt`, the `tools/web_derivatives.sh` pin) | project license | The Meshopt derivative of the fixture's LOD2; same provenance. |
| `humans/c4d_fixture.lod3.glb` | `tools/human_export.sh` (this repo, Blender 4.5.3): `tools/human_fixture_blend.py` builds the master, `tools/human_export.py` exports it | project license | The portable-human pipeline's CI fixture (T-1787, liberty L417): a figure that is nobody, built from primitives. Its master is the script, so the `.blend` is rebuilt on every run and this file is never the only copy. Its one texture, a 64 px twill, is generated in the script; nothing third-party is sampled or embedded. |
| `humans/web/c4d_fixture.lod3.glb` | `tools/human_export.sh` from the master above (gltf-transform `meshopt`, the `tools/web_derivatives.sh` pin) | project license | The Meshopt derivative of the fixture's LOD3; same provenance. |

`authored/` holds hero assets that cannot come from a structure record (Fort Dearborn
detailing, signboards). They are exempt from regeneration but **not** from provenance:
each needs a row here and a source record explaining what the form is based on.
### Glessner House stone-occlusion atlases (T-2431)

T-2494 retains each atlas's generated UV coordinates in the same NPZ, with the exact
mesh/unwrap-recipe key and a coordinate checksum. These are coordinates generated
from this project's own mesh, under the same project license; no reference pixels
or third-party mesh data are incorporated.

Generated output of this repository's own Cycles bake (`generators/archetypes/masonry_house_v4_occlusion.py`, Blender 4.5.3) of the Glessner House's own geometry: the quantised ambient-occlusion atlas of its granite, kept so a bake on any CPU reproduces the committed models. Nothing third-party is sampled or embedded; project license. Provenance is the model's, tracked in `assets/manifest.json`.

- `bakes/stone-occlusion/README.md`
- `bakes/stone-occlusion/granite_stone_occlusion_1024.npz`
- `bakes/stone-occlusion/granite_stone_occlusion_2048.npz`

### Glessner House v4 original surface studies

The following 43 files are original project material assets: eleven deterministic numeric PBR fabrics, three unchanged original generated albedo studies, their executable recipe and provenance. No historical, owner, Google or other third-party image pixels are sampled or embedded. Numeric maps are reproduced by `generate.py`; generated image prompts, hashes, methods and reconstructed confidence are preserved in the three provenance JSON files. Exact appearance is reconstructed, not historical evidence. Use, modification and redistribution with this project are permitted under the accompanying `LICENSE.txt`; retain provenance and confidence.

- `textures/glessner-v4/LICENSE.txt`
- `textures/glessner-v4/README.md`
- `textures/glessner-v4/brick_basecolor.jpg`
- `textures/glessner-v4/brick_normal.png`
- `textures/glessner-v4/brick_roughness.png`
- `textures/glessner-v4/court_brick_basecolor.jpg`
- `textures/glessner-v4/copper_basecolor.jpg`
- `textures/glessner-v4/copper_normal.png`
- `textures/glessner-v4/copper_roughness.png`
- `textures/glessner-v4/generate.py`
- `textures/glessner-v4/granite_basecolor.jpg`
- `textures/glessner-v4/granite_normal.png`
- `textures/glessner-v4/granite_occlusion.png`
- `textures/glessner-v4/granite_photographic_basecolor.png`
- `textures/glessner-v4/granite_photographic_provenance.json`
- `textures/glessner-v4/granite_roughness.png`
- `textures/glessner-v4/gravel_basecolor.jpg`
- `textures/glessner-v4/gravel_normal.png`
- `textures/glessner-v4/gravel_roughness.png`
- `textures/glessner-v4/limestone_basecolor.jpg`
- `textures/glessner-v4/limestone_normal.png`
- `textures/glessner-v4/limestone_roughness.png`
- `textures/glessner-v4/material-library.json`
- `textures/glessner-v4/mortar_basecolor.jpg`
- `textures/glessner-v4/mortar_normal.png`
- `textures/glessner-v4/mortar_roughness.png`
- `textures/glessner-v4/oak_basecolor.jpg`
- `textures/glessner-v4/oak_normal.png`
- `textures/glessner-v4/oak_roughness.png`
- `textures/glessner-v4/painted_wood_basecolor.jpg`
- `textures/glessner-v4/painted_wood_normal.png`
- `textures/glessner-v4/painted_wood_roughness.png`
- `textures/glessner-v4/terracotta_basecolor.jpg`
- `textures/glessner-v4/terracotta_normal.png`
- `textures/glessner-v4/terracotta_roughness.png`
- `textures/glessner-v4/roof_tiles_basecolor.jpg`
- `textures/glessner-v4/roof_tiles_normal.png`
- `textures/glessner-v4/roof_tiles_roughness.png`
- `textures/glessner-v4/turf_basecolor.jpg`
- `textures/glessner-v4/turf_normal.png`
- `textures/glessner-v4/turf_patch_photographic_basecolor.png`
- `textures/glessner-v4/turf_patch_provenance.json`
- `textures/glessner-v4/turf_photographic_basecolor.png`
- `textures/glessner-v4/turf_photographic_provenance.json`
- `textures/glessner-v4/turf_roughness.png`


T-2220 copper: `textures/glessner-v4/copper_basecolor.jpg` and
`copper_roughness.png` are original procedural pixels from `generate.py --only
copper`, under the existing material-library LICENSE.txt. Drainage streaks are
numeric fields, not sampled photographs. The low hood and seam geometry derive
from unrestricted HABS section controls and declared stock reconstructions
(L-glessner-copper-2220). The three `wlemay_glessner_courtyard_2024_*` source
records are CC BY-SA 2.0 reference comparisons; their credited library display
and thumbnail copies retain that license in the separate chicago-images store.
No photographic pixels or traced patterns are embedded in model assets.

### T-2495 outer lakefront terrain

`data/terrain/epochs/e1871_postfire/context_ground.glb` (stored beside its terrain
sidecars, outside assets/) is generated by `tools/extend_ic_lakefront_1904.py` from
project heightfield data and map-coordinate readings. Project license; no raster
texture is embedded. The underlying 1904 Talbot map is public domain, credited to
the University of Chicago Library, Map Collection; source record
`data/sources/talbot_1904_railroad_map.json` records the provenance.

### Glessner chimney refinement (T-2222)

The regenerated Glessner master and Full/Light derivatives retain their existing
asset license. New chimney placement/cap construction rests on unrestricted HABS
IL-1015 measured drawings and public-domain Taylor2135; service masonry is a
bounded reconstruction corroborated by w_lemay's CC BY-SA2.0 courtyard photographs
159537051 and159537085. Source records retain creator, license and catalog links.
These are credited reference copies, not projected texture pixels or traced stone
patterns. The existing metric granite/brick/limestone textures are unchanged.
The Inland1888 digital reproduction and copied HABS05 remain textual/qualitative
cross-checks only and supply no new derived geometry or texture. Full/Light
simplifications and invented flue dimensions are declared in L-glessner-stacks-2222.
The HABS drawing excerpts in the T-2222 research folder are annotated diagnostic
crops of unrestricted federal measured drawings, not newly surveyed dimensions.

### Glessner service-access refinement (T-2223)

Generated Glessner Full/web/Light geometry and recovery assets follow the
existing model license. Service-access layout uses cleared HABS IL-1015 drawing
sheets 2 and 4. The qualitative stair/rail/capital comparison uses w_lemay's
October 26, 2024 Commons photograph 159537058 and the previously credited
159537051; CC BY-SA 2.0, https://creativecommons.org/licenses/by-sa/2.0/.
The new Prairie library display and thumbnail retain w_lemay attribution and
that license. They derive from the recorded 1920×1440 display rendition,
not the unavailable native original. No photographic pixels become textures.
Gate finish and hidden joints are procedural bounded reconstructions; no
uncleared photograph is traced. Research browser screenshots are generated
from this project's scene and contain no imported reference photograph.

### Glessner courtyard ground (T-2224)

The regenerated Full/web/Light model and recovery assets retain the existing model
license. New functional circulation is independently reconstructed from the cleared
HABS IL-1015 sheet 2 opening/stair locations and public-domain written alteration
history. HABS05 is rights-uncleared and is not traced for this work. The plan does not
identify 1904 paths or paving materials; those choices are declared in
L-glessner-court-ground-2224. Existing original procedural gravel and turf textures
are unchanged. Browser screenshots and the schematic ground plot are generated
project diagnostics, not reproductions of a historical courtyard photograph.


### T-2225 — Original Glessner vine atlas and generated planting

`assets/textures/glessner-v4/vines_atlas.png` is original procedural artwork generated by `python3 tools/generate_glessner_vines.py` from `form.vines_details` and `generators/archetypes/masonry_house_v4_vines.py`. It contains no sampled photograph, external illustration or imported texture. The numeric profiles, vein/serration strokes and reconstructed summer colours are created for this project and covered by the repository license. The public-domain USDA NRCS Plant Guide by Kellie King and James Henson (edited2005/2006, source `usda_nrcs_virginia_creeper_2006`) bounds Virginia-creeper botanical facts only. HABS supplies the walls/openings; no source supplies the invented July1904 coverage. Boston ivy profiles are independent original botanical reconstructions. The Full and Light Glessner assets share this atlas and carry L-glessner-vines-2225; existing house/master/derivative provenance remains applicable.


### Glessner plain-brick surface study — T-2226

`textures/glessner-v4/flat_brick_basecolor.png`, `textures/glessner-v4/flat_brick_normal.png` and `textures/glessner-v4/flat_brick_roughness.png` are original procedural artwork generated by `python3 tools/generate_glessner_finish.py` from `form.surface_finish`, the existing original courtyard clay/mortar maps and `generators/archetypes/masonry_house_v4_finish.py`. They contain no photograph pixels, tracings or imported material and are covered by the repository license. Cleared HABS measured drawings, the licensed w_lemay courtyard reference and the owner brief bound the declared reconstruction; the family typescript remains a textual comparison with unresolved rights unchanged and supplies no asset pixels or traced pattern. Full and Light share these maps. See L-glessner-finish-2226; existing house/master/derivative provenance remains applicable.


### T-1883 — Keith house stone-front finish (2026-10-16)

`gltf/keith_house_1808_prairie__as_built_1886.glb` and its `web/` derivative are
procedurally generated from the structure record by `generators/k01_emit.py`.
The geometry is project-authored under the repository licence. Existing K02 granite
and dressed-stone textures retain their own entries above; no photograph is used
as a texture. The reconstruction uses the February 1888 Inland Architect plate,
credited to Inland Architect Press, scan via Internet Archive (Serials in Microfilm).
The project owner expressly approved this image for T-1883 on 2026-10-16; see
`data/sources/inland_architect_1888_02_keith_plate.json` for the scope and exact quote.
The reference scan is `data/sources/assets/inland_architect_1888_02_keith/plate.jpg`.
The September 1886 notice is public-domain textual evidence for granite; the
neutral light greige tint is reconstructed, not a colour sampled from the monochrome plate.

The additional comparison photographs retain the credits, source links and unresolved
rights recorded in [the reference credit ledger](../data/sources/assets/inland_architect_1888_02_keith/README.md).
They are research copies under the owner’s library instruction, not material textures or
a claim that the plate approval covers later photographs.


Glessner T-2228 entrance-section update (2026-10-16): generated geometry additionally cites public-domain Richardson office doorway23A, `artic_glessner_sheet_23a_entrance_detail`, corroborated by U.S. Government HABS IL-1015 sheet5. No photographic or drawing pixels are embedded in the asset; exact relief dimensions remain reconstructed.

## textures/trees/ — the grown trees' leaf and bark atlases (T-2743)

textures/trees/leaf_atlas.webp
textures/trees/bark_basecolor.webp
textures/trees/bark_normal.webp
textures/trees/leaf_atlas.ktx2
textures/trees/bark_basecolor.ktx2
textures/trees/bark_normal.ktx2

These are painted from code (the .ktx2 files are GPU-compressed copies of the same maps) by `tools/generate_tree_atlas.py` (seeded noise, cell patterns and drawn leaf
outlines), and the generator reproduces them. One photograph is sampled: since T-3247 the elm
tiles' blades take their surface (lightness only) from Steven J. Baskauf, *Ulmus americana
(Ulmaceae) - leaf - whole upper surface*, 2 June 2002, [Bioimages, Vanderbilt University
image 11688](https://bioimages.vanderbilt.edu/baskauf/11688.htm), **CC BY 4.0**
(https://creativecommons.org/licenses/by/4.0/); source record `bioimages_ulmus_americana_11688`,
the photograph at `data/sources/assets/bioimages_ulmus_americana_11688/`. The leaf atlas is an
adaptation of it and carries that attribution; everything else in these files is
project-authored under the repository licence. They show what a species' leaf and bark
generally look like; they are not evidence about any tree that stood (docs/LIBERTIES.md
L-tree-architecture-2743).


### Anonymous adult source and preparation — `authored/humans/makehuman_hm08/`

The verbatim MakeHuman graphical assets are **CC0-1.0**,
pinned to [MakeHuman commit a8bc2d54ff0ac92e78ff71431b1023eda42bf482](https://github.com/makehumancommunity/makehuman/tree/a8bc2d54ff0ac92e78ff71431b1023eda42bf482).
The upstream license documents are preserved verbatim under their own distribution
terms; LICENSE.CODE.md is a license notice, not included program code.
`SOURCE.json` records per-file upstream URLs and SHA-256 hashes; the OBJ, skeleton,
weights and material retain their own CC0 notices. Upstream application code is AGPL
and is not included or copied into the preprocessing tool. `LICENSE.md.gz` losslessly preserves
the upstream explanation of this distinction. Original `prepared.json`,
`prepared.report.json`, `SOURCE.json` and README adaptations are CC0-1.0.
Height, pose, joint mapping and weight pruning are reconstructed (L418). This is a
cleared modeling input, not a finished photographic person. No external skin-image
pack has been imported.

Originally authored canonical workwear masters under `authored/humans/teamsters/`
and their `humans/*_1835.lod*.glb` / `humans/web/*_1835.lod*.glb`
exports are CC0-1.0 with the same base provenance and L418 reconstruction declaration.
These paths become deliverables only after the CI bake produces and validates them;
listing the license does not assert the files already exist or meet production quality.

Exact covered paths (future canonical/export paths retain the provisional status above):

```text
authored/humans/makehuman_hm08/LICENSE.ASSETS.md
authored/humans/makehuman_hm08/LICENSE.CODE.md
authored/humans/makehuman_hm08/LICENSE.md.gz
authored/humans/makehuman_hm08/README.md
authored/humans/makehuman_hm08/SOURCE.json
authored/humans/makehuman_hm08/adult_25.recipe.json
authored/humans/makehuman_hm08/adult_35.recipe.json
authored/humans/makehuman_hm08/makehuman/data/3dobjs/base.obj
authored/humans/makehuman_hm08/makehuman/data/rigs/default.mhskel
authored/humans/makehuman_hm08/makehuman/data/rigs/default_weights.mhw
authored/humans/makehuman_hm08/makehuman/data/skins/default.mhmat
authored/humans/makehuman_hm08/makehuman/data/targets/macrodetails/african-male-old.target
authored/humans/makehuman_hm08/makehuman/data/targets/macrodetails/african-male-young.target
authored/humans/makehuman_hm08/makehuman/data/targets/macrodetails/asian-male-old.target
authored/humans/makehuman_hm08/makehuman/data/targets/macrodetails/asian-male-young.target
authored/humans/makehuman_hm08/makehuman/data/targets/macrodetails/caucasian-male-old.target
authored/humans/makehuman_hm08/makehuman/data/targets/macrodetails/caucasian-male-young.target
authored/humans/makehuman_hm08/makehuman/data/targets/macrodetails/universal-male-young-averagemuscle-averageweight.target
authored/humans/makehuman_hm08/prepared.json
authored/humans/makehuman_hm08/prepared.report.json
authored/humans/makehuman_hm08/prepared_adult_25.json
authored/humans/makehuman_hm08/prepared_adult_25.report.json
authored/humans/makehuman_hm08/prepared_adult_35.json
authored/humans/makehuman_hm08/prepared_adult_35.report.json
authored/humans/teamsters/bardwell_otis_1835/canonical.blend
humans/bardwell_otis_1835.lod0.glb
humans/web/bardwell_otis_1835.lod0.glb
humans/bardwell_otis_1835.lod1.glb
humans/web/bardwell_otis_1835.lod1.glb
humans/bardwell_otis_1835.lod2.glb
humans/web/bardwell_otis_1835.lod2.glb
humans/bardwell_otis_1835.lod3.glb
humans/web/bardwell_otis_1835.lod3.glb
authored/humans/teamsters/dufresne_joseph_1835/canonical.blend
humans/dufresne_joseph_1835.lod0.glb
humans/web/dufresne_joseph_1835.lod0.glb
humans/dufresne_joseph_1835.lod1.glb
humans/web/dufresne_joseph_1835.lod1.glb
humans/dufresne_joseph_1835.lod2.glb
humans/web/dufresne_joseph_1835.lod2.glb
humans/dufresne_joseph_1835.lod3.glb
humans/web/dufresne_joseph_1835.lod3.glb
authored/humans/teamsters/flynn_martin_1835/canonical.blend
humans/flynn_martin_1835.lod0.glb
humans/web/flynn_martin_1835.lod0.glb
humans/flynn_martin_1835.lod1.glb
humans/web/flynn_martin_1835.lod1.glb
humans/flynn_martin_1835.lod2.glb
humans/web/flynn_martin_1835.lod2.glb
humans/flynn_martin_1835.lod3.glb
humans/web/flynn_martin_1835.lod3.glb
```


### Skin material component — `authored/humans/skin_toigo_bronze/`

MargaretToigo, *young light-skinned male, bronze variation* (2017, changed 2019),
**CC0-1.0** in the actual official MakeHuman pack metadata; source
<https://files2.makehumancommunity.org/asset_packs/skins02/skins02_cc0.zip>,
asset page <http://www.makehumancommunity.org/node/1136>. The unchanged 2048² PNG
is SHA-256 `5a53213f061bfa97ee0afd6b40650ffbc089a479c144e63f3c39acceca5853c0`.
Exact metadata, material, official-page copies and extraction checks are retained
beside it; those documentary copies retain their source terms, while the original
SOURCE/README are project-authored CC0. This component conveys no historical likeness.

Additional exact covered CC0 graphical/derived and documentary paths:

```text
authored/humans/skin_toigo_bronze/README.md
authored/humans/skin_toigo_bronze/SOURCE.json
authored/humans/skin_toigo_bronze/skins02.official-page.md
authored/humans/skin_toigo_bronze/skins02.original.json
authored/humans/skin_toigo_bronze/toigo_light_skin_male_bronze.mhmat
authored/humans/skin_toigo_bronze/young_lightskinned_male_diffuse_Bronze.png
```

The upstream MakeHuman overview notice is retained verbatim as deterministic gzip:
its original seven-equals Markdown heading conflicts with the repository's literal
marker scan. SOURCE.json records both original and stored hashes and sizes, and the
preparation tool verifies the decompressed original too. No notice wording or
conflict-check assertion is changed.


### Hair component — `authored/humans/hair_short04/` (CC0-1.0)

MakeHuman system **short04**, UUID `e09bfd91-f83f-4f9a-ba8c-4635cd1ae0d8`, officially listed author `makehuman_system`. Actual original OBJ, mhclo and mhmat headers EACH state:

> This asset was explicitly released as CC0 in september 2020.
> Copyright (C) 2020 Data Collection AB, https://www.datacollection.se
> Copyright (C) 2020 Joel Palmius
> Copyright (C) 2020 Jonas Hauquier

Original archive: <https://files2.makehumancommunity.org/asset_packs/makehuman_system_assets/makehuman_system_assets_cc0.zip>, ETag `"10bbb7ea-6160e7c0d7996"`. The original material directly names `short04_diffuse.png`; that texture is part of the expressly CC0 asset. No separate PNG license exception found. The headers refer to the upstream CC0 legal text; this component does not falsely claim a separate legal-text file was extracted from the archive. Retain original notices verbatim. No MakeHuman AGPL program or shader code included in the asset.

The periodic padded PNG is an original CC0 source derivative, explicitly labeled draft. README.md and SOURCE.json are original project-authored CC0 documentary provenance; original `.mhmat`/`.mhclo`/`.obj` notices retain their exact upstream wording. All exact component paths and SHA-256 hashes:

| Path relative to assets/ | Kind | SHA-256 |
|---|---|---|
| authored/humans/hair_short04/README.md | CC0 original project documentary | `fb920ea8d0082d3080db8acf6ed0d98805335ee166e1e1957861a3c520ac7679` |
| authored/humans/hair_short04/SOURCE.json | CC0 original project documentary | `68a02130cd50dd0d727f31f8f53702fe91bd9ecb9aa98309a7814191abf89e99` |
| authored/humans/hair_short04/short04.mhclo | CC0 original graphical/source metadata | `d60640aa4c4ffce1aa269647ba436b6ee0bb21bb948f927b84e27a48d2107157` |
| authored/humans/hair_short04/short04.mhmat | CC0 original graphical/source metadata | `7a3ac74db8478aa0afdb8a596c6fe3997d1a8a09d12211d70e8f1e9f0b7e0e97` |
| authored/humans/hair_short04/short04.obj | CC0 original graphical/source metadata | `676964a133ee35ffcea1195382bf75542da7a298931e4001bc7b0d7b707225de` |
| authored/humans/hair_short04/short04_diffuse.png | CC0 original graphical/source metadata | `0bef7fc0e403db5a40fabb2111ebfa6f7e8158e204c6e56b8da98e9ef527846e` |
| authored/humans/hair_short04/short04_diffuse_periodic_pad_draft.png | CC0 derived periodic-padded texture | `194e53741c7c96e16d4aac8ba10a1bb87c9cb86e976bda82655ad10d38b58871` |

This is a component entry additive to existing canonical-master and human master/web export entries for `bardwell_otis_1835`, `dufresne_joseph_1835` and `flynn_martin_1835`; their rebuilt byte hashes do not exist yet and must be measured after CI, never fabricated. The source component conveys no period hairstyle, resident likeness, ancestry or historically observed action. Fitting tools remain project GPL-3.0-or-later code; those tools are not CC0 graphical assets.


## Original paired equine head/neck and headstrap refinement (T-2800/T-2801/T-2803)

CC0-1.0 original generated geometry and original generator source: `tools/transport/horse_geometry.py`, `tools/transport/generate_horse.py`, `tools/transport/generate_harness.py`; original parameter data `data/transport/studies/horse.json` (unchanged) and `data/transport/studies/harness.json`; derived `renderers/web/transport/horse/{equine_light_harness_skinned_prototype_01.glb,manifest.json}` and `renderers/web/transport/harness/{light_breastcollar_harness_reconstructed_01.glb,manifest.json,geometry-stats.json}`. Exact hashes are recorded in `docs/RESEARCH/period-transport-2026-10-18/head-neck-refinement/integration-inputs.json`. No external model, texture, source pixels or traced plate geometry. Research text informs provisional anatomy/construction but does not attest a horse, owner, breed, exact anatomy or strap dimensions. Original additions retain CC0-1.0 SPDX headers. Demo/integration and reused project fit methodology remain under the project's existing GPL license; CC0 geometry does not relicense those tools. Documentary screenshots/receipts are original diagnostic outputs, not source photographs.


## Grounded trot study (2026-10-19)

Original grounded-trot engineering addition (T-2803): tools/transport/horse_geometry.py, unchanged original tools/transport/generate_horse.py, data/transport/studies/horse.json, generated renderers/web/transport/horse/{equine_light_harness_skinned_prototype_01.glb,manifest.json} contain project-original CC0-1.0 procedural geometry/solver/animation/data; no externally copied program/model/texture or image tracing. Original3Dtwo-bone solver uses geometric sphere intersection and shortest-arc quaternions. renderers/web/transport/horse/{demo.js,index.html} and diagnostic test glue retain project's existing GPL license. No source-bounded measured biological gait or historic animal identity asserted. Concrete checkpoint hashes are in `docs/RESEARCH/period-transport-2026-10-18/head-neck-refinement/trot-inputs.json`.


## Original harness chest-clearance repair (T-2801, 2026-10-19)

The original CC0-1.0 harness generator, parameter data and generated web geometry retain the existing original reconstructed-asset license. Only breastcollar, two support straps and saddle-pad surfaces change; no external model, photograph, texture or traced source plate is copied. Current exact hashes appear in `docs/RESEARCH/period-transport-2026-10-18/harness-body-fit/INTEGRATION-MANIFEST.json`. Diagnostic screenshots are original project outputs, not historical source images.

`tools/transport/fixtures/harness-before-body-fit.json` is unchanged original CC0 parameter data (SHA-256 `7473be06e127388b07cd67af69db671bcc134999fa66849a5866f40c0794d85d`). `tools/transport/fixtures/harness-before-body-fit.glb.gz` is the original CC0 generated geometry, stored SHA-256 `cce8c06f3ff46346c133bdc4954546aa7533febd645bff61e6db5a2a11b5ebf9`, decompressed SHA-256 `b4a7318053e8508617a24fff64f02beb7eee77684db689dc04771d209a54fa8b`. Both are regression controls, not newly licensed third-party assets. The new standard-library diagnostic `tools/transport/test_harness_body_fit.py` remains project GPL-3.0-or-later code.

## C02 enclosed carriage reconstruction (T-2794,2026-10-19)

Original project-derived GPL-3.0-or-later source/geometry, based on the already licensed C01 procedural conventions; C02 is standalone source, not a runtime import or downloaded base. Exact source/input/output hashes are in docs/RESEARCH/period-transport-2026-10-18/c02-enclosed-door/INTEGRATION-MANIFEST.json. New files are tools/transport/generate_carriage_c02.py, tools/transport/test_carriage_c02_door.py, tools/transport/smoke_carriage_c02.cjs, data/transport/studies/carriage-c02.json, tools/transport/fixtures/carriage-c02-flag-off.json and renderers/web/transport/carriage-c02/{carriage-c02.glb,carriage-c02.json,parameters.json,index.html,demo.js}; gallery/orchestrator changes and original documentary receipts/screenshots retain projectGPL terms. No external model/texture/sourcepixels or proprietary program code is included. ExistingThree/vendor remains separately licensed and is not copied. No asset under assets/ is added; this entry records original generated-output provenance, not a CC0 external-asset exception.

All cabin/hardware/color dimensions are reconstructed. Reference catalog wording is 'No known restrictions on publication', not a new unconditional license. No rights-pending local photo or unseenWareplate derivation, attested ownership/subtype or historical paint is asserted. BaselineGLB SHA256 93d4020036e5c685ce95010fe64b26c55a1561db4517405f0590f7a398253331.


**Metadata and articulation qualification:** The pre-door project scope quotation is preserved separately with its original branch and explicit non-period origin; the enabled branch now describes reconstructed rigid door/hinge geometry and endpoint transforms. Current model metadata hash is 93d4020036e5c685ce95010fe64b26c55a1561db4517405f0590f7a398253331 (860956 bytes). Corrected checks bind all 424 actual moving triangles to the unique active exported door and compose actual hierarchy transforms at each angle; closed-world shape alone cannot qualify detached geometry. Old closed-mapping/source-posed receipts are retained only as limited historical checkpoints. No continuous/occupant/photographic acceptance or installed-head gate is implied.


### Supported W01 driver-bench study and named seated authoring (T-2804, 2026-10-19)

`renderers/web/transport/wagon-driver/wagon-w01.glb` and its JSON sidecar are original GPL-3.0-or-later procedural geometry produced by `tools/transport/generate_wagon.py` from `data/transport/studies/wagon-driver-bench.json`. The unoccupied variant is separate from the existing W01 and introduces no external image/model/texture derivation. Bench/hardware dimensions and construction are reconstructed engineering choices; license provenance does not establish period accuracy.

Optional seated resident pose data in `data/humans/poses/w01/` is original reconstructed CC0-1.0 numerical authoring based on the already-cleared CC0 human inputs. Helper, viewer and authoring code remains GPL-3.0-or-later. Existing MakeHuman graphical-base, skin, hair, canonical-master and human-export provenance continues unchanged. Existing L418 records these residents' reconstructed appearance and actions. New seated canonical export hashes and garment/contact/photographic acceptance must be measured after the actual CI export; no new master hash or likeness is invented here.


## Named era authoring studies (1812/1904), unaccepted prototypes

New files under assets/authored/humans/era_studies/{1812,1904} contain CC0-source prepared MakeHuman software bodies and original project-authored conjectural garment arrays/recipes. Body source metadata preserves the existing cleared source hashes and license; exact age target recipes accompany each immutable body. Original garment arrays, canonical composition adapters and engineering derivations are authored for this repository under its applicable original-work license. Garment_sources is empty: no photograph, museum garment, personal outfit, portrait or unknown-rights image was used to derive these garments.

The canonical caller reuses existing cleared skin_toigo_bronze and hair_short04 inputs under their existing unchanged SOURCE.json license evidence and exact file hashes. It does not relicense those assets. The source atlas is labeled young; using it on mature software bodies is an unaccepted engineering color-map choice, not an age-specific or personal complexion claim. Historical OCR citations remain identity/text evidence only and do not confer appearance rights or likeness provenance.

Exact body/garment hashes and derivations are in data/humans/recipes/era_studies/{1812,1904}.json and actual master metadata. No output is photographic, source-matched, period-wardrobe accepted, deformation accepted or scene eligible solely because this source is integrated.


Exact asset registrations for the named era studies (CC0-1.0 software graphical
inputs retain their existing source records; original numerical authoring below
is dedicated to CC0-1.0 alongside those inputs):

| path relative to assets/ | license | provenance |
| --- | --- | --- |
| `authored/humans/era_studies/1812/body-target.json` | CC0-1.0 | Original reconstructed age49/height parameters; existing cleared MakeHuman graphical targets, not application code. |
| `authored/humans/era_studies/1812/body.json` | CC0-1.0 | Prepared existing cleared hm08 graphical body; exact source and target hashes remain in this file. |
| `authored/humans/era_studies/1812/garments.json` | CC0-1.0 | Original project-authored conjectural garment arrays; no external garment or picture derived. |
| `authored/humans/era_studies/1904/body-target.json` | CC0-1.0 | Original reconstructed age61/height parameters; existing cleared MakeHuman graphical targets, not application code. |
| `authored/humans/era_studies/1904/glessner_john_j_1904.prepared.json` | CC0-1.0 | Prepared existing cleared hm08 graphical body; exact source and target hashes remain in this file. |
| `authored/humans/era_studies/1904/glessner_john_j_1904.garments.json` | CC0-1.0 | Original project-authored conjectural garment arrays; no external garment or picture derived. |


## Parked original transport variants (T-2979)

W01 geometry and source: GPL-3.0-or-later; nine original generated timber/paint/iron maps: CC0-1.0. See each SOURCE.json/ORIGINAL-MATERIAL-LICENSE.txt. No external photographic pixels or scans are incorporated.

| path relative to assets/ | license | provenance |
| --- | --- | --- |
| `authored/transport/wagon_parked/ORIGINAL-MATERIAL-LICENSE.txt` | CC0-1.0 | Original project-authored procedural graphical input; reproducible by tools/transport/generate_parked_wagon.py. |
| `authored/transport/wagon_parked/SOURCE.json` | CC0-1.0 | Original project-authored procedural graphical input; reproducible by tools/transport/generate_parked_wagon.py. |
| `authored/transport/wagon_parked/textures/iron_color.png` | CC0-1.0 | Original project-authored procedural graphical input; reproducible by tools/transport/generate_parked_wagon.py. |
| `authored/transport/wagon_parked/textures/iron_normal.png` | CC0-1.0 | Original project-authored procedural graphical input; reproducible by tools/transport/generate_parked_wagon.py. |
| `authored/transport/wagon_parked/textures/iron_orm.png` | CC0-1.0 | Original project-authored procedural graphical input; reproducible by tools/transport/generate_parked_wagon.py. |
| `authored/transport/wagon_parked/textures/paint_color.png` | CC0-1.0 | Original project-authored procedural graphical input; reproducible by tools/transport/generate_parked_wagon.py. |
| `authored/transport/wagon_parked/textures/paint_normal.png` | CC0-1.0 | Original project-authored procedural graphical input; reproducible by tools/transport/generate_parked_wagon.py. |
| `authored/transport/wagon_parked/textures/paint_orm.png` | CC0-1.0 | Original project-authored procedural graphical input; reproducible by tools/transport/generate_parked_wagon.py. |
| `authored/transport/wagon_parked/textures/wood_color.png` | CC0-1.0 | Original project-authored procedural graphical input; reproducible by tools/transport/generate_parked_wagon.py. |
| `authored/transport/wagon_parked/textures/wood_normal.png` | CC0-1.0 | Original project-authored procedural graphical input; reproducible by tools/transport/generate_parked_wagon.py. |
| `authored/transport/wagon_parked/textures/wood_orm.png` | CC0-1.0 | Original project-authored procedural graphical input; reproducible by tools/transport/generate_parked_wagon.py. |

## Original covered-wagon surfaces (T-2980)

| path relative to assets/ | license | provenance |
| --- | --- | --- |
| `authored/transport/wagon_covered/SOURCE.json` | CC0-1.0 original procedural pixels and descriptive data; geometry/source retain GPL-3.0-or-later | Original analytic reconstruction, no external pixels; reproducible by tools/transport/generate_covered_wagons.py; exact source and output hashes in SOURCE.json. |
| `authored/transport/wagon_covered/ORIGINAL-LICENSE.txt` | CC0-1.0 original procedural pixels and descriptive data; geometry/source retain GPL-3.0-or-later | Original analytic reconstruction, no external pixels; reproducible by tools/transport/generate_covered_wagons.py; exact source and output hashes in SOURCE.json. |
| `authored/transport/wagon_covered/textures/canvas_color.png` | CC0-1.0 original procedural pixels and descriptive data; geometry/source retain GPL-3.0-or-later | Original analytic reconstruction, no external pixels; reproducible by tools/transport/generate_covered_wagons.py; exact source and output hashes in SOURCE.json. |
| `authored/transport/wagon_covered/textures/canvas_normal.png` | CC0-1.0 original procedural pixels and descriptive data; geometry/source retain GPL-3.0-or-later | Original analytic reconstruction, no external pixels; reproducible by tools/transport/generate_covered_wagons.py; exact source and output hashes in SOURCE.json. |
| `authored/transport/wagon_covered/textures/canvas_orm.png` | CC0-1.0 original procedural pixels and descriptive data; geometry/source retain GPL-3.0-or-later | Original analytic reconstruction, no external pixels; reproducible by tools/transport/generate_covered_wagons.py; exact source and output hashes in SOURCE.json. |


## Original authored W01 material charts (T-2980)

The existing project-authored geometry supplies these original UV/tangent source inputs. Their GPL license is separate from the CC0 original procedural pixel maps. Exact hardware, ownership, recipe and original authoring hashes are recorded in SOURCE.json and the chart manifest. The ordinary producer validates these authored inputs; the original numerical authoring remains explicit opt-in. No outside geometry or photographic pixels are incorporated.

| path relative to assets/ | license | provenance |
| --- | --- | --- |
| `authored/transport/wagon_parked/charts/original-w01-charts.bin` | GPL-3.0-or-later | Original project-authored ordered UV/tangent data and author-time mapping from the reviewed W01 source; exact provenance in the manifest and SOURCE.json. |
| `authored/transport/wagon_parked/charts/original-w01-charts.json` | GPL-3.0-or-later | Original project-authored ordered UV/tangent data and author-time mapping from the reviewed W01 source; exact provenance in the manifest and SOURCE.json. |
| `authored/transport/wagon_parked/charts/original-w01-charts.mapping.json` | GPL-3.0-or-later | Original project-authored ordered UV/tangent data and author-time mapping from the reviewed W01 source; exact provenance in the manifest and SOURCE.json. |

### Actual Bardwell initial-standing canonical exports — 2026-10-22

Actual run39712579846, head34cf462ed343b8b2b70da70303344fff7e5e083f, artifact12398870779; exact existing CC0-1.0 graphical/component/master-export licenses and notices above continue. This receipt records actual bytes, not likeness, photographic or full-fit acceptance.

|Path under assets/|Bytes|SHA256|
|---|---:|---|
|humans/bardwell_otis_1835.lod0.glb|8633684|8b7d165bedfa5c8f12fd7e9aeb8d51e1cfc3cab816675a7817900f4bd9418198|
|humans/bardwell_otis_1835.lod1.glb|8004644|7935a45d0332020adae619b05fe84c5010a84a260ba04764bea6371ad953f318|
|humans/bardwell_otis_1835.lod2.glb|7459216|555432bfd5ca37c96755d33ed8ff24cc1ff7d77ad50896fa75ec0b61497c00c4|
|humans/bardwell_otis_1835.lod3.glb|7238540|4ec095034edbe19e91a53d34d82f5eb47ed99a0ec620ca2e487e328170872aa4|
|humans/web/bardwell_otis_1835.lod0.glb|4439324|47132fdfe27c1c144039e2db708bca6da6db63c201b37351a7632f1c0f45a953|
|humans/web/bardwell_otis_1835.lod1.glb|1564256|485856360666b48ea0534e645ebda0e678af63be9e66514be78df0621a262454|
|humans/web/bardwell_otis_1835.lod2.glb|617540|b9976874ae6a20a1e884bec62d97c4039312ae2e8ac4bd5cfbffd8148192485a|
|humans/web/bardwell_otis_1835.lod3.glb|308100|c86fff664ac893d0fb5d6877040a0d0a9d388dc9f25acfc208be0eeb13e12ad2|

### Actual Bardwell connected-waistcoat canonical replacement — 2026-10-22

Actual source96c4da4b1fe68e6dec3b18c15da2f14c596a60c5, successful canonical run39736567239 attempt1, artifact12408480668, ZIP SHA2569ca4e1e692da77d3cbb1e0089f2d53cc01cd360d8cafc2b0e97230434326d5f5. These eight exact same-run exports replace the earlier Bardwell initial-standing bytes only. Existing CC0-1.0 graphical/master/base/skin/hair provenance and notices above remain; project build-code licensing is unchanged. Source/web/sole/normal/rigid-frame/container/seated/W01 mechanical qualification is actual. Root reviewed actual publishedLOD0front/profile and accepted the repaired upper panels for the initial visible increment; broad photographic/full-fit/occupied acceptance remains open. Historical export receipts above remain historical.

|Path under assets/|Bytes|SHA256|
|---|---:|---|
|humans/bardwell_otis_1835.lod0.glb|8656876|84cdeb6d362aa1a85549b18daef41ae492f18595a19ff5b7e6eff539a3576d04|
|humans/bardwell_otis_1835.lod1.glb|8018176|e2ff6d6d4df02b3852248c4712b9472c86fe7ca14a60b3db02788deed8db73c3|
|humans/bardwell_otis_1835.lod2.glb|7465876|bc7ab6752b92f5451b285b070d2f76d896edddffa46d976c3569820745b8be7f|
|humans/bardwell_otis_1835.lod3.glb|7241808|8d36ceade3b2dce3b8d081dc484faa98bb57dd2c0d288c1043f0a6da9d3dc233|
|humans/web/bardwell_otis_1835.lod0.glb|4447008|3c75b33e5130fb8fe4813866d52d248bdab4207ab7a10c78b4074cc5fc30e999|
|humans/web/bardwell_otis_1835.lod1.glb|1568968|af2492264df071facce2c4ba128d851a5624f93bcf3f9e507eb406694e3124f1|
|humans/web/bardwell_otis_1835.lod2.glb|619964|ac21fdb00c402f76810a23467e299612042aa3ce21b017e7705ca675793df77a|
|humans/web/bardwell_otis_1835.lod3.glb|309428|b61d09e2efdb204a90d5d3c8fe49d1a6502108fd6ac62a592350129db48f8d40|

## V18 catalogue-guided Brougham lamps (T-2794)

Original project GPL-3.0-or-later source and generated geometry: `tools/transport/brougham/{generate.py,lamp_geometry.py,source_details.py,quarter_surface.py,index_streams.py,static_master.py,parameters.json,lods.json,rear-quarter.json,ring16-mid-lods.json,LICENSE}`. Current V18 near raw SHA256 `99f2ca33f0228d486db274f461c59eecdfa19dcb70d1eb2c080c30d4d5456b4a`, indexed SHA256 `bce1ecc757a7175cb193b1263fc8dbcdf1ce76a263916d3cff5e41dc4a835938` (33,374 triangles). Current mid raw SHA256 `f184d0fc96ecca92ae4ed51a57c468e9cf7e689264865ae45b23ccb007236f0d`, indexed SHA256 `65eec8b7e04e636c90e2d797f5e7e8c1d2695f0f45c6fb5c7f340f73e5616fa1` (11,706 triangles). The existing ring16 distance recipe uses 480 near and 314 mid subdivision records. Protected non-lamp positions/normals, seven materials, nodes, anchors, contacts and original conservative collision proxy remain exact; only the reconstructed lamp form changes. No external geometry or image textures are used.

The public-domain appearance reference is US1893 Studebaker catalogue leaf0095, source `studebaker_1893_illustrated_souvenir`, plate SHA256 `b458565ec06ba1e8e59d1455cc2d3f277c2371910b3085c2085749fc59a68abe`. No plate pixels are embedded. Maker/design availability is evidenced; this specimen, owner, stop, absolute dimensions, hidden construction and optical materials remain reconstructed. No Pullman/Glessner ownership is claimed. Rounder twin-faced lamp heads replace the earlier tall angular cages; a fixed-camera software projection comparison supports that limited form improvement, not Three PBR, browser, world, photographic or occupied acceptance. New native desktop/mobile image acceptance remains false after environment-limited launches. Eight earlier native views applied only to historical V17 distance appearance and are not transferred to V18. V17 source/contracts/metadata/receipts are retained explicitly as historical under `tools/transport/brougham/archive-v17/`, with its original GLBs in PR1175 Git history. The earlier22,238-triangle mid likewise remains historical. No Brougham file is added under assets/.

## W01 fine-grained timber material increment (T-2793)

`parked-wagon-fine-wood/` uses unchanged original project W01 geometry and project-authored UV/tangent/index charts (GPL-3.0-or-later). Side timber pixels derive from [Fine Grained Wood](https://polyhaven.com/a/fine_grained_wood), Rob Tuytel / Poly Haven, [CC0-1.0](https://creativecommons.org/publicdomain/zero/1.0/); original paint, iron and cut-end pixels remain CC0. Native2K maps were rotated, cropped, reduced2x, narrow8pxperiodic edge blended, and albedo given bounded1.5linear exposure; GL normal vectors were correspondingly rotated and renormalized. This is a modern optical analogy and reconstructed brown finish, with no species/date/coating/maker/Chicago-specimen attestation. Photographic/world/budget acceptance remains open. Source map URLs, official hashes and derivation are in `assets/authored/transport/wagon_parked_fine_wood/SOURCE.json`.

The authored binding files `assets/authored/transport/wagon_parked_fine_wood/{surface.json,surface.bin}` combine original project GPL-3.0-or-later UV/tangent/index charts with the documented CC0 image derivatives; the geometry is freshly regenerated by `tools/transport/generate_parked_wagon_fine_wood.py` through the unchanged original W01 pipeline. `ATTRIBUTION.txt` and `SOURCE.json` preserve creator, URLs, source hashes and transformations. The installed `renderers/web/transport/parked-wagon-fine-wood/wagon-w01.glb` SHA256 is e1e5b4f1d7dfe6bf08cca21e8cfae2e88748a3f6e6c6959753334ae2b0c84dd8. The original parked-wagon asset remains unchanged. The two covered variants retain distinct finish families and take only the separately documented cloth-drape increment.

| Asset | License | Provenance |
| --- | --- | --- |
| `authored/transport/wagon_parked_fine_wood/ATTRIBUTION.txt` | GPL-3.0-or-later | Original project attribution text identifying the separately licensed CC0 texture maps and their transformations. |
| `authored/transport/wagon_parked_fine_wood/surface.json` | GPL-3.0-or-later (project binding and charts); CC0-1.0 (texture derivatives) | Original project UV/tangent/index binding; Fine Grained Wood maps by Rob Tuytel / Poly Haven and original CC0 paint, iron and cut-end pixels, as documented above and in SOURCE.json. |
| `authored/transport/wagon_parked_fine_wood/surface.bin` | GPL-3.0-or-later (project charts); CC0-1.0 (texture pixels) | Original project chart streams and documented CC0 texture derivatives; no third-party geometry. |

The covered-cloth refinement under T-2980 changes only the reconstructed inter-bow drape constants (8–10mm to20–28mm over750mm spans), retaining original GPL geometry/source lineage and CC0 analytic texture pixels. Current source/product hashes are in `assets/authored/transport/wagon_covered/SOURCE.json`: core679fc439, blue GLB aaffa339, oak GLB22072e6f. Variant identities, seeded finish colors/aging, yokes, pivots, stands and newer terrain qualification are preserved. This is not an attested historic textile form or physical cloth simulation.


## Canonical26 planted-standing horse development derivative (T-2800/T-2803)

“Horse” by sevketkabatas, [CC BY4.0](https://creativecommons.org/licenses/by/4.0/), original https://sketchfab.com/3d-models/horse-53a6eb7ccf054aa2a378dd7ec08f88fe, retrieved via Objaverse on2026-10-22. Exact original source SHA41acd9bee7bf05fbcdd813fad965027b01b8801d6a21ca1c22eb2178c8842988 is unchanged in preserved acquisition/recovery. Current derivative b479442cb03ac46eb13c19da15a79cdfaf28dbdf356b116f78de7ce7ecdc60be is3,783,600bytes. Source rest surface baked to canonical metres; reconstructed26controls/V16skin and12s planted body-shift clip are explicit project adaptations. UV/maps/index topology and source shape retain CC BY4.0; no source six-clip or earlier head/tail playback is composed.

Rigged Mid-Poly Horse by antemeossa, CC BY4.0, https://sketchfab.com/3d-models/rigged-mid-poly-horse-fea999c1d8d64eb4a9c2bb1fac1e7d83 supplied hierarchy analogy only, not copied mesh or animation keys. Objaverse database notice remains ODC-By1.0 (Deitke etal.,2022); individual object rights remain CC BY4.0. Modern source publication/rights do not attest a Chicago individual, breed, owner or period appearance.

|Path relative to assets/|License and provenance|
|---|---|
|`authored/transport/horse_standing/horse-sevket-v16-planted-standing-v1.glb`|CC-BY-4.0 derivative; exact source/field/export lineage in SOURCE.json and ADAPTATION.md.|
|`authored/transport/horse_standing/SOURCE.json`|Project-authored source/change/binary binding; original third-party rights preserved.|
|`authored/transport/horse_standing/ADAPTATION.md`|Project-authored exact reconstruction/normalization/motion scope notice.|
|`authored/transport/horse_standing/ATTRIBUTION.md`|Preserved author/listing/license/acquisition credit and dataset notice.|
|`authored/transport/horse_standing/CC-BY-4.0-legal-text.txt`|Creative Commons legal-text notice preserved verbatim.|
|`authored/transport/horse_standing/dataset-README.md`|Preserved Objaverse ODC-By1.0 database notice; individual CC object license remains separate.|
|`authored/transport/horse_standing/53a6eb7ccf054aa2a378dd7ec08f88fe-public-metadata.json`|Preserved modern author/source/CC-BY-4.0 metadata, not period evidence.|
|`authored/transport/horse_standing/selected-dataset-metadata.json`|Preserved individual object license/creator metadata, not a new license grant.|
|`authored/transport/horse_standing/selected-acquisition.json`|Preserved exact-source acquisition provenance.|
|`authored/transport/horse_standing/planted-standing-export-receipt.json`|Project-authored source-protection/export receipt; export-only scope.|

Byte-identical runtime copy: `renderers/web/transport/standing-horse/horse-sevket-v16-planted-standing-v1.glb`. The renderer's declared organic_dielectric_v1 variant changes only cloned material metalness0, with original PBR maps/roughness/UV policy unchanged. Loaded129 CPU/Mixer PASS is recorded separately; yard/mobile/GPU/photographic/gait/tack/riding acceptance is not implied.

## Verified 1902 jail reference pages — T-3056

| item | licence | cleared for | NOT established |
|---|---|---|---|
| `data/sources/assets/trowbridge_first_jail_gale_1902/` — three unmodified JPEG scans, exact URLs/hashes in its manifest; [Internet Archive](https://archive.org/details/reminiscencesofe00ingale/page/n79/mode/1up) | **Public domain by age: US publication 1902**, verified actual title and copyright pages | Faithful reference copies and model derivation from W. E. S. Trowbridge’s published illustration in Edwin O. Gale’s book; credit retained in the source record and companion README | Exact July 1835 condition, metric dimensions, rights in added 1947 newspaper layout, or an item-specific licence for the separate UCR copy |


## Verified1902 Green Tree and Sauganash reference pages — T-3055

| item | licence | provenance and limits |
|---|---|---|
| `data/sources/assets/trowbridge_green_tree_1902/gale-n55.jpg` and `data/sources/assets/trowbridge_sauganash_hotel/gale-n49.jpg` | Public domain by independently verified 1902 US publication | Unmodified InternetArchive page scans of W. E. S. Trowbridge illustrations in Edwin O. Gale, *Reminiscences of Early Chicago and Vicinity* (Fleming H. Revell Company,1902), facing printed pp. 35 and31. Exact URLs/hashes in adjacent manifests; actual title/copyright proof shared with `trowbridge_first_jail_gale_1902`. Retrospective 1835 caption does not establish July 1835 fitting dates, metrics, colours or modern stock reproduction licences. |


## T-3055 first Tremont reconstructed arch name

The optional baked TREMONT paint strokes are original project GPL-3.0-or-later procedural geometry, adapting six existing prairie_draft.GLYPHS capitals locally through MeshBuilder. No external font, photograph or source-image pixels are baked. The independently known house name bounds the explicit reconstructed word; Gifford/Chicagology remains owner-approved attributed reference use, with no claim of a legible original inscription or public-domain finding. Exact glyph/colour/placement choices and source limits are recorded in L-tremont-reconstructed-arch-name-2385.

## Eye-UV-v1 planted-standing derivative amendment (T-2800)

The historical b479 entry above describes the preserved previous stage. The current separately versioned selection is d4544c2845256858dfa614235bcb37cb964ab63095a53a2436225182cefbb914,3,784,176bytes, `horse-sevket-v16-planted-standing-eye-uv-v1.glb`. Its eye UV10/bounds and derivative notice change; source texture pixels, other UVs, material records, geometry, rig and planted animation are exact b479 data. Reconstructed gaze/pupil is an adaptation under the same sevketkabatas Horse CC BY4.0 source credit and Objaverse database notice, not attested Chicago anatomy or photographic completion. The preceding unchanged-UV statements apply to the historical b479 stage only. Fresh d454 loaded129 CPU qualification is distinct from historical b479 results; neither certifies native/mobile/GPU/world/photographic quality.

|Path relative to assets/|License and provenance|
|---|---|
|`authored/transport/horse_standing/horse-sevket-v16-planted-standing-eye-uv-v1.glb`|CC-BY-4.0 derivative of Horse by sevketkabatas; exact changes in ADAPTATION.md.|
|`authored/transport/horse_standing/generate_eye_uv_v1.py`|Project-authored UV recipe/source-aperture evidence/protection receipt; source mesh/image rights and author credit remain CC-BY-4.0.|
|`authored/transport/horse_standing/eye-uv-v1-source-aperture-rays.json`|Project-authored UV recipe/source-aperture evidence/protection receipt; source mesh/image rights and author credit remain CC-BY-4.0.|
|`authored/transport/horse_standing/eye-uv-v1-boundary-receipt.json`|Project-authored UV recipe/source-aperture evidence/protection receipt; source mesh/image rights and author credit remain CC-BY-4.0.|
|`authored/transport/horse_standing/eye-uv-v1-derivation-receipt.json`|Project-authored UV recipe/source-aperture evidence/protection receipt; source mesh/image rights and author credit remain CC-BY-4.0.|

Byte-identical current runtime copy: `renderers/web/transport/standing-horse/horse-sevket-v16-planted-standing-eye-uv-v1.glb`. Protected b479 authored/runtime files and original receipts remain unchanged.

## V19 catalogue-guided Brougham body and finish (T-3084)

Original GPL-3.0-or-later source and generated geometry: `tools/transport/brougham/{generate.py,body_finish.py,body_geometry.py,build_body.py,parameters.json,quarter_surface.py,source_details.py,index_streams.py,static_master.py,LICENSE}` and `renderers/web/transport/parked-brougham/`. Current near raw SHA256 `fbe0f9b3d60c69ff85678b877a7d5c5e86fea05262d5fe13cfe246687e6b2d45`, indexed SHA256 `80bdf8a64ff2205de6575675f81efce7de0a6d41f45f934e3730f454cc1ab87f` (45,338triangles); mid raw SHA256 `5fa3a2127a805c52d040e17c533105ce43c545bcb3903f1ea717afb52c429694`, indexed SHA256 `6b8134c697c5538a004ca34e0a5a5822377b3e16d856ee098e1422bdf290fb2f` (23,062triangles). Both are deterministic original source exports with lossless indexing, freshly validated by gltf-validator2.0.0-dev.3.10 with0errors/0warnings. No external geometry, source pixels or texture images are embedded.

Appearance reference remains the cleared public-domain1893 Studebaker catalogue Brougham leaf0095, source `studebaker_1893_illustrated_souvenir`, plate SHA256 `b458565ec06ba1e8e59d1455cc2d3f277c2371910b3085c2085749fc59a68abe`. Native model studies are original project renders. Dark green/black colour families and narrow bright lining are visible in the colour plate; metric dimensions, hidden/opposite construction, empty upholstery, wood species, lacquer pigments/optics and physical glass coefficients are reconstructed. Maker/type availability does not identify an actual1904 specimen or household. Original V18 lamp geometry/materials and physical interfaces are preserved. V18 source/contracts/metadata remain under `archive-v18/`; its original GLBs remain in accepted cb93 Git history. Final source-camera/published/phone/world budget and photographic acceptance remain pending; T-3085's later qualification is not claimed here.

### V19 C1 front-slope output amendment (T-3084,2026-10-26)

Current near raw SHA256 `50f56eed76942ed65b232dfa005912e2587184020aca5b058837a8b4d41c3635`, indexed `5bbdb1932074b0bddfa72afc99f34773a0fb337cb02480136deb8fe65ef0cec0`; mid raw `d2e2452b04f63c366a8debac88833d7ca21ef9f6a8031d57c240b600e3740b0a`, indexed `90e258c14ea9201b055e1862066c28077ea4ee48d699b9ca59928a371c13bcc3`. Same original GPL source and public-domain1893 plate, no embedded source pixels. Limited continuous front slopes replace the previous fbe0 candidate; source-bearing values, interval envelope, V18 lamps/physical interfaces remain protected. Fresh four raw/indexed validator reports retain0errors/0warnings. Earlier image evidence is explicitly PRE-C1; current native/photographic/published qualification remains pending.

### Analytical-front-normal-only current output (T-3084,2026-10-26)

Near raw `206cd7a9141896361abd312ce73cd4de0e0868eca532b097a995a0488fa3dfe4`, indexed `3d2f3a802f4b32dba6a3e61f2c188dddce4db05cecfcbba81e1e8d369d5dfe89`; mid raw `560373980cc70524c4f85071fb4e3df6bc29df8a884f3dc17960fabcaa625f9d`, indexed `d5cdd34e981d29db41634ac780c22526742f6a20527b5866d2349c727a67400d`. Original GPL geometry/source and the same cleared1893plate. All priorC1POSITION streams remain exact; only owned front NORMAL changes, with inverse-transpose body scaling and separate thin-rim normals. Current actual close-up is source-bound; older17-image proofs remain historical. No new geometry source, texture image, source pixel, pigment attestation or photographic/published acceptance is introduced.


### Optical-only V19 runtime delivery (T-3084, 2026-10-26)

`renderers/web/transport/parked-brougham/brougham-near-delivery-v1.glb` (SHA256 `b5b183b4f115c5c7779ba0cb4ccba83fbffb62349647a9a6487f50cde49aef77`) and `brougham-mid-delivery-v1.glb` (`16daaf1d5003aae3ea64de9d037962aaabf2a5c8638ac77a5a2e037564ef2d63`) are original GPL-3.0-or-later optical derivatives of the retained indexed V19 masters. Canonical source is `tools/transport/brougham/generate_optical_delivery.mjs`; `OPTICAL-DELIVERY-RECEIPT.json` records its exact producer/source bindings. Every BIN byte, geometry/layout/node/scene value and material0–6 remains exact; 45,338/23,062 triangles and eight batches are retained. Only cabin glass uses the declared reconstructed BLEND/0.14-opacity/zero-transmission/IOR1.5 delivery approximation. All four physical raw/indexed masters remain unchanged, including their separate0.98-transmission optics. No new geometry, pixels, textures or outside material rights are introduced; the same cleared1893 catalogue/source limits apply. Actual source-bound diagnostic images are project renders and retain their NONPASS whole-budget result; a source derivative or Full-only allowance is not photographic/Light/memory acceptance.

## T-3088 source-bounded horse anatomy authoring

The anatomy recipes derive from the preserved selected d454 standing horse above,
under the same sevketkabatas **CC-BY-4.0** credit, source URL and change-notice
requirements. Existing source images, repaired eye UVs, acquired original,
b479 and d454 parent files remain preserved. The project-authored recipe code
and bounds are **GPL-3.0-or-later**; no claim is made that a software licence
replaces the model's attribution licence.

|Path relative to assets/|Licence and provenance|
|---|---|
|`authored/transport/horse_standing/generate_anatomy_v1.py`|Project-authored GPL-3.0-or-later source-only smooth rest-surface recipe; parent mesh rights remain CC-BY-4.0.|
|`authored/transport/horse_standing/anatomy-v1-recipe.json`|Project-authored reconstructed source bounds and exact reference-image bindings; no reference pixels copied into the model.|
|`authored/transport/horse_standing/generate_anatomy_v2.py`|Project-authored GPL-3.0-or-later canonical authored-mesh derivation with immutable-parent and live-field lineage.|
|`authored/transport/horse_standing/anatomy_topology_v2.py`|Project-authored GPL-3.0-or-later adaptive hoof-wall/coronet/toe subdivision and bounded fairing; generated geometry remains an attributed CC-BY-4.0 model derivative.|
|`authored/transport/horse_standing/anatomy-v2-recipe.json`|Project-authored reconstructed anatomy/topology choices, per-feature source IDs, confidence and immutable reference hashes.|
|`authored/transport/horse_standing/ANATOMY.md`|Project-authored source, reconstruction, authoring and acceptance boundary notice; original model attribution remains separate.|
|`authored/transport/horse_standing/horse-sevket-anatomy-v2.glb`|CC-BY-4.0 derivative of sevketkabatas' Horse; reconstructed eyelid and hoof topology changes declared in ANATOMY.md and the versioned recipe. Repaired eye UVs and original six image payloads retain the source rights and credit.|

The anatomy runtime copy is byte-identical at
`renderers/web/transport/standing-horse/horse-sevket-anatomy-v2.glb`.
The original acquired model and b479/d454 authored parents and their old receipts
remain unchanged. Fresh selected-body Mixer129 physical proof is separate from
surface, LOD, world, device performance and photographic qualification.

The input plates by Ellenberger/Baum/Dittrich and Seton are recorded public-domain
anatomical works. The Vassil and Joselodos living-animal photographs are cleared
CC0 references. These supply anatomical relationships and visible continuity;
neither the modern animals' breeds/markings nor their dimensions become evidence
for an 1835 Chicago animal. Their pixels are not sampled into output textures.
The unchanged six model texture payloads retain the source model's CC-BY-4.0
provenance. Source recipes and uninstalled candidate generation do not constitute
native, physical, historical or photographic acceptance.


### T-1789 modular workwear source construction (canonical outputs pending)

`tools/human_period_wardrobe.py` is original project GPL-3.0-or-later code; the original graphical arrays generated by its garment returns, fitted buttons, short jacket/lapel and felt-hat constructors are dedicated CC0-1.0, as declared in `data/humans/recipes/worker_1835.json`. They use existing cleared CC0 MakeHuman body/hair components without copying upstream program logic. No new outside image/texture or rights-pending source is derived into an asset. Colors, materials and garment dimensions are original reconstructions. The currently committed human GLBs remain the prior outputs with their existing provenance; this source checkpoint does not relabel them as the new wardrobe. Canonical new masters/exports and their hashes/licenses must accompany their eventual integration.


### T-1789 original adult dress components and verified female source base

`assets/authored/humans/makehuman_hm08/prepared_adult_female_25.json`, its report and `adult_female_25.recipe.json` are original CC0-1.0 engineering derivatives of the same pinned MakeHuman graphical data. The three female-young category targets and header-only universal-female target preserve their upstream CC0 notices; exact upstream commit, source URLs, bytes and SHA256 are in `SOURCE-female.json`. The universal target has zero delta rows and is not claimed as a deformation. Upstream category labels are software provenance, not an inference of a resident ancestry. Existing MakeHuman graphical/license notices remain unchanged.

Generated bodice, skirt, apron and low-shoe arrays from `tools/human_dress_components.py` are original CC0-1.0 geometry. Generator/test code is GPL-3.0-or-later. Cuts, cloth dimensions, color and drape are reconstructed, not traced from a historical pattern or painting. The held credited public-domain Wild1835 Cincinnati image is a narrow cross-check via source wild_1835_third_vine; no image pixel enters any texture or asset. Generic cleared skin/hair components retain their existing source notices and remain unqualified for photographic female appearance.

| Path relative to assets/ | Licence and provenance |
|---|---|
| `authored/humans/makehuman_hm08/SOURCE-female.json` | Project-authored CC0-1.0 graphical-source provenance, exact official upstream hashes and notices. |
| `authored/humans/makehuman_hm08/adult_female_25.recipe.json` | Original CC0-1.0 graphical blend recipe; reconstructed engineering parameters, no resident ancestry or portrait. |
| `authored/humans/makehuman_hm08/prepared_adult_female_25.json` | CC0-1.0 engineering derivative of verified MakeHuman graphical data; complete anatomy/UV/rig retained. |
| `authored/humans/makehuman_hm08/prepared_adult_female_25.report.json` | Project-authored CC0-1.0 preparation measurements and explicit unqualified limitations. |
| `authored/humans/makehuman_hm08/makehuman/data/targets/macrodetails/african-female-young.target` | Verbatim MakeHuman graphical asset, CC0-1.0 explicit upstream header; original credit retained, pinned commit/URL/hash in SOURCE-female.json. |
| `authored/humans/makehuman_hm08/makehuman/data/targets/macrodetails/asian-female-young.target` | Verbatim MakeHuman graphical asset, CC0-1.0 explicit upstream header; original credit retained, pinned commit/URL/hash in SOURCE-female.json. |
| `authored/humans/makehuman_hm08/makehuman/data/targets/macrodetails/caucasian-female-young.target` | Verbatim MakeHuman graphical asset, CC0-1.0 explicit upstream header; original credit retained, pinned commit/URL/hash in SOURCE-female.json. |
| `authored/humans/makehuman_hm08/makehuman/data/targets/macrodetails/universal-female-young-averagemuscle-averageweight.target` | Verbatim MakeHuman graphical asset, CC0-1.0 explicit upstream header; original credit retained, pinned commit/URL/hash in SOURCE-female.json. |


## Licensed Old Cart farm-box development master — T-2793

| Path | License and attribution | Scope |
|---|---|---|
| `authored/transport/farm_box_master_v1/old-cart-original.glb` | **CC BY4.0**, “Old Cart” by Lyskilde (longtail), https://sketchfab.com/longtail; https://sketchfab.com/3d-models/old-cart-f536745fd82144eeb5cc4900a48e816e; https://creativecommons.org/licenses/by/4.0/ | Exact unchanged9,809,548B original, SHA25613600b73c1777545e1454d452c58d141469f031b2c5e6c29b1c6fdefe9145046. Individual author/model/Objaverse credit retained in ORIGINAL-CREDIT.json. Modern artistic source; no maker, historical date, Chicago presence or original metric calibration. |
| `authored/transport/farm_box_master_v1/{ORIGINAL-CREDIT.json,ATTRIBUTION.md}` | Saved individual source rights metadata and project attribution/change notice | Credits accompany the artist-authored geometry, UVs and maps; producer-code SPDX does not replace these rights. |
| `renderers/web/transport/farm-box-master/` licensed wagon derivatives | **CC BY4.0** adaptation of Lyskilde/longtail's Old Cart, exact original author/source/license extras retained | Explicit Chicago changes: metre/axis calibration, independently circular front/rear wheels, neutralised source front-steer pose, reconstructed single pole and central bearing, articulated frames and proposed unloaded interfaces. No source texture pixels are repainted in the near master. Compression/LOD changes are disclosed in their actual export receipts. |

The Python/JS producer and preview code are original project GPL-3.0-or-later. The credited source geometry/maps and their derivatives retain CC BY4.0; neither a code header nor the project author's source changes erase the original credit. See L-farm-box-licensed-master-2793.

Exact authored paths for the same credited CC BY4.0 adaptation above:

| Path relative to assets/ | License and provenance |
|---|---|
| `authored/transport/farm_box_master_v1/ORIGINAL-CREDIT.json` | Unmodified individual source attribution/rights metadata; original Old Cart author and CC BY4.0 license retained. |
| `authored/transport/farm_box_master_v1/ATTRIBUTION.md` | Project adaptation notice retaining Old Cart by Lyskilde/longtail, CC BY4.0. |
| `authored/transport/farm_box_master_v1/SOURCE.json` | Project provenance/derivation inventory; licensed underlying geometry/maps remain CC BY4.0. |
| `authored/transport/farm_box_master_v1/derived/farm-box-source.glb` | CC BY4.0 derivative of Old Cart by Lyskilde/longtail. Original image bytes retained in this authored master; web derivatives use separately measured WebP representations. |
| `authored/transport/farm_box_master_v1/derived/farm-box-source.json` | Engine-neutral reconstruction/attribution/ownership sidecar accompanying that CC BY4.0 geometry. |

The optional muted warm finish multiplies existing source material colors; it
adds no texture maps and identifies no historic paint, timber species or finish.
It is an explicit reconstructed display alternative. The default weathered
finish retains source material factors. Source geometry/UVs/maps remain CC BY4.0;
producer/checker code is GPL-3.0-or-later project work. This amendment preserves
the earlier exact-pixel statements for the authored master: production WebP
images intentionally have bounded, recorded codec loss rather than byte identity.

Exact reconstructed-fit limitation: the retained artist kingbolt axis is 4.994mm eccentric from the tyre-centre yaw frame (XZ+1.925/+4.609mm), moving0.697mm over an8degree turn. No exact coaxial/strength claim. Original rims retain at most2.617mm radial ground irregularity; this is not a perfect-circle/suspension simulation.

The final farm-box master also includes an actual central90x55mm coupling reach, reconstructed from the same licensed shaft surface/UVs and separately owned in vehicle_reach. Its end connections are geometry-checked against the fixed front bolster and rear axle. The actual original28-triangle kingbolt is separately owned in vehicle_kingbolt; this is a component split, not an empty proxy or a hidden change to source surfaces. Both remain CC BY4.0 derivatives with the same author credit; fit/strength/historic-design limits remain reconstruction.
