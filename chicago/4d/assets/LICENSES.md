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
16-bit displacement. The `.webp` beside fourteen of the maps is a lossless derivative of
its PNG master, the same pixels in fewer bytes, written and held pixel-identical by
`tools/web_textures.py` (T-1973). Those fourteen are the one exception to "not published":
`tools/publish.sh` copies them by name to `data/textures/`, where the relief modules bind them.
They carry the library's licence and its one condition unchanged.

Every file, as the checker matches them one by one:

```
textures/chicago_1835_pbr/LICENSE.txt
textures/chicago_1835_pbr/README.md
textures/chicago_1835_pbr/RESEARCH_NOTES.md
textures/chicago_1835_pbr/contact_sheet.jpg
textures/chicago_1835_pbr/ground/lake_michigan_dune_sand/lake_michigan_dune_sand_ao.png
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
textures/chicago_1835_pbr/props/signboard_weathered/signboard_weathered_basecolor.webp
textures/chicago_1835_pbr/props/signboard_weathered/signboard_weathered_height16.png
textures/chicago_1835_pbr/props/signboard_weathered/signboard_weathered_metallic.png
textures/chicago_1835_pbr/props/signboard_weathered/signboard_weathered_normal_dx.png
textures/chicago_1835_pbr/props/signboard_weathered/signboard_weathered_normal_gl.png
textures/chicago_1835_pbr/props/signboard_weathered/signboard_weathered_normal_gl.webp
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
textures/chicago_1835_pbr/roofs/roof_boards_weathered/roof_boards_weathered_normal_gl.png
textures/chicago_1835_pbr/roofs/roof_boards_weathered/roof_boards_weathered_normal_gl.webp
textures/chicago_1835_pbr/roofs/roof_boards_weathered/roof_boards_weathered_orm.png
textures/chicago_1835_pbr/roofs/roof_boards_weathered/roof_boards_weathered_orm.webp
textures/chicago_1835_pbr/roofs/roof_boards_weathered/roof_boards_weathered_roughness.png
textures/chicago_1835_pbr/roofs/wood_shingles_weathered/material.json
textures/chicago_1835_pbr/roofs/wood_shingles_weathered/wood_shingles_weathered_ao.png
textures/chicago_1835_pbr/roofs/wood_shingles_weathered/wood_shingles_weathered_basecolor.png
textures/chicago_1835_pbr/roofs/wood_shingles_weathered/wood_shingles_weathered_height16.png
textures/chicago_1835_pbr/roofs/wood_shingles_weathered/wood_shingles_weathered_metallic.png
textures/chicago_1835_pbr/roofs/wood_shingles_weathered/wood_shingles_weathered_normal_dx.png
textures/chicago_1835_pbr/roofs/wood_shingles_weathered/wood_shingles_weathered_normal_gl.png
textures/chicago_1835_pbr/roofs/wood_shingles_weathered/wood_shingles_weathered_normal_gl.webp
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
textures/chicago_1835_pbr/timber/heavy_timber_weathered/heavy_timber_weathered_basecolor.webp
textures/chicago_1835_pbr/timber/heavy_timber_weathered/heavy_timber_weathered_height16.png
textures/chicago_1835_pbr/timber/heavy_timber_weathered/heavy_timber_weathered_metallic.png
textures/chicago_1835_pbr/timber/heavy_timber_weathered/heavy_timber_weathered_normal_dx.png
textures/chicago_1835_pbr/timber/heavy_timber_weathered/heavy_timber_weathered_normal_gl.png
textures/chicago_1835_pbr/timber/heavy_timber_weathered/heavy_timber_weathered_normal_gl.webp
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
textures/chicago_1835_pbr/walls/clapboard_board_face/clapboard_board_face_height16.png
textures/chicago_1835_pbr/walls/clapboard_board_face/clapboard_board_face_metallic.png
textures/chicago_1835_pbr/walls/clapboard_board_face/clapboard_board_face_normal_dx.png
textures/chicago_1835_pbr/walls/clapboard_board_face/clapboard_board_face_normal_gl.png
textures/chicago_1835_pbr/walls/clapboard_board_face/clapboard_board_face_normal_gl.webp
textures/chicago_1835_pbr/walls/clapboard_board_face/clapboard_board_face_orm.png
textures/chicago_1835_pbr/walls/clapboard_board_face/clapboard_board_face_orm.webp
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
textures/chicago_1835_pbr/walls/hewn_log_face/hewn_log_face_normal_gl.webp
textures/chicago_1835_pbr/walls/hewn_log_face/hewn_log_face_orm.png
textures/chicago_1835_pbr/walls/hewn_log_face/hewn_log_face_orm.webp
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

Every file, as the checker matches them one by one:

```
textures/prairie_1904_pbr/LICENSE.txt
textures/prairie_1904_pbr/README.md
textures/prairie_1904_pbr/alley/earth_and_cinders/earth_and_cinders_ao.png
textures/prairie_1904_pbr/alley/earth_and_cinders/earth_and_cinders_basecolor.png
textures/prairie_1904_pbr/alley/earth_and_cinders/earth_and_cinders_basecolor_web.jpg
textures/prairie_1904_pbr/alley/earth_and_cinders/earth_and_cinders_height16.png
textures/prairie_1904_pbr/alley/earth_and_cinders/earth_and_cinders_metallic.png
textures/prairie_1904_pbr/alley/earth_and_cinders/earth_and_cinders_normal_dx.png
textures/prairie_1904_pbr/alley/earth_and_cinders/earth_and_cinders_normal_gl.png
textures/prairie_1904_pbr/alley/earth_and_cinders/earth_and_cinders_normal_gl_web.jpg
textures/prairie_1904_pbr/alley/earth_and_cinders/earth_and_cinders_orm.png
textures/prairie_1904_pbr/alley/earth_and_cinders/earth_and_cinders_orm_web.jpg
textures/prairie_1904_pbr/alley/earth_and_cinders/earth_and_cinders_roughness.png
textures/prairie_1904_pbr/alley/earth_and_cinders/material.json
textures/prairie_1904_pbr/contact_sheet.jpg
textures/prairie_1904_pbr/curb/sandstone_curbstone/material.json
textures/prairie_1904_pbr/curb/sandstone_curbstone/sandstone_curbstone_ao.png
textures/prairie_1904_pbr/curb/sandstone_curbstone/sandstone_curbstone_basecolor.png
textures/prairie_1904_pbr/curb/sandstone_curbstone/sandstone_curbstone_basecolor_web.jpg
textures/prairie_1904_pbr/curb/sandstone_curbstone/sandstone_curbstone_height16.png
textures/prairie_1904_pbr/curb/sandstone_curbstone/sandstone_curbstone_metallic.png
textures/prairie_1904_pbr/curb/sandstone_curbstone/sandstone_curbstone_normal_dx.png
textures/prairie_1904_pbr/curb/sandstone_curbstone/sandstone_curbstone_normal_gl.png
textures/prairie_1904_pbr/curb/sandstone_curbstone/sandstone_curbstone_normal_gl_web.jpg
textures/prairie_1904_pbr/curb/sandstone_curbstone/sandstone_curbstone_orm.png
textures/prairie_1904_pbr/curb/sandstone_curbstone/sandstone_curbstone_orm_web.jpg
textures/prairie_1904_pbr/curb/sandstone_curbstone/sandstone_curbstone_roughness.png
textures/prairie_1904_pbr/parkway/grass_plat/grass_plat_ao.png
textures/prairie_1904_pbr/parkway/grass_plat/grass_plat_basecolor.png
textures/prairie_1904_pbr/parkway/grass_plat/grass_plat_basecolor_web.jpg
textures/prairie_1904_pbr/parkway/grass_plat/grass_plat_height16.png
textures/prairie_1904_pbr/parkway/grass_plat/grass_plat_metallic.png
textures/prairie_1904_pbr/parkway/grass_plat/grass_plat_normal_dx.png
textures/prairie_1904_pbr/parkway/grass_plat/grass_plat_normal_gl.png
textures/prairie_1904_pbr/parkway/grass_plat/grass_plat_normal_gl_web.jpg
textures/prairie_1904_pbr/parkway/grass_plat/grass_plat_orm.png
textures/prairie_1904_pbr/parkway/grass_plat/grass_plat_orm_web.jpg
textures/prairie_1904_pbr/parkway/grass_plat/grass_plat_roughness.png
textures/prairie_1904_pbr/parkway/grass_plat/material.json
textures/prairie_1904_pbr/roadway/macadam_limestone/macadam_limestone_ao.png
textures/prairie_1904_pbr/roadway/macadam_limestone/macadam_limestone_basecolor.png
textures/prairie_1904_pbr/roadway/macadam_limestone/macadam_limestone_basecolor_web.jpg
textures/prairie_1904_pbr/roadway/macadam_limestone/macadam_limestone_height16.png
textures/prairie_1904_pbr/roadway/macadam_limestone/macadam_limestone_metallic.png
textures/prairie_1904_pbr/roadway/macadam_limestone/macadam_limestone_normal_dx.png
textures/prairie_1904_pbr/roadway/macadam_limestone/macadam_limestone_normal_gl.png
textures/prairie_1904_pbr/roadway/macadam_limestone/macadam_limestone_normal_gl_web.jpg
textures/prairie_1904_pbr/roadway/macadam_limestone/macadam_limestone_orm.png
textures/prairie_1904_pbr/roadway/macadam_limestone/macadam_limestone_orm_web.jpg
textures/prairie_1904_pbr/roadway/macadam_limestone/macadam_limestone_roughness.png
textures/prairie_1904_pbr/roadway/macadam_limestone/material.json
textures/prairie_1904_pbr/roadway/sheet_asphalt/material.json
textures/prairie_1904_pbr/roadway/sheet_asphalt/sheet_asphalt_ao.png
textures/prairie_1904_pbr/roadway/sheet_asphalt/sheet_asphalt_basecolor.png
textures/prairie_1904_pbr/roadway/sheet_asphalt/sheet_asphalt_basecolor_web.jpg
textures/prairie_1904_pbr/roadway/sheet_asphalt/sheet_asphalt_height16.png
textures/prairie_1904_pbr/roadway/sheet_asphalt/sheet_asphalt_metallic.png
textures/prairie_1904_pbr/roadway/sheet_asphalt/sheet_asphalt_normal_dx.png
textures/prairie_1904_pbr/roadway/sheet_asphalt/sheet_asphalt_normal_gl.png
textures/prairie_1904_pbr/roadway/sheet_asphalt/sheet_asphalt_normal_gl_web.jpg
textures/prairie_1904_pbr/roadway/sheet_asphalt/sheet_asphalt_orm.png
textures/prairie_1904_pbr/roadway/sheet_asphalt/sheet_asphalt_orm_web.jpg
textures/prairie_1904_pbr/roadway/sheet_asphalt/sheet_asphalt_roughness.png
textures/prairie_1904_pbr/roadway/vitrified_paving_brick/material.json
textures/prairie_1904_pbr/roadway/vitrified_paving_brick/vitrified_paving_brick_ao.png
textures/prairie_1904_pbr/roadway/vitrified_paving_brick/vitrified_paving_brick_basecolor.png
textures/prairie_1904_pbr/roadway/vitrified_paving_brick/vitrified_paving_brick_basecolor_web.jpg
textures/prairie_1904_pbr/roadway/vitrified_paving_brick/vitrified_paving_brick_height16.png
textures/prairie_1904_pbr/roadway/vitrified_paving_brick/vitrified_paving_brick_metallic.png
textures/prairie_1904_pbr/roadway/vitrified_paving_brick/vitrified_paving_brick_normal_dx.png
textures/prairie_1904_pbr/roadway/vitrified_paving_brick/vitrified_paving_brick_normal_gl.png
textures/prairie_1904_pbr/roadway/vitrified_paving_brick/vitrified_paving_brick_normal_gl_web.jpg
textures/prairie_1904_pbr/roadway/vitrified_paving_brick/vitrified_paving_brick_orm.png
textures/prairie_1904_pbr/roadway/vitrified_paving_brick/vitrified_paving_brick_orm_web.jpg
textures/prairie_1904_pbr/roadway/vitrified_paving_brick/vitrified_paving_brick_roughness.png
textures/prairie_1904_pbr/tools/generate_prairie_1904_pbr.py
textures/prairie_1904_pbr/walk/portland_cement_walk/material.json
textures/prairie_1904_pbr/walk/portland_cement_walk/portland_cement_walk_ao.png
textures/prairie_1904_pbr/walk/portland_cement_walk/portland_cement_walk_basecolor.png
textures/prairie_1904_pbr/walk/portland_cement_walk/portland_cement_walk_basecolor_web.jpg
textures/prairie_1904_pbr/walk/portland_cement_walk/portland_cement_walk_height16.png
textures/prairie_1904_pbr/walk/portland_cement_walk/portland_cement_walk_metallic.png
textures/prairie_1904_pbr/walk/portland_cement_walk/portland_cement_walk_normal_dx.png
textures/prairie_1904_pbr/walk/portland_cement_walk/portland_cement_walk_normal_gl.png
textures/prairie_1904_pbr/walk/portland_cement_walk/portland_cement_walk_normal_gl_web.jpg
textures/prairie_1904_pbr/walk/portland_cement_walk/portland_cement_walk_orm.png
textures/prairie_1904_pbr/walk/portland_cement_walk/portland_cement_walk_orm_web.jpg
textures/prairie_1904_pbr/walk/portland_cement_walk/portland_cement_walk_roughness.png
```

### The Prairie Avenue 1904 stone library (K02) — `textures/prairie_1904_stone/`

T-2288, piece 1 of T-1844. Six procedural stone fabrics for the 1904 programme's walls, trim and
foundations (rock-faced granite, brown sandstone, Lemont and Bedford limestone, dressed trim,
foundation rubble), built by the generator that ships inside it
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
textures/prairie_1904_stone/tools/generate_prairie_1904_stone.py
```

