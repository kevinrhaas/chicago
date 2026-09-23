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
derivative (ROADMAP K39).

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

*(none yet — the first entries will arrive with textures and ambience audio)*

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
| `gltf/recon_1835_*__inferred_1835.glb` and matching `web/` derivatives | `generators/inferred_placeholder.py` from the matching `data/structures/recon_1835_*.json` record | project license | Pure-Python review massing for the 108 anonymous inferred roofs. Every file self-identifies as a placeholder and is replaced, not silently promoted, when the canonical family bake lands. |

`authored/` holds hero assets that cannot come from a structure record (Fort Dearborn
detailing, signboards). They are exempt from regeneration but **not** from provenance:
each needs a row here and a source record explaining what the form is based on.