| path | source | license | notes |
|---|---|---|---|

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
| `gltf/recon_1835_*__inferred_1835.glb` and matching `web/` derivatives | `generators/inferred_placeholder.py` from the matching `data/structures/recon_1835_*.json` record | project license | Pure-Python review massing for the 108 anonymous inferred roofs. Every file self-identifies as a placeholder and is replaced, not silently promoted, when the canonical family bake lands. |

`authored/` holds hero assets that cannot come from a structure record (Fort Dearborn
detailing, signboards). They are exempt from regeneration but **not** from provenance:
each needs a row here and a source record explaining what the form is based on.
### Glessner House v4 original surface studies

The following 43 files are original project material assets: eleven deterministic numeric PBR fabrics, three unchanged original generated albedo studies, their executable recipe and provenance. No historical, owner, Google or other third-party image pixels are sampled or embedded. Numeric maps are reproduced by `generate.py`; generated image prompts, hashes, methods and reconstructed confidence are preserved in the three provenance JSON files. Exact appearance is reconstructed, not historical evidence. Use, modification and redistribution with this project are permitted under the accompanying `LICENSE.txt`; retain provenance and confidence.

- `textures/glessner-v4/LICENSE.txt`
- `textures/glessner-v4/README.md`
- `textures/glessner-v4/brick_basecolor.jpg`
- `textures/glessner-v4/brick_normal.png`
- `textures/glessner-v4/brick_roughness.png`
- `textures/glessner-v4/copper_basecolor.jpg`
- `textures/glessner-v4/copper_normal.png`
- `textures/glessner-v4/copper_roughness.png`
- `textures/glessner-v4/generate.py`
- `textures/glessner-v4/granite_basecolor.jpg`
- `textures/glessner-v4/granite_normal.png`
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
